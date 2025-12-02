import os
import sys
from typing import Optional

from agent.world_state import WorldState, load_world_state
from cli.renderer import CLIRenderer
from controller.llm import CharacterResponder
from controller.simulation_controller import SimulationController

try:  # POSIX raw input support
    import termios
    import tty
except ImportError:  # pragma: no cover - platform fallback
    termios = None
    tty = None


async def run_cli(
    turns: Optional[int] = None,
    debug: bool = False,
    fast_mode: bool = False,
    use_llm: bool = True,
    max_characters: Optional[int] = None,
    trace_llm: bool = False,
    interactive: bool = False,
) -> None:
    desired_turns = _resolve_turn_goal(turns, interactive)
    if fast_mode:
        use_llm = False
        if max_characters is None or max_characters > 3:
            max_characters = 3

    if interactive and not _stdin_supports_raw():
        print(
            "Interactive mode requested, but stdin is not a TTY. Falling back to autoplay mode."
        )
        interactive = False
        desired_turns = desired_turns or _env_turns() or 3
    world_state = load_world_state()
    _apply_character_limit(world_state, max_characters)

    responder = CharacterResponder(
        enabled=use_llm,
        thinking_enabled=False,
        trace_llm=trace_llm,
    )
    controller = SimulationController(world_state, responder, debug=debug)
    renderer = CLIRenderer(debug=debug)

    if interactive:
        print(
            "Interactive mode enabled. Press Enter to run the next turn. Esc or Ctrl+C exits."
        )

    try:
        while True:
            if desired_turns is not None and controller.turn_counter >= desired_turns:
                break

            renderer.render_area_overview(controller.turn_counter + 1, world_state)

            if interactive:
                if not _await_interactive_ack(controller.turn_counter + 1):
                    print("Exiting interactive mode.")
                    break

            events = await controller.play_turn()
            renderer.render_turn(controller.turn_counter, events, world_state)

    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")


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


def _resolve_turn_goal(turns: Optional[int], interactive: bool) -> Optional[int]:
    if turns is not None:
        return max(1, turns)
    env_value = _env_turns()
    if env_value is not None:
        return env_value
    if interactive:
        return None
    return 3


def _stdin_supports_raw() -> bool:
    return sys.stdin.isatty() and termios is not None and tty is not None


def _await_interactive_ack(next_turn: int) -> bool:
    prompt = f"\nPress Enter to run turn {next_turn} (Esc/Ctrl+C to exit): "
    if not _stdin_supports_raw():
        try:
            input(prompt)
            return True
        except EOFError:
            return False

    print(prompt, end="", flush=True)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            key = sys.stdin.read(1)
            if key in ("\r", "\n"):
                print()
                return True
            if key == "\x1b":  # ESC
                print("\nESC received.")
                return False
            if key == "\x03":  # Ctrl+C
                raise KeyboardInterrupt
            if key == "\x04":  # Ctrl+D / EOF
                print("\nCTRL+D received.")
                return False
            if key.lower() == "q":
                print("\n'q' pressed; exiting.")
                return False
            # Ignore any other key presses until Enter/Esc/Ctrl+C
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

