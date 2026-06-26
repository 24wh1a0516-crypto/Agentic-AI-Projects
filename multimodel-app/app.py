import os
import time
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

load_dotenv()

client = OpenAI(
    api_key=os.environ["OPENROUTER_API_KEY"],
    base_url="https://openrouter.ai/api/v1",
)

MODELS = [
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-120b:free",
]

# Prices in USD per million tokens — free-tier models are $0
PRICES = {
    "google/gemma-4-31b-it:free": {"in": 0.00, "out": 0.00},
    "openai/gpt-oss-120b:free":   {"in": 0.00, "out": 0.00},
}

TIMEOUT = 30
RETRY_WAIT = 5
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
            answer = response.choices[0].message.content
            in_tokens  = response.usage.prompt_tokens
            out_tokens = response.usage.completion_tokens
            p = PRICES[model]
            cost = (in_tokens * p["in"] + out_tokens * p["out"]) / 1_000_000
            return answer, latency, in_tokens, out_tokens, cost
        except RateLimitError:
            if attempt == MAX_RETRIES:
                raise
            time.sleep(RETRY_WAIT)


# ── UI ────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Multi-Model Comparison", layout="wide")
st.title("Multi-Model Comparison")

question = st.text_area(
    "Your question",
    placeholder="Type your question here…",
    height=120,
)
run = st.button("Run", type="primary", use_container_width=True)

if run and question.strip():
    cols = st.columns(len(MODELS))
    for col, model in zip(cols, MODELS):
        with col:
            # Strip the provider prefix for a cleaner heading
            st.subheader(model.split("/", 1)[1])
            with st.spinner("Querying…"):
                try:
                    answer, latency, in_tok, out_tok, cost = ask(question, model)
                except Exception as e:
                    st.error(str(e))
                    continue

            with st.container(border=True):
                st.write(answer)

            left, right = st.columns(2)
            left.metric("Latency", f"{latency:.2f}s")
            right.metric("Cost", f"${cost:.6f}")
