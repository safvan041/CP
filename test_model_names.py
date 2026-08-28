import requests
from decouple import config


API_KEY = config("NVIDIA_API_KEY")

response = requests.get(
    "https://integrate.api.nvidia.com/v1/models",
    headers={
        "Authorization": f"Bearer {API_KEY}"
    },
    timeout=30,
)

print("Status:", response.status_code)

if response.ok:

    data = response.json()

    for model in data.get("data", []):

        model_id = model.get("id", "")

        if "deepseek-v4-pro" in model_id.lower():
            print(model)

else:

    print(response.text)