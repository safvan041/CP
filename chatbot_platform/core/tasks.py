# core/tasks.py

import logging
import uuid
from celery import shared_task
from django.db import transaction
from django.db.models import F 

from core.models import KnowledgeBase
from core.utils.file_reader import extract_text_from_file
from core.utils.vector.vector_logic import embed_and_store
from core.utils.embeddings.embedding_service import get_embedding_model

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_knowledge_base_embedding(self, kb_id):
    try:
        logger.info(f"Task {self.request.id} received for KB {kb_id}. Attempting to get lock.")

        with transaction.atomic():
            kb = KnowledgeBase.objects.select_for_update().get(pk=kb_id)
            logger.info(f"Task {self.request.id} acquired lock for KB {kb_id}. Current status from DB: {kb.status}")

            if kb.is_embedded and kb.status == 'completed':
                logger.info(f"Task {self.request.id} - KB {kb_id} already completed. Skipping this task instance.")
                return

            if kb.status == 'processing' and not self.request.retries:
                 logger.info(f"Task {self.request.id} - KB {kb_id} is already marked as 'processing'. Likely a duplicate dispatch or race. Skipping this instance.")
                 return

            # If we reach here, this task is the chosen one to actually perform the embedding.
            kb.status = 'processing'
            kb.error_message = ""
            kb.save(update_fields=['status', 'error_message'])
            logger.info(f"Task {self.request.id} - KB {kb_id} status updated to 'processing' by this task. Committing lock.")

        logger.info(f"Proceeding with heavy lifting (extraction/embedding) for Knowledge Base: {kb.title} (ID: {kb_id}) - Task ID: {self.request.id}")

        # --- CRITICAL FIX: Extract text from ALL associated source files ---
        all_extracted_texts = []
        source_files_count = kb.source_files.count() # Get count of linked files
        if source_files_count == 0:
            kb.status = 'failed'
            kb.error_message = "No source files found for this Knowledge Base to embed."
            kb.save(update_fields=['status', 'error_message'])
            logger.error(f"KB {kb_id}: No source files found for embedding.")
            return

        for i, source_file_obj in enumerate(kb.source_files.all()):
            logger.debug(f"KB {kb_id}: Extracting text from file {i+1}/{source_files_count}: '{source_file_obj.filename}'")
            # extract_text_from_file expects a FileField object, so pass source_file_obj.file
            extracted_text = extract_text_from_file(source_file_obj.file) 

            if extracted_text.startswith("Error:"):
                kb.status = 'failed'
                kb.error_message = f"Failed to extract text from '{source_file_obj.filename}': {extracted_text}"
                kb.save(update_fields=['status', 'error_message'])
                logger.error(f"KB {kb_id}: Error extracting text from '{source_file_obj.filename}': {extracted_text}")
                return # Fail the whole KB if one file fails

            if not extracted_text.strip():
                logger.warning(f"KB {kb_id}: File '{source_file_obj.filename}' has no readable text or is empty.")
                # Decide if empty file should fail the KB or just be skipped.
                # For now, let's allow it to be empty, but log warning.
                # If you want to fail KB on empty, set status='failed' here and return.
                continue # Skip this file if empty, but proceed with others

            all_extracted_texts.append(extracted_text)

        if not all_extracted_texts: # If all files were empty or failed
            kb.status = 'failed'
            kb.error_message = "No readable text found in any uploaded files for this Knowledge Base."
            kb.save(update_fields=['status', 'error_message'])
            logger.error(f"KB {kb_id}: No readable text found in any source files.")
            return

        # --- Embedding ---
        model = get_embedding_model()
        vector_index_name = f"kb_{kb.id}"

        # Pass all_extracted_texts (a list of strings) to embed_and_store
        logger.info(f"KB {kb_id}: Starting embedding for {len(all_extracted_texts)} file(s) combined content.")
        embed_and_store(all_extracted_texts, vector_index_name, model) # Assuming embed_and_store can take list

        # --- Success ---
        if not kb.widget_slug:
            kb.widget_slug = str(uuid.uuid4())[:8]

        kb.is_embedded = True
        kb.status = 'completed'
        kb.save(update_fields=['is_embedded', 'status', 'widget_slug'])
        logger.info(f"Knowledge Base {kb_id} ({kb.title}) embedded successfully.")

    except KnowledgeBase.DoesNotExist:
        logger.error(f"KnowledgeBase with ID {kb_id} not found in process_knowledge_base_embedding task.")
    except Exception as e:
        error_msg = f"Failed to embed knowledge base {kb_id} ({kb.title if kb else 'N/A'}): {e}"
        logger.error(error_msg, exc_info=True)
        if kb and kb.status != 'completed':
            kb.status = 'failed'
            kb.error_message = str(e)
            kb.save(update_fields=['status', 'error_message'])
        raise self.retry(exc=e)