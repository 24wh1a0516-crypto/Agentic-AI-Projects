"""Stage 2: Reason — determine priority, routing, and chain-of-thought from Stage 1 output."""

import json
from app.llm import call_llm
from app.parser import parse_json
from app.prompts import PROMPT_STAGE2


def stage2_reason(stage1_output: dict) -> dict:
    """Determine ticket priority, routing team, and reasoning from extracted ticket data.

    Args:
        stage1_output: Dictionary produced by stage1_understand, containing
                       customer, order_id, issue, days_waiting, and sentiment.

    Returns:
        Dictionary with keys:
            - priority (str): One of P1 | P2 | P3.
            - route (str): One of billing | shipping | technical | account | general.
            - why (str): Step-by-step chain-of-thought reasoning for the decision.
    """
    prompt = PROMPT_STAGE2.format(stage1_output=json.dumps(stage1_output, indent=2))
    response = call_llm(prompt)
    return parse_json(response)
