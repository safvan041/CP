import numpy as np
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class NvidiaEmbeddingModel:
    def __init__(self):
        self.api_key = settings.NVIDIA_EMBEDDING_API_KEY
        self.base_url = settings.NVIDIA_EMBEDDING_BASE_URL
        self.model = settings.NVIDIA_EMBEDDING_MODEL
        logger.info(
            f"NvidiaEmbeddingModel initialized with "
            f"base_url={self.base_url}, model={self.model}"
        )

    def encode(self, texts):
        """
        Get embeddings from NVIDIA API using the embeddings-specific API key
        """
        if isinstance(texts, str):
            texts = [texts]

        logger.info(
            f"Calling embeddings API with model={self.model}, texts count={len(texts)}"
        )

        try:
            # Prepare headers with embeddings API key
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # Prepare payload
            payload = {
                "model": self.model,
                "input": texts,
            }

            # Primary endpoint: /embeddings
            endpoint = f"{self.base_url}/embeddings"
            logger.debug(f"Attempting embeddings endpoint: {endpoint}")

            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=30,
            )

            logger.debug(f"Embeddings API response status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Extract embeddings from response
                if "data" in data:
                    embeddings = [item["embedding"] for item in data["data"]]
                    logger.debug(
                        f"Embeddings API response received: {len(embeddings)} embeddings"
                    )
                    return np.asarray(embeddings, dtype="float32")
                else:
                    logger.error(f"Unexpected response format: {data}")
                    raise ValueError(f"Unexpected API response format: {data}")
            else:
                logger.error(
                    f"Embeddings API error - Status: {response.status_code}, "
                    f"Response: {response.text}"
                )
                raise Exception(
                    f"Embeddings API returned {response.status_code}: {response.text}"
                )

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Network error calling embeddings API - URL: {endpoint}, Error: {e}",
                exc_info=True,
            )
            raise
        except Exception as e:
            logger.error(
                f"Embeddings API error - Base URL: {self.base_url}, "
                f"Model: {self.model}, API Key: {self.api_key[:20]}..., Error: {e}",
                exc_info=True,
            )
            raise


def get_embedding_model():
    return NvidiaEmbeddingModel()
