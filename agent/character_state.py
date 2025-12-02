"""Backward-compatible shim for legacy imports.

Prefer importing :class:`CharacterState` from ``models.character`` going forward.
"""

from models.character import CharacterState

__all__ = ["CharacterState"]