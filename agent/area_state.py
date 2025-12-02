from dataclasses import dataclass


@dataclass
class AreaState:
    name: str
    description: str
    informal_state: str = ""