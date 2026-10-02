# 02 — Architecture

## Overview

```text
Claude Code
    |
    | Anthropic Messages + SSE
    v
API FastAPI
    |
    +--> input normalization
    +--> tool filtering
    +--> route resolution
    v
Attempt Orchestrator
    |
    +--> concurrency limit
    +--> retry with backoff
    +--> pre-stream failover
    v
Provider Registry
    |
    +--> NVIDIA NIM
    +--> OpenRouter
    +--> DeepSeek
    +--> Ollama
    +--> LM Studio
    +--> llama.cpp
    v
Event Normalization --> SSE --> Claude Code
```

## Components

### HTTP Layer

- `ARCH-001` — Validate local authentication, body, types, and basic limits.
- `ARCH-002` — Must not contain provider-specific rules.
- `ARCH-003` — Convert pre-streaming exceptions to appropriate HTTP response.
- `ARCH-004` — After opening streaming, convert terminal error to valid SSE event.

### Configuration

- `ARCH-005` — Read environment once at startup.
- `ARCH-006` — Validate types, URLs, and required values before accepting traffic.
- `ARCH-007` — Expose immutable configuration to other components.
- `ARCH-008` — Never provide secret value in textual representation or log.

### Model Router

- `ARCH-009` — Transform requested name into an ordered candidate list.
- `ARCH-010` — Expand provider entries into their configured models.
- `ARCH-011` — Remove duplicate candidates preserving order.
- `ARCH-012` — Do not make network calls.

### Orchestrator

- `ARCH-013` — Solely responsible for retry, failover, and attempt lifecycle.
- `ARCH-014` — Record result of each candidate.
- `ARCH-015` — Control the point after which failover is prohibited.

### Adapters

- `ARCH-016` — Implement a common interface to prepare and stream the response.
- `ARCH-017` — Isolate SDK specifics, URL, authentication, and external format.
- `ARCH-018` — Normalize errors without losing useful status and message.
- `ARCH-019` — Do not import another provider's implementation.

### Anthropic Core

- `ARCH-020` — Contains shared models, events, and protocol conversions.
- `ARCH-021` — Does not depend on FastAPI or specific SDK.

## Conceptual Adapter Interface

```python
class ProviderAdapter(Protocol):
    name: str

    async def stream(
        self,
        request: NormalizedRequest,
        candidate: ModelCandidate,
    ) -> AsyncIterator[NormalizedEvent]: ...
```

The adapter returns normalized events. Anthropic/SSE serialization belongs to the core, avoiding divergent implementations per provider.

## Target Directory Structure

```text
server.py
api/
  routes.py
  services.py
  model_router.py
config/
  settings.py
core/
  anthropic/
    models.py
    normalize.py
    stream_response.py
  errors.py
providers/
  base.py
  registry.py
  openai_compat.py
  rate_limit.py
  nvidia_nim/
  openrouter/
  deepseek/
  ollama/
  lmstudio/
  llamacpp/
scripts/
  benchmark_model_tools.py
tests/
spec/
```

## Architectural Decisions

| Decision | Choice | Consequence |
| --- | --- | --- |
| Internal Contract | Normalized events | Smaller adapters and consistent streaming |
| Configuration | Validated env at startup | Errors appear early |
| Failover | Only before significant content | Avoids duplicate actions |
| Tools | Minimum allowlist | Fewer tokens, with less optional tool availability |
| OpenAI Providers | Shared compatible base | Reuse without coupling between adapters |
| Server | FastAPI/Uvicorn | Good async integration and SSE |

## Invariants

1. A request has at most one candidate that has emitted significant content.
2. Every external connection is closed, including on cancellation.
3. Candidate order is stable.
4. The original request is not altered by the tool filter.
5. External events are never passed through without validation and normalization.