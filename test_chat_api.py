#!/usr/bin/env python

import requests
from decouple import config


API_KEY = config("NVIDIA_API_KEY")

BASE_URL = config(
    "NVIDIA_CHAT_BASE_URL",
    default="https://integrate.api.nvidia.com/v1",
)

MODEL = config(
    "NVIDIA_CHAT_MODEL",
    default="deepseek-ai/deepseek-v4-pro-0813",
)

ENDPOINT = f"{BASE_URL}/chat/completions"


headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
}


payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": "Reply with exactly: Hello"
        }
    ],
    "temperature": 0,
    "max_tokens": 16,
    "stream": False,
}


print("=" * 70)
print("NVIDIA DEEPSEEK V4 PRO STREAMING TEST")
print("=" * 70)

print(f"Endpoint : {ENDPOINT}")
print(f"Model    : {MODEL}")
print("API Key  : configured")
print()

print("Sending request...")
print()


try:

    with requests.post(
        ENDPOINT,
        headers=headers,
        json=payload,
        stream=True,
        timeout=(10, 300),
    ) as response:

        print(f"HTTP Status: {response.status_code}")
        print()

        if response.status_code not in (200, 202):

            print("❌ REQUEST FAILED")
            print("=" * 70)
            print(response.text)
            raise SystemExit(1)

        print("✅ Request accepted")
        print()
        print("Model output:")
        print("-" * 70)

        for line in response.iter_lines(decode_unicode=True):

            if not line:
                continue

            print(line, flush=True)

        print()
        print("-" * 70)
        print("Stream ended.")


except requests.exceptions.ReadTimeout:

    print()
    print("❌ READ TIMEOUT")
    print("No response/data received within 300 seconds.")

except requests.exceptions.RequestException as exc:

    print()
    print("❌ REQUEST ERROR")
    print(type(exc).__name__)
    print(exc)