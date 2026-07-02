"""OpenRouter LLM client."""

import os
import requests
from app.config import API_URL


def call_llm(prompt: str) -> str:
    """Send a prompt to OpenRouter and return the response text.

    Args:
        prompt: The prompt string to send.

    Returns:
        The model's response as a string.

    Raises:
        RuntimeError: On API or HTTP errors.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    model = os.environ.get("MODEL", "openai/gpt-4o-mini")

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.HTTPError as e:
        raise RuntimeError(f"HTTP error from OpenRouter: {e.response.status_code} {e.response.text}") from e
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected response format: {response.text}") from e
    except requests.RequestException as e:
        raise RuntimeError(f"Request failed: {e}") from e
