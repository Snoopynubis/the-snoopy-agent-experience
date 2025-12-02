from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class AreaEvent:
    """A single action or utterance emitted during a turn."""

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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> AreaEvent:
        return cls(
            area_id=int(payload["area_id"]),
            turn=int(payload["turn"]),
            character=str(payload["character"]),
            content=str(payload.get("content", "")),
            addressed_to=payload.get("addressed_to"),
            informal=bool(payload.get("informal", False)),
            tool=str(payload.get("tool", "informal_action")),
        )
