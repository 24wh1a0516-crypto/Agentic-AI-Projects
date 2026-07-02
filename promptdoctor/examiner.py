"""
examiner.py — The AI examiner that grades the student's prompt.

The examiner:
  1. Receives the student's prompt, the level's principles, and the live model output.
  2. Reasons step-by-step about each principle.
  3. Returns a structured JSON verdict that app.py renders as pass/fail cards.

The examiner NEVER rewrites the student's prompt — it diagnoses only.
"""

from __future__ import annotations

import json
import os
import re

import requests
from dotenv import load_dotenv

from levels import get_level, get_principles_text

load_dotenv(override=True)

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

# Pin ONE capable judge model so grading stays consistent across runs.
EXAMINER_MODEL: str = os.getenv(
    "EXAMINER_MODEL",
    "openai/gpt-4o",  # strong reasoning + reliable JSON output
)
OPENROUTER_BASE: str = "https://openrouter.ai/api/v1"


# ---------------------------------------------------------------------------
# The examiner system prompt.
#
# IMPORTANT: This string uses __SENTINEL__ tokens for substitution via
# str.replace(), NOT str.format(). This avoids any KeyError from curly braces
# in the JSON example block or in any user-supplied content.
# ---------------------------------------------------------------------------

EXAMINER_SYSTEM: str = """
You are the Examiner: a strict but fair prompt-engineering assessor working inside
the Prompt Doctor dojo. Your only job is to diagnose — you MUST NOT write, rewrite,
complete, or suggest an example of a corrected prompt under any circumstances.

You are grading a STUDENT_PROMPT submitted for Level __LEVEL__ (__LEVEL_NAME__).
Judge it ONLY against the following principles for this level:

__PRINCIPLES__

GRADING RULES

1. Judge against the principles in your OWN words — be specific to what you see
   (or don't see) in the student's prompt. Generic remarks such as "the prompt
   could be clearer" fail this rule.

2. For each principle that fails:
   - Quote the EXACT weak phrase from the student's prompt (use double-quotes).
   - If something required is completely absent, state clearly what is missing.

3. Ask EXACTLY ONE pointed question per failed principle that leads the student
   toward the fix without giving it away.

4. NEVER write, rewrite, give an example of, or paraphrase a corrected prompt.
   Diagnose only — the cure must come from the student.

5. Reason step by step through each principle first, THEN emit the JSON verdict.
   Wrap your reasoning in <thinking>...</thinking> tags so it is hidden from the
   student. Only the JSON appears in the final output.

6. The "verdict" field must be:
   - "pass"   if EVERY principle.pass is true
   - "revise" if ANY principle.pass is false

OUTPUT FORMAT — emit ONLY valid JSON, nothing before or after:

{
  "level": <int>,
  "principles": [
    {
      "name": "<principle_name>",
      "pass": <true|false>,
      "weakness": "<quoted weak phrase or MISSING: what is absent — null if pass>",
      "question": "<one pointed question — null if pass>"
    }
  ],
  "ran_ok": <true|false>,
  "overall_comment": "<two sentences max: what the student did well + the most important gap>",
  "verdict": "<pass|revise>"
}
"""

# ---------------------------------------------------------------------------
# The examiner user message template.
# Also uses __SENTINEL__ tokens — no .format() anywhere on user-controlled text.
# ---------------------------------------------------------------------------

EXAMINER_USER_TEMPLATE: str = """Grade this student submission.

== STUDENT PROMPT ==
__STUDENT_PROMPT__

== SAMPLE INPUT (what the prompt was run on) ==
__SAMPLE_INPUT__

== LIVE MODEL OUTPUT (produced by the student's prompt on the sample input) ==
__MODEL_OUTPUT__

== TASK (so you know what a passing output looks like) ==
__TASK_DESCRIPTION__

Return ONLY the JSON verdict as specified in your system instructions.
Do not include markdown fences or any text outside the JSON object.
"""


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

class ExaminerError(Exception):
    """Raised when the examiner API call or JSON parse fails."""


