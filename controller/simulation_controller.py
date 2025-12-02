from __future__ import annotations

from typing import List, Optional, Tuple

from agent.area_state import AreaState
from agent.character_state import CharacterState
from agent.events import AreaEvent
from agent.world_state import AreaId, WorldState
from controller.llm import CharacterResponder


class SimulationController:
    """Coordinates character turns and persists resulting events."""

    def __init__(
        self,
        world_state: WorldState,
        responder: Optional[CharacterResponder] = None,
    ) -> None:
        self.world_state = world_state
        self.responder = responder or CharacterResponder()
        self.turn_counter = 0

    async def play_turn(self) -> List[AreaEvent]:
        """Run one sequential turn for every character."""

        self.turn_counter += 1
        turn_events: List[AreaEvent] = []

        for idx, character in enumerate(self.world_state.characters):
            area_id = self.world_state.characters_in_area[idx]
            area = self.world_state.get_area_by_id(area_id)
            public_context, directed_context = self._compile_context(
                area_id=area_id,
                character_name=character.name,
            )
            action = await self.responder.generate_action(
                character=character,
                area=area,
                public_context=public_context,
                directed_context=directed_context,
            )

            if not action.content.strip():
                continue

            event = AreaEvent(
                area_id=area_id,
                turn=self.turn_counter,
                character=character.name,
                content=action.content,
                addressed_to=action.addressed_to,
                informal=action.informal,
            )
            self.world_state.events.append(event)
            turn_events.append(event)

        return turn_events

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
