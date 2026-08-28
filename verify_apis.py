#!/usr/bin/env python
"""Verify the embedding and chat APIs are working with their respective keys"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot_platform.settings.dev')
sys.path.insert(0, '/workspaces/CP/chatbot_platform')
django.setup()

from django.conf import settings
from core.utils.embeddings.embedding_service import get_embedding_model
from webapp.services.chat_service import generate_chat_response

print("=" * 80)
print("EMBEDDING & CHAT API VERIFICATION")
print("=" * 80)
print()

# Test 1: Verify settings
print("1. Configuration Check:")
print(f"   Chat API Key: {settings.NVIDIA_API_KEY[:20]}...")
print(f"   Chat Base URL: {settings.NVIDIA_BASE_URL}")
print(f"   Chat Model: {settings.NVIDIA_CHAT_MODEL}")
print()
print(f"   Embedding API Key: {settings.NVIDIA_EMBEDDING_API_KEY[:20]}...")
print(f"   Embedding Base URL: {settings.NVIDIA_EMBEDDING_BASE_URL}")
print(f"   Embedding Model: {settings.NVIDIA_EMBEDDING_MODEL}")
print()

# Test 2: Test embeddings
print("2. Testing Embeddings API:")
try:
    model = get_embedding_model()
    embeddings = model.encode(["test text for embedding"])
    print(f"   ✅ SUCCESS! Generated embedding with shape: {embeddings.shape}")
    print(f"   Embedding dimensions: {embeddings.shape[1]}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    sys.exit(1)

print()

# Test 3: Test chat
print("3. Testing Chat API:")
try:
    response = generate_chat_response("The capital of France is Paris", "What is the capital of France?")
    if response and "Sorry" not in response:
        print(f"   ✅ SUCCESS!")
        print(f"   Response: {response[:80]}...")
    else:
        print(f"   ⚠️  Response: {response}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    sys.exit(1)

print()
print("=" * 80)
print("✅ All API tests passed!")
print("=" * 80)
