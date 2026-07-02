# Customer Support Ticket Pipeline

An AI-powered pipeline that triages customer support tickets in three stages using OpenRouter LLMs: extract → reason → draft reply.

## Folder Structure

```
prompt/
├── app/
│   ├── config.py              # Loads API key, model, URL from .env
│   ├── llm.py                 # call_llm() — sends prompts to OpenRouter
│   ├── prompts.py             # Prompt templates (PROMPT_STAGE1–3, PROMPT_FIX_JSON)
│   ├── parser.py              # parse_json() with LLM retry on failure
│   ├── stage1_understand.py   # Stage 1: extract structured ticket fields
│   ├── stage2_reason.py       # Stage 2: determine priority, routing & reasoning
│   ├── stage3_produce.py      # Stage 3: draft on-brand customer reply
│   ├── utils.py               # print_stage(), save_output()
│   └── pipeline.py            # run_pipeline() — orchestrates all 3 stages
├── inputs/
│   └── sample_ticket.txt      # Sample support ticket to test with
├── outputs/                   # JSON results saved here after each run
├── main.py                    # Entry point
├── streamlit_app.py           # Streamlit UI
├── requirements.txt
└── .env.example               # Environment variable template
```

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your OpenRouter API key:
   ```
   OPENROUTER_API_KEY=your_key_here
   MODEL=openai/gpt-4o-mini
   API_URL=https://openrouter.ai/api/v1/chat/completions
   ```
   Get a free API key at [openrouter.ai](https://openrouter.ai).

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `OPENROUTER_API_KEY` | Your OpenRouter API key (required) | — |
| `MODEL` | Model identifier on OpenRouter | `openai/gpt-4o-mini` |
| `API_URL` | OpenRouter chat completions endpoint | `https://openrouter.ai/api/v1/chat/completions` |

## How to Run

```bash
# Run with the default sample ticket
python main.py

# Run with a custom ticket file
python main.py inputs/my_ticket.txt

# Launch the Streamlit UI
streamlit run streamlit_app.py
```

## Pipeline Stages

| Stage | Module | Role | Input | Output |
|---|---|---|---|---|
| 1 — Understand | `stage1_understand.py` | Structured extraction | Raw ticket text | Ticket fields JSON |
| 2 — Reason | `stage2_reason.py` | Chain-of-thought | Stage 1 JSON | Priority, route & reasoning JSON |
| 3 — Produce | `stage3_produce.py` | Goal-oriented generation | Stage 1 + Stage 2 JSON | Drafted reply (plain string) |

Each stage communicates via JSON dictionaries. The final output (all stages + reply) is saved to `outputs/result_<timestamp>.json`.

## Stage Schemas

### Stage 1 — Understand
```json
{
  "customer": "Marcus Delgado",
  "order_id": "ORD-84712",
  "issue": "Package not delivered after 12 days; tracking stuck on In Transit",
  "days_waiting": 12,
  "sentiment": "Angry"
}
```

### Stage 2 — Reason
```json
{
  "priority": "P1",
  "route": "shipping",
  "why": "Customer waited 12 days — double the promised 5–7 day window. Sentiment is Angry. A birthday gift was missed, adding emotional urgency. Prior support contact did not resolve it. This is P1 requiring immediate escalation to the shipping team."
}
```

### Stage 3 — Produce
```
Hi Marcus,

Thank you for reaching out, and I sincerely apologise for the frustration this delay
has caused — especially knowing this was meant to be a birthday gift.

I've escalated your case with Order #ORD-84712 and our team is actively investigating
what happened with your shipment. We'll be in touch with an update as soon as we have
more information.

We truly appreciate your patience, and we're committed to making this right for you.

Warm regards,
The Support Team
```

## Prompt Design Principles

- **Stage 1** uses a *role + structured output* pattern: the model acts as a data specialist and returns only well-defined JSON fields.
- **Stage 2** uses *chain-of-thought*: the model reasons step by step before committing to a priority and route, surfacing its logic in the `why` field.
- **Stage 3** uses *goal-oriented generation with constraints*: the model produces a plain-text reply that is on-brand, ≤120 words, and explicitly instructed not to make promises it cannot keep.
