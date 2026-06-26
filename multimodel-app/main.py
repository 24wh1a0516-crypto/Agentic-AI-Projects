import os
import time
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

# Pull OPENROUTER_API_KEY into os.environ from the .env file
load_dotenv()

# Point the OpenAI client at OpenRouter instead of api.openai.com
client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

QUESTION = "What is the capital of France? Answer in one sentence."

MODELS = [
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-120b:free",
]

# Prices in USD per million tokens — free-tier models are $0
PRICES = {
    "google/gemma-4-31b-it:free": {"in": 0.00, "out": 0.00},
    "openai/gpt-oss-120b:free":   {"in": 0.00, "out": 0.00},
}


TIMEOUT = 30  # seconds before a model call is abandoned
RETRY_WAIT = 5  # seconds to wait before retrying a rate-limited call
MAX_RETRIES = 3


def ask(question, model):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            t0 = time.perf_counter()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": question}],
                timeout=TIMEOUT,
            )
            latency = time.perf_counter() - t0

            # response.choices[0].message.content holds the model's reply
            answer = response.choices[0].message.content

            in_tokens  = response.usage.prompt_tokens
            out_tokens = response.usage.completion_tokens

            p = PRICES[model]
            cost = (in_tokens * p["in"] + out_tokens * p["out"]) / 1_000_000

            return answer, latency, in_tokens, out_tokens, cost

        except RateLimitError:
            if attempt == MAX_RETRIES:
                raise
            print(f"  [{model}] rate-limited, retrying in {RETRY_WAIT}s "
                  f"(attempt {attempt}/{MAX_RETRIES})...")
            time.sleep(RETRY_WAIT)


COL_MODEL   = 28
COL_PREVIEW = 46
COL_LATENCY =  7   # "12.34s"
COL_COST    = 10   # "$0.001234"


def _preview(text, width):
    text = text.strip().replace("\n", " ")
    return text if len(text) <= width else text[: width - 1] + "…"


# Collect results so the table can be printed all at once
rows = []
for model in MODELS:
    try:
        answer, latency, in_tok, out_tok, cost = ask(QUESTION, model)
        rows.append((model, answer, f"{latency:.2f}s", f"${cost:.6f}"))
    except Exception as e:
        rows.append((model, f"ERROR: {e}", "", ""))

# Header
header = (
    f"{'Model':<{COL_MODEL}}"
    f"{'Answer preview':<{COL_PREVIEW}}"
    f"{'Latency':>{COL_LATENCY}}"
    f"{'Cost':>{COL_COST}}"
)
rule = "─" * len(header)
print(f"\n{header}\n{rule}")

for model, answer, latency, cost in rows:
    print(
        f"{model:<{COL_MODEL}}"
        f"{_preview(answer, COL_PREVIEW):<{COL_PREVIEW}}"
        f"{latency:>{COL_LATENCY}}"
        f"{cost:>{COL_COST}}"
    )