def grade(
    level_id: int,
    domain: str,
    student_prompt: str,
    model_output: str,
    ran_ok: bool = True,
) -> dict:
    """
    Grade *student_prompt* for *level_id* and return the parsed verdict dict.

    Args:
        level_id:       1-5
        domain:         The domain the student chose (e.g. 'healthcare').
        student_prompt: The prompt the student submitted.
        model_output:   The raw output produced by runner.run_prompt().
        ran_ok:         False if the runner raised an error.

    Returns:
        A dict matching the JSON schema above.

    Raises:
        ExaminerError:    if the API call fails or the JSON cannot be parsed.
        EnvironmentError: if OPENROUTER_API_KEY is not set.
    """
    if not OPENROUTER_API_KEY:
        raise EnvironmentError(
            "OPENROUTER_API_KEY is not set. Add it to your .env file."
        )

    lvl = get_level(level_id)
    principles_text = get_principles_text(level_id)

    # Build task description — {domain} and {sample_input} are safe controlled
    # strings from levels.py, not user input, so .format() is fine here.
    task_desc = lvl["task"].format(domain=domain, sample_input=lvl["sample_input"])

    # Build system prompt via str.replace() — zero risk of KeyError from braces
    # in the JSON example block or any injected content.
    system_prompt = (
        EXAMINER_SYSTEM
        .replace("__LEVEL__", str(level_id))
        .replace("__LEVEL_NAME__", lvl["name"])
        .replace("__PRINCIPLES__", principles_text)
    )

    # Build user message via str.replace() — student_prompt and model_output
    # may contain arbitrary curly braces (e.g. JSON schemas), so .format()
    # must never be used on them.
    user_message = (
        EXAMINER_USER_TEMPLATE
        .replace("__STUDENT_PROMPT__", student_prompt)
        .replace("__SAMPLE_INPUT__", lvl["sample_input"])
        .replace("__MODEL_OUTPUT__", model_output if ran_ok else "(runner failed — no output)")
        .replace("__TASK_DESCRIPTION__", task_desc)
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://promptdoctor.local",
        "X-Title": "PromptDoctor-Examiner",
    }

    payload = {
        "model": EXAMINER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.0,   # deterministic grading
        "max_tokens": 2048,
    }

    try:
        response = requests.post(
            f"{OPENROUTER_BASE}/chat/completions",
            json=payload,
            headers=headers,
            timeout=90,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise ExaminerError("Examiner request timed out. Try again.")
    except requests.exceptions.HTTPError as exc:
        body = exc.response.text if exc.response is not None else "(no body)"
        raise ExaminerError(f"HTTP {exc.response.status_code}: {body}") from exc
    except requests.exceptions.RequestException as exc:
        raise ExaminerError(f"Network error: {exc}") from exc

    data = response.json()

    if "error" in data:
        err = data["error"]
        msg = err.get("message", str(err))
        raise ExaminerError(f"OpenRouter error: {msg}")

    try:
        raw_content: str = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise ExaminerError(f"Unexpected response shape: {data}") from exc

    return _parse_verdict(raw_content, level_id, ran_ok)


def _parse_verdict(raw: str, level_id: int, ran_ok: bool) -> dict:
    """
    Extract and parse the JSON verdict from the examiner's raw output.

    The model may wrap reasoning in <thinking>...</thinking> tags before
    emitting the JSON, or wrap the JSON in markdown fences. Both are handled.
    """
    # Strip <thinking>...</thinking> blocks.
    cleaned = re.sub(r"<thinking>.*?</thinking>", "", raw, flags=re.DOTALL)

    # Strip markdown code fences (```json ... ``` or ``` ... ```).
    cleaned = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", cleaned, flags=re.DOTALL)

    cleaned = cleaned.strip()

    # Find the outermost JSON object by locating the first { and last }.
    start = cleaned.find("{")
    end   = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ExaminerError(
            f"Examiner returned no JSON object. Raw output:\n{raw[:500]}"
        )

    json_str = cleaned[start : end + 1]

    try:
        verdict = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise ExaminerError(
            f"Could not parse examiner JSON: {exc}\nRaw JSON snippet:\n{json_str[:500]}"
        ) from exc

    # Normalise: ensure all required top-level keys exist.
    verdict.setdefault("level", level_id)
    verdict.setdefault("ran_ok", ran_ok)
    verdict.setdefault("principles", [])
    verdict.setdefault("overall_comment", "")
    verdict.setdefault("verdict", "revise")

    return verdict
