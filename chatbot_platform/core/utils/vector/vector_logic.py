# core/utils/vector/vector_logic.py

import faiss
import pickle
import numpy as np
import os
import tempfile
from django.conf import settings
from google.cloud import storage

# --- GCS Helper Functions ---

def _get_gcs_client():
    project_id = getattr(settings, "GS_PROJECT_ID", None)
    # If project_id is "None" string (from default config), treat as None
    return storage.Client(project=project_id if project_id and project_id != "None" else None)

def _upload_blob(bucket_name, source_file_name, destination_blob_name):
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    try:
        blob.upload_from_filename(source_file_name)
        print(f"Uploaded {source_file_name} to gs://{bucket_name}/{destination_blob_name}")
    except Exception as e:
        print(f"GCS upload failed for {destination_blob_name}: {e}")
        raise

def _download_blob(bucket_name, source_blob_name, destination_file_name):
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    try:
        blob.download_to_filename(destination_file_name)
        print(f"Downloaded gs://{bucket_name}/{source_blob_name} to {destination_file_name}")
    except Exception as e:
        print(f"GCS download failed for {source_blob_name}: {e}")
        raise

# --- Path Helper (Crucial for consistency) ---
def _get_vector_store_paths(index_name: str, use_gcs: bool):
    """
    Generates the expected file paths/keys for FAISS index and pickle files.
    Ensures consistency across save, load, and delete operations.
    """
    faiss_file_name = f"{index_name}.faiss"
    pkl_file_name = f"{index_name}.pkl"

    if use_gcs:
        # GCS keys include index_name as a subdirectory
        # Use settings.GS_FAISS_PREFIX for the top-level folder in GCS
        gcs_base_prefix = getattr(settings, "GS_FAISS_PREFIX", "faiss_indices/")
        faiss_key = f"{gcs_base_prefix}{index_name}/{faiss_file_name}"
        pkl_key = f"{gcs_base_prefix}{index_name}/{pkl_file_name}"
        return faiss_key, pkl_key
    else:
        # Local paths relative to BASE_DIR and into 'faiss_data' directory
        local_base_dir = settings.BASE_DIR / "faiss_data"
        subdir = local_base_dir / index_name
        return subdir / faiss_file_name, subdir / pkl_file_name

# --- embed_and_store (Modified to use _get_vector_store_paths) ---
def embed_and_store(chunks, index_name, model):
    if not isinstance(chunks, list) or not all(isinstance(c, str) for c in chunks):
        print("Error: 'chunks' must be a list of strings")
        return

    # Ensure chunks are not empty to avoid issues with model.encode
    if not chunks:
        print("Warning: Chunks list is empty. No embeddings will be created.")
        return

    embeddings = np.array(model.encode(chunks)).astype("float32")

    if embeddings.shape[0] == 0:
        print("Warning: No embeddings created from chunks after encoding.")
        return

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    print(f"FAISS index created for {index_name} with {index.ntotal} vectors.")

    use_gcs = getattr(settings, "USE_GCS", False)
    faiss_path, pkl_path = _get_vector_store_paths(index_name, use_gcs)

    if use_gcs:
        bucket_name = getattr(settings, "GS_BUCKET_NAME", None)
        if not bucket_name:
            raise ValueError("GS_BUCKET_NAME must be set in settings for GCS operations.")

        # Use temporary files for GCS upload/download
        with tempfile.TemporaryDirectory() as tmpdir:
            local_faiss_temp = os.path.join(tmpdir, f"{index_name}.faiss")
            local_pkl_temp = os.path.join(tmpdir, f"{index_name}.pkl")

            faiss.write_index(index, local_faiss_temp)
            with open(local_pkl_temp, "wb") as f:
                pickle.dump(chunks, f)

            _upload_blob(bucket_name, local_faiss_temp, str(faiss_path))
            _upload_blob(bucket_name, local_pkl_temp, str(pkl_path))
            print(f"FAISS index and chunks saved to GCS: {faiss_path}, {pkl_path}")
    else:
        # Local paths are PurePath objects, convert to string for os.makedirs, open, faiss.write_index
        os.makedirs(faiss_path.parent, exist_ok=True)

        faiss.write_index(index, str(faiss_path))
        with open(str(pkl_path), "wb") as f:
            pickle.dump(chunks, f)
        print(f"FAISS index and chunks saved locally at {faiss_path.parent}/")


