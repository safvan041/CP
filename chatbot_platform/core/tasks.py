# core/tasks.py

import logging
import uuid # For widget_slug generation
from celery import shared_task
from django.db.models import F # For atomic update

from core.models import KnowledgeBase
from core.utils.file_reader import extract_text_from_file
from core.utils.vector.vector_logic import embed_and_store # Ensure this is correct
from core.utils.embeddings.embedding_service import get_embedding_model # Ensure this is correct

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60) # Add retry logic
def process_knowledge_base_embedding(self, kb_id):
    kb = None # Initialize kb to None
    try:
        kb = KnowledgeBase.objects.get(pk=kb_id)

        # Skip if already embedded or currently processing (defensive)
        if kb.is_embedded and kb.status == 'completed':
            logger.info(f"Knowledge Base {kb_id} ({kb.title}) already completed. Skipping task.")
            return

        if kb.status == 'processing' and not self.request.retries: # Allow retries if it's a retry
             logger.info(f"Knowledge Base {kb_id} ({kb.title}) is already processing. Skipping new task for this KB.")
             return

        logger.info(f"Starting embedding for Knowledge Base: {kb.title} (ID: {kb_id}) - Task ID: {self.request.id}")

        # Ensure the status is 'processing' before starting
        kb.status = 'processing'
        kb.error_message = "" # Clear any previous error messages
        kb.save(update_fields=['status', 'error_message']) # Update only these fields atomically

        # --- Extraction ---
        extracted_text = extract_text_from_file(kb.file) # Pass FileField object directly

        if extracted_text.startswith("Error:"):
            kb.status = 'failed'
            kb.error_message = extracted_text # The specific error from extract_text_from_file
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

        # Assuming embed_and_store handles the entire process
        embed_and_store([extracted_text], vector_index_name, model)

        # --- Success ---
        # Generate slug only if not already set or if you want to regenerate on re-embedding
        if not kb.widget_slug:
            kb.widget_slug = str(uuid.uuid4())[:8] # Generates a unique 8-char slug

        kb.is_embedded = True
        kb.status = 'completed'
        kb.save(update_fields=['is_embedded', 'status', 'widget_slug'])
        logger.info(f"Knowledge Base {kb_id} ({kb.title}) embedded successfully.")

    except KnowledgeBase.DoesNotExist:
        logger.error(f"KnowledgeBase with ID {kb_id} not found in process_knowledge_base_embedding task.")
    except Exception as e:
        error_msg = f"Failed to embed knowledge base {kb_id} ({kb.title if kb else 'N/A'}): {e}"
        logger.error(error_msg, exc_info=True)
        if kb:
            kb.status = 'failed'
            kb.error_message = str(e) # Store the exception message
            kb.save(update_fields=['status', 'error_message'])
        # Optional: Retry the task on certain exceptions
        raise self.retry(exc=e, countdown=60)