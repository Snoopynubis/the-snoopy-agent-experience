import asyncio
import json
import logging
from typing import List, Optional

from agent.area_state import AreaState
from agent.character_state import CharacterState
from agent.constants import (
    DEFAULT_MAX_TOKENS,
    OLLAMA_MODEL,
    OLLAMA_SERVER_URL,
)
from controller.mcp_tools import MCPTool, MCP_TOOLS
from controller.models import CharacterAction

logger = logging.getLogger(__name__)

PROMPT_COLOR = "\033[95m"
RESPONSE_COLOR = "\033[92m"
TRACE_RESET = "\033[0m"


class CharacterResponder:
    """Formats prompts for characters and queries the local Ollama model."""

    def __init__(
        self,
        model_name: str = OLLAMA_MODEL,
        base_url: str = OLLAMA_SERVER_URL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        enabled: bool = True,
        thinking_enabled: bool = False,
        trace_llm: bool = False,
    ) -> None:
        self.max_tokens = max_tokens
        self.enabled = enabled
        self.trace_llm = trace_llm
        self._llm = (
            self._build_llm(model_name, base_url, thinking_enabled)
            if enabled
            else None
        )

    async def generate_action(
        self,
        character: CharacterState,
        area: AreaState,
        public_context: str,
        directed_context: str,
        area_catalog: Optional[List[AreaState]] = None,
        room_occupants: Optional[List[str]] = None,
        area_state: str = "",
        tool_catalog: Optional[List[MCPTool]] = None,
        turn_seed: int = 0,
        area_overview: Optional[List[tuple[str, List[str]]]] = None,
    ) -> CharacterAction:
        tool_catalog = tool_catalog or MCP_TOOLS
        prompt = self._compose_prompt(
            character=character,
            area=area,
            public_context=public_context,
            directed_context=directed_context,
            area_catalog=area_catalog,
            room_occupants=room_occupants,
            area_state=area_state,
            tool_catalog=tool_catalog,
            area_overview=area_overview,
        )

        sent_to_llm = self._llm is not None
        if self.trace_llm:
            status = "submitted" if sent_to_llm else "skipped (LLM disabled)"
            self._trace("PROMPT", prompt, PROMPT_COLOR, status)

        if self._llm is None:
            fallback = self._fallback_action(
                character=character,
                area=area,
                room_occupants=room_occupants or [],
                public_context=public_context,
                directed_context=directed_context,
                area_state=area_state,
                turn_seed=turn_seed,
                area_overview=area_overview,
            )
            if self.trace_llm:
                self._trace("RESPONSE", f"[fallback] {fallback.content}", RESPONSE_COLOR)
            return fallback

        try:
            response_text = await asyncio.to_thread(self._llm.invoke, prompt)
            if self.trace_llm:
                self._trace("RESPONSE", response_text, RESPONSE_COLOR)
            return self._parse_response(response_text)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Falling back to heuristic action: %s", exc)
            fallback = self._fallback_action(
                character=character,
                area=area,
                room_occupants=room_occupants or [],
                public_context=public_context,
                directed_context=directed_context,
                area_state=area_state,
                turn_seed=turn_seed,
                area_overview=area_overview,
            )
            if self.trace_llm:
                self._trace(
                    "RESPONSE",
                    f"[fallback after error] {fallback.content}",
                    RESPONSE_COLOR,
                )
            return fallback

    def _build_llm(self, model_name: str, base_url: str, thinking_enabled: bool):
        try:
            from langchain_ollama import OllamaLLM

            return OllamaLLM(
                model=model_name,
                base_url=base_url,
                options={
                    "thinking": thinking_enabled,
                    "temperature": 0.6,
                },
            )
        except Exception as exc:  # pragma: no cover - missing runtime dependency
            logger.info("Ollama client unavailable, using heuristic actions: %s", exc)
            return None

    def _compose_prompt(
        self,
        character: CharacterState,
        area: AreaState,
        public_context: str,
        directed_context: str,
        area_catalog: Optional[List[AreaState]] = None,
        room_occupants: Optional[List[str]] = None,
        area_state: str = "",
        tool_catalog: Optional[List[MCPTool]] = None,
        area_overview: Optional[List[tuple[str, List[str]]]] = None,
    ) -> str:
        available_names = (
            ", ".join(entry.name for entry in area_catalog)
            if area_catalog
            else area.name
        )
        occupants = ", ".join(room_occupants or []) or "Just you"
        area_vibe = area_state or "No informal notes yet."
        tool_lines = "\n".join(
            f"- {tool.name}: {tool.summary} Usage: {tool.usage}"
            for tool in (tool_catalog or [])
        )
        overview_lines = []
        if area_overview:
            for name, names in area_overview:
                roster = ", ".join(names) if names else "empty"
                label = f"{name}: {roster}"
                if name == area.name:
                    label += " (you are here)"
                overview_lines.append(f"- {label}")
        room_peek_text = "\n".join(overview_lines) if overview_lines else "No additional rooms to peek."
        action_tool_names = [
            tool.name
            for tool in (tool_catalog or [])
            if tool.name not in {"room_status", "room_peek"}
        ]
        allowed_actions = ", ".join(action_tool_names) or "informal_action"
        return (
            f"{character.internal_prompt}\n"
            f"You are currently in '{area.name}' described as: {area.description}.\n"
            f"Mood: {character.mood}. Energy: {character.energy_level}.\n"
            f"Personal memory: {character.memory}.\n"
            f"Occupants in the room (via room_status tool): {occupants}.\n"
            f"Current informal scene notes: {area_vibe}\n"
            "Room peek overview (who is in every area):\n"
            f"{room_peek_text}\n"
            "Recent public happenings in this area:\n"
            f"{public_context if public_context else 'None yet.'}\n"
            "Messages specifically to you:\n"
            f"{directed_context if directed_context else 'None.'}\n"
            "Available MCP tools:\n"
            f"{tool_lines}\n"
            "Respond with JSON containing keys 'content' (string under 80 words),\n"
            "'addressed_to' (array of character names or null), and 'informal'\n"
            "(boolean, true when the action is a gesture/aside rather than dialogue).\n"
            "Optionally include 'move_to_area' set to the exact name of another area\n"
            "if you want to relocate after speaking. Available areas: \n"
            f"{available_names}.\n"
            "Always include 'tool' (one of "
            f"{allowed_actions}) and 'area_state_update' (string or null).\n"
            "Default to 'broadcast' when more than one listener is present."
            "Use 'direct_message' only when focusing someone specific and reserve"
            " 'reflect' for rare moments when you are completely alone.\n"
            "Use the room_peek overview if you feel lonely—it's encouraged to move where the conversation is.\n"
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
            move_to = payload.get("move_to_area")
            if isinstance(move_to, str) and move_to.strip():
                move_to = move_to.strip()
            else:
                move_to = None
            area_update = payload.get("area_state_update")
            if isinstance(area_update, str) and area_update.strip():
                area_update = area_update.strip()
            else:
                area_update = None
            tool = str(payload.get("tool", "informal_action")).strip() or "informal_action"

            return CharacterAction(
                content=str(payload.get("content", "")).strip(),
                addressed_to=addressed_to,
                informal=bool(payload.get("informal", False)),
                move_to_area=move_to,
                tool=tool,
                area_state_update=area_update,
            )
        except Exception as exc:
            logger.warning("Could not parse model response '%s': %s", response_text, exc)
            return CharacterAction(content=response_text.strip() or "...")

    def _fallback_action(
        self,
        character: CharacterState,
        area: AreaState,
        room_occupants: List[str],
        public_context: str,
        directed_context: str,
        area_state: str,
        turn_seed: int,
    ) -> CharacterAction:
        others = [name for name in room_occupants if name != character.name]
        topic_source = directed_context or public_context or area_state or area.description
        topic_line = topic_source.splitlines()[-1] if topic_source else ""
        if ":" in topic_line:
            topic_line = topic_line.split(":", 1)[1].strip()
        topic_line = topic_line or f"what to do in {area.name}"
        lowered = topic_line.lower()
        if any(
            marker in lowered
            for marker in ("let's tackle", "hey everyone", "what do you think")
        ) or "@" in topic_line or "->" in topic_source:
            topic_line = area.description
        topic_line = topic_line[:120]

        def _clean_fragment(fragment: str) -> str:
            fragment = " ".join(fragment.split())
            fragment = fragment.strip(" ,.!?")
            return fragment or area.description

        if others:
            listener = others[0]
            if listener.lower() in topic_line.lower():
                topic_line = area.description
            for token in (listener, listener.split()[0] if " " in listener else listener):
                topic_line = topic_line.replace(token, "").strip()
            for token in (character.name, character.name.split()[0]):
                topic_line = topic_line.replace(token, "").strip()
            if not topic_line:
                topic_line = area.description
            topic_line = _clean_fragment(topic_line)
            templates = [
                "{listener}, let's tackle {topic}. I'll cover the opening move if you chime in.",
                "{listener}, can you back me up while I handle {topic}?",
                "Hey {listener}, {topic}. What do you think?",
            ]
            seed = sum(ord(c) for c in (character.name + topic_line)) + turn_seed
            template = templates[seed % len(templates)]
            content = template.format(listener=listener, topic=topic_line)
            return CharacterAction(
                content=content,
                addressed_to=[listener],
                informal=False,
                tool="direct_message",
            )

        broadcast_templates = [
            "Hey everyone, {topic}. Let's bend {area} to our plan.",
            "Team, {topic}. We can turn {area} into momentum.",
            "Listen up! {topic}. {area} gives us room to improvise.",
        ]
        seed = sum(ord(c) for c in (character.name + area.name + topic_line)) + turn_seed
        if character.name.lower() in topic_line.lower():
            topic_line = area.description
        for token in (character.name, character.name.split()[0]):
            topic_line = topic_line.replace(token, "").strip()
        if not topic_line:
            topic_line = area.description
        topic_line = _clean_fragment(topic_line)
        content = broadcast_templates[seed % len(broadcast_templates)].format(
            topic=topic_line,
            area=area.name,
        )
        return CharacterAction(
            content=content,
            addressed_to=None,
            informal=False,
            tool="broadcast",
        )

    def _trace(self, label: str, text: str, color: str, status: str = "") -> None:
        suffix = f" ({status})" if status else ""
        print(f"{color}[LLM {label}{suffix}]{TRACE_RESET} {text}")
