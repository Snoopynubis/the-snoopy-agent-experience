from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, List, Sequence
import json

from models.area import AreaState
from models.character import CharacterState
from models.event import AreaEvent

AreaId = int


@dataclass
class WorldState:
    """Complete snapshot of the world at a point in time."""

    available_areas: List[AreaState]
    characters_in_area: List[AreaId]
    characters: List[CharacterState]
    events: List[AreaEvent] = field(default_factory=list)

    def get_area_by_id(self, area_id: AreaId) -> AreaState:
        return self.available_areas[area_id]

    def snapshot(self) -> dict[str, Any]:
        return {
            "areas": [area.to_dict() for area in self.available_areas],
            "characters": [character.to_dict() for character in self.characters],
            "characters_in_area": list(self.characters_in_area),
            "events": [event.to_dict() for event in self.events],
        }

    @classmethod
    def from_snapshot(cls, payload: dict[str, Any]) -> WorldState:
        return cls(
            available_areas=[AreaState.from_dict(
                item) for item in payload.get("areas", [])],
            characters=[CharacterState.from_dict(
                item) for item in payload.get("characters", [])],
            characters_in_area=[int(idx) for idx in payload.get(
                "characters_in_area", [])],
            events=[AreaEvent.from_dict(item)
                    for item in payload.get("events", [])],
        )


def load_world_state(
    areas_path: str | Path | None = None,
    characters_path: str | Path | None = None,
) -> WorldState:
    base_dir = Path(__file__).resolve().parent.parent / "data"
    resolved_areas_path = _resolve_data_path(
        areas_path, base_dir / "areas" / "areas.json"
    )
    resolved_characters_path = _resolve_character_path(
        characters_path, base_dir / "characters"
    )

    areas_payload = _load_json_array(resolved_areas_path)
    characters_payload = _load_character_payloads(resolved_characters_path)

    area_states = [AreaState.from_dict(item) for item in areas_payload]
    area_index_by_name = {area.name: idx for idx,
                          area in enumerate(area_states)}

    character_states: List[CharacterState] = []
    characters_in_area: List[AreaId] = []
    for item in characters_payload:
        character = CharacterState.from_dict(item)
        home_area = item.get("home_area")
        if home_area not in area_index_by_name:
            raise ValueError(
                f"Character '{character.name}' references unknown area '{home_area}'"
            )
        characters_in_area.append(area_index_by_name[home_area])
        character_states.append(character)

    return WorldState(
        available_areas=area_states,
        characters_in_area=characters_in_area,
        characters=character_states,
    )


def save_world_state(world_state: WorldState, path: str | Path) -> None:
    payload = world_state.snapshot()
    path = Path(path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _resolve_data_path(provided: str | Path | None, default: Path) -> Path:
    path = Path(provided) if provided else default
    if not path.is_file():
        raise FileNotFoundError(f"Missing data file: {path}")
    return path


def _load_json_array(path: Path) -> List[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError(
            f"Expected list in {path}, got {type(payload).__name__}")
    return payload


def _resolve_character_path(provided: str | Path | None, default: Path) -> Path:
    path = Path(provided) if provided else default
    if not path.exists():
        raise FileNotFoundError(f"Missing character data path: {path}")
    return path


def _load_character_payloads(path: Path) -> List[dict[str, Any]]:
    if path.is_file():
        return [_load_json_object(path)]
    if path.is_dir():
        payloads: List[dict[str, Any]] = []
        for file_path in sorted(path.glob("*.json")):
            payloads.append(_load_json_object(file_path))
        if not payloads:
            raise ValueError(f"No character JSON files found in {path}")
        return payloads
    raise ValueError(f"Unsupported character path type: {path}")


def _load_json_object(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(
            f"Expected dict in character file {path}, got {type(payload).__name__}"
        )
    return payload


__all__ = [
    "AreaId",
    "WorldState",
    "load_world_state",
    "save_world_state",
]
