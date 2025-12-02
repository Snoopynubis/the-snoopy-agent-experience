from agent.world_state import load_world_state


def main():
    world_state = load_world_state()
    print(
        "Loaded",
        len(world_state.available_areas),
        "areas and",
        len(world_state.characters),
        "characters from data files.",
    )


if __name__ == "__main__":
    main()
