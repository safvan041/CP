# webapp/utils/genai_llm.py

import traceback
import google.generativeai as genai
from django.conf import settings

genai.configure(api_key=settings.GOOGLE_GENAI_API_KEY)

GENAI_MODEL_NAME = "gemini-2.5-flash" 

def generate_genai_response(context, question):
    """
    Generates a response from the Gemini model based on provided context and question.
    """
    prompt = f"""You are a helpful assistant. Only answer based on the context below.
If the answer cannot be found in the context, politely state that you don't have enough information.

Context:
{context}

Question: {question}
Answer:"""
    try:
        # Initialize the generative model with the updated name
        model = genai.GenerativeModel(GENAI_MODEL_NAME)
        response = model.generate_content(prompt)

        # Handle potential empty or blocked responses
        if response.text:
            return response.text.strip()
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
            block_reason = response.prompt_feedback.block_reason.name
            print(f"[GENAI INFO] Prompt blocked due to: {block_reason}")
            # You can customize this message based on the block reason
            return "Sorry, I cannot provide an answer based on this request due to safety concerns."
        else:
            return "Sorry, I received an empty or uninterpretable response from the GenAI model."

    except Exception as e:
        print(f"[GENAI ERROR] An unexpected error occurred during generation: {e}")
        traceback.print_exc() # This will print the full traceback for debugging
        return "Sorry, I encountered an internal error while trying to get a response."
