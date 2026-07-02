"""JSON parser with LLM-assisted retry."""

import json
import re


def _extract_json(text: str) -> str:
    """Strip markdown code fences if present."""
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    return match.group(1) if match else text.strip()


def parse_json(text: str) -> dict:
    """Parse JSON from LLM response text, retrying once via LLM on failure.

    Args:
        text: Raw LLM response that should contain JSON.

    Returns:
        Parsed dictionary.

    Raises:
        ValueError: If JSON cannot be parsed after retry.
    """
    cleaned = _extract_json(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Retry: ask LLM to fix the malformed JSON
    from app.llm import call_llm
    from app.prompts import PROMPT_FIX_JSON

    fixed = call_llm(PROMPT_FIX_JSON.format(text=text))
    cleaned_fixed = _extract_json(fixed)
    try:
        return json.loads(cleaned_fixed)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON after retry: {e}\nRaw text: {text}") from e
