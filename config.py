"""DeepSeek wiring for the CAD spec planner agent.

DeepSeek exposes an OpenAI-compatible API, so we use langchain-openai's
ChatOpenAI against DeepSeek's base URL.
"""

import os

# Paste your opencode API key here (or set the OPENCODE_API_KEY env var).
API_KEY = os.environ.get("OPENCODE_API_KEY", "sk-ZCp4tz1ziqHV6InV7SzEbYmfQ4wtmYpqcewSi9bR3z87rbAonYetCylCrG1zMbiK")

BASE_URL = "https://opencode.ai/zen/go/v1"
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
TEMPERATURE = 0.0