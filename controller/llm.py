import asyncio
import json
import logging

from agent.area_state import AreaState
from agent.character_state import CharacterState
from agent.constants import (
    DEFAULT_MAX_TOKENS,
    OLLAMA_MODEL,
    OLLAMA_SERVER_URL,
)
from controller.models import CharacterAction

logger = logging.getLogger(__name__)


class CharacterResponder:
    """Formats prompts for characters and queries the local Ollama model."""

    def __init__(
        self,
        model_name: str = OLLAMA_MODEL,
        base_url: str = OLLAMA_SERVER_URL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self.max_tokens = max_tokens
        self._llm = self._build_llm(model_name, base_url)

    async def generate_action(
        self,
        character: CharacterState,
        area: AreaState,
        public_context: str,
        directed_context: str,
    ) -> CharacterAction:
        prompt = self._compose_prompt(
            character=character,
            area=area,
            public_context=public_context,
            directed_context=directed_context,
        )

        if self._llm is None:
            return self._fallback_action(character, public_context, directed_context)

        try:
            response_text = await asyncio.to_thread(self._llm.invoke, prompt)
            return self._parse_response(response_text)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Falling back to heuristic action: %s", exc)
            return self._fallback_action(character, public_context, directed_context)

    def _build_llm(self, model_name: str, base_url: str):
        try:
            from langchain_ollama import OllamaLLM

            return OllamaLLM(model=model_name, base_url=base_url)
        except Exception as exc:  # pragma: no cover - missing runtime dependency
            logger.info("Ollama client unavailable, using heuristic actions: %s", exc)
            return None

    def _compose_prompt(
        self,
        character: CharacterState,
        area: AreaState,
        public_context: str,
        directed_context: str,
    ) -> str:
        return (
            f"{character.internal_prompt}\n"
            f"You are currently in '{area.name}' described as: {area.description}.\n"
            f"Mood: {character.mood}. Energy: {character.energy_level}.\n"
            f"Personal memory: {character.memory}.\n"
            "Recent public happenings in this area:\n"
            f"{public_context if public_context else 'None yet.'}\n"
            "Messages specifically to you:\n"
            f"{directed_context if directed_context else 'None.'}\n"
            "Respond with JSON containing keys 'content' (string under 80 words),\n"
            "'addressed_to' (array of character names or null), and 'informal'\n"
            "(boolean, true when the action is a gesture/aside rather than dialogue).\n"
            f"Stay in character, keep the reply concise (< {min(self.max_tokens, 120)} tokens),\n"
            "and never include additional commentary besides the JSON object."
        )

    def _parse_response(self, response_text: str) -> CharacterAction:
        try:
            payload = json.loads(response_text)
            if not isinstance(payload, dict):
                raise ValueError("Model response was not a JSON object")
            addressed_to = payload.get("addressed_to")
            if addressed_to is not None and not isinstance(addressed_to, list):
                addressed_to = None
            return CharacterAction(
                content=str(payload.get("content", "")).strip(),
                addressed_to=addressed_to,
                informal=bool(payload.get("informal", False)),
            )
        except Exception as exc:
            logger.warning("Could not parse model response '%s': %s", response_text, exc)
            return CharacterAction(content=response_text.strip() or "...")

    def _fallback_action(
        self,
        character: CharacterState,
        public_context: str,
        directed_context: str,
    ) -> CharacterAction:
        snippet = directed_context or public_context or "Quiet room."
        summary = snippet.splitlines()[0] if snippet else "Quiet room."
        content = (
            f"{character.name} reflects: {summary}"
            if summary
            else f"{character.name} pauses to gather their thoughts."
        )
        informal = "gesture" in summary.lower() or "quiet" in summary.lower()
        return CharacterAction(content=content, informal=informal)
