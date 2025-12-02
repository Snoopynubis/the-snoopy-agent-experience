from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CharacterAction:
    content: str
    addressed_to: Optional[List[str]] = None
    informal: bool = False
    move_to_area: Optional[str] = None
    tool: str = "informal_action"
    area_state_update: Optional[str] = None
