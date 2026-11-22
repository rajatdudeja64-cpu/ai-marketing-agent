import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL_ID = "gemini-3.5-flash-lite"


def ask_gemini_json(prompt: str) -> dict:
    """Call Gemini and return a parsed Python dictionary (JSON)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing in your .env file.")

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)
