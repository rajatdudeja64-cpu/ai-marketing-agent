import json
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]


def ask_gemini_json(prompt: str) -> dict:
    """Call Gemini with automatic retry and model fallback, returning parsed JSON."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing in your .env file.")

    client = genai.Client(api_key=api_key)
    last_error = None

    for model_id in MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                )
                return json.loads(response.text)
            except Exception as e:
                last_error = e
                if "503" in str(e) or "429" in str(e):
                    time.sleep(2 * (attempt + 1))
                    continue
                raise

    raise last_error