# --- search_similar_chunks (Modified to use _get_vector_store_paths) ---
def search_similar_chunks(query, index_name, model, top_k=1):
    use_gcs = getattr(settings, "USE_GCS", False)
    faiss_file_path, pkl_file_path = _get_vector_store_paths(index_name, use_gcs)

    index = None
    texts = None

    if use_gcs:
        bucket_name = getattr(settings, "GS_BUCKET_NAME", None)
        if not bucket_name:
            print("Error: GS_BUCKET_NAME not set for GCS operations.")
            return ["Error retrieving knowledge base."]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            local_faiss_temp = os.path.join(tmpdir, f"{index_name}.faiss")
            local_pkl_temp = os.path.join(tmpdir, f"{index_name}.pkl")
            
            try:
                _download_blob(bucket_name, str(faiss_file_path), local_faiss_temp)
                _download_blob(bucket_name, str(pkl_file_path), local_pkl_temp)
            except Exception as e:
                print(f"Error downloading FAISS files from GCS: {e}")
                return ["Knowledge base not found or error accessing cloud storage."]

            try:
                index = faiss.read_index(local_faiss_temp)
                with open(local_pkl_temp, "rb") as f:
                    texts = pickle.load(f)
            except Exception as e:
                print(f"Error loading FAISS files from temporary paths: {e}")
                return ["Error processing knowledge base data."]
    else:
        if not faiss_file_path.exists() or not pkl_file_path.exists():
            print(f"FAISS index or chunks not found locally at {faiss_file_path.parent}")
            return ["Knowledge base not found or not embedded."]
        
        try:
            index = faiss.read_index(str(faiss_file_path))
            with open(str(pkl_file_path), "rb") as f:
                texts = pickle.load(f)
        except Exception as e:
            print(f"Error loading FAISS files from local paths: {e}")
            return ["Error processing knowledge base data."]

    if index is None or texts is None or not texts:
        return ["No data in knowledge base."]

    query_vec = model.encode([query]).astype("float32")

    if index.ntotal == 0:
        return ["Knowledge base is empty."]

    actual_top_k = min(top_k, index.ntotal)
    D, I = index.search(query_vec, actual_top_k)
    
    # Ensure indices 'I' are valid before accessing 'texts'
    results = [texts[i] for i in I[0] if i >= 0 and i < len(texts)]

    return results if results else ["No relevant results found."]

# --- delete_vector_store (Crucially fixed to use _get_vector_store_paths) ---
def delete_vector_store(index_name: str):
    """Deletes both FAISS index and chunk file from GCS or local disk based on storage mode."""
    use_gcs = getattr(settings, "USE_GCS", False)
    faiss_file_path, pkl_file_path = _get_vector_store_paths(index_name, use_gcs)

    if use_gcs:
        client = _get_gcs_client()
        bucket_name = getattr(settings, "GS_BUCKET_NAME", None)
        if not bucket_name:
            print("Error: GS_BUCKET_NAME not set for GCS operations. Cannot delete remote files.")
            return # Or raise an error to indicate critical failure
        bucket = client.bucket(bucket_name)

        # The GCS paths are the full blob keys generated by _get_vector_store_paths
        for blob_key in [str(faiss_file_path), str(pkl_file_path)]:
            try:
                blob = bucket.blob(blob_key)
                if blob.exists(): # Check if blob exists before trying to delete
                    blob.delete()
                    print(f"Deleted GCS blob: gs://{bucket_name}/{blob_key}")
                else:
                    print(f"GCS blob not found (skipping deletion): {blob_key}")
            except Exception as e:
                print(f"Failed to delete GCS blob {blob_key}: {e}")
                # Log this error but don't stop the process if other file exists.
    else:
        # Local paths are Path objects from _get_vector_store_paths
        parent_dir = faiss_file_path.parent # Get the directory Path object
        
        for local_file_path in [faiss_file_path, pkl_file_path]:
            if local_file_path.exists():
                try:
                    os.remove(str(local_file_path)) # Convert Path object to string for os.remove
                    print(f"Deleted local file: {local_file_path}")
                except OSError as e:
                    print(f"Failed to delete local file {local_file_path}: {e}")
            else:
                print(f"Local file not found (skipping deletion): {local_file_path}")

        # After deleting files, attempt to remove the empty subdirectory
        # Check if the parent directory still exists and is empty
        if parent_dir.exists() and not os.listdir(parent_dir):
            try:
                os.rmdir(str(parent_dir)) # Convert Path object to string for os.rmdir
                print(f"Deleted empty local directory: {parent_dir}")
            except OSError as e:
                print(f"Failed to delete empty directory {parent_dir}: {e}")