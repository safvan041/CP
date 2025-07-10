# webapp/utils/genai_llm.py

import traceback
import google.generativeai as genai
from django.conf import settings

genai.configure(api_key=settings.GOOGLE_GENAI_API_KEY)

def generate_genai_response(context, question):
    prompt = f"""You are a helpful assistant. Only answer based on the context below.
Context:
{context}

Question: {question}
Answer:"""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-001")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("[GENAI ERROR]", e)
        traceback.print_exc()
        return "Sorry, I couldn't get a response from the GenAI model."
