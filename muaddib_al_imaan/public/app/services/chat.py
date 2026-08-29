"""NVIDIA chat completion service."""
import logging

from openai import OpenAI

from app.config import NVIDIA_API_KEY, NVIDIA_BASE_URL, NVIDIA_CHAT_MODEL

logger = logging.getLogger(__name__)


def _client():
    return OpenAI(api_key=NVIDIA_API_KEY, base_url=NVIDIA_BASE_URL)


def generate_chat_response(context, question):
    prompt = f"""You are a knowledgeable Islamic fiqh assistant. Use only the context below to answer the question.
If the answer is not in the context, say that you do not have enough information.
When the context contains a chain of references (e.g. "X narrated from Y from Z"), preserve and include the entire chain in your answer.

Context:
{context}

Question: {question}"""

    try:
        response = _client().chat.completions.create(
            model=NVIDIA_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful Islamic fiqh assistant that answers from provided context.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        logger.exception("NVIDIA chat request failed")
        return "Sorry, I couldn't get a response from the NVIDIA model."