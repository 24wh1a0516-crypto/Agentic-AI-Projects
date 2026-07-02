"""Configuration loader for OpenRouter API settings."""

import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
MODEL: str = os.getenv("MODEL", "openai/gpt-4o-mini")
API_URL: str = os.getenv("API_URL", "https://openrouter.ai/api/v1/chat/completions")
