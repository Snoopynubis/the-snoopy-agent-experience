# Services

Reusable integrations such as LLM clients or MCP connectors live under
`services/`. Keeping them isolated makes controllers stateless and easy to mock
in tests. At the moment the folder contains the Ollama `LLMClient`; MCP support
plugs in next to it.
