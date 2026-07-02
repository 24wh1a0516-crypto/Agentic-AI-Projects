"""Stage 3: Produce — draft an on-brand customer support reply."""

import json
from app.llm import call_llm
from app.prompts import PROMPT_STAGE3


def stage3_produce(stage1_output: dict, stage2_output: dict) -> str:
    """Draft a customer-facing reply using Stage 1 ticket data and Stage 2 reasoning.

    The reply is:
        - 120 words or fewer
        - Addresses the customer by name
        - Empathetic and on-brand
        - Makes no false promises about timelines or outcomes
        - Contains no internal priority labels or routing team names

    Args:
        stage1_output: Dictionary produced by stage1_understand.
        stage2_output: Dictionary produced by stage2_reason.

    Returns:
        A plain string containing the drafted customer reply.
    """
    prompt = PROMPT_STAGE3.format(
        stage1_output=json.dumps(stage1_output, indent=2),
        stage2_output=json.dumps(stage2_output, indent=2),
    )
    return call_llm(prompt).strip()
