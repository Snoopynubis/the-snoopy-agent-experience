from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class CharacterState:
    """Represents a character's current configuration and personality."""

    name: str
    description: str
    memory: str
    mood: str
    energy_level: float
    internal_prompt: str
    external_prompt: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> CharacterState:
        return cls(
            name=str(payload["name"]),
            description=str(payload.get("description", "")),
            memory=str(payload.get("memory", "")),
            mood=str(payload.get("mood", "Neutral")),
            energy_level=float(payload.get("energy_level", 0.5)),
            internal_prompt=str(payload.get("prompt_internal", payload.get("internal_prompt", ""))),
            external_prompt=str(payload.get("prompt_external", payload.get("external_prompt", ""))),
        )
