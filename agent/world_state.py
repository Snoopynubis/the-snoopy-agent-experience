from dataclasses import dataclass
from typing import List
from agent.area_state import AreaState
from agent.character_state import CharacterState


@dataclass
class WorldState:
    areas: List[AreaState]
    characters: List[CharacterState]
