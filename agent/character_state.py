from dataclasses import dataclass


@dataclass
class CharacterState:
    name: str
    description: str

    memory: str
    mood: str
    energy_level: float
    internal_prompt: str
    external_prompt: str