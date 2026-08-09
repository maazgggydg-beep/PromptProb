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
    """Build a model config from env vars, falling back to defaults.
    Lets anyone swap models via .env only, without touching this file.
    e.g. TARGET_MODEL, TARGET_BASE_URL, TARGET_API_KEY, TARGET_TYPE"""
    return {
        "name": os.environ.get(f"{env_prefix}_NAME", default_model),
        "type": os.environ.get(f"{env_prefix}_TYPE", default_type),
        "base_url": os.environ.get(f"{env_prefix}_BASE_URL", default_base_url),
        "api_key": os.environ.get(f"{env_prefix}_API_KEY", default_api_key),
        "model": os.environ.get(f"{env_prefix}_MODEL", default_model),
    }


# ---------------------------------------------------------------------------
# TARGET MODEL(S) — the system under test
# ---------------------------------------------------------------------------
# Default: Groq (fast, generous free tier). Override via .env — see .env.example.
TARGETS = [
    _model(
        "TARGET",
        default_type="openai_compatible",
        default_base_url="https://api.groq.com/openai/v1",
        default_model="llama-3.3-70b-versatile",
        default_api_key=os.environ.get("GROQ_API_KEY", ""),
    ),
]

# ---------------------------------------------------------------------------
# ATTACKER MODEL — generates & adapts attack prompts
# ---------------------------------------------------------------------------
# Default: local Ollama. Swap to a stronger model via .env for smarter,
# more coherent multi-turn escalation (see README "Using a stronger attacker").
ATTACKER_MODEL = _model(
    "ATTACKER",
    default_type="openai_compatible",
    default_base_url="http://localhost:11434/v1",
    default_model="llama3.2:3b",
    default_api_key="ollama",
)

# ---------------------------------------------------------------------------
# JUDGE MODEL — scores whether the target complied or refused
# ---------------------------------------------------------------------------
# Judge accuracy matters most of the three roles — a weak judge means the
# report can't be trusted. Prefer at least a 3B-class model here.
JUDGE_MODEL = _model(
    "JUDGE",
    default_type="openai_compatible",
    default_base_url="http://localhost:11434/v1",
    default_model="llama3.2:3b",
    default_api_key="ollama",
)

# ---------------------------------------------------------------------------
# RUN SETTINGS
# ---------------------------------------------------------------------------
VARIATIONS_PER_STRATEGY = int(os.environ.get("VARIATIONS_PER_STRATEGY", 5))
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", 120))
MAX_CONCURRENT_REQUESTS = int(os.environ.get("MAX_CONCURRENT_REQUESTS", 3))
REPORT_DIR = os.environ.get("REPORT_DIR", "reports")
VERBOSE = os.environ.get("VERBOSE", "false").lower() == "true"
