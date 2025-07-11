#webapp/views.py

import os
import json
import uuid
import logging
import shutil
import tempfile
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from webapp.forms import KnowledgeBaseForm
from core.models import KnowledgeBase
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
def home_view(request):
    if request.method == "POST":
        form = KnowledgeBaseForm(request.POST, request.FILES)
        if form.is_valid():
            knowledge_base = form.save(commit=False)
            knowledge_base.user = request.user
            try:
                knowledge_base.save() # This is where the GCS upload happens

                messages.success(request, "Knowledge base uploaded successfully!")
                return redirect("dashboard")
            except ValueError as ve:
                logger.error("caught ValueError during file upload", exc_info=True)
                messages.error(request, f"Failed to save knowledge base: {ve}")
                return redirect("home")
            except notImplementedError as e:
                logger.error("caught NotImplementedError during file upload", exc_info=True)
                messages.error(request, "File upload failed to storage: {e} ")
                return redirect("dashboard")
            except Exception as e:
                logger.error("caught unexpected exception during file upload: {type(e).__name__}", exc_info=True)
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
    kb = get_object_or_404(KnowledgeBase, pk=kb_id, user=request.user) # Added user filter for security

    if not kb.is_embedded:
        print("[DEBUG] File storage backend:", kb.file.storage.__class__)
        # Pass the FileField object (kb.file) directly to the extraction function
        extracted_text = extract_text_from_file(kb.file) # <--- CRITICAL CHANGE

        # Check if the extracted_text indicates an error during processing
        if extracted_text.startswith("Error:"):
            messages.error(request, extracted_text) # Display the specific error message
            return redirect("dashboard")

        if not extracted_text.strip():
            messages.warning(request, "The uploaded file has no readable text or is empty.")
            return redirect("dashboard")
        try:
            model = get_embedding_model() # Ensure this is correctly defined and returns your Gemini model
            vector_index_name = f"kb_{kb.id}"

            # Assuming embed_and_store handles the entire process and doesn't need file paths anymore
            embed_and_store([extracted_text], vector_index_name, model)

            kb.widget_slug = str(uuid.uuid4())[:8] # Generates a unique 8-char slug
            kb.is_embedded = True
            kb.save()
            messages.success(request, "Knowledge base embedded successfully!") # Add success message
        except Exception as e:
            messages.error(request, f"Failed to embed knowledge base: {e}")
            return redirect("dashboard")
    else:
        messages.info(request, "Knowledge base is already embedded.")

    return render(request, 'webapp/proceed.html', {'knowledge_base': kb})

@login_required
@require_POST
def delete_kb_view(request, kb_id):
    kb = get_object_or_404(KnowledgeBase, id=kb_id, user=request.user)

    # Delete file from media storage (local or GCS)
    if kb.file and kb.file.storage.exists(kb.file.name):
        kb.file.delete()
        print(f"Deleted media file: {kb.file.name}")

    # Delete associated FAISS index and chunk files
    index_name = f"kb_{kb.id}"
    remove_faiss_data(index_name)

    # Delete from DB
    kb.delete()
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
