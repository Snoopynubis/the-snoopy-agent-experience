from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.constants import OLLAMA_MODEL, OLLAMA_SERVER_URL
from agent.world_state import load_world_state


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def check_ollama_instance() -> CheckResult:
    url = f"{OLLAMA_SERVER_URL}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status != 200:
                return CheckResult(
                    name="ollama",
                    ok=False,
                    detail=f"Unexpected status {response.status} for {url}",
                )
            payload = json.load(response)
    except urllib.error.URLError as exc:
        return CheckResult(
            name="ollama",
            ok=False,
            detail=f"Cannot reach {url}. Start Ollama? ({exc})",
        )

    models = {item.get("name") for item in payload.get("models", []) if item}
    if OLLAMA_MODEL not in models:
        return CheckResult(
            name="ollama",
            ok=False,
            detail=f"Model '{OLLAMA_MODEL}' not listed in Ollama tags",
        )
    return CheckResult(
        name="ollama",
        ok=True,
        detail=f"Ollama reachable with model '{OLLAMA_MODEL}' registered",
    )


def check_world_state_loading() -> CheckResult:
    try:
        world = load_world_state()
    except Exception as exc:  # pragma: no cover - defensive
        return CheckResult("world_state", False, f"load_world_state() failed: {exc}")

    if not world.available_areas:
        return CheckResult("world_state", False, "No areas defined")
    if not world.characters:
        return CheckResult("world_state", False, "No characters defined")

    missing_prompts = [
        character.name
        for character in world.characters
        if not character.internal_prompt or not character.external_prompt
    ]
    if missing_prompts:
        return CheckResult(
            "world_state",
            False,
            f"Characters missing prompts: {', '.join(missing_prompts)}",
        )

    return CheckResult(
        "world_state",
        True,
        f"Loaded {len(world.characters)} characters across {len(world.available_areas)} areas",
    )


def main() -> None:
    checks = [check_ollama_instance(), check_world_state_loading()]
    failures = [check for check in checks if not check.ok]

    for check in checks:
        status = "OK" if check.ok else "FAIL"
        print(f"[{status}] {check.name}: {check.detail}")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
