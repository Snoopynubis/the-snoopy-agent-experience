# Actors

Actor modules encapsulate the behavior of individual characters. Each actor is
implemented as a LangGraph workflow that consumes a snapshot of the world
(`PromptContext`) and produces a `CharacterAction`. The `CharacterAgent`
combines the prompt builder, LangChain LLM client, and heuristic fallbacks so it
can run deterministically (fast mode) or delegate to Ollama.
