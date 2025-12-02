import os
from typing import Optional

from agent.world_state import WorldState, load_world_state
from cli.renderer import CLIRenderer
from controller.llm import CharacterResponder
from controller.simulation_controller import SimulationController


async def run_cli(
    turns: Optional[int] = None,
    debug: bool = False,
    fast_mode: bool = False,
    use_llm: bool = True,
    max_characters: Optional[int] = None,
) -> None:
    desired_turns = turns or _env_turns() or 3
    if fast_mode:
        use_llm = False
        if max_characters is None or max_characters > 3:
            max_characters = 3
    world_state = load_world_state()
    _apply_character_limit(world_state, max_characters)

    responder = CharacterResponder(enabled=use_llm, thinking_enabled=False)
    controller = SimulationController(world_state, responder, debug=debug)
    renderer = CLIRenderer(debug=debug)

    for _ in range(desired_turns):
        renderer.render_area_overview(controller.turn_counter + 1, world_state)
        events = await controller.play_turn()
        renderer.render_turn(controller.turn_counter, events, world_state)


def _env_turns() -> Optional[int]:
    raw_value = os.getenv("SNOOPY_TURNS")
    if raw_value is None:
        return None
    try:
        return max(1, int(raw_value))
    except ValueError:
        return None


def _apply_character_limit(world_state: WorldState, limit: Optional[int]) -> None:
    if not limit:
        return
    limited = max(1, min(limit, len(world_state.characters)))
    world_state.characters = world_state.characters[:limited]
    world_state.characters_in_area = world_state.characters_in_area[:limited]
