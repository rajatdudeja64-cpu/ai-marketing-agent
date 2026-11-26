import json
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]
_RETRYABLE_ERROR_MARKERS = ("503", "429", "500", "504", "RESOURCE_EXHAUSTED", "UNAVAILABLE")


def _parse_json_object(raw_text: str) -> dict:
    text = (raw_text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected JSON object from Gemini, got {type(parsed).__name__}.")
    return parsed


def _get_gemini_api_key() -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key
    try:
        import streamlit as st
        secret_key = st.secrets.get("GEMINI_API_KEY")
        if secret_key:
            return str(secret_key)
    except Exception:
        pass
    return None


def ask_gemini_json(prompt: str) -> dict:
    """Call Gemini with automatic retry and model fallback, returning parsed JSON."""
    api_key = _get_gemini_api_key()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing in your .env file or Streamlit secrets.")

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
                return _parse_json_object(response.text)
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                if attempt < 2:
                    time.sleep(1)
                continue
            except Exception as e:
                last_error = e
                err_str = str(e)
                if any(marker in err_str for marker in _RETRYABLE_ERROR_MARKERS):
                    time.sleep(2 * (attempt + 1))
                    continue
                raise

    raise last_error
