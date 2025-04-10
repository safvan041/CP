import os
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import KnowledgeBaseForm
from .models import KnowledgeBase
from .utils.file_reader import extract_text_from_file
from .utils.vector_logic import embed_and_store


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

    file_path = kb.file.path
    extracted_text = extract_text_from_file(file_path)

    # Embed and store
    vector_index_name = f"kb_{kb.id}"
    success = embed_and_store([extracted_text], index_name=vector_index_name)

    # Mark KB as embedded
    kb.is_embedded = True
    kb.save()

    return render(request, 'proceed.html', {'knowledge_base': kb})
def test_widget_view(request, pk):
    kb = get_object_or_404(KnowledgeBase, pk=pk)
    return render(request, 'widget_test.html', {'kb': kb})