# Codex Switcher

## Project Identity

This project is a local, independent router for using Codex with different providers and AI models. The solution must offer transparent model switching, fault tolerance, compatible streaming, and low operational cost, preserving the normal Codex experience.

The project, its documentation, its technical decisions, and its code are authored by the owner of this repository. Do not introduce references, documentation dependencies, or attributions to projects previously used as inspiration or prototype.

## Design Specifications

Before analyzing, planning, or changing code, read `spec/README.md` and the SDDs related to the affected area. The `spec` folder is the source of truth for requirements, contracts, states, acceptance criteria, and implementation order.

- Do not implement behavior that contradicts an SDD.
- If a decision needs to change, update the corresponding SDD in the same work.
- Cite the requirement identifiers addressed when summarizing an implementation.
- Preserve existing identifiers to maintain traceability.

## Objectives

- Expose a local API compatible with the Anthropic Messages protocol.
- Allow logical names `opus`, `sonnet`, and `haiku` to be routed without being tied to a single model.
- Automatically switch between providers and models when unavailability occurs.
- Prioritize fast responses and reliable tool usage.
- Reduce the tool set sent to models to decrease tokens, latency, and confusion.
- Support local models and external APIs in the same installation.
- Keep sensitive configuration exclusively in environment variables.

## Development Environment

- Primary operating system: Windows with PowerShell.
- Python: 3.14.
- Environment and execution manager: `uv`.
- HTTP server: FastAPI with Uvicorn.
- Never run the project with global Python when there is an equivalent command via `uv run`.
- The server is controlled by the user. Do not start, stop, or restart processes without explicit request.

Default execution command:

```powershell
uv run uvicorn server:app --host 0.0.0.0 --port 8082
```

Client configuration:

```text
ANTHROPIC_BASE_URL=http://127.0.0.1:8082
ANTHROPIC_AUTH_TOKEN=<local-token>
```

The base address must not end in `/v1`, as the client adds the endpoint path.

## Supported Providers

The router must work with the following providers:

- NVIDIA NIM
- OpenRouter
- DeepSeek
- Ollama
- LM Studio
- llama.cpp

Each provider must be implemented as an isolated adapter and registered in a central catalog. Shared Anthropic protocol code must remain in neutral modules, without cross-imports between providers.

Model prefixes:

| Provider | Prefix |
| --- | --- |
| NVIDIA NIM | `nvidia_nim/` |
| OpenRouter | `open_router/` |
| DeepSeek | `deepseek/` |
| Ollama | `ollama/` |
| LM Studio | `lmstudio/` |
| llama.cpp | `llamacpp/` |

## Configuration by Environment

Never write real keys in this file, in code, in tests, logs, or commits. Use only the `.env` file, which must remain ignored by Git. The `.env.example` must contain only fictitious values.

Expected variables:

```dotenv
# Credentials
NVIDIA_API_KEY=
OPENROUTER_API_KEY=
DEEPSEEK_API_KEY=

# NVIDIA Models; numbering can grow without fixed limit
NVIDIA_NIM_MODEL1=nvidia/nemotron-3-super-120b-a12b
NVIDIA_NIM_MODEL2=nvidia/nemotron-3-ultra-550b-a55b
NVIDIA_NIM_MODEL3=poolside/laguna-xs-2.1

# Compatibility with old configuration, if needed
NVIDIA_NIM_MODEL=

# Other models
OPENROUTER_MODEL=deepseek/deepseek-v4.1-flash
DEEPSEEK_MODEL=deepseek-chat
OLLAMA_MODEL=qwen3.5:9b

# Local endpoints
OLLAMA_BASE_URL=http://localhost:11434/v1
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LLAMACPP_BASE_URL=http://localhost:8080/v1

# Logical routes, in priority order
ROUTER_OPUS=nvidia_nim,open_router,ollama
ROUTER_SONNET=nvidia_nim,open_router,ollama
ROUTER_HAIKU=nvidia_nim,open_router,ollama

# Performance and tools
TOOL_ALLOWLIST=Read,Edit,Write,Bash,Glob,Grep
ENABLE_THINKING=false
HTTP_READ_TIMEOUT=600
PROVIDER_MAX_CONCURRENCY=5

# Optional Ollama adjustments for Haiku
HAIKU_LOCAL_NUM_CTX=
HAIKU_LOCAL_THINK=false
HAIKU_LOCAL_MAX_CONCURRENCY=
```

