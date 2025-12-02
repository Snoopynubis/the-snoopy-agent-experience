import os
from typing import Optional

from agent.world_state import load_world_state
from cli.renderer import CLIRenderer
from controller.llm import CharacterResponder
from controller.simulation_controller import SimulationController


async def run_cli(turns: Optional[int] = None) -> None:
    desired_turns = turns or _env_turns() or 3
    world_state = load_world_state()
    controller = SimulationController(world_state, CharacterResponder())
    renderer = CLIRenderer()

    for _ in range(desired_turns):
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
