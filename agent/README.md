# Agent (Legacy)

This package now acts as a compatibility shim for older imports. All core data
classes live under `models/`, and JSON definitions live in `data/`. Existing
code that imports `agent.area_state` or `agent.world_state` will continue to
work, but new code should prefer the dedicated `models.*` modules.
