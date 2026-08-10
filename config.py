"""
Configuration for PromptProb — automated AI guardrail auditing tool.

Only test target(s) you are AUTHORIZED to test: your own local models,
API models you hold the key for, or third-party models you have explicit
written permission to red-team. See README.md "Scope" section.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # loads variables from a .env file in the project root, if present


def _model(env_prefix: str, default_type: str, default_base_url: str,
           default_model: str, default_api_key: str = "") -> dict:
    return {
        "name": os.environ.get(f"{env_prefix}_NAME", default_model),
        "type": os.environ.get(f"{env_prefix}_TYPE", default_type),
        "base_url": os.environ.get(f"{env_prefix}_BASE_URL", default_base_url),
        "api_key": os.environ.get(f"{env_prefix}_API_KEY", default_api_key),
        "model": os.environ.get(f"{env_prefix}_MODEL", default_model),
    }



TARGETS = [
    _model(
        "TARGET",
        default_type="openai_compatible",
        default_base_url="https://api.groq.com/openai/v1",
        default_model="llama-3.3-70b-versatile",
        default_api_key=os.environ.get("GROQ_API_KEY", ""),
    ),
]


ATTACKER_MODEL = _model(
    "ATTACKER",
    default_type="openai_compatible",
    default_base_url="http://localhost:11434/v1",
    default_model="llama3.2:3b",
    default_api_key="ollama",
)


JUDGE_MODEL = _model(
    "JUDGE",
    default_type="openai_compatible",
    default_base_url="http://localhost:11434/v1",
    default_model="llama3.2:3b",
    default_api_key="ollama",
)


VARIATIONS_PER_STRATEGY = int(os.environ.get("VARIATIONS_PER_STRATEGY", 5))
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", 120))
MAX_CONCURRENT_REQUESTS = int(os.environ.get("MAX_CONCURRENT_REQUESTS", 3))
REPORT_DIR = os.environ.get("REPORT_DIR", "reports")
VERBOSE = os.environ.get("VERBOSE", "false").lower() == "true"
