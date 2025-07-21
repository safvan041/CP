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

            # First, check if it's already completed (idempotency check for re-dispatch)
            if kb.is_embedded and kb.status == 'completed':
                logger.info(f"Task {self.request.id} - KB {kb_id} already completed. Skipping this task instance.")
                return # Task exits cleanly if already done

            # If it's already processing AND it's not a retry of this task,
            # it means another task instance (or a retry) is already handling it.
            # So, this task instance should yield.
            if kb.status == 'processing' and not self.request.retries:
                 logger.info(f"Task {self.request.id} - KB {kb_id} is already marked as 'processing'. Likely a duplicate dispatch or race. Skipping this instance.")
                 return # Task exits cleanly as another instance is expected to handle it

            # --- If we reach here, this task is the chosen one to actually perform the embedding ---
            # Set status to 'processing' NOW, inside the lock, before proceeding to actual work.
            kb.status = 'processing'
            kb.error_message = "" # Clear any previous error
            kb.save(update_fields=['status', 'error_message']) # Update immediately and commit lock
            logger.info(f"Task {self.request.id} - KB {kb_id} status updated to 'processing' by this task. Committing lock.")

        # --- ACTUAL PROCESSING STARTS HERE, OUTSIDE THE INITIAL TRANSACTION LOCK ---
        # The lock on the KB object is released once the with transaction.atomic(): block exits.
        # This means the heavy lifting of extraction and embedding can happen without holding the DB lock.
        logger.info(f"Proceeding with heavy lifting (extraction/embedding) for Knowledge Base: {kb.title} (ID: {kb_id}) - Task ID: {self.request.id}")

        # --- Extraction ---
        extracted_text = extract_text_from_file(kb.file)

        if extracted_text.startswith("Error:"):
            # Update status to failed, this will be a separate save operation
            # No need for another transaction.atomic() here unless you have other related DB changes
            kb.status = 'failed'
            kb.error_message = extracted_text
            kb.save(update_fields=['status', 'error_message'])
            logger.error(f"Error extracting text for KB {kb_id} ({kb.title}): {extracted_text}")
            return

        if not extracted_text.strip():
            kb.status = 'failed'
            kb.error_message = "The uploaded file has no readable text or is empty after extraction."
            kb.save(update_fields=['status', 'error_message'])
            logger.warning(f"No readable text in file for KB {kb_id} ({kb.title}).")
            return

        # --- Embedding ---
        model = get_embedding_model()
        vector_index_name = f"kb_{kb.id}"

        embed_and_store([extracted_text], vector_index_name, model)

        # --- Success ---
        # After successful embedding, update the KB to completed
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
        # Only mark as failed if it wasn't already successfully completed by this or another task
        if kb and kb.status != 'completed':
            kb.status = 'failed'
            kb.error_message = str(e)
            kb.save(update_fields=['status', 'error_message'])
        raise self.retry(exc=e) # Retries the task on failure