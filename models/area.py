from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AreaState:
    """Represents a physical location in the Snoopy simulation."""

    name: str
    description: str
    informal_state: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "description": self.description,
            "informal_state": self.informal_state,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, str]) -> AreaState:
        return cls(
            name=payload["name"],
            description=payload["description"],
            informal_state=payload.get("informal_state", ""),
        )
