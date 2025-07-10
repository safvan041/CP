import faiss
import pickle
import numpy as np
import os
import tempfile
from django.conf import settings
from google.cloud import storage

# --- GCS Helper Functions ---

def _get_gcs_client():
    return storage.Client(project=getattr(settings, "GS_PROJECT_ID", None))

def _upload_blob(bucket_name, source_file_name, destination_blob_name):
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    try:
        blob.upload_from_filename(source_file_name)
        print(f"Uploaded {source_file_name} to gs://{bucket_name}/{destination_blob_name}")
    except Exception as e:
        print(f"GCS upload failed: {e}")
        raise

def _download_blob(bucket_name, source_blob_name, destination_file_name):
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    try:
        blob.download_to_filename(destination_file_name)
        print(f"Downloaded gs://{bucket_name}/{source_blob_name} to {destination_file_name}")
    except Exception as e:
        print(f"GCS download failed: {e}")
        raise

# --- Core Functions ---

def embed_and_store(chunks, index_name, model):
    if not isinstance(chunks, list) or not all(isinstance(c, str) for c in chunks):
        print("'chunks' must be a list of strings")
        return

    embeddings = np.array(model.encode(chunks)).astype("float32")

    if embeddings.shape[0] == 0:
        print("No embeddings created.")
        return

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    print(f"FAISS index created for {index_name} with {index.ntotal} vectors.")

    if getattr(settings, "USE_GCS", False):
        gcs_faiss_blob = f"faiss_indices/{index_name}/{index_name}.faiss"
        gcs_chunks_blob = f"faiss_indices/{index_name}/{index_name}.pkl"

        with tempfile.TemporaryDirectory() as tmpdir:
            faiss_path = os.path.join(tmpdir, f"{index_name}.faiss")
            chunks_path = os.path.join(tmpdir, f"{index_name}.pkl")

            faiss.write_index(index, faiss_path)
            with open(chunks_path, "wb") as f:
                pickle.dump(chunks, f)

            _upload_blob(settings.GS_BUCKET_NAME, faiss_path, gcs_faiss_blob)
            _upload_blob(settings.GS_BUCKET_NAME, chunks_path, gcs_chunks_blob)
    else:
        subdir = settings.BASE_DIR / "faiss_data" / index_name
        os.makedirs(subdir, exist_ok=True)

        faiss_path = subdir / f"{index_name}.faiss"
        chunks_path = subdir / f"{index_name}.pkl"

        faiss.write_index(index, str(faiss_path))
        with open(str(chunks_path), "wb") as f:
            pickle.dump(chunks, f)

        print(f"FAISS index and chunks saved locally at {subdir}/")

def search_similar_chunks(query, index_name, model, top_k=1):
    if getattr(settings, "USE_GCS", False):
        gcs_faiss_blob = f"faiss_indices/{index_name}/{index_name}.faiss"
        gcs_chunks_blob = f"faiss_indices/{index_name}/{index_name}.pkl"

        with tempfile.TemporaryDirectory() as tmpdir:
            faiss_path = os.path.join(tmpdir, f"{index_name}.faiss")
            chunks_path = os.path.join(tmpdir, f"{index_name}.pkl")

            _download_blob(settings.GS_BUCKET_NAME, gcs_faiss_blob, faiss_path)
            _download_blob(settings.GS_BUCKET_NAME, gcs_chunks_blob, chunks_path)

            index = faiss.read_index(faiss_path)
            with open(chunks_path, "rb") as f:
                texts = pickle.load(f)
    else:
        subdir = settings.BASE_DIR / "faiss_data" / index_name
        faiss_path = subdir / f"{index_name}.faiss"
        chunks_path = subdir / f"{index_name}.pkl"

        if not faiss_path.exists() or not chunks_path.exists():
            print("FAISS index or chunks not found locally.")
            return ["Knowledge base not found or not embedded."]

        index = faiss.read_index(str(faiss_path))
        with open(str(chunks_path), "rb") as f:
            texts = pickle.load(f)

    if not texts:
        return ["No data in knowledge base."]

    query_vec = model.encode([query]).astype("float32")

    actual_top_k = min(top_k, index.ntotal)
    if index.ntotal == 0:
        return ["Knowledge base is empty."]

    D, I = index.search(query_vec, actual_top_k)
    results = [texts[i] for i in I[0] if 0 <= i < len(texts)]

    return results if results else ["No relevant results found."]

def delete_vector_store(index_name):
    """Deletes both FAISS index and chunk file from GCS or local disk based on storage mode."""
    use_gcs = getattr(settings, "USE_GCS", False)

    if use_gcs:
        client = _get_gcs_client()
        bucket = client.bucket(settings.GS_BUCKET_NAME)
        for blob_name in [f"{index_name}/kb_index.faiss", f"{index_name}/kb_chunks.pkl"]:
            try:
                blob = bucket.blob(blob_name)
                blob.delete()
                print(f"Deleted blob: gs://{settings.GS_BUCKET_NAME}/{blob_name}")
            except Exception as e:
                print(f"Failed to delete GCS blob {blob_name}: {e}")
    else:
        base_path = os.path.join(settings.BASE_DIR, "faiss_indices", index_name)
        for suffix in ["kb_index.faiss", "kb_chunks.pkl"]:
            file_path = f"{base_path}/{suffix}"
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted local file: {file_path}")