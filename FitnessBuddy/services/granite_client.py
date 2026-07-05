"""
FitnessBuddy — IBM Watsonx.ai Granite Client
=============================================
Handles all communication with the IBM Watsonx.ai API.
Supports token generation, model inference, and graceful fallbacks.
"""
import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Environment variables ──────────────────────────────────────────────────────
IBM_API_KEY     = os.getenv("IBM_API_KEY", "")
WATSONX_URL     = os.getenv("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
PROJECT_ID      = os.getenv("IBM_PROJECT_ID", "")
MODEL_ID        = os.getenv("IBM_MODEL_ID", "ibm/granite-3-8b-instruct")
IAM_TOKEN_URL   = "https://iam.cloud.ibm.com/identity/token"

# ── Default generation parameters ─────────────────────────────────────────────
DEFAULT_PARAMS = {
    "max_new_tokens":  1024,
    "min_new_tokens":  20,
    "temperature":     0.7,
    "top_p":           0.9,
    "top_k":           50,
    "repetition_penalty": 1.1,
    "stop_sequences":  ["<|endoftext|>", "Human:", "User:"],
}


# ── Token cache (module-level, refreshed when stale) ──────────────────────────
_cached_token: str = ""
_token_expiry:  int = 0


def _get_iam_token() -> str:
    """
    Fetch an IAM bearer token from IBM Cloud, with in-memory caching.
    Tokens are valid for ~1 hour; we refresh 5 minutes early.
    """
    global _cached_token, _token_expiry
    import time

    if _cached_token and time.time() < _token_expiry:
        return _cached_token

    if not IBM_API_KEY or IBM_API_KEY == "your_ibm_cloud_api_key_here":
        raise ValueError(
            "IBM_API_KEY is not configured. "
            "Add your IBM Cloud API key to the .env file."
        )

    try:
        resp = requests.post(
            IAM_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type":   "urn:ibm:params:oauth:grant-type:apikey",
                "apikey":       IBM_API_KEY,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        _cached_token = data["access_token"]
        _token_expiry = int(time.time()) + data.get("expires_in", 3600) - 300
        logger.info("IAM token refreshed successfully.")
        return _cached_token

    except requests.RequestException as exc:
        logger.error("Failed to obtain IAM token: %s", exc)
        raise RuntimeError(f"IBM IAM token error: {exc}") from exc


def generate_text(prompt: str, params: dict | None = None) -> str:
    """
    Send a prompt to IBM Granite and return the generated text.

    Args:
        prompt: Full formatted prompt string
        params: Override default generation parameters (optional)

    Returns:
        Generated text string, or error message on failure
    """
    if not PROJECT_ID or PROJECT_ID == "your_watsonx_project_id_here":
        return _fallback_response("IBM_PROJECT_ID is not configured in the .env file.")

    generation_params = {**DEFAULT_PARAMS, **(params or {})}

    try:
        token  = _get_iam_token()
        url    = f"{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
            "Accept":        "application/json",
        }
        payload = {
            "model_id":   MODEL_ID,
            "project_id": PROJECT_ID,
            "input":      prompt,
            "parameters": generation_params,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()

        data    = resp.json()
        results = data.get("results", [])
        if results:
            text = results[0].get("generated_text", "").strip()
            return text if text else _fallback_response("Empty response from model.")

        return _fallback_response("No results in API response.")

    except ValueError as exc:
        logger.warning("Config error: %s", exc)
        return _fallback_response(str(exc))

    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response else "unknown"
        logger.error("Watsonx API HTTP error %s: %s", status, exc)
        return _fallback_response(
            f"API returned HTTP {status}. Check your credentials and project ID."
        )

    except requests.Timeout:
        logger.warning("Watsonx API request timed out.")
        return _fallback_response(
            "The AI is taking longer than expected. Please try again in a moment."
        )

    except Exception as exc:
        logger.exception("Unexpected error calling Watsonx API: %s", exc)
        return _fallback_response(f"Unexpected error: {exc}")


def _fallback_response(reason: str) -> str:
    """Return a helpful fallback when the API is unavailable."""
    return (
        f"⚠️ AI service temporarily unavailable: {reason}\n\n"
        "In the meantime, here are some universal fitness tips:\n"
        "• Aim for 150 minutes of moderate exercise per week.\n"
        "• Stay hydrated — drink 2.5–3 litres of water daily.\n"
        "• Prioritise 7–9 hours of quality sleep for recovery.\n"
        "• Include both strength training and cardio in your routine.\n\n"
        "_Please add your IBM Cloud API key to the .env file to unlock full AI features._"
    )


def is_configured() -> bool:
    """Check whether the Watsonx credentials appear to be set."""
    return (
        bool(IBM_API_KEY) and IBM_API_KEY != "your_ibm_cloud_api_key_here"
        and bool(PROJECT_ID) and PROJECT_ID != "your_watsonx_project_id_here"
    )
