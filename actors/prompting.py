from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from models.area import AreaState
from models.character import CharacterState

from controller.mcp_tools import MCPTool


@dataclass(frozen=True)
class PromptContext:
    character: CharacterState
    area: AreaState
    public_context: str
    directed_context: str
    room_occupants: Sequence[str]
    area_state: str
    area_catalog: Sequence[AreaState]
    tool_catalog: Sequence[MCPTool]
    area_overview: Sequence[tuple[str, List[str]]]


class PromptBuilder:
    def build(self, context: PromptContext) -> str:
        return "\n".join(
            [
                self._character_header(context),
                self._room_snapshot(context),
                self._area_overview(context),
                self._context_threads(context),
                self._tool_directions(context),
                self._response_instructions(context),
            ]
        )

    def _character_header(self, context: PromptContext) -> str:
        character = context.character
        area = context.area
        return (
            f"{character.internal_prompt}\n"
            f"You are currently in '{area.name}' described as: {area.description}.\n"
            f"Mood: {character.mood}. Energy: {character.energy_level}.\n"
            f"Personal memory: {character.memory}."
        )

    def _room_snapshot(self, context: PromptContext) -> str:
        occupants = ", ".join(context.room_occupants) or "Just you"
        area_vibe = context.area_state or "No informal notes yet."
        return (
            f"Occupants in the room: {occupants}.\n"
            f"Current informal scene notes: {area_vibe}"
        )

    def _area_overview(self, context: PromptContext) -> str:
        lines = []
        for area_name, names in context.area_overview:
            roster = ", ".join(names) if names else "empty"
            suffix = " (you are here)" if area_name == context.area.name else ""
            lines.append(f"- {area_name}: {roster}{suffix}")
        overview = "\n".join(lines) if lines else "- No additional rooms to peek."
        return "Room peek overview (who is in every area):\n" + overview

    def _context_threads(self, context: PromptContext) -> str:
        public_block = context.public_context or "None yet."
        directed_block = context.directed_context or "None."
        return (
            "Recent public happenings in this area:\n"
            f"{public_block}\n"
            "Messages specifically to you:\n"
            f"{directed_block}"
        )

    def _tool_directions(self, context: PromptContext) -> str:
        lines = [
            f"- {tool.name}: {tool.summary} Usage: {tool.usage}"
            for tool in context.tool_catalog
        ]
        available = "\n".join(lines)
        return "Available MCP tools:\n" + available

    def _response_instructions(self, context: PromptContext) -> str:
        action_tool_names = [
            tool.name
            for tool in context.tool_catalog
            if tool.name not in {"room_status", "room_peek"}
        ]
        allowed_actions = ", ".join(action_tool_names) or "informal_action"
        available_names = ", ".join(area.name for area in context.area_catalog)
        return (
            "Respond with JSON containing keys 'content' (string under 80 words),\n"
            "'addressed_to' (array of character names or null), and 'informal' (boolean).\n"
            "Optionally include 'move_to_area' set to the exact name of another area if you want to relocate after speaking.\n"
            f"Available areas: {available_names}.\n"
            "Always include 'tool' (one of " + allowed_actions + ") and 'area_state_update' (string or null).\n"
            "Default to 'broadcast' when more than one listener is present. Use 'direct_message' when focusing someone specific and reserve 'reflect' for when you are alone.\n"
            "Use the room peek overview if you feel lonely—it's encouraged to move where the conversation is.\n"
            "Stay in character, keep the reply concise (< 120 tokens), and never include additional commentary besides the JSON object."
        )


__all__ = ["PromptBuilder", "PromptContext"]
