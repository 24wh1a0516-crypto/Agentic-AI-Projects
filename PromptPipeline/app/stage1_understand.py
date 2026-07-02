"""Stage 1: Understand — extract structured fields from a raw support ticket."""

from app.llm import call_llm
from app.parser import parse_json
from app.prompts import PROMPT_STAGE1


def stage1_understand(ticket: str) -> dict:
    """Extract structured ticket information from raw customer support text.

    Args:
        ticket: Raw customer support ticket text.

    Returns:
        Dictionary with keys:
            - customer (str): Customer name or identifier.
            - order_id (str | None): Order or reference ID.
            - issue (str): Concise one-line description of the problem.
            - days_waiting (int | None): Number of days the customer has been waiting.
            - sentiment (str): One of Angry | Frustrated | Neutral | Polite | Urgent.
    """
    prompt = PROMPT_STAGE1.format(ticket=ticket)
    response = call_llm(prompt)
    return parse_json(response)
