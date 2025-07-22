# webapp/views.py

import os
import json
import uuid
import logging
# Removed: import shutil
# Removed: import tempfile
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
# Removed: from django.utils import timezone # No longer needed for custom lockout
# Removed: from datetime import timedelta # No longer needed for custom lockout
# Removed: from django.db.models import F # No longer needed for custom lockout

from webapp.forms import KnowledgeBaseForm, CustomUserCreationForm
from core.models import KnowledgeBase
# Removed: from core.models import FailedLoginAttempt # No longer needed for custom lockout

# If you decided to keep Celery setup, but it's not active due to resource:
# from core.tasks import process_knowledge_base_embedding

# Standard utility imports
from core.utils.file_reader import extract_text_from_file
from core.utils.vector.vector_logic import delete_vector_store as remove_faiss_data, embed_and_store, search_similar_chunks
from .utils.genai_llm import generate_genai_response
from core.utils.embeddings.embedding_service import get_embedding_model

logger = logging.getLogger(__name__)



def signup_view(request):
    """
    Handles user registration using CustomUserCreationForm for consistent password validation.
    """
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST) # Use the new form here
        if form.is_valid():
            user = form.save() # The form's save() method creates the user and hashes the password
            messages.success(request, "Account created successfully. Please log in.")
            logger.info(f"New user '{user.username}' signed up.")
            return redirect("login")
        else:
            # # If the form is invalid, its errors will contain validation messages
            # # from AUTH_PASSWORD_VALIDATORS and any custom clean methods (like unique email).
            # for field, errors in form.errors.items():
            #     for error in errors:
            #         # 'non_field_errors' is for errors not tied to a specific field (e.g., password mismatch)
            #         if field == '__all__': 
            #             messages.error(request, f"Error: {error}")
            #         else:
            #             messages.error(request, f"Error in {field}: {error}")
            messages.error(request, "There were errors in your registration. Please correct them and try again.")
    else:
        form = CustomUserCreationForm() # Initialize an empty form for GET requests

    return render(request, "webapp/signup.html", {"form": form})


