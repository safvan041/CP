# embeddings/embedding_service.py

from sentence_transformers import SentenceTransformer

def get_embedding_model():
    # You can change the model name based on your needs
    return SentenceTransformer('all-MiniLM-L6-v2')
