import os
from typing import Optional, List
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEFAULT_MODEL_ID = "gemini-2.5-flash"
API_VERSION = "v1beta"

# Singleton client cache to prevent unnecessary client re-instantiations
_cached_client: Optional[genai.Client] = None
_cached_api_key: Optional[str] = None


def get_gemini_client(api_key: Optional[str] = None) -> genai.Client:
    """
    Initializes and returns a singleton genai.Client according to latest Google AI Studio docs.
    Automatically checks GEMINI_API_KEY and GOOGLE_API_KEY environment variables.
    Configures http_options with api_version='v1beta' to enable JSON mode and structured outputs.
    """
    global _cached_client, _cached_api_key

    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY or GOOGLE_API_KEY is not set. "
            "Please configure your API key in the .env file or Streamlit sidebar."
        )

    if _cached_client is not None and _cached_api_key == key:
        return _cached_client

    _cached_client = genai.Client(
        api_key=key,
        http_options=types.HttpOptions(api_version=API_VERSION)
    )
    _cached_api_key = key
    return _cached_client


def reset_gemini_client():
    """Resets the cached genai.Client instance (e.g. when API key is updated in the UI)."""
    global _cached_client, _cached_api_key
    _cached_client = None
    _cached_api_key = None


def get_model_id() -> str:
    """Returns the configured model id, defaulting to gemini-2.5-flash."""
    return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL_ID)


def get_default_safety_settings() -> List[types.SafetySetting]:
    """
    Returns standard safety settings tailored for legal aid assistance.
    Ensures legitimate discussion of legal disputes, police FIRs, or harassment
    is not inadvertently blocked by overly sensitive filters.
    """
    return [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        ),
    ]

