#webapp/views.py

import os
import json
import uuid
import logging
import shutil
import tempfile
import base64 
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.files.base import ContentFile 
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import QueryDict
from django.views.decorators.http import require_GET



from webapp.forms import KnowledgeBaseForm
from core.models import KnowledgeBase, KnowledgeBaseSourceFile
from core.tasks import process_knowledge_base_embedding
from core.utils.file_reader import extract_text_from_file
from core.utils.vector.vector_logic import delete_vector_store as remove_faiss_data, embed_and_store, search_similar_chunks
from .utils.genai_llm import generate_genai_response
from core.utils.embeddings.embedding_service import get_embedding_model

logger = logging.getLogger(__name__)

def signup_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "Account created successfully. Please log in.")
            return redirect("login")

    return render(request, "webapp/signup.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid credentials")

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

@csrf_exempt 
def home_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error("JSONDecodeError in home_view: Invalid JSON payload on POST.")
            return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

        title = data.get('title', '').strip()
        files_data = data.get('files', []) # List of {filename, content_type, base64_content}
        
        # --- MANUAL VALIDATION AND PROCESSING OF FILES ---
        errors = {} # Collect errors for JSON response
        
        # 1. Validate title using the form (since it's still in the form)
        _post_data = QueryDict('', mutable=True)
        _post_data['title'] = title
        _post_data['csrfmiddlewaretoken'] = data.get('csrfmiddlewaretoken', '')
        
        form = KnowledgeBaseForm(_post_data) # Only validate title field now
        if not form.is_valid():
            errors.update(form.errors) # Add title errors

        # 2. Validate and process files manually
        _files_for_kb_creation = [] # This will hold InMemoryUploadedFile objects for DB save
        if not files_data:
            errors['files'] = ["No file was submitted. Please select at least one file."]
        else:
            allowed_extensions = ['.txt', '.pdf', '.docx'] # Define allowed extensions
            for i, file_info in enumerate(files_data):
                filename = file_info.get('filename')
                base64_content = file_info.get('base64_content')
                content_type = file_info.get('content_type')

                if not filename or not base64_content:
                    errors.setdefault('files', []).append(f"File {i+1}: Missing filename or content.")
                    continue # Skip to next file

                ext = '.' + filename.split('.')[-1].lower()
                if ext not in allowed_extensions:
                    errors.setdefault('files', []).append(f"File '{filename}': Unsupported type. Only {', '.join(allowed_extensions)} allowed.")
                    continue

                try:
                    decoded_file_content = base64.b64decode(base64_content)
                    
                    content_file = ContentFile(decoded_file_content, name=filename)
                    uploaded_file = InMemoryUploadedFile(
                        file=content_file,
                        field_name='files', # This is just a placeholder, not used by form anymore
                        name=filename,
                        content_type=content_type,
                        size=len(decoded_file_content),
                        charset=None
                    )
                    _files_for_kb_creation.append(uploaded_file)

                except Exception as e:
                    logger.error(f"Error decoding/processing file '{filename}': {e}", exc_info=True)
                    errors.setdefault('files', []).append(f"File '{filename}': Failed to process ({e}).")
                    continue
        
        # --- Check for overall errors before saving ---
        if errors:
            logger.warning(f"Manual form validation failed in home_view (POST): {json.dumps(errors)}")
            return JsonResponse({'errors': errors}, status=400) # Send 400 for validation errors

        # --- If no errors, proceed with saving to DB ---
        try:
            knowledge_base = KnowledgeBase.objects.create(
                user=request.user,
                title=title,
                status='uploaded'
            )
            logger.info(f"New Knowledge Base '{title}' (ID: {knowledge_base.id}) created by {request.user}.")

            for f in _files_for_kb_creation:
                source_file = KnowledgeBaseSourceFile.objects.create(
                    knowledge_base=knowledge_base,
                    file=f,
                    filename=f.name
                )
                logger.info(f"Saved source file '{source_file.filename}' for KB ID {knowledge_base.id}.")

            messages.success(request, f"Knowledge Base '{title}' uploaded successfully with {len(_files_for_kb_creation)} file(s).")
            return JsonResponse({
                'success': True,
                'message': f"Knowledge Base '{title}' uploaded successfully with {len(_files_for_kb_creation)} file(s).",
                'redirect_url': redirect('dashboard').url # Provide URL for frontend redirect
            }, status=200)
        
        except Exception as e:
            logger.error(f"Failed to save Knowledge Base or source files to DB: {e}", exc_info=True)
            if 'knowledge_base' in locals() and knowledge_base.pk:
                knowledge_base.delete() 
            return JsonResponse({'error': f"Failed to upload Knowledge Base: {e}"}, status=500)

    else: # This is a GET request
        form = KnowledgeBaseForm()
        return render(request, "webapp/home.html", {"form": form})

