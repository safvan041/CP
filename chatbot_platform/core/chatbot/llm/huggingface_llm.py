import requests
from django.conf import settings

HUGGINGFACE_API_KEY = settings.HUGGINGFACE_API_KEY
def query_huggingface_model(prompt, model="mistralai/Mistral-7B-Instruct-v0.2"):
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.7,
            "top_p": 0.95,
            "do_sample": True,
            "max_new_tokens": 200,
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        generated = response.json()
        return generated[0]["generated_text"]
    else:
        return f"Error: {response.status_code} {response.text}"
