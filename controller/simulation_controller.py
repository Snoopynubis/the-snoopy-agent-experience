from __future__ import annotations

from typing import List, Optional, Tuple

from actors.character_agent import CharacterAgent
from models.area import AreaState
from models.character import CharacterState
from models.event import AreaEvent
from models.world import AreaId, WorldState
from controller.game_master import GameMaster
from controller.mcp_tools import MCP_TOOLS
from controller.models import CharacterAction


class SimulationController:
    """Coordinates character turns and persists resulting events."""

    def __init__(
        self,
        world_state: WorldState,
        character_agent: Optional[CharacterAgent] = None,
        debug: bool = False,
        game_master: Optional[GameMaster] = None,
    ) -> None:
        self.world_state = world_state
        self.character_agent = character_agent or CharacterAgent()
        self.turn_counter = 0
        self.debug = debug
        self._area_name_to_id = {
            area.name: idx for idx, area in enumerate(world_state.available_areas)
        }
        self.game_master = game_master or GameMaster()

    async def play_turn(self) -> List[AreaEvent]:
        """Run one sequential turn for every character."""
        self.turn_counter += 1
        turn_events: List[AreaEvent] = []
        area_snapshot = self.snapshot_area_overview()

        for idx, character in enumerate(self.world_state.characters):
            area_id = self.world_state.characters_in_area[idx]
            event = await self._handle_character_turn(
                idx, character, area_id, area_snapshot
            )
            if event:
                self.world_state.events.append(event)
                turn_events.append(event)

        return turn_events

    async def _handle_character_turn(
        self,
        idx: int,
        character: CharacterState,
        area_id: AreaId,
        area_snapshot: List[tuple[AreaState, List[str]]],
    ) -> Optional[AreaEvent]:
        """Process a single character's turn and return an event or None."""
        self._log(
            f"Character {character.name} preparing to act in {self.world_state.get_area_by_id(area_id).name}"
        )
        area = self.world_state.get_area_by_id(area_id)
        room_occupants = [char.name for char in self.get_area_population(area_id)]
        area_overview = [
            (snapshot_area.name, occupants)
            for snapshot_area, occupants in area_snapshot
        ]
        public_context, directed_context = self._compile_context(
            area_id=area_id, character_name=character.name
        )

        action = await self.character_agent.generate_action(
            character=character,
            area=area,
            public_context=public_context,
            directed_context=directed_context,
            area_catalog=self.world_state.available_areas,
            room_occupants=room_occupants,
            area_state=area.informal_state,
            tool_catalog=MCP_TOOLS,
            area_overview=area_overview,
            turn_seed=self.turn_counter,
        )

        if not action.content.strip():
            return None

        addressed = self._determine_audience(action, room_occupants, character.name)

        event = AreaEvent(
            area_id=area_id,
            turn=self.turn_counter,
            character=character.name,
            content=action.content,
            addressed_to=addressed,
            informal=action.informal or action.tool == "informal_action",
            tool=action.tool,
        )

        if action.move_to_area:
            self._move_character(idx, character, action.move_to_area)

        if action.area_state_update:
            approved, reason = self.game_master.approve_area_update(
                area, character.name, action.area_state_update
            )
            if approved:
                area.informal_state = action.area_state_update
                self._log(
                    f"Area '{area.name}' vibe updated by {character.name}: {area.informal_state}"
                )
            else:
                self._log(
                    f"Area update rejected ({reason}) for {character.name} in {area.name}"
                )

        return event

    def _compile_context(
        self,
        area_id: AreaId,
        character_name: str,
    ) -> Tuple[str, str]:
        public_lines: List[str] = []
        directed_lines: List[str] = []

        for event in self.world_state.events:
            if event.area_id != area_id:
                continue
            line = f"{event.character}: {event.content}"
            if event.addressed_to and character_name in event.addressed_to:
                directed_lines.append(line)
            elif event.addressed_to is None:
                public_lines.append(line)
            else:
                # The event was directed to someone else but still audible.
                public_lines.append(line)

        return "\n".join(public_lines[-5:]), "\n".join(directed_lines[-3:])

    def get_area_population(self, area_id: AreaId) -> List[CharacterState]:
        return [
            character
            for idx, character in enumerate(self.world_state.characters)
            if self.world_state.characters_in_area[idx] == area_id
        ]

    def get_area(self, area_id: AreaId) -> AreaState:
        return self.world_state.get_area_by_id(area_id)

    def snapshot_area_overview(self) -> List[tuple[AreaState, List[str]]]:
        snapshot: List[tuple[AreaState, List[str]]] = []
        for area_id, area in enumerate(self.world_state.available_areas):
            occupants = self.get_area_population(area_id)
            snapshot.append((area, [char.name for char in occupants]))
        return snapshot

    def _determine_audience(
        self,
        action: CharacterAction,
        room_occupants: List[str],
        speaker_name: str,
    ) -> Optional[List[str]]:
        if action.tool == "broadcast":
            return None
        if action.tool == "direct_message":
            targets = [
                name for name in (action.addressed_to or []) if name in room_occupants
            ]
            return targets or None
        if action.tool == "reflect":
            return [speaker_name]
        return action.addressed_to

    def _move_character(
        self, idx: int, character: CharacterState, destination: str
    ) -> None:
        target_id = self._area_name_to_id.get(destination)
        if target_id is None:
            self._log(
                f"Character {character.name} requested unknown area '{destination}'. Ignoring move."
            )
            return
        self.world_state.characters_in_area[idx] = target_id
        self._log(
            f"Character {character.name} moves to {self.world_state.get_area_by_id(target_id).name}"
        )

    def _log(self, message: str) -> None:
        if self.debug:
            print(f"[DEBUG] {message}")
