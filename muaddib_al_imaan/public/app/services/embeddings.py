"""NVIDIA embedding client."""
import logging

import numpy as np
import requests

from app.config import (
    NVIDIA_EMBEDDING_API_KEY,
    NVIDIA_EMBEDDING_BASE_URL,
    NVIDIA_EMBEDDING_MODEL,
)

logger = logging.getLogger(__name__)


class NvidiaEmbeddingModel:
    def __init__(self):
        self.api_key = NVIDIA_EMBEDDING_API_KEY
        self.base_url = NVIDIA_EMBEDDING_BASE_URL
        self.model = NVIDIA_EMBEDDING_MODEL

    def encode(self, texts):
        """Return float32 numpy array of embeddings for the given texts."""
        if isinstance(texts, str):
            texts = [texts]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "input": texts}
        endpoint = f"{self.base_url}/embeddings"

        response = requests.post(
            endpoint, json=payload, headers=headers, timeout=60
        )
        if response.status_code != 200:
            raise Exception(
                f"Embeddings API returned {response.status_code}: {response.text}"
            )

        data = response.json()
        if "data" not in data:
            raise ValueError(f"Unexpected API response format: {data}")

        embeddings = [item["embedding"] for item in data["data"]]
        return np.asarray(embeddings, dtype="float32")


def get_embedding_model():
    return NvidiaEmbeddingModel()