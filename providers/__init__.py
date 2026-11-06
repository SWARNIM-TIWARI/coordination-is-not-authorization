"""Provider interfaces for the Protocol Premium experiment."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Abstract interface for LLM inference providers."""

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        seed: int | None = None,
    ) -> dict[str, Any]:
        """Generate a completion.

        Args:
            messages: list of {"role": "system"|"user"|"assistant", "content": str}
            model: model identifier (provider-specific)
            temperature: sampling temperature
            max_tokens: max output tokens
            seed: optional seed for reproducibility

        Returns:
            {
                "content": str,  # the generated text
                "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int},
                "model": str,
                "finish_reason": str
            }
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Provider name for logging."""
        pass
