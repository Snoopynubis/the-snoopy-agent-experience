# Controller Layer

Controllers are stateless orchestrators that coordinate models, actors, and
services. They accept fully-populated world snapshots, call high-level bricks
like `CharacterAgent`, and emit events without embedding domain logic.
