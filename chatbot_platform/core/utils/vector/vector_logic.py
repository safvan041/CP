# core/utils/vector/vector_logic.py

import faiss
import pickle
import numpy as np
import os
import tempfile # For creating temporary local files
# Import Django settings to access GCS_BUCKET_NAME etc.
from django.conf import settings
# Import Google Cloud Storage client library
from google.cloud import storage

# --- GCS Helper Functions (These will interact with your GCS bucket) ---

def _get_gcs_client():
    """Initializes and returns a Google Cloud Storage client."""
    # The client automatically picks up credentials from the environment
    # (e.g., service account in Cloud Run or Application Default Credentials locally)
    return storage.Client(project=settings.GS_PROJECT_ID)

def _upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to a GCS bucket."""
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    try:
        blob.upload_from_filename(source_file_name)
        print(f"File {source_file_name} uploaded to gs://{bucket_name}/{destination_blob_name}.")
    except Exception as e:
        print(f"Error uploading blob {source_file_name} to {destination_blob_name}: {e}")
        raise # Re-raise to signal failure

def _download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from a GCS bucket to a local file."""
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    try:
        blob.download_to_filename(destination_file_name)
        print(f"Blob gs://{bucket_name}/{source_blob_name} downloaded to {destination_file_name}.")
    except Exception as e:
        print(f"Error downloading blob {source_blob_name}: {e}")
        raise # Re-raise to signal failure


# --- FAISS Indexing and Storage Logic ---

def embed_and_store(chunks, index_name, model):
    """
    Embeds text chunks, builds a FAISS index, and saves both the index and
    the original chunks to Google Cloud Storage.
    """
    if not isinstance(chunks, list) or not all(isinstance(c, str) for c in chunks):
        print("Warning: 'chunks' should be a list of strings.")
        if not chunks:
            print("No chunks provided for processing.")
            return

    # Step 1: Embed chunks
    # Assuming model.encode() takes a list of strings and returns embeddings
    embeddings = model.encode(chunks)
    
    # Ensure embeddings are float32, which FAISS expects
    embeddings = np.array(embeddings).astype('float32')

    if embeddings.shape[0] == 0:
        print("No embeddings generated. FAISS index not created or stored.")
        return

    # Step 2: Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim) # Common choice, use your preferred FAISS index type
    index.add(embeddings)
    print(f"FAISS index created for {index_name} with {index.ntotal} vectors and dimension {dim}.")

    # Define GCS paths for the files
    # We'll store them under 'faiss_indices/' prefix in the bucket
    gcs_faiss_blob = f"faiss_indices/{index_name}.faiss"
    gcs_chunks_blob = f"faiss_indices/{index_name}.pkl"

    # Step 3 & 4: Save index and chunks to temporary local files, then upload to GCS
    # Use a temporary directory as FAISS expects local file paths for read/write
    with tempfile.TemporaryDirectory() as tmpdir:
        local_faiss_path = os.path.join(tmpdir, f"{index_name}.faiss")
        local_chunks_path = os.path.join(tmpdir, f"{index_name}.pkl")

        # Save FAISS index locally
        faiss.write_index(index, local_faiss_path)

        # Save chunks (original text) locally to map back results later
        with open(local_chunks_path, "wb") as f:
            pickle.dump(chunks, f) # Save the original chunks list

        try:
            # Upload the temporary files to GCS
            _upload_blob(settings.GS_BUCKET_NAME, local_faiss_path, gcs_faiss_blob)
            _upload_blob(settings.GS_BUCKET_NAME, local_chunks_path, gcs_chunks_blob)
            print(f"FAISS index and chunks for '{index_name}' successfully stored in GCS.")
        except Exception as e:
            print(f"Failed to upload FAISS index or chunks for '{index_name}' to GCS: {e}")
            raise # Re-raise error to signal failure to the calling view

def search_similar_chunks(query, index_name, model, top_k=1):
    """
    Searches for top-k most similar chunks for a given query by:
    1. Downloading FAISS index and original chunks from GCS.
    2. Loading them into memory.
    3. Encoding the query.
    4. Performing a FAISS search.
    5. Retrieving the relevant original text chunks.
    """
    # Define GCS paths for the files to download
    gcs_faiss_blob = f"faiss_indices/{index_name}.faiss"
    gcs_chunks_blob = f"faiss_indices/{index_name}.pkl"

    # Use a temporary directory for downloading files from GCS
    with tempfile.TemporaryDirectory() as tmpdir:
        local_faiss_path = os.path.join(tmpdir, f"{index_name}.faiss")
        local_chunks_path = os.path.join(tmpdir, f"{index_name}.pkl")

        try:
            # Step 1: Download FAISS index and chunks from GCS to temporary local files
            _download_blob(settings.GS_BUCKET_NAME, gcs_faiss_blob, local_faiss_path)
            _download_blob(settings.GS_BUCKET_NAME, gcs_chunks_blob, local_chunks_path)
        except Exception as e:
            print(f"Error downloading FAISS index or chunks for '{index_name}': {e}")
            return ["Error: Could not retrieve knowledge base. Please ensure it was embedded correctly."]

        # Step 2: Load FAISS index and original chunks from local temporary files
        try:
            index = faiss.read_index(local_faiss_path)
            with open(local_chunks_path, 'rb') as f:
                texts = pickle.load(f) # Load the original chunks list
            print(f"FAISS index and chunks for '{index_name}' loaded from GCS.")
        except Exception as e:
            print(f"Error loading FAISS index or chunks from local temp files for '{index_name}': {e}")
            return ["Error: Failed to load knowledge base content."]

        if not texts:
            print(f"No original text chunks found for index '{index_name}'.")
            return ["No relevant context found in this knowledge base."]

        # Step 3: Embed the query
        query_vec = model.encode([query]).astype("float32") # Assuming model.encode takes a list
        
        # Step 4: Perform search
        # Clamp top_k to the number of available vectors in the index if top_k is too high
        actual_top_k = min(top_k, index.ntotal)
        
        if index.ntotal == 0:
            print(f"FAISS index '{index_name}' is empty. No search can be performed.")
            return ["No relevant context found in this knowledge base (index empty)."]

        D, I = index.search(query_vec, actual_top_k)

        # Step 5: Retrieve relevant original text chunks
        results = []
        if I.size > 0: # Check if any results were found
            for idx in I[0]: # I[0] contains the indices of the top_k results for the first query
                if 0 <= idx < len(texts): # Ensure the index is within bounds of the original chunks
                    results.append(texts[idx])
                else:
                    print(f"Warning: FAISS returned out-of-bounds index {idx} for '{index_name}'.")

        if not results:
            return ["No relevant context found in this knowledge base."] # Or a more specific message

        print(f"Search completed for '{index_name}'. Found {len(results)} relevant chunks.")
        return results