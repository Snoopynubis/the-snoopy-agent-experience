"""Backward-compatible shim for legacy imports.

Prefer importing :class:`AreaState` from ``models.area`` going forward.
"""

from models.area import AreaState

__all__ = ["AreaState"]