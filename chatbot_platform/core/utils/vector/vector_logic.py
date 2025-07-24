# core/utils/vector/vector_logic.py

import faiss
import pickle
import numpy as np
import os
import tempfile
import logging # NEW: Import logging
from pathlib import Path # NEW: For robust path handling

# Ensure these are installed if you plan to use LangChain text splitter
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter # NEW: For text splitting
    from langchain_core.documents import Document # NEW: For creating LangChain Document objects
except ImportError:
    RecursiveCharacterTextSplitter = None
    Document = None
    logging.warning("LangChain text_splitters not installed. Text splitting will be basic/not work.")


from django.conf import settings
from google.cloud import storage

logger = logging.getLogger(__name__) # NEW: Initialize logger

# --- GCS Helper Functions ---

def _get_gcs_client():
    project_id = getattr(settings, "GS_PROJECT_ID", None)
    return storage.Client(project=project_id if project_id and project_id != "None" else None)

def _upload_blob(bucket_name, source_file_name, destination_blob_name):
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    try:
        blob.upload_from_filename(source_file_name)
        logger.info(f"Uploaded {source_file_name} to gs://{bucket_name}/{destination_blob_name}") # Use logger
    except Exception as e:
        logger.error(f"GCS upload failed for {destination_blob_name}: {e}", exc_info=True) # Use logger
        raise

def _download_blob(bucket_name, source_blob_name, destination_file_name):
    client = _get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    try:
        blob.download_to_filename(destination_file_name)
        logger.info(f"Downloaded gs://{bucket_name}/{source_blob_name} to {destination_file_name}") # Use logger
    except Exception as e:
        logger.error(f"GCS download failed for {source_blob_name}: {e}", exc_info=True) # Use logger
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
        gcs_base_prefix = getattr(settings, "GS_FAISS_PREFIX", "faiss_indices/")
        faiss_key = Path(f"{gcs_base_prefix}{index_name}/{faiss_file_name}") # Use Path for consistency
        pkl_key = Path(f"{gcs_base_prefix}{index_name}/{pkl_file_name}") # Use Path for consistency
        return faiss_key, pkl_key
    else:
        local_base_dir = Path(settings.BASE_DIR) / "faiss_data" # Use Path for BASE_DIR
        subdir = local_base_dir / index_name
        return subdir / faiss_file_name, subdir / pkl_file_name

# --- embed_and_store (MODIFIED for Multi-File/Text Splitting) ---
def embed_and_store(all_extracted_texts: list[str], index_name: str, model): # Renamed 'chunks' to 'all_extracted_texts'
    """
    Combines text from multiple sources, splits into chunks, embeds, and stores in FAISS.
    Args:
        all_extracted_texts: A list of strings, where each string is text from one source file.
        index_name: Name for the FAISS index.
        model: Your HuggingFace/Gemini embedding model instance (e.g., from embedding_service.py).
               Assumes model.encode(list_of_strings) returns list of embeddings.
    """
    if not isinstance(all_extracted_texts, list) or not all(isinstance(t, str) for t in all_extracted_texts):
        logger.error("Error: 'all_extracted_texts' must be a list of strings.") # Use logger
        return # Or raise appropriate error

    # 1. Combine all texts into a single corpus
    combined_text = "\n\n".join(all_extracted_texts)

    # 2. Text Splitting
    if not combined_text.strip():
        logger.warning(f"Combined text for index {index_name} is empty. No embeddings will be created.") # Use logger
        return # No content to split/embed

    chunks = [] # This will be the list of smaller text chunks
    if RecursiveCharacterTextSplitter:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, # Adjust as needed
            chunk_overlap=200, # Adjust as needed
            length_function=len,
            add_start_index=True,
        )
        # LangChain text splitter expects a list of Document objects or strings
        # If you want to retain metadata per chunk, you'd make Document objects with metadata
        # For simplicity, passing combined text directly for splitting
        chunks = text_splitter.split_text(combined_text) # Use split_text for string input
    else:
        # Fallback if LangChain is not installed: simple splitting by paragraph/line
        # This is very basic, consider installing langchain-text-splitters
        chunks = [c.strip() for c in combined_text.split('\n\n') if c.strip()]
        if not chunks: # If simple split yields nothing
            chunks = [combined_text] # Use the whole text as one chunk

    if not chunks:
        logger.warning(f"No text chunks generated for index {index_name} after splitting.") # Use logger
        return

    # 3. Embedding
    try:
        # model.encode expects a list of strings and returns embeddings
        embeddings = np.array(model.encode(chunks)).astype("float32")
    except Exception as e:
        logger.error(f"Error encoding text chunks for index {index_name}: {e}", exc_info=True) # Use logger
        return # Or raise appropriate error

    if embeddings.shape[0] == 0:
        logger.warning(f"No embeddings created from chunks for index {index_name}.") # Use logger
        return

    # 4. FAISS Indexing
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    logger.info(f"FAISS index created for {index_name} with {index.ntotal} vectors from {len(chunks)} chunks.") # Use logger

    use_gcs = getattr(settings, "USE_GCS", False)
    faiss_path, pkl_path = _get_vector_store_paths(index_name, use_gcs)

    # 5. Save to Local or GCS
    if use_gcs:
        bucket_name = getattr(settings, "GS_BUCKET_NAME", None)
        if not bucket_name:
            logger.error("GS_BUCKET_NAME must be set in settings for GCS operations.") # Use logger
            raise ValueError("GS_BUCKET_NAME must be set in settings for GCS operations.")

        # Use temporary files for GCS upload/download
        with tempfile.TemporaryDirectory() as tmpdir:
            local_faiss_temp = os.path.join(tmpdir, faiss_path.name) # Use Path.name for just filename
            local_pkl_temp = os.path.join(tmpdir, pkl_path.name)

            faiss.write_index(index, local_faiss_temp)
            with open(local_pkl_temp, "wb") as f:
                pickle.dump(chunks, f) # Store the actual text chunks

            _upload_blob(bucket_name, local_faiss_temp, str(faiss_path))
            _upload_blob(bucket_name, local_pkl_temp, str(pkl_path))
            logger.info(f"FAISS index and chunks saved to GCS: {faiss_path}, {pkl_path}") # Use logger
    else:
        # Local paths are Path objects, ensure parent directory exists
        os.makedirs(faiss_path.parent, exist_ok=True)

        faiss.write_index(index, str(faiss_path))
        with open(str(pkl_path), "wb") as f:
            pickle.dump(chunks, f) # Store the actual text chunks
        logger.info(f"FAISS index and chunks saved locally at {faiss_path.parent}/") # Use logger


