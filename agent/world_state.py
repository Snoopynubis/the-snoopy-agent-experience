from __future__ import annotations

import json

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Tuple

from agent.area_state import AreaState
from agent.character_state import CharacterState

AreaId = int


@dataclass
class WorldState:
    available_areas: List[AreaState]
    characters_in_area: List[AreaId]
    characters: List[CharacterState]
    events: List[Tuple[AreaId, str]]

    def get_area_by_id(self, area_id: AreaId) -> AreaState:
        return self.available_areas[area_id]

    def update_character(self, character_id: int) -> WorldState:
        # TODO
        return self


def load_world_state(
    areas_path: str | Path | None = None,
    characters_path: str | Path | None = None,
) -> WorldState:
    """Load the world definition from JSON files.

    When ``areas_path`` or ``characters_path`` is omitted, the files inside the
    package (``agent/areas/areas.json`` and ``agent/characters/characters.json``)
    are used.
    """

    base_dir = Path(__file__).resolve().parent
    resolved_areas_path = _resolve_data_path(
        areas_path, base_dir / "areas" / "areas.json"
    )
    resolved_characters_path = _resolve_data_path(
        characters_path, base_dir / "characters" / "characters.json"
    )

    areas_payload = _load_json_array(resolved_areas_path)
    characters_payload = _load_json_array(resolved_characters_path)

    area_states = [
        AreaState(name=item["name"], description=item["description"])
        for item in areas_payload
    ]

    area_index_by_name = {area.name: idx for idx,
                          area in enumerate(area_states)}

    character_states: List[CharacterState] = []
    characters_in_area: List[AreaId] = []
    for item in characters_payload:
        home_area = item.get("home_area")
        if home_area not in area_index_by_name:
            raise ValueError(
                f"Character '{item.get('name')}' references unknown area '{home_area}'"
            )

        characters_in_area.append(area_index_by_name[home_area])
        character_states.append(
            CharacterState(
                name=item["name"],
                description=item["description"],
                memory=item.get("memory", ""),
                mood=item.get("mood", "Neutral"),
                energy_level=float(item.get("energy_level", 0.5)),
            )
        )

    return WorldState(
        available_areas=area_states,
        characters_in_area=characters_in_area,
        characters=character_states,
        events=[],
    )


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
