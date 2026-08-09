"""
Thin unified client so the rest of the tool doesn't care whether it's
talking to an OpenAI-compatible endpoint (OpenAI, Ollama, Groq, LM Studio,
vLLM, OpenRouter, etc.) or the Anthropic Messages API.
"""

import requests
import time


class ModelClient:
    def __init__(self, model_config: dict, timeout: int = 60, verbose: bool = False, max_retries: int = 1):
        self.cfg = model_config
        self.timeout = timeout
        self.verbose = verbose
        self.max_retries = max_retries

    def chat(self, messages: list[dict], max_tokens: int = 1024) -> str:
        """messages: [{"role": "user"/"assistant"/"system", "content": "..."}]
        Returns the assistant's reply text."""
        last_error = None
        for attempt in range(1, self.max_retries + 2):  # +1 initial try, +max_retries retries
            if self.verbose:
                host = self.cfg.get("base_url", self.cfg.get("type", "?"))
                suffix = f" (retry {attempt - 1})" if attempt > 1 else ""
                print(f"     [calling {self.cfg.get('model', '?')} @ {host}{suffix} ...]", flush=True)
            start = time.time()
            try:
                if self.cfg["type"] == "openai_compatible":
                    result = self._chat_openai_compatible(messages, max_tokens)
                elif self.cfg["type"] == "anthropic":
                    result = self._chat_anthropic(messages, max_tokens)
                else:
                    raise ValueError(f"Unknown model type: {self.cfg['type']}")
                if self.verbose:
                    print(f"     [done in {time.time() - start:.1f}s]", flush=True)
                return result
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_error = e
                if self.verbose:
                    print(f"     [attempt {attempt} failed after {time.time() - start:.1f}s: {e}]", flush=True)
                continue  # transient network/timeout issue — worth a retry
        raise last_error

    def _chat_openai_compatible(self, messages, max_tokens):
        url = f"{self.cfg['base_url'].rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.cfg['api_key']}",
        }
        payload = {
            "model": self.cfg["model"],
            "messages": messages,
            "max_tokens": max_tokens,
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        if not resp.ok:
            raise RuntimeError(f"{resp.status_code} error from {url}: {resp.text[:500]}")
        try:
            data = resp.json()
        except ValueError:
            raise RuntimeError(f"Non-JSON response ({resp.status_code}) from {url}: {resp.text[:500]!r}")
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise RuntimeError(f"Unexpected response shape from {url}: {str(data)[:500]}")

    def _chat_anthropic(self, messages, max_tokens):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.cfg["api_key"],
            "anthropic-version": "2023-06-01",
        }
        # Anthropic wants system prompt separated out
        system = None
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                chat_messages.append(m)
        payload = {
            "model": self.cfg["model"],
            "max_tokens": max_tokens,
            "messages": chat_messages,
        }
        if system:
            payload["system"] = system
        resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return "".join(
            block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
        )
