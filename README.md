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
- `--max-characters N` is handy when profiling or iterating on a subset.

By default the Ollama client is invoked with `thinking` disabled to keep DeepSeek
responses short. Combine `--fast` or `--no-llm` to bypass Ollama entirely.

### Data-driven characters

Each character now lives in its own JSON file under `agent/characters/`. These
definitions include the internal pre-prompt (only visible to the model) and the
external description that other characters or UIs may show. Areas remain defined
in `agent/areas/areas.json`, and characters may optionally move between areas by
returning a `move_to_area` value in their action JSON.

## Smoke tests

Before running the CLI you can double-check that the local Ollama instance is
reachable and that the world definition loads correctly:

```bash
uv run python tests/test_environment.py
```