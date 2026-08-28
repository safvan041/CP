import logging

from django.conf import settings
from openai import OpenAI


logger = logging.getLogger(__name__)


def _client():
    return OpenAI(
        api_key=settings.NVIDIA_API_KEY,
        base_url=settings.NVIDIA_BASE_URL,
    )


def generate_chat_response(context, question):
    prompt = f"""Use only the context below to answer the question. If the answer is not in the context, say that you do not have enough information.
Context:
{context}

Question: {question}"""

    try:
        response = _client().chat.completions.create(
            model=settings.NVIDIA_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers from provided context.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        logger.exception("NVIDIA chat request failed")
        return "Sorry, I couldn't get a response from the NVIDIA model."