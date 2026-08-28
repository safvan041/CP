import faiss
import pickle
import numpy as np
import os
from django.conf import settings

EMBEDDING_BATCH_SIZE = 8


def _get_vector_store_paths(index_name: str):
    faiss_file_name = f"{index_name}.faiss"
    pkl_file_name = f"{index_name}.pkl"
    subdir = settings.BASE_DIR / "faiss_data" / index_name
    return subdir / faiss_file_name, subdir / pkl_file_name


def embed_and_store(chunks, index_name, model):
    batch = []
    stored_chunks = []
    index = None
    for chunk in chunks:
        if not isinstance(chunk, str) or not chunk.strip():
            continue
        batch.append(chunk)
        if len(batch) < EMBEDDING_BATCH_SIZE:
            continue

        embeddings = np.asarray(model.encode(batch), dtype="float32")
        if index is None:
            index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        stored_chunks.extend(batch)
        batch = []

    if batch:
        embeddings = np.asarray(model.encode(batch), dtype="float32")
        if index is None:
            index = faiss.IndexFlatL2(embeddings.shape[1])
        index.add(embeddings)
        stored_chunks.extend(batch)

    if index is None or index.ntotal == 0:
        print("Warning: No embeddings were created.")
        return 0

    faiss_path, pkl_path = _get_vector_store_paths(index_name)
    os.makedirs(faiss_path.parent, exist_ok=True)
    faiss.write_index(index, str(faiss_path))
    with open(str(pkl_path), "wb") as file:
        pickle.dump(stored_chunks, file)
    return index.ntotal


def search_similar_chunks(query, index_name, model, top_k=1):
    faiss_path, pkl_path = _get_vector_store_paths(index_name)
    if not faiss_path.exists() or not pkl_path.exists():
        return ["Knowledge base not found or not embedded."]
    try:
        index = faiss.read_index(str(faiss_path))
        with open(str(pkl_path), "rb") as file:
            texts = pickle.load(file)
    except Exception as error:
        print(f"Error loading FAISS files from local paths: {error}")
        return ["Error processing knowledge base data."]

    if index is None or not texts or index.ntotal == 0:
        return ["No data in knowledge base."]
    query_vec = model.encode([query]).astype("float32")
    _, indices = index.search(query_vec, min(top_k, index.ntotal))
    results = [texts[i] for i in indices[0] if 0 <= i < len(texts)]
    return results if results else ["No relevant results found."]


def delete_vector_store(index_name: str):
    faiss_path, pkl_path = _get_vector_store_paths(index_name)

    for file_path in [faiss_path, pkl_path]:
        if file_path.exists():
            os.remove(str(file_path))
    if faiss_path.parent.exists() and not os.listdir(faiss_path.parent):
        os.rmdir(str(faiss_path.parent))