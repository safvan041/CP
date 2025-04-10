# utils/vector_logic.py
import sys
import os

# Ensure root directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faiss
import pickle
import numpy as np

VECTOR_DIR = 'vectorstore'  # Folder for storing FAISS indexes

def embed_and_store(texts, index_name, model):
    """Embeds and stores texts into a FAISS index along with raw text."""
    if not os.path.exists(VECTOR_DIR):
        os.makedirs(VECTOR_DIR)

    embeddings = model.encode(texts)
    embeddings = np.array(embeddings).astype("float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, os.path.join(VECTOR_DIR, f"{index_name}.index"))

    with open(os.path.join(VECTOR_DIR, f"{index_name}.pkl"), 'wb') as f:
        pickle.dump(texts, f)

    return True

def search_similar_chunks(query, index_name, model, top_k=1):
    """Search for top-k most similar chunks for a given query."""
    index_path = os.path.join(VECTOR_DIR, f"{index_name}.index")
    text_path = os.path.join(VECTOR_DIR, f"{index_name}.pkl")

    if not os.path.exists(index_path) or not os.path.exists(text_path):
        return ["Vector index or associated texts not found."]

    index = faiss.read_index(index_path)
    with open(text_path, 'rb') as f:
        texts = pickle.load(f)

    query_vec = model.encode([query]).astype("float32")
    D, I = index.search(query_vec, top_k)

    results = [texts[i] for i in I[0] if i < len(texts)]
    return results
