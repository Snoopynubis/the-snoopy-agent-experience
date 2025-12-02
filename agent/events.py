"""Backward-compatible shim for legacy imports.

Prefer importing :class:`AreaEvent` from ``models.event`` going forward.
"""

from models.event import AreaEvent

__all__ = ["AreaEvent"]
