"""Prompt templates for the customer support ticket pipeline."""

PROMPT_STAGE1 = """\
You are a customer support data specialist.

Your job is to read a raw customer support ticket and extract only the factual information present.

Instructions:
- Read the ticket carefully.
- Do NOT infer or guess information not explicitly stated.
- If a value is missing or not mentioned, return null.
- Return ONLY valid JSON — no markdown, no explanations.

Output Schema:
{{
  "customer": "<customer name or identifier>",
  "order_id": "<order or reference ID, or null>",
  "issue": "<concise one-line description of the core problem>",
  "days_waiting": <integer number of days the customer has been waiting, or null>,
  "sentiment": "<Angry | Frustrated | Neutral | Polite | Urgent>"
}}

Support Ticket:
{ticket}
"""

PROMPT_STAGE2 = """\
You are a senior customer support analyst.

Think step by step before producing your final answer. Show your reasoning in the "why" field.

You are given the following extracted ticket information:
{stage1_output}

Your tasks:
1. Determine the priority level based on issue severity, sentiment, and wait time.
   - P1: Critical — high frustration, long wait, or financial/legal risk
   - P2: Standard — moderate urgency, needs timely response
   - P3: Low — routine inquiry, patient tone
2. Choose the correct routing team:
   - "billing"        → payment issues, refunds, charges
   - "shipping"       → delivery status, lost packages, delays
   - "technical"      → product defects, app or website errors
   - "account"        → login, account access, profile issues
   - "general"        → anything else
3. Write a brief chain-of-thought reasoning explaining why you chose this priority and route.
4. Do NOT invent facts.
5. Return ONLY valid JSON — no markdown, no explanations.

Schema:
{{
  "priority": "P1 | P2 | P3",
  "route": "billing | shipping | technical | account | general",
  "why": "<step-by-step reasoning for priority and routing decision>"
}}
"""

PROMPT_STAGE3 = """\
You are a friendly, professional customer support agent representing the brand.

You are drafting a reply to a customer. Use the extracted ticket details and the reasoning below:

Ticket details:
{stage1_output}

Priority & routing analysis:
{stage2_output}

Constraints — your reply MUST:
- Be 120 words or fewer.
- Open by acknowledging the customer by name (use "customer" field if no name given).
- Empathise briefly with the issue.
- State what action is being taken or what the customer should do next.
- NEVER promise a specific resolution time, refund, or outcome you cannot guarantee.
- NEVER mention internal priority labels (P1, P2, P3) or team routing names.
- End with a warm, on-brand sign-off.
- Return ONLY a plain string — the reply text itself, with no JSON wrapper, no markdown.
"""

PROMPT_FIX_JSON = """\
The following text was supposed to be valid JSON but failed to parse. Fix it and return ONLY valid JSON, no extra text.

Text:
{text}
"""