@login_required
def proceed_view(request, kb_id):
    kb = get_object_or_404(KnowledgeBase, pk=kb_id, user=request.user)

    # Check current status of the knowledge base
    # These checks are primarily for user feedback to prevent re-triggering tasks
    if kb.status == 'completed':
        messages.info(request, f"Knowledge base '{kb.title}' is already embedded.")
        return redirect("dashboard")
    elif kb.status == 'processing':
        messages.info(request, f"Knowledge base '{kb.title}' is currently being processed. Please check back shortly.")
        return redirect("dashboard")
    else: # status is 'uploaded' or 'failed' (can retry)
        try:
            process_knowledge_base_embedding.delay(kb.id)

            messages.success(request, f"Embedding process for '{kb.title}' has been initiated. Status will update shortly.")
        except Exception as e:
            logger.error(f"Failed to dispatch embedding task for KB {kb.id}: {e}", exc_info=True)
            messages.error(request, f"Failed to start embedding process for '{kb.title}': {e}. Please try again.")

    return redirect("dashboard")
    
@login_required
@require_POST
def delete_kb_view(request, kb_id):
    """
    Handles deleting a KnowledgeBase, its associated source files from storage,
    and its FAISS index.
    """
    kb = get_object_or_404(KnowledgeBase, id=kb_id, user=request.user)

    logger.info(f"Attempting to delete Knowledge Base '{kb.title}' (ID: {kb.id}).")

    deleted_files_count = 0
    for source_file in kb.source_files.all(): 

        if source_file.file and source_file.file.storage.exists(source_file.file.name):
            try:
                source_file.file.delete() # Delete the actual file from storage
                deleted_files_count += 1
                logger.info(f"Deleted source file: '{source_file.filename}' for KB ID {kb.id}.")
            except Exception as e:
                logger.error(f"Failed to delete file '{source_file.filename}' from storage for KB ID {kb.id}: {e}", exc_info=True)
        else:
            logger.warning(f"Source file '{source_file.filename}' for KB ID {kb.id} not found in storage or already deleted.")
    
    logger.info(f"Deleted {deleted_files_count} associated source file(s) from storage for KB ID {kb.id}.")



    # Delete associated FAISS index and chunk files
    index_name = f"kb_{kb.id}"
    remove_faiss_data(index_name) 
    logger.info(f"Deleted FAISS data for index: '{index_name}' for KB ID {kb.id}.")

    # Delete the KnowledgeBase record from the database
    kb.delete()
    messages.success(request, f"Knowledge Base '{kb.title}' and all associated data deleted successfully.")
    logger.info(f"Knowledge Base '{kb.title}' (ID: {kb.id}) deleted from DB.")
    return redirect("dashboard")


def chat_widget_view(request, widget_slug):
    kb = get_object_or_404(KnowledgeBase, widget_slug=widget_slug)
    return render(request, 'webapp/chat_widget.html', {'kb': kb})


@csrf_exempt
def chat_api_view(request, widget_slug):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')

        kb = get_object_or_404(KnowledgeBase, widget_slug=widget_slug)
        model = get_embedding_model()
        index_name = f"kb_{kb.id}"

        results = search_similar_chunks(user_message, index_name, model, top_k=3)
        context = "\n".join(results[:3]) if results else "No relevant information found."

        response = generate_genai_response(context, user_message)

        return JsonResponse({'response': response})

    return JsonResponse({'error': 'Invalid request'}, status=400)


def chat_view(request, widget_slug):
    kb = get_object_or_404(KnowledgeBase, widget_slug=widget_slug)
    index_name = f"kb_{kb.id}"
    chat_history = []

    if request.method == "POST":
        user_query = request.POST.get("message", "")
        retrieved_chunks = search_similar_chunks(user_query, index_name, get_embedding_model())
        context = "\n".join(retrieved_chunks)

        bot_response = generate_genai_response(context, user_query)

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
    kb = get_object_or_404(KnowledgeBase, widget_slug=widget_slug, user=request.user)
    iframe_code = f'<iframe src="{request.build_absolute_uri(f"/chat/{kb.widget_slug}/")}" width="100%" height="500px" frameborder="0"></iframe>'
    return JsonResponse({"iframe_code": iframe_code})


@login_required 
@require_GET 
def get_kb_status_api_view(request, kb_id):
    """
    Returns the current status of a specific KnowledgeBase as JSON.
    """
    try:
        kb = get_object_or_404(KnowledgeBase, pk=kb_id, user=request.user)
        return JsonResponse({
            'id': kb.id,
            'status': kb.status,
            'status_display': kb.get_status_display(), 
            'is_embedded': kb.is_embedded,
            'widget_slug': kb.widget_slug,
            'error_message': kb.error_message if kb.status == 'failed' else None,
            'source_files_count': kb.source_files.count() 
        })
    except KnowledgeBase.DoesNotExist:
        return JsonResponse({'error': 'Knowledge Base not found.'}, status=404)
    except Exception as e:
        logger.error(f"Error fetching KB status for ID {kb_id}: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error.'}, status=500)
