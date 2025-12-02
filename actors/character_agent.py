from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from langgraph.graph import END, START, StateGraph

from actors.fallbacks import FallbackContext, HeuristicFallback
from actors.prompting import PromptBuilder, PromptContext
from controller.mcp_tools import MCPTool, MCP_TOOLS
from controller.models import CharacterAction
from models.area import AreaState
from models.character import CharacterState
from services.llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentSettings:
    tool_catalog: Sequence[MCPTool] = field(
        default_factory=lambda: tuple(MCP_TOOLS)
    )
    trace_llm: bool = False


class CharacterAgent:
    """Encapsulates the LangChain/LangGraph powered reasoning flow for a character."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        settings: Optional[AgentSettings] = None,
    ) -> None:
        self.llm_client = llm_client or LLMClient(enabled=True)
        self.settings = settings or AgentSettings()
        self._prompt_builder = PromptBuilder()
        self._fallback = HeuristicFallback()
        self._graph = self._build_graph()

    async def generate_action(
        self,
        character: CharacterState,
        area: AreaState,
        public_context: str,
        directed_context: str,
        area_catalog: Sequence[AreaState],
        room_occupants: Sequence[str],
        area_state: str,
        area_overview: Sequence[tuple[str, List[str]]],
        tool_catalog: Optional[Sequence[MCPTool]] = None,
        turn_seed: int = 0,
    ) -> CharacterAction:
        catalog = tool_catalog or self.settings.tool_catalog
        prompt_context = PromptContext(
            character=character,
            area=area,
            public_context=public_context,
            directed_context=directed_context,
            room_occupants=room_occupants,
            area_state=area_state,
            area_catalog=area_catalog,
            tool_catalog=catalog,
            area_overview=area_overview,
        )
        fallback_context = FallbackContext(
            character=character,
            area=area,
            room_occupants=room_occupants,
            public_context=public_context,
            directed_context=directed_context,
            area_state=area_state,
            turn_seed=turn_seed,
            area_overview=area_overview,
        )

        if not self.llm_client.enabled:
            return self._fallback.generate(fallback_context)

        state: Dict[str, object] = {"prompt_context": prompt_context}
        try:
            result_state = await asyncio.to_thread(self._graph.invoke, state)
            action = result_state.get("action")
            if isinstance(action, CharacterAction):
                return action
            raise ValueError("Graph finished without producing a CharacterAction")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Falling back to heuristic action: %s", exc)
            return self._fallback.generate(fallback_context)

    def _build_graph(self):
        graph = StateGraph(dict)
        graph.add_node("compose_prompt", self._node_compose_prompt)
        graph.add_node("invoke_model", self._node_invoke_model)
        graph.add_node("parse_response", self._node_parse_response)
        graph.add_edge(START, "compose_prompt")
        graph.add_edge("compose_prompt", "invoke_model")
        graph.add_edge("invoke_model", "parse_response")
        graph.add_edge("parse_response", END)
        return graph.compile()

    def _node_compose_prompt(self, state: Dict[str, object]) -> Dict[str, object]:
        context = state["prompt_context"]
        if not isinstance(context, PromptContext):
            raise TypeError("prompt_context missing from state")
        prompt = self._prompt_builder.build(context)
        if self.settings.trace_llm:
            self._trace("PROMPT", prompt)
        state["prompt"] = prompt
        return state

    def _node_invoke_model(self, state: Dict[str, object]) -> Dict[str, object]:
        prompt = state.get("prompt")
        if not isinstance(prompt, str):
            raise TypeError("prompt missing from state")
        response_text = self.llm_client.invoke(prompt)
        if self.settings.trace_llm:
            self._trace("RESPONSE", response_text)
        state["raw_response"] = response_text
        return state

    def _node_parse_response(self, state: Dict[str, object]) -> Dict[str, object]:
        response_text = state.get("raw_response")
        if not isinstance(response_text, str):
            raise TypeError("raw_response missing from state")
        action = self._parse_response(response_text)
        state["action"] = action
        return state

    def _parse_response(self, response_text: str) -> CharacterAction:
        payload = json.loads(response_text)
        if not isinstance(payload, dict):
            raise ValueError("Model response was not a JSON object")
        addressed_to = payload.get("addressed_to")
        if addressed_to is not None and not isinstance(addressed_to, list):
            addressed_to = None
        move_to = payload.get("move_to_area")
        move_to = move_to.strip() if isinstance(move_to, str) else None
        area_update = payload.get("area_state_update")
        area_update = area_update.strip() if isinstance(area_update, str) else None
        tool = str(payload.get("tool", "informal_action")).strip() or "informal_action"
        content = str(payload.get("content", "")).strip()
        informal = bool(payload.get("informal", False))
        return CharacterAction(
            content=content,
            addressed_to=addressed_to,
            informal=informal,
            move_to_area=move_to,
            tool=tool,
            area_state_update=area_update,
        )

    def _trace(self, label: str, text: str) -> None:
        print(f"[LLM {label}] {text}")


__all__ = ["CharacterAgent", "AgentSettings"]
