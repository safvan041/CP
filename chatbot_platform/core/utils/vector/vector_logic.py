# utils/vector_logic.py
import sys
import os

# Ensure root directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faiss
import pickle
import numpy as np

# Set base directory to chatbot_platform/vectorstore
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE_PATH = os.path.join(BASE_DIR, 'vectorstore')

def embed_and_store(chunks, index_name, model):
    os.makedirs(BASE_PATH, exist_ok=True)
    index_path = os.path.join(BASE_PATH, index_name)
    os.makedirs(index_path, exist_ok=True)

    # Step 1: Embed chunks
    embeddings = model.encode(chunks)

    # Step 2: Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))

    # Step 3: Save index
    faiss.write_index(index, os.path.join(index_path, "index.faiss"))

    # Step 4: Save chunks (to map back results later)
    with open(os.path.join(index_path, "chunks.pkl"), "wb") as f:
        pickle.dump(chunks, f)

    print(f"FAISS index and chunks stored at: {index_path}")

def search_similar_chunks(query, index_name, model, top_k=1):
    """Search for top-k most similar chunks for a given query."""
    index_path = os.path.join(BASE_PATH, index_name, "index.faiss")
    text_path = os.path.join(BASE_PATH, index_name, "chunks.pkl")

    if not os.path.exists(index_path) or not os.path.exists(text_path):
        return ["Vector index or associated texts not found."]

    index = faiss.read_index(index_path)
    with open(text_path, 'rb') as f:
        texts = pickle.load(f)

    query_vec = model.encode([query]).astype("float32")
    D, I = index.search(query_vec, top_k)

    results = [texts[i] for i in I[0] if i < len(texts)]
    # print("results--------\n",results)
    return results
