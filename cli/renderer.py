from collections import defaultdict
from typing import Dict, Iterable, List

from agent.events import AreaEvent
from agent.world_state import WorldState

TURN_COLOR = "\033[31m"
RESET_COLOR = "\033[0m"
LABEL_COLOR = "\033[36m"
INFORMAL_COLOR = "\033[33m"


class CLIRenderer:
    def render_turn(
        self,
        turn_number: int,
        events: List[AreaEvent],
        world_state: WorldState,
    ) -> None:
        print(f"{TURN_COLOR}-------- TURN {turn_number}{RESET_COLOR}")

        if not events:
            print("No characters acted this turn.\n")
            return

        events_by_area: Dict[int, List[AreaEvent]] = defaultdict(list)
        for event in events:
            events_by_area[event.area_id].append(event)

        for area_id, area_events in events_by_area.items():
            area = world_state.get_area_by_id(area_id)
            occupants = self._characters_in_area(area_id, world_state)
            print(f"{LABEL_COLOR}[{area.name}] {', '.join(occupants)}{RESET_COLOR}")
            for event in area_events:
                prefix = "(informal)" if event.informal else f"{event.character}:"
                color = INFORMAL_COLOR if event.informal else ""
                reset = RESET_COLOR if color else ""
                addressed = (
                    f" -> {', '.join(event.addressed_to)}"
                    if event.addressed_to
                    else ""
                )
                print(f"  {color}{prefix}{reset} {event.content}{addressed}")
            print()

    def _characters_in_area(self, area_id: int, world_state: WorldState) -> List[str]:
        names: List[str] = []
        for idx, character in enumerate(world_state.characters):
            if world_state.characters_in_area[idx] == area_id:
                names.append(character.name)
        return names
