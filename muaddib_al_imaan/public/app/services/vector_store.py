"""Vector storage: embeddings persisted in SQLite, FAISS index per fiqha.

Vectors are stored in the database (Chunk.embedding) as required, and a
FAISS index is built per fiqha for fast similarity search.
"""
import logging
import os
import pickle

import faiss
import numpy as np
from sqlalchemy.orm import Session

from app.config import EMBEDDING_BATCH_SIZE, FAISS_DIR, TOP_K
from app.models import Book, Chunk

logger = logging.getLogger(__name__)


def _faiss_path(fiqha: str) -> str:
    return os.path.join(str(FAISS_DIR), f"{fiqha}.faiss")


def _pkl_path(fiqha: str) -> str:
    return os.path.join(str(FAISS_DIR), f"{fiqha}.pkl")


def embed_and_store(db: Session, book: Book, chunks, model) -> int:
    """Embed chunks, persist them in the DB, and update the fiqha FAISS index.

    Returns the number of chunks stored.
    """
    batch = []
    stored = 0

    def flush():
        nonlocal stored
        if not batch:
            return
        embeddings = np.asarray(model.encode(batch), dtype="float32")
        for text, vec in zip(batch, embeddings):
            db.add(
                Chunk(
                    book_id=book.id,
                    fiqha=book.fiqha,
                    chunk_index=stored,
                    text=text,
                    embedding=vec.tobytes(),
                )
            )
            stored += 1
        batch.clear()

    for chunk in chunks:
        if not isinstance(chunk, str) or not chunk.strip():
            continue
        batch.append(chunk)
        if len(batch) >= EMBEDDING_BATCH_SIZE:
            flush()

    flush()
    db.commit()

    if stored == 0:
        logger.warning("No embeddings were created for book %s", book.id)
        return 0

    rebuild_fiqha_index(db, book.fiqha)
    return stored


def rebuild_fiqha_index(db: Session, fiqha: str) -> None:
    """Rebuild the FAISS index for a fiqha from DB-stored vectors."""
    chunks = db.query(Chunk).filter(Chunk.fiqha == fiqha).all()
    if not chunks:
        return

    vectors = np.asarray(
        [np.frombuffer(c.embedding, dtype="float32") for c in chunks],
        dtype="float32",
    )
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    os.makedirs(str(FAISS_DIR), exist_ok=True)
    faiss.write_index(index, _faiss_path(fiqha))
    with open(_pkl_path(fiqha), "wb") as f:
        pickle.dump([c.text for c in chunks], f)


def search_similar_chunks(db: Session, query, fiqha: str, model, top_k=TOP_K):
    """Search the fiqha FAISS index and return matching chunk texts."""
    faiss_file = _faiss_path(fiqha)
    pkl_file = _pkl_path(fiqha)

    if not os.path.exists(faiss_file) or not os.path.exists(pkl_file):
        return []

    index = faiss.read_index(faiss_file)
    with open(pkl_file, "rb") as f:
        texts = pickle.load(f)

    if index.ntotal == 0 or not texts:
        return []

    query_vec = model.encode([query]).astype("float32")
    _, indices = index.search(query_vec, min(top_k, index.ntotal))
    return [texts[i] for i in indices[0] if 0 <= i < len(texts)]