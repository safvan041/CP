import os
import uuid
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import KnowledgeBaseForm
from .models import KnowledgeBase
from .utils.file_reader import extract_text_from_file
from .utils.vector_logic import embed_and_store
from embeddings.embedding_service import get_embedding_model
from .utils.vector_logic import search_similar_chunks


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

    return render(request, "signup.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid credentials")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def dashboard_view(request):
    # Retrieve all uploaded knowledge bases for the logged-in user
    knowledge_bases = KnowledgeBase.objects.filter(user=request.user)

    return render(request, "dashboard.html", {"knowledge_bases": knowledge_bases})

@login_required
def home_view(request):
    if request.method == "POST":
        form = KnowledgeBaseForm(request.POST, request.FILES)
        if form.is_valid():
            knowledge_base = form.save(commit=False)
            knowledge_base.user = request.user
            knowledge_base.save()
            messages.success(request, "Knowledge base uploaded successfully!")
            return redirect('dashboard')  # Redirect to the dashboard after successful upload
        else:
            messages.error(request, "There was an error with your upload.")
    else:
        form = KnowledgeBaseForm()
    if form.is_valid():
        knowledge_base = form.save(commit=False)
        knowledge_base.user = request.user
        knowledge_base.save()
        print(f"Knowledge base saved: {knowledge_base.title}")

    return render(request, "home.html", {"form": form})

@login_required
def proceed_view(request, kb_id):
    kb = get_object_or_404(KnowledgeBase, pk=kb_id)

    if not kb.is_embedded:
        file_path = kb.file.path
        extracted_text = extract_text_from_file(file_path)

        model = get_embedding_model()
        vector_index_name = f"kb_{kb.id}"
        embed_and_store([extracted_text], vector_index_name, model)

        # Generate a unique widget slug
        kb.widget_slug = str(uuid.uuid4())[:8]  # short, unique
        kb.is_embedded = True
        kb.save()

    return render(request, 'proceed.html', {'knowledge_base': kb})

def chat_widget_view(request, widget_slug):
    kb = get_object_or_404(KnowledgeBase, widget_slug=widget_slug)
    return render(request, 'chat_widget.html', {'kb': kb})

def chat_api_view(request, widget_slug):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get('message', '')

        kb = get_object_or_404(KnowledgeBase, widget_slug=widget_slug)
        model = get_embedding_model()
        index_name = f"kb_{kb.id}"

        # Search similar content from vector store
        results = search_similar_chunks(user_message, index_name, model)

        # For now, just return the top match
        top_response = results[0] if results else "Sorry, I couldn't find anything relevant."
        return JsonResponse({'response': top_response})

    return JsonResponse({'error': 'Invalid request'}, status=400)

