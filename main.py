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
    args = parser.parse_args()
    asyncio.run(run_cli(args.turns))


if __name__ == "__main__":
    main()