def login_view(request):
    """
    Handles user login. django-axes will handle brute-force protection
    via its middleware.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        
        # All custom brute-force protection logic removed.
        # django-axes middleware automatically intercepts failed login attempts
        # and manages lockouts before this view's authentication.

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully!")
            # django-axes automatically clears its own records on successful login.
            logger.info(f"User '{username}' logged in successfully.")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid credentials")
            # django-axes automatically logs and tracks failed attempts here.
            logger.warning(f"Failed login attempt for username '{username}'.") 

    return render(request, "webapp/login.html")


def logout_view(request):
    messages.success(request, "Logged out successfully!")
    logout(request)
    return redirect("login")


@login_required
def dashboard_view(request):
    knowledge_bases = KnowledgeBase.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "webapp/dashboard.html", {"knowledge_bases": knowledge_bases})


@login_required
def home_view(request):
    """
    Handles uploading a single knowledge base file.
    Assumes KnowledgeBase model still has a 'file' field.
    """
    if request.method == "POST":
        form = KnowledgeBaseForm(request.POST, request.FILES)
        if form.is_valid():
            knowledge_base = form.save(commit=False)
            knowledge_base.user = request.user
            # Initial status will be 'uploaded' as per model default
            try:
                knowledge_base.save() # This is where file is saved to storage

                messages.success(request, "Knowledge base uploaded successfully!")
                return redirect("dashboard")
            except ValueError as ve:
                logger.error("Caught ValueError during file upload", exc_info=True)
                messages.error(request, f"Failed to save knowledge base: {ve}")
                return redirect("home")
            except NotImplementedError as e:
                logger.error("Caught NotImplementedError during file upload", exc_info=True)
                messages.error(request, "File upload failed to storage: {e} ")
                return redirect("dashboard")
            except Exception as e:
                logger.error(f"Caught unexpected exception during file upload: {type(e).__name__}", exc_info=True)
                messages.error(request, f"Failed to upload file to storage: {e}")
                return redirect("dashboard") # Or return to upload page with error
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
            messages.error(request, "There were errors in your form. Please correct them and try again.")
    else:
        form = KnowledgeBaseForm()
    return render(request, "webapp/home.html", {"form": form})


@login_required
def proceed_view(request, kb_id):
    """
    Handles processing (embedding) a single KnowledgeBase.
    This remains synchronous as per resource constraints.
    It will update the status and error_message fields on KnowledgeBase.
    """
    kb = get_object_or_404(KnowledgeBase, pk=kb_id, user=request.user)

    # Check if already completed or processing
    if kb.status == 'completed':
        messages.info(request, "Knowledge base is already embedded.")
        return redirect("dashboard")
    elif kb.status == 'processing':
        messages.info(request, "Knowledge base is already being processed.")
        return redirect("dashboard")

    # Set status to processing, clear old errors
    kb.status = 'processing'
    kb.error_message = ""
    kb.save(update_fields=['status', 'error_message']) # Update DB immediately

    try:
        # Assuming KnowledgeBase still has a 'file' field here
        if not hasattr(kb, 'file') or not kb.file: # Defensive check
            raise ValueError("Knowledge Base record has no associated file.")

        logger.info(f"Starting synchronous embedding for KB: {kb.title} (ID: {kb.id})")
        extracted_text = extract_text_from_file(kb.file)

        if extracted_text.startswith("Error:"):
            kb.status = 'failed'
            kb.error_message = extracted_text
            kb.save(update_fields=['status', 'error_message'])
            messages.error(request, extracted_text)
            logger.error(f"Text extraction failed for KB {kb.id}: {extracted_text}")
            return redirect("dashboard")

        if not extracted_text.strip():
            kb.status = 'failed'
            kb.error_message = "The uploaded file has no readable text or is empty."
            kb.save(update_fields=['status', 'error_message'])
            messages.warning(request, "The uploaded file has no readable text or is empty.")
            logger.warning(f"No readable text found for KB {kb.id}.")
            return redirect("dashboard")
        
        model = get_embedding_model()
        vector_index_name = f"kb_{kb.id}"

        embed_and_store([extracted_text], vector_index_name, model)

        kb.widget_slug = str(uuid.uuid4())[:8] # Generates a unique 8-char slug
        kb.is_embedded = True
        kb.status = 'completed'
        kb.save(update_fields=['is_embedded', 'widget_slug', 'status'])
        messages.success(request, "Knowledge base embedded successfully!")
        logger.info(f"KB {kb.id} ({kb.title}) embedded successfully.")

    except Exception as e:
        kb.status = 'failed'
        kb.error_message = str(e)
        kb.save(update_fields=['status', 'error_message'])
        messages.error(request, f"Failed to embed knowledge base: {e}")
        logger.error(f"Error during embedding for KB {kb.id}: {e}", exc_info=True)
        return redirect("dashboard")

    return redirect("dashboard") # Redirect to dashboard to show updated status


@login_required
@require_POST
def delete_kb_view(request, kb_id):
    kb = get_object_or_404(KnowledgeBase, id=kb_id, user=request.user)

    # Delete file from media storage (local or GCS)
    if hasattr(kb, 'file') and kb.file and kb.file.storage.exists(kb.file.name):
        kb.file.delete()
        logger.info(f"Deleted media file: {kb.file.name}")
    else:
        logger.warning(f"No file found to delete for KB ID {kb.id} (file field missing or empty).")

    # Delete associated FAISS index and chunk files
    index_name = f"kb_{kb.id}"
    remove_faiss_data(index_name)
    logger.info(f"Deleted FAISS data for index: {index_name}")

    # Delete from DB
    kb.delete()
    messages.success(request, f"Knowledge Base '{kb.title}' and associated data deleted successfully.")
    logger.info(f"KB '{kb.title}' (ID: {kb.id}) deleted from DB.")
    return redirect("dashboard")


def chat_widget_view(request, widget_slug):
    """
    Renders the chat widget iframe content.
    """
    kb = get_object_or_404(KnowledgeBase, widget_slug=widget_slug)
    return render(request, 'webapp/chat_widget.html', {'kb': kb})


@csrf_exempt
def chat_api_view(request, widget_slug):
    """
    Handles chat messages from the widget, performs RAG, and gets LLM response.
    This remains stateless for now (no history management).
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()

            if not user_message:
                return JsonResponse({'response': 'Please type a message.'}, status=200)

            kb = get_object_or_404(KnowledgeBase, widget_slug=widget_slug)
            model = get_embedding_model()
            index_name = f"kb_{kb.id}"

            # Perform RAG (Retrieval Augmented Generation)
            results = search_similar_chunks(user_message, index_name, model, top_k=3)
            context = "\n".join(results) if results else "No relevant information found."
            logger.debug(f"Retrieved context for '{user_message}': {context[:100]}...")

            # Generate LLM response
            # Note: generate_genai_response expects chat_history, so pass empty list or None
            response_content = generate_genai_response(context, user_message, chat_history=None)
            logger.info(f"Chatbot response for '{user_message}': {response_content[:100]}...")

            return JsonResponse({'response': response_content})

        except KnowledgeBase.DoesNotExist:
            logger.error(f"Chat API: KnowledgeBase with slug {widget_slug} not found.", exc_info=True)
            return JsonResponse({'error': 'Chatbot not found.'}, status=404)
        except json.JSONDecodeError:
            logger.error("Chat API: Invalid JSON in request body.", exc_info=True)
            return JsonResponse({'error': 'Invalid request body.'}, status=400)
        except Exception as e:
            logger.error(f"Chat API: An unexpected error occurred for widget {widget_slug}: {e}", exc_info=True)
            return JsonResponse({'error': 'An internal error occurred. Please try again.'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def chat_view(request, widget_slug):
    """
    Renders the full chat page (not the iframe widget).
    This also remains stateless for now.
    """
    kb = get_object_or_404(KnowledgeBase, widget_slug=widget_slug)
    index_name = f"kb_{kb.id}"
    chat_history = [] # Remains empty for stateless

    if request.method == "POST":
        user_query = request.POST.get("message", "").strip()
        if not user_query:
            bot_response = "Please type a message."
        else:
            retrieved_chunks = search_similar_chunks(user_query, index_name, get_embedding_model())
            context = "\n".join(retrieved_chunks) if retrieved_chunks else "No relevant information found."

            bot_response = generate_genai_response(context, user_query, chat_history=None) # No history passed here

        chat_history.append(("You", user_query))
        chat_history.append(("Bot", bot_response))
    else:
        bot_response = ""
        user_query = ""

    return render(request, "webapp/chat.html", {
        "knowledge_base": kb,
        "chat_history": chat_history,
    })


@login_required
def get_widget_api_view(request, widget_slug):
    """
    Provides the iframe embed code for a specific widget.
    """
    kb = get_object_or_404(KnowledgeBase, widget_slug=widget_slug, user=request.user)
    # Using request.build_absolute_uri to ensure correct scheme (http/https) and domain
    iframe_code = f'<iframe src="{request.build_absolute_uri(f"/chat/{kb.widget_slug}/")}" width="100%" height="500px" frameborder="0"></iframe>'
    return JsonResponse({"iframe_code": iframe_code})