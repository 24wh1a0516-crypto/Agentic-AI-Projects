"""
runner.py — Executes the student's prompt against the level's sample input
via the OpenRouter API and returns the raw model output.

The student writes a *system* or *user* prompt.  We inject the sample input
as a user message so the model sees:

  [system]  <student_prompt>
  [user]    <sample_input>

If the student's prompt contains the placeholder {input}, we substitute the
sample input there instead of appending a separate user message, giving
experienced students finer control.
"""

from __future__ import annotations

import os
import re

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
RUNNER_MODEL: str = os.getenv(
    "RUNNER_MODEL",
    "openai/gpt-4o-mini",  # fast, cheap, capable enough for the student's prompt
)
OPENROUTER_BASE: str = "https://openrouter.ai/api/v1"


class RunnerError(Exception):
    """Raised when the OpenRouter call fails."""


def run_prompt(student_prompt: str, sample_input: str) -> str:
    """
    Execute *student_prompt* on *sample_input* and return the model's reply.

    Args:
        student_prompt: The prompt written by the student (system instructions).
        sample_input:   The level's sample input text.

    Returns:
        The model's text output as a string.

    Raises:
        RunnerError: if the API call fails or returns an error.
        EnvironmentError: if OPENROUTER_API_KEY is not set.
    """
    if not OPENROUTER_API_KEY:
        raise EnvironmentError(
            "OPENROUTER_API_KEY is not set. Add it to your .env file."
        )

    # If the student embedded {input} in their prompt, substitute it.
    if "{input}" in student_prompt:
        filled = student_prompt.replace("{input}", sample_input)
        messages = [{"role": "user", "content": filled}]
    else:
        # Treat the student's prompt as a system message.
        messages = [
            {"role": "system", "content": student_prompt},
            {"role": "user", "content": sample_input},
        ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://promptdoctor.local",
        "X-Title": "PromptDoctor",
    }

    payload = {
        "model": RUNNER_MODEL,
        "messages": messages,
        "temperature": 0.2,       # low temperature → more deterministic output
        "max_tokens": 1024,
    }

    try:
        response = requests.post(
            f"{OPENROUTER_BASE}/chat/completions",
            json=payload,
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RunnerError("Request timed out. Try again.")
    except requests.exceptions.HTTPError as exc:
        body = exc.response.text if exc.response is not None else "(no body)"
        raise RunnerError(f"HTTP {exc.response.status_code}: {body}") from exc
    except requests.exceptions.RequestException as exc:
        raise RunnerError(f"Network error: {exc}") from exc

    data = response.json()

    # Surface API-level errors (e.g. rate-limit, model not found)
    if "error" in data:
        err = data["error"]
        msg = err.get("message", str(err))
        raise RunnerError(f"OpenRouter error: {msg}")

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise RunnerError(f"Unexpected response shape: {data}") from exc
