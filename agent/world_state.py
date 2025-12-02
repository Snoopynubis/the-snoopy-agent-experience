from dataclasses import dataclass
from typing import List
from agent.area_state import AreaState
from agent.character_state import CharacterState

AreaId = int


@dataclass
class WorldState:
    available_areas: List[AreaState]
    characters_in_area: List[AreaId]
    characters: List[CharacterState]
    events: List[(AreaId, str)]

    def get_area_by_id(self, area_id: AreaId) -> AreaState:
        return self.available_areas[area_id]

    def update_character(self, character_id: int) -> WorldState:
        # TODO
        return self
