from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AreaEvent:
    area_id: int
    turn: int
    character: str
    content: str
    addressed_to: Optional[List[str]]
    informal: bool = False
    tool: str = "informal_action"

    def is_addressed_to(self, target: str) -> bool:
        if self.addressed_to is None:
            return True
        return target in self.addressed_to
