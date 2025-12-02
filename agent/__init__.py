"""Legacy namespace maintained for backwards compatibility.

Prefer importing from ``models`` going forward.
"""

from models import (  # re-export
	AreaEvent,
	AreaId,
	AreaState,
	CharacterState,
	WorldState,
	load_world_state,
	save_world_state,
)

__all__ = [
	"AreaState",
	"CharacterState",
	"AreaEvent",
	"WorldState",
	"AreaId",
	"load_world_state",
	"save_world_state",
]