# --- search_similar_chunks (MODIFIED to use _get_vector_store_paths and proper loading) ---
def search_similar_chunks(query: str, index_name: str, model, top_k: int = 3): # Added type hints, top_k default
    use_gcs = getattr(settings, "USE_GCS", False)
    faiss_file_path, pkl_file_path = _get_vector_store_paths(index_name, use_gcs)

    index = None
    chunks_text = None # Renamed 'texts' to 'chunks_text' for clarity, as these are the smaller chunks

    if use_gcs:
        bucket_name = getattr(settings, "GS_BUCKET_NAME", None)
        if not bucket_name:
            logger.error("GS_BUCKET_NAME not set for GCS operations.") # Use logger
            return ["Error retrieving knowledge base."]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            local_faiss_temp = os.path.join(tmpdir, faiss_file_path.name)
            local_pkl_temp = os.path.join(tmpdir, pkl_file_path.name)
            
            try:
                _download_blob(bucket_name, str(faiss_file_path), local_faiss_temp)
                _download_blob(bucket_name, str(pkl_file_path), local_pkl_temp)
            except Exception as e:
                logger.error(f"Error downloading FAISS files from GCS: {e}", exc_info=True) # Use logger
                return ["Knowledge base not found or error accessing cloud storage."]

            try:
                index = faiss.read_index(local_faiss_temp)
                with open(local_pkl_temp, "rb") as f:
                    chunks_text = pickle.load(f) # Load the chunks
            except Exception as e:
                logger.error(f"Error loading FAISS files from temporary paths: {e}", exc_info=True) # Use logger
                return ["Error processing knowledge base data."]
    else:
        if not faiss_file_path.exists() or not pkl_file_path.exists():
            logger.warning(f"FAISS index or chunks not found locally at {faiss_file_path.parent}") # Use logger
            return ["Knowledge base not found or not embedded."]
        
        try:
            index = faiss.read_index(str(faiss_file_path))
            with open(str(pkl_file_path), "rb") as f:
                chunks_text = pickle.load(f) # Load the chunks
        except Exception as e:
            logger.error(f"Error loading FAISS files from local paths: {e}", exc_info=True) # Use logger
            return ["Error processing knowledge base data."]

    if index is None or chunks_text is None or not chunks_text:
        logger.warning(f"No data loaded from FAISS for index {index_name}.") # Use logger
        return ["No data in knowledge base."]

    # Encode query for search
    try:
        query_vec = model.encode([query]).astype("float32")
    except Exception as e:
        logger.error(f"Error encoding query '{query}' for FAISS search: {e}", exc_info=True)
        return ["Error processing your query."]


    if index.ntotal == 0:
        logger.warning(f"FAISS index {index_name} is empty (0 vectors).") # Use logger
        return ["Knowledge base is empty."]

    actual_top_k = min(top_k, index.ntotal)
    D, I = index.search(query_vec, actual_top_k)
    
    # Ensure indices 'I' are valid before accessing 'chunks_text'
    results = [chunks_text[i] for i in I[0] if i >= 0 and i < len(chunks_text)]

    return results if results else ["No relevant results found."]

# --- delete_vector_store (Logging and robustness improvements) ---
def delete_vector_store(index_name: str):
    """Deletes both FAISS index and chunk file from GCS or local disk based on storage mode."""
    use_gcs = getattr(settings, "USE_GCS", False)
    faiss_file_path, pkl_file_path = _get_vector_store_paths(index_name, use_gcs)

    if use_gcs:
        client = _get_gcs_client()
        bucket_name = getattr(settings, "GS_BUCKET_NAME", None)
        if not bucket_name:
            logger.error("GS_BUCKET_NAME not set for GCS operations. Cannot delete remote files.") # Use logger
            return # Or raise an error to indicate critical failure
        bucket = client.bucket(bucket_name)

        for blob_key in [str(faiss_file_path), str(pkl_file_path)]:
            try:
                blob = bucket.blob(blob_key)
                if blob.exists():
                    blob.delete()
                    logger.info(f"Deleted GCS blob: gs://{bucket_name}/{blob_key}") # Use logger
                else:
                    logger.warning(f"GCS blob not found (skipping deletion): {blob_key}") # Use logger
            except Exception as e:
                logger.error(f"Failed to delete GCS blob {blob_key}: {e}", exc_info=True) # Use logger
    else:
        parent_dir = faiss_file_path.parent
        
        # Check if the parent directory exists before iterating over files
        if parent_dir.exists():
            for local_file_path in [faiss_file_path, pkl_file_path]:
                if local_file_path.exists():
                    try:
                        os.remove(str(local_file_path))
                        logger.info(f"Deleted local file: {local_file_path}") # Use logger
                    except OSError as e:
                        logger.error(f"Failed to delete local file {local_file_path}: {e}", exc_info=True) # Use logger
                else:
                    logger.warning(f"Local file not found (skipping deletion): {local_file_path}") # Use logger

            # After deleting files, attempt to remove the empty subdirectory
            if parent_dir.exists() and not os.listdir(parent_dir):
                try:
                    os.rmdir(str(parent_dir))
                    logger.info(f"Deleted empty local directory: {parent_dir}") # Use logger
                except OSError as e:
                    logger.error(f"Failed to delete empty directory {parent_dir}: {e}", exc_info=True) # Use logger
        else:
            logger.warning(f"Local FAISS directory not found at {parent_dir} for deletion.") # Use logger