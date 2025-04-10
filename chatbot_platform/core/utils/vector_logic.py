# utils/vector_logic.py
import sys
import os

# Ensure root directory is in the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import faiss
import pickle
import numpy as np
from embeddings.embedding_service import get_embedding_model

VECTOR_DIR = 'vectorstore'  # Folder for storing FAISS indexes

# Load model globally so it's reused
model = get_embedding_model()

def embed_and_store(texts, index_name):
    # Ensure vectorstore directory exists
    if not os.path.exists(VECTOR_DIR):
        os.makedirs(VECTOR_DIR)

    # Create embeddings
    embeddings = model.encode(texts)
    embeddings = np.array(embeddings).astype("float32")

    # Create FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Save FAISS index
    faiss.write_index(index, os.path.join(VECTOR_DIR, f"{index_name}.index"))

    # Save raw texts
    with open(os.path.join(VECTOR_DIR, f"{index_name}.pkl"), 'wb') as f:
        pickle.dump(texts, f)

    return True
