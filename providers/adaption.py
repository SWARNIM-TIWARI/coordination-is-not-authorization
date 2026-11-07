"""Adaption Platform API adapter for the Protocol Premium experiment.

Uses the Adaption Responses API or official Python SDK. The API key is read strictly
from the ADAPTION_API_KEY environment variable. Under no circumstances is the
key printed, logged, stored in output files, or committed to version control.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

import httpx

try:
    from dotenv import load_dotenv
    # Load from current directory and from project root
    load_dotenv()
    _proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _env_file = os.path.join(_proj_root, ".env")
    if os.path.exists(_env_file):
        load_dotenv(_env_file)
except ImportError:
    pass

from providers import LLMProvider


class AdaptionProvider(LLMProvider):
    """Adaption Platform API provider for LLM inference.

    Features:
    - Session-level safety caps on total calls and tokens
    - Automatic exponential backoff on transient errors (429, 500, 502, 503)
    - Strict handling of 401/403 authorization failures
    - Detailed token usage tracking without leaking credentials
    - Supports both official SDK client and direct HTTP fallback
    """

    DEFAULT_MODEL = os.environ.get("ADAPTION_MODEL", "qwen3.5-397b")
    DEFAULT_BASE_URL = "https://api.prod.adaptionlabs.ai"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        max_calls_per_session: int = 250,
        max_tokens_per_session: int = 500_000,
        timeout_seconds: float = 60.0,
    ) -> None:
        api_key = os.environ.get("ADAPTION_API_KEY")
        if not api_key or not api_key.strip():
            raise EnvironmentError(
                "ADAPTION_API_KEY environment variable is not set. "
                "Please configure ADAPTION_API_KEY in your local .env file before initializing AdaptionProvider."
            )

        self._api_key = api_key.strip()
        self._model = model or os.environ.get("ADAPTION_MODEL", self.DEFAULT_MODEL)
        
        raw_base = (base_url or os.environ.get("ADAPTION_BASE_URL", self.DEFAULT_BASE_URL)).rstrip("/")
        if raw_base.endswith("/api/v1"):
            self._sdk_base_url = raw_base[:-len("/api/v1")]
            self._http_url = f"{raw_base}/responses"
        else:
            self._sdk_base_url = raw_base
            self._http_url = f"{raw_base}/api/v1/responses"
        self._base_url = self._sdk_base_url

        self._max_calls = max_calls_per_session
        self._max_tokens = max_tokens_per_session
        self._timeout = timeout_seconds

        self._call_count = 0
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._total_tokens = 0

        # Try initializing official Adaption SDK client if available
        self._sdk_client: Any = None
        try:
            import adaption
            self._sdk_client = adaption.Adaption(api_key=self._api_key, base_url=self._sdk_base_url)
        except Exception:
            self._sdk_client = None

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """Generate a response using Adaption Responses API."""
        if self._call_count >= self._max_calls:
            raise RuntimeError(
                f"[AdaptionProvider] Session call limit reached ({self._call_count}/{self._max_calls}). "
                "Halting to prevent unintended usage."
            )

        if self._total_tokens >= self._max_tokens:
            raise RuntimeError(
                f"[AdaptionProvider] Session token limit reached ({self._total_tokens}/{self._max_tokens}). "
                "Halting to prevent unintended usage."
            )

        target_model = model or self._model

        # Attempt via SDK if available, otherwise direct HTTP POST
        if self._sdk_client is not None and hasattr(self._sdk_client, "responses"):
            return self._generate_via_sdk(messages, target_model, temperature, max_tokens, seed)
        return self._generate_via_http(messages, target_model, temperature, max_tokens, seed)

    def _split_messages(self, messages: list[dict[str, str]]) -> tuple[str | None, Any]:
        """Separate system instructions from input content/messages."""
        system_instructions: str | None = None
        cleaned_input: list[dict[str, str]] = []

        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                system_instructions = content
            else:
                cleaned_input.append({"role": role, "content": content})

        if len(cleaned_input) == 1 and isinstance(cleaned_input[0].get("content"), str):
            input_payload: Any = cleaned_input[0]["content"]
        elif cleaned_input:
            input_payload = cleaned_input
        else:
            input_payload = messages

        return system_instructions, input_payload

    def _generate_via_http(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        seed: int | None,
    ) -> dict[str, Any]:
        """HTTP POST to /api/v1/responses endpoint with exponential backoff."""
        url = self._http_url
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ProtocolPremium/1.0",
        }

        system_instructions, input_payload = self._split_messages(messages)

        payload: dict[str, Any] = {
            "model": model,
            "input": input_payload,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_instructions:
            payload["instructions"] = system_instructions
        if seed is not None:
            payload["seed"] = seed

        max_retries = 3
        backoff_delays = [1.0, 2.5, 5.0]

        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=self._timeout) as client:
                    resp = client.post(url, headers=headers, json=payload)

                if resp.status_code == 200:
                    data = resp.json()
                    content = self._extract_content(data)
                    usage = data.get("usage", {})
                    p_tokens = usage.get("input_tokens", usage.get("prompt_tokens", len(str(messages).split())))
                    c_tokens = usage.get("output_tokens", usage.get("completion_tokens", len(content.split())))
                    t_tokens = usage.get("total_tokens", p_tokens + c_tokens)

                    self._call_count += 1
                    self._prompt_tokens += p_tokens
                    self._completion_tokens += c_tokens
                    self._total_tokens += t_tokens

                    return {
                        "content": content,
                        "usage": {
                            "prompt_tokens": p_tokens,
                            "completion_tokens": c_tokens,
                            "total_tokens": t_tokens,
                        },
                        "model": model,
                        "finish_reason": data.get("finish_reason", "stop"),
                    }

                elif resp.status_code in (401, 403):
                    raise PermissionError(
                        f"[AdaptionProvider] Authentication failed (HTTP {resp.status_code}): "
                        f"{resp.text}. Please verify ADAPTION_API_KEY and grant credits."
                    )
                elif resp.status_code == 429:
                    retry_after = float(resp.headers.get("Retry-After", backoff_delays[attempt]))
                    print(f"[AdaptionProvider] Rate limited (429). Waiting {retry_after}s...", file=sys.stderr)
                    time.sleep(retry_after)
                else:
                    print(
                        f"[AdaptionProvider] HTTP error {resp.status_code}: {resp.text}. "
                        f"Retrying (attempt {attempt + 1}/{max_retries})...",
                        file=sys.stderr,
                    )
                    time.sleep(backoff_delays[attempt])

            except httpx.RequestError as exc:
                print(f"[AdaptionProvider] Network error: {exc}. Retrying...", file=sys.stderr)
                time.sleep(backoff_delays[attempt])

        raise RuntimeError(f"[AdaptionProvider] Failed to generate after {max_retries} attempts.")

    def _generate_via_sdk(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        seed: int | None,
    ) -> dict[str, Any]:
        """Call Adaption official SDK directly."""
        try:
            system_instructions, input_payload = self._split_messages(messages)

            kwargs: dict[str, Any] = {
                "model": model,
                "input": input_payload,
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            if system_instructions:
                kwargs["instructions"] = system_instructions

            response = self._sdk_client.responses.create(**kwargs)

            # Extract output text from official Response object
            content = getattr(response, "output_text", None)
            if not content:
                output = getattr(response, "output", None)
                if isinstance(output, str):
                    content = output
                elif isinstance(output, list) and output:
                    content = str(output[0])
                else:
                    content = getattr(response, "content", "") or str(response)

            usage = getattr(response, "usage", None)
            p_tokens = getattr(usage, "input_tokens", getattr(usage, "prompt_tokens", len(str(messages).split()))) if usage else len(str(messages).split())
            c_tokens = getattr(usage, "output_tokens", getattr(usage, "completion_tokens", len(content.split()))) if usage else len(content.split())
            t_tokens = getattr(usage, "total_tokens", p_tokens + c_tokens) if usage else (p_tokens + c_tokens)

            self._call_count += 1
            self._prompt_tokens += p_tokens
            self._completion_tokens += c_tokens
            self._total_tokens += t_tokens

            return {
                "content": content,
                "usage": {
                    "prompt_tokens": p_tokens,
                    "completion_tokens": c_tokens,
                    "total_tokens": t_tokens,
                },
                "model": model,
                "finish_reason": getattr(response, "status", "stop") or "stop",
            }
        except Exception as exc:
            # Fall back to HTTP if SDK fails or raises an error
            print(f"[AdaptionProvider] SDK call encountered issue ({exc}), falling back to HTTP.", file=sys.stderr)
            return self._generate_via_http(messages, model, temperature, max_tokens, seed)

    @staticmethod
    def _extract_content(data: dict[str, Any]) -> str:
        """Extract text content across variations of API response payloads."""
        if "output_text" in data and isinstance(data["output_text"], str):
            return data["output_text"]
        if "content" in data:
            if isinstance(data["content"], str):
                return data["content"]
            if isinstance(data["content"], list):
                return "\n".join(str(item) for item in data["content"])
        if "output" in data and isinstance(data["output"], str):
            return data["output"]
        if "response" in data and isinstance(data["response"], str):
            return data["response"]
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice:
                return choice["message"].get("content", "")
            return choice.get("text", "")
        return str(data)

    def get_name(self) -> str:
        return "adaption"

    def get_usage(self) -> dict[str, Any]:
        """Return session usage statistics."""
        return {
            "calls": self._call_count,
            "prompt_tokens": self._prompt_tokens,
            "completion_tokens": self._completion_tokens,
            "total_tokens": self._total_tokens,
            "max_calls": self._max_calls,
            "max_tokens": self._max_tokens,
        }

    def check_health(self) -> bool:
        """Verify API key validity and platform connectivity."""
        try:
            res = self.generate(
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return bool(res.get("content"))
        except Exception as exc:
            print(f"[AdaptionProvider] Health check failed: {exc}", file=sys.stderr)
            return False
