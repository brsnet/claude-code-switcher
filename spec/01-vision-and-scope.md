# 01 — Vision and Scope

## Problem

Claude Code normally selects models by logical names, but different environments may require local models, external APIs, fallback on unavailability, and cost control. The system needs to intermediate these requests without forcing the client to know details of each provider.

## Solution

The Claude Code Switcher will be a local HTTP proxy compatible with Anthropic Messages. It will receive a request, normalize content, filter tools, resolve a candidate chain, and stream the chosen provider's response in the format expected by the client.

## Functional Goals

- `SCOPE-001` — Expose a local API compatible with the messages endpoint used by Claude Code.
- `SCOPE-002` — Map `opus`, `sonnet`, and `haiku` to configurable routes.
- `SCOPE-003` — Support NVIDIA NIM, OpenRouter, DeepSeek, Ollama, LM Studio, and llama.cpp.
- `SCOPE-004` — Try more than one NVIDIA model configured via numbered variables.
- `SCOPE-005` — Execute retries and failover without duplicating content or tools.
- `SCOPE-006` — Restrict tools to the configured minimum set.
- `SCOPE-007` — Emit valid SSE streaming.
- `SCOPE-008` — Offer health check, structured logs, and candidate benchmarking.

## Non-Functional Goals

- `NFR-001` — Proxy overhead before external call less than 100 ms on normal path.
- `NFR-002` — No credentials in logs, responses, documentation, or exceptions.
- `NFR-003` — Deterministic behavior for the same route configuration.
- `NFR-004` — Failure of one provider cannot make healthy candidates unavailable.
- `NFR-005` — System must run on Windows with PowerShell, Python 3.14, and `uv`.
- `NFR-006` — Every async operation must release connections and tasks on completion.

## Out of Initial Scope

- Graphical interface.
- Conversation storage.
- Provider billing management.
- Automatic `.env` modification in production.
- Real-time cost-based balancing.
- Guarantee of features not offered by the model, such as vision or forced tools.
- Automatic server execution without user authorization.

## Actors

- **Claude Code:** Client sending messages and tools.
- **User:** Configures models, starts server, evaluates results.
- **Router:** Resolves candidates and coordinates attempts.
- **Adapter:** Translates requests and responses of a provider.
- **Provider:** Local or remote service executing inference.

## Success Criteria

- A compatible request produces a valid response from the first healthy candidate.
- An eligible error before first content advances to the next candidate.
- A failure after content start terminates the response without silent second execution.
- The model receives only the necessary tools.
- A benchmark identifies slow, invalid, or tool-incapable models.