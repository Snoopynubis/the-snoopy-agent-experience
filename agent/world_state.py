"""Backward-compatible shim for legacy imports.

Prefer importing objects from ``models.world``.
"""

from models.world import (
    AreaId,
    WorldState,
    load_world_state,
    save_world_state,
)

__all__ = [
    "AreaId",
    "WorldState",
    "load_world_state",
    "save_world_state",
]
