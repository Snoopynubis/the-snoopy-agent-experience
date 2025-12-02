from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from agent.constants import (
    DEFAULT_MAX_TOKENS,
    OLLAMA_MODEL,
    OLLAMA_SERVER_URL,
)

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    model_name: str = OLLAMA_MODEL
    base_url: str = OLLAMA_SERVER_URL
    max_tokens: int = DEFAULT_MAX_TOKENS
    thinking_enabled: bool = False


class LLMClient:
    """Thin wrapper around LangChain's Ollama integration."""

    def __init__(self, enabled: bool = True, config: Optional[LLMConfig] = None) -> None:
        self.enabled = enabled
        self.config = config or LLMConfig()
        self._llm = self._build_llm() if enabled else None

    def _build_llm(self):
        try:
            from langchain_ollama import OllamaLLM

            return OllamaLLM(
                model=self.config.model_name,
                base_url=self.config.base_url,
                options={
                    "thinking": self.config.thinking_enabled,
                    "temperature": 0.6,
                    "num_predict": self.config.max_tokens,
                },
            )
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.warning("Unable to initialize OllamaLLM, falling back to heuristics: %s", exc)
            self.enabled = False
            return None

    def invoke(self, prompt: str) -> str:
        if not self.enabled or self._llm is None:
            raise RuntimeError("LLM client invoked while disabled")
        return self._llm.invoke(prompt)


__all__ = ["LLMClient", "LLMConfig"]
