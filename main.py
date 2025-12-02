import argparse
import asyncio

from cli.app import run_cli


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Snoopy simulation CLI")
    parser.add_argument(
        "--turns",
        type=int,
        default=None,
        help="Number of turns to simulate (defaults to env or 3)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print detailed step-by-step information during the simulation",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: disable LLM calls and limit to three characters",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip Ollama completions and use heuristic actions",
    )
    parser.add_argument(
        "--max-characters",
        type=int,
        default=None,
        help="Limit the number of active characters (useful for profiling)",
    )
    args = parser.parse_args()

    use_llm = not args.no_llm
    asyncio.run(
        run_cli(
            turns=args.turns,
            debug=args.debug,
            fast_mode=args.fast,
            use_llm=use_llm,
            max_characters=args.max_characters,
        )
    )


if __name__ == "__main__":
    main()
