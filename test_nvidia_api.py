#!/usr/bin/env python

import requests
from decouple import config


# ============================================================
# EMBEDDING CONFIGURATION
# ============================================================

EMBEDDING_API_KEY = config("NVIDIA_EMBEDDING_API_KEY")

EMBEDDING_BASE_URL = config(
    "NVIDIA_EMBEDDING_BASE_URL",
    default="https://integrate.api.nvidia.com/v1"
)

EMBEDDING_MODEL = config(
    "NVIDIA_EMBEDDING_MODEL",
    default="nvidia/nemotron-3-embed-1b"
)


# ============================================================
# Endpoint
# ============================================================

ENDPOINT = f"{EMBEDDING_BASE_URL}/embeddings"


# ============================================================
# Headers
# ============================================================

HEADERS = {
    "Authorization": f"Bearer {EMBEDDING_API_KEY}",
    "Content-Type": "application/json",
}


# ============================================================
# Test Payload
# ============================================================

PAYLOAD = {
    "model": EMBEDDING_MODEL,
    "input": [
        "This is a test sentence for the NVIDIA Nemotron embedding model."
    ],
    "input_type": "passage",
    "encoding_format": "float",
}


# ============================================================
# Display
# ============================================================

print("=" * 80)
print("NVIDIA EMBEDDING API TEST")
print("=" * 80)

print(f"Endpoint : {ENDPOINT}")
print(f"Model    : {EMBEDDING_MODEL}")
print("API Key  : NVIDIA_EMBEDDING_API_KEY")
print()

print("Sending request...")
print()


# ============================================================
# Request
# ============================================================

try:

    response = requests.post(
        ENDPOINT,
        headers=HEADERS,
        json=PAYLOAD,
        timeout=60,
    )

except requests.exceptions.RequestException as exc:

    print("❌ REQUEST FAILED")
    print()
    print(f"{type(exc).__name__}: {exc}")

    raise SystemExit(1)


# ============================================================
# Response
# ============================================================

print(f"HTTP Status: {response.status_code}")
print()


if response.status_code != 200:

    print("❌ EMBEDDING REQUEST FAILED")
    print("=" * 80)
    print()
    print(response.text)
    print()

    raise SystemExit(1)


# ============================================================
# Parse Response
# ============================================================

try:

    data = response.json()

except ValueError:

    print("❌ NVIDIA returned a non-JSON response:")
    print(response.text)

    raise SystemExit(1)


embeddings = data.get("data", [])


if not embeddings:

    print("❌ No embedding data returned.")
    print()
    print(data)

    raise SystemExit(1)


vector = embeddings[0].get("embedding")


if not vector:

    print("❌ Embedding vector missing.")
    print()
    print(data)

    raise SystemExit(1)


# ============================================================
# SUCCESS
# ============================================================

print("✅ EMBEDDING API SUCCESS")
print("=" * 80)
print()

print(f"Response model      : {data.get('model')}")
print(f"Embeddings returned : {len(embeddings)}")
print(f"Vector dimensions   : {len(vector)}")

print()
print("First 10 vector values:")
print(vector[:10])

print()
print("Usage:")
print(data.get("usage"))

print()
print("=" * 80)
print("🎉 NVIDIA EMBEDDING MODEL IS WORKING")
print("=" * 80)