# 04 — Routing and Resilience

## Logical Model Resolution

| Client Input | Route |
| --- | --- |
| contains `opus` | `ROUTER_OPUS` |
| contains `sonnet` | `ROUTER_SONNET` |
| contains `haiku` | `ROUTER_HAIKU` |
| explicit prefix | indicated candidate |
| unknown | clear configuration error |

- `ROUTE-001` — Logical name comparison must be normalized and tested.
- `ROUTE-002` — A route is a comma-separated ordered list.
- `ROUTE-003` — Empty entries are discarded.
- `ROUTE-004` — Unknown prefixes fail before external call.

## Candidate Expansion

Example:

```dotenv
ROUTER_SONNET=nvidia_nim,open_router,ollama
NVIDIA_NIM_MODEL1=model-a
NVIDIA_NIM_MODEL2=model-b
OPENROUTER_MODEL=model-c
OLLAMA_MODEL=model-d
```

Result:

```text
nvidia_nim/model-a
nvidia_nim/model-b
open_router/model-c
ollama/model-d
```

- `ROUTE-005` — Discover all `NVIDIA_NIM_MODEL<N>` variables.
- `ROUTE-006` — Accept gaps and order numerically, not alphabetically.
- `ROUTE-007` — Remove duplicate models preserving first position.
- `ROUTE-008` — Include legacy `NVIDIA_NIM_MODEL` only per explicit compatibility rule.
- `ROUTE-009` — Exclude providers without required credentials or endpoint and log the reason.
- `ROUTE-010` — Never modify configuration during a request.

## Attempt State Machine

```text
RESOLVING
   |
   v
TRYING_CANDIDATE --> RETRY_WAIT --> TRYING_CANDIDATE
   |                       |
   | exhausted error       | cancellation
   v                       v
NEXT_CANDIDATE          CANCELLED
   |
   +--> TRYING_CANDIDATE
   |
   +--> FAILED

TRYING_CANDIDATE --> STREAMING --> COMPLETED
                       |
                       +--> STREAM_FAILED
```

- `RES-001` — Transition to `STREAMING` occurs on first significant event.
- `RES-002` — In `STREAMING`, `NEXT_CANDIDATE` is prohibited.
- `RES-003` — Keepalive, internal metadata, and headers don't count as significant content.
- `RES-004` — Text, visible reasoning, and tool call start count as significant content.

## Retry Policy

Eligible statuses:

```text
402, 429, 500, 502, 503, 504, 529
```

Classification:

| Category | Retry on Same Candidate | Failover |
| --- | --- | --- |
| timeout/connection | yes | yes |
| `429`/overload | yes | yes |
| `5xx`/`529` | yes | yes |
| `402` balance | no | yes |
| `401`/`403` | no | yes, if another provider can work |
| `400` invalid request | no | no, unless proven provider-specific incompatibility |
| client cancellation | no | no |

- `RES-005` — Exponential backoff must have maximum limit and jitter.
- `RES-006` — Attempt count must be configurable and limited.
- `RES-007` — `Retry-After`, when valid, takes precedence within configured limit.
- `RES-008` — Sum of retries respects total request deadline.
- `RES-009` — Each attempt logs duration, candidate, and result.

## Concurrency

- `RES-010` — Each provider has its own semaphore.
- `RES-011` — Initial default is `PROVIDER_MAX_CONCURRENCY=5`.
- `RES-012` — Ollama/Haiku may have its own limit.
- `RES-013` — Semaphore wait must respect cancellation and timeout.

## Acceptance Scenarios

1. First model returns `429`; retry exhausts; second model responds; client receives only the second response.
2. First model emits text then returns `500`; client receives terminal error; no second model is called.
3. DeepSeek returns `402`; OpenRouter is tried without useless retry on DeepSeek.
4. Client cancels during backoff; no additional attempt starts.
5. Two NVIDIA entries point to the same model; only one attempt occurs.