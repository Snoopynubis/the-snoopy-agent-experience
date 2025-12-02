from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from controller.models import CharacterAction
from models.area import AreaState
from models.character import CharacterState


@dataclass(frozen=True)
class FallbackContext:
    character: CharacterState
    area: AreaState
    room_occupants: Sequence[str]
    public_context: str
    directed_context: str
    area_state: str
    turn_seed: int
    area_overview: Sequence[tuple[str, List[str]]]


class HeuristicFallback:
    def __init__(self) -> None:
        self._dm_templates = [
            "{listener}, let's tackle {topic}. I'll cover the opening move if you back me up.",
            "{listener}, can you back me up while I handle {topic}?",
            "Hey {listener}, {topic}. What do you think?",
        ]
        self._broadcast_templates = [
            "Hey everyone, {topic}. Let's bend {area} to our plan.",
            "Team, {topic}. We can turn {area} into momentum.",
            "Listen up! {topic}. {area} gives us room to improvise.",
        ]

    def generate(self, context: FallbackContext) -> CharacterAction:
        others = [name for name in context.room_occupants if name != context.character.name]
        topic = self._derive_topic(context)
        if others:
            listener = others[0]
            seed = self._seed(context.character.name + topic, context.turn_seed)
            template = self._dm_templates[seed % len(self._dm_templates)]
            content = template.format(listener=listener, topic=topic)
            return CharacterAction(
                content=content,
                addressed_to=[listener],
                informal=False,
                tool="direct_message",
            )

        move_target = self._pick_move_target(context)
        seed = self._seed(context.character.name + context.area.name + topic, context.turn_seed)
        template = self._broadcast_templates[seed % len(self._broadcast_templates)]
        content = template.format(topic=topic, area=context.area.name)
        return CharacterAction(
            content=content,
            addressed_to=None,
            informal=False,
            tool="broadcast",
            move_to_area=move_target,
        )

    def _derive_topic(self, context: FallbackContext) -> str:
        topic_source = (
            context.directed_context
            or context.public_context
            or context.area_state
            or context.area.description
        )
        topic_line = topic_source.splitlines()[-1] if topic_source else context.area.description
        for token in (context.character.name, context.character.name.split()[0]):
            topic_line = topic_line.replace(token, "").strip()
        topic_line = topic_line or context.area.description
        return topic_line[:120]

    def _pick_move_target(self, context: FallbackContext) -> Optional[str]:
        populated = [
            (name, len(names or []))
            for name, names in context.area_overview
            if name != context.area.name and names
        ]
        if not populated:
            return None
        populated.sort(key=lambda item: item[1], reverse=True)
        return populated[0][0]

    def _seed(self, text: str, turn_seed: int) -> int:
        return sum(ord(ch) for ch in text) + turn_seed


__all__ = ["FallbackContext", "HeuristicFallback"]