Empty or unused variables must be removed from active configuration. Do not keep dead options just for compatibility, except when the interface is already published and migration needs to be gradual.

## NVIDIA Model Catalog

- Automatically discover `NVIDIA_NIM_MODEL1`, `NVIDIA_NIM_MODEL2`, up to `NVIDIA_NIM_MODEL[N]`.
- Accept gaps in numbering.
- Order models by numeric index.
- Remove duplicates preserving first occurrence.
- Keep optional support for `NVIDIA_NIM_MODEL` as legacy variable.
- When expanding `nvidia_nim` in a route, test all configured models in declared order.
- An invalid model must not prevent the use of others.

## Logical Routing

Names received from Codex must be treated as capability categories, not as permanent binding to a provider:

- Opus requests use `ROUTER_OPUS`.
- Sonnet requests use `ROUTER_SONNET`.
- Haiku requests use `ROUTER_HAIKU`.
- A name with explicit prefix selects the indicated provider directly.
- Each route item can represent an entire provider or a specific model.

The router must generate an ordered candidate chain and advance only when the current attempt fails before producing significant content.

## Retries and Failover

Errors eligible for retry or candidate switch:

```text
402, 429, 500, 502, 503, 504, 529
```

Rules:

- Retry transient errors using exponential backoff with small random variation.
- Respect per-provider concurrency limits.
- After exhausting candidate attempts, proceed to the next model in the chain.
- Failover only before emission of significant text or tool call.
- After streaming starts, never silently switch models, as this can duplicate text, commands, or edits.
- Definitive errors occurring after streaming starts must be sent as valid SSE events.
- A `402` balance failure may trigger failover but must appear clearly in logs.

## Minimum Tool Policy

By default, send only:

```text
Read, Edit, Write, Bash, Glob, Grep
```

Filter rules:

- Create a copy of the request before altering the tool list.
- Preserve a tool explicitly required in `tool_choice`, even if not in the default list.
- Remove or clear `tool_choice` when no compatible tools remain.
- Do not send dozens of tools the model won't need.
- Add extra tools only when the work actually requires them.
- Consider that web search or subagent tools won't be available until included or explicitly required.

## Thinking and Local Models

- Extended reasoning mode is disabled by default to prioritize speed and compatibility.
- The Ollama adapter must accept automatic selection or absence of tool.
- Do not assume Ollama supports forced tool, images, or specific extensions without testing the active model.
- Context, concurrency, and local thinking may have separate configuration for the Haiku route.
- Slow local models on first load can be kept as last fallback, never as first option without favorable benchmark.

## Streaming and Compatibility

- Accept messages with `system`, `user`, and `assistant` roles, converting them correctly for the target provider format.
- Produce valid SSE events compatible with Codex.
- The keepalive mechanism must use a single producer to avoid context conflict between async tasks.
- OpenAI-compatible clients must be closed with the async method actually offered by the installed library.
- A failure before the first content must be able to propagate internally to trigger failover.
- Never return corrupted text, repeated fragments, or provider internal structures as normal response.

## Optimizations

- Ignore title generation when it adds no value to the main execution.
- Load and validate environment variables once at startup.
- Use list accumulation to build strings during loops.
- Avoid recursion in flows with variable depth.
- Keep prompts and tool schemas small.
- Do not repeat file reading or tool discovery unnecessarily.
- Measure time to first token, total time, tool call validity, and failure rate.

## Observability

Logs must allow reconstructing a request without revealing secrets. Recommended events:

- `ROUTE`: chosen logical route.
- `ROUTE_CHAIN`: expanded candidates in attempt order.
- `API_REQUEST`: provider call start.
- `<PROVIDER>_STREAM`: streaming start or progress.
- `ROUTE_FAILOVER`: reason and next candidate.
- `<PROVIDER>_ERROR`: normalized error and request identifier.

