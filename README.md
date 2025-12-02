# The Snoopy Agent Experience

This project simulates a dynamic environment where characters from the Peanuts universe interact in various locations, each with their own unique personalities and memories. 

The characters include Snoopy, Woodstock, Lucy, Charlie Brown, Schroeder, and Peppermint Patty. They inhabit locations such as The Doghouse, The Treehouse, The Baseball Field, The Schoolyard, and The Music Room.


## Quick Start

```bash
# Install uv
uv sync
uv run main.py -- --turns 5  # simulate 5 turns (defaults to 3)
```

The CLI renderer outputs one section per turn, grouped by area with the
characters present. Informal actions (stage directions) are highlighted so you
can distinguish them from dialogue.

### Useful runtime flags

- `--debug` prints the per-character flow, including moves between areas.
- `--fast` disables LLM calls and caps the cast at three characters.
- `--no-llm` keeps the full roster but still skips Ollama.
- `--trace-llm` color-codes every prompt/response pair exchanged with the LLM (or
	highlights when prompts are skipped because the LLM is disabled).
- `--max-characters N` is handy when profiling or iterating on a subset.
- `--interactive` waits for you to press Enter before each turn (Esc/Ctrl+C exits).

By default the Ollama client is invoked with `thinking` disabled to keep DeepSeek
responses short. Combine `--fast` or `--no-llm` to bypass Ollama entirely.

### Fast mode vs standard play

Standard mode (no `--fast`) keeps the full cast, lets each character call out to
the local Ollama model, and therefore produces slower—but more varied—turns. Use
this when you want the richest RP output and do not mind the latency of local
LLM calls.

Fast mode flips three switches at once: it disables the LLM entirely, trims the
active roster to the first three characters, and relies on deterministic
heuristics for dialogue. The run finishes much faster and is perfect for smoke
tests or exercising the controller logic, but the conversations are intentionally
repetitive. If you only want to skip LLM calls while keeping the full cast, use
`--no-llm` instead of `--fast`.

### Interactive stepping

Need to narrate the action turn-by-turn? Launch the CLI with `--interactive` to
pause the simulation before each round. After the area overview prints, tap
Enter to advance. Press Esc or `Ctrl+C` any time to end the session. Provide
`--turns N` if you still want a hard cap; otherwise the simulation continues
until you exit.

## Architecture overview

- `models/`: world dataclasses plus JSON load/save helpers.
- `actors/`: LangGraph-powered character agents, prompt builders, and fallbacks.
- `controller/`: thin orchestrators (`SimulationController`, `GameMaster`, MCP tool metadata).
- `services/`: infrastructure concerns such as the Ollama `LLMClient` (and MCP wiring next to it).
- `cli/`: renderer plus runtime harness; only composes higher-level bricks.
- `data/`: authoritative source-of-truth JSON for areas and characters.

The controller never embeds prompt logic; it simply passes world snapshots into
`CharacterAgent` instances. That keeps serialization straightforward (use
`WorldState.snapshot()`) and lets tests simulate specific scenarios by
instantiating actors directly.

### Data-driven characters

Each character now lives in its own JSON file under `agent/characters/`. These
definitions include the internal pre-prompt (only visible to the model) and the
external description that other characters or UIs may show. Areas remain defined
in `agent/areas/areas.json`, ship with a mutable `informal_state`, and
characters may optionally move between areas by returning a `move_to_area`
value in their action JSON.

## MCP-oriented turn flow

Every character turn is modelled as an MCP-style tool call. The following tools
are available (see `controller/mcp_tools.py`):

- `room_status` (auto-run each turn) — returns the occupants and current vibe of
	the room.
- `broadcast` — talk to everyone present (@all).
- `direct_message` — focus on one or more listeners inside the same room.
- `informal_action` — stage directions or gestures flagged as informal.
- `reflect` — think out loud; only the speaker “hears” it.
- `area_update` — suggest a change to the area's informal state; the in-engine
	Game Master validates the proposal before applying it.

Each LLM response must specify which tool it is invoking plus optional fields
such as `addressed_to`, `area_state_update`, and `move_to_area`. The
`GameMaster` (see `controller/game_master.py`) reviews requested area updates to
keep the RP consistent.

## Smoke tests

Before running the CLI you can double-check that the local Ollama instance is
reachable and that the world definition loads correctly:

```bash
uv run python tests/test_environment.py
```