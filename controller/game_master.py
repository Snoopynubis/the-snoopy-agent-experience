from __future__ import annotations

import re
from typing import Tuple

from agent.area_state import AreaState


class GameMaster:
    """Simple arbiter that approves or rejects requested area-state updates."""

    _max_length = 220
    _forbidden_pattern = re.compile(r"\b(bomb|blood|murder)\b", re.IGNORECASE)

    def approve_area_update(
        self,
        area: AreaState,
        character_name: str,
        proposal: str,
    ) -> Tuple[bool, str]:
        text = proposal.strip()
        if not text:
            return False, "empty proposal"
        if len(text) > self._max_length:
            return False, "too long"
        if self._forbidden_pattern.search(text):
            return False, "fails safety filter"
        if text == area.informal_state:
            return False, "no change"
        return True, "accepted"