Never log tokens, authorization headers, or full content of private files. A `HEAD /api/hello` probe returning `404` may be just a client check and does not characterize router failure.

## Model Benchmark

Maintain a small, reproducible test for each candidate model:

- Use only the synthetic `Read` tool.
- Do not send real project code.
- Limit response to approximately 128 tokens.
- Disable thinking.
- Apply 30-second limit per model.
- Record latency, HTTP status, and tool call validity.
- Warn that external APIs may consume credits.

Criteria for remaining in active route:

- Respond within expected limit.
- Emit a valid tool call when requested.
- Do not return corrupted characters or incoherent text.
- Do not persistently fail due to nonexistent model, authorization, or balance.

Reference results obtained during initial build, subject to remeasurement:

| Candidate | Observed Result | Initial Decision |
| --- | --- | --- |
| Nemotron Super 120B | temporary overload in one run | keep as primary with fallback |
| Nemotron Ultra 550B | valid tool in ~2.9 s | keep |
| Laguna XS 2.1 | valid tool in ~1.2 s | keep |
| OpenRouter DeepSeek | valid tool in ~1.7 s | keep |
| DeepSeek direct | insufficient balance (`402`) | exclude from route until regularized |
| GLM 5.3 tested | nonexistent model (`404`) | remove |
| Kimi K3 tested | above 30 s | remove |
| Ollama Qwen local | above 30 s in cold test | keep only as final fallback |

These numbers are not guarantees. Repeat benchmark after model, hardware, network, or provider changes.

## Recommended Structure

```text
api/
  model_router.py       # catalog, routes, expansion, and tool filter
  services.py           # execution, streaming, retries, and failover
config/
  settings.py           # environment variable reading and validation
core/
  anthropic/            # shared Anthropic protocol
providers/
  registry.py           # central adapter registry
  openai_compat.py      # base for OpenAI-compatible APIs
  anthropic_messages.py # protocol conversions
  rate_limit.py         # concurrency and wait
  ollama/               # Ollama-specific behavior
scripts/
  benchmark_model_tools.py
tests/
```

## Engineering Principles

- Fix the root cause, not just the symptom.
- Prefer the simplest implementation that preserves reliability.
- Avoid duplication and extract common behavior to neutral modules.
- Prefer composition over code copying.
- Encapsulate internal state with appropriate public methods.
- Keep provider-specific configuration inside the corresponding adapter.
- Remove dead code, old options, and unnecessary fixed values.
- Use platform-independent names in shared modules.
- Complete migrations in the same work, removing obsolete shortcuts when safe.
- Do not add `# type: ignore` or `# ty: ignore`; fix the type at the source.

## Mandatory Change Flow

1. Read relevant files and reproduce behavior.
2. Identify cause and affected components.
3. Plan the smallest complete change.
4. Implement incrementally.
5. Add or update tests, including edge cases.
6. Run checks in the order below.
7. Check logs and streaming behavior.
8. Document residual risks.

Checks:

```powershell
uv run ruff format
uv run ruff check
uv run ty check
uv run pytest
```

All must pass. The initial suite reference is 1,025 tests passed; the number may grow and must not be used as a fixed limit.

## Security

- Treat any key published in terminal, conversation, screenshot, or log as compromised and replace it at the provider.
- Do not copy secrets to documentation, examples, fixtures, or error messages.
- Validate local and external URLs before sending data.
- Do not execute destructive commands or external changes without explicit authorization.
- Do not start the server automatically when the user prefers to control it.

## Project Constraints

- Do not create technical or documentary link with the previously used prototype.
- Do not mention third-party repositories as the origin of this project.
- Do not bind `opus`, `sonnet`, or `haiku` to a single model.
- Do not switch provider after significant content has been emitted.
- Do not increase the tool list without proven necessity.
- Do not mask authentication, balance, or limit errors as success.
- Do not claim a model works without validating response and tool usage.

## Agent Delivery Pattern

Every technical delivery must end with:

- `[Changed Files]`
- `[Changed Logic]`
- `[Verification Method]`
- `[Residual Risks]`

If there are no known residual risks, explicitly declare `none`.