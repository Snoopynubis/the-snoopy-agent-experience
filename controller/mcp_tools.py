from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class MCPTool:
    name: str
    summary: str
    usage: str


MCP_TOOLS: List[MCPTool] = [
    MCPTool(
        name="room_status",
        summary="List everyone in the current area and summarize the latest scene notes.",
        usage="Use before acting so you know who can hear you."
    ),
    MCPTool(
        name="room_peek",
        summary="Preview who is in every other area to decide whether to relocate.",
        usage="Consult this before setting 'move_to_area'—prefer rooms that already have people."
    ),
    MCPTool(
        name="broadcast",
        summary="Address everyone in the current area (@all).",
        usage="Set 'addressed_to' to null and write dialogue for the whole room."
    ),
    MCPTool(
        name="direct_message",
        summary="Speak to one or more specific characters in the room.",
        usage="Populate 'addressed_to' with the character names you are focusing on."
    ),
    MCPTool(
        name="informal_action",
        summary="Describe a non-verbal or stage-direction style action.",
        usage="Set 'informal' to true and keep the text short, third-person works well."
    ),
    MCPTool(
        name="reflect",
        summary="Think out loud to yourself without addressing others.",
        usage="Mark the tool as 'reflect'; the system will treat it as self-talk."
    ),
    MCPTool(
        name="area_update",
        summary="Suggest an update to the area's informal state / vibe (GM validated).",
        usage="Provide 'area_state_update' with new descriptive text; only use when you have meaningfully changed the scene."
    ),
]
