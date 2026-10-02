# 08 — Implementation Plan

## Strategy

Implement in small vertical slices. Each phase must end with passing tests before the next. Do not connect paid APIs until the same flow works with simulated providers.

## Phase 0 — Quality Baseline

- Separate automated tests from manual scripts.
- Remove reading and printing of secrets from validation artifacts.
- Make full collection work without network and without implicit dependencies.
- Create contracts for routing, orchestration, tools, streaming, and logging.
- Establish the canonical gate defined in chapter 09.

Output: any subsequent phase can detect regressions before manual test.

## Phase 1 — Foundation

- Create Python 3.14 project with `uv`.
- Configure FastAPI, Uvicorn, Ruff, ty, and pytest.
- Create immutable settings and secret redaction.
- Implement `GET /health` and local authentication.
- Add startup and authentication tests.

Output: secure local server, still without inference.

## Phase 2 — Protocol and Simulated Provider

- Define internal models for request, candidate, event, and error.
- Implement Anthropic normalization and SSE serialization.
- Create simulated adapter with text, tool, and controlled failures.
- Test Unicode, cancellation, and stream closure.

Output: `POST /v1/messages` validated without external cost.

## Phase 3 — Routing

- Resolve Opus, Sonnet, and Haiku.
- Implement explicit prefixes.
- Expand numbered NVIDIA models.
- Remove duplicates and unconfigured candidates.
- Implement minimum tool filter.

Output: deterministic chain and reduced request.

## Phase 4 — Resilience

- Add provider semaphores.
- Implement retry with backoff, jitter, and `Retry-After`.
- Create attempt state machine.
- Block failover after significant content.
- Propagate terminal SSE error.

Output: safe failover covered by integration tests.

## Phase 5 — Remote Providers

- Create OpenAI-compatible base.
- Integrate NVIDIA NIM.
- Integrate OpenRouter.
- Integrate DeepSeek.
- Validate async closure and error normalization.

Output: functional external routes with fallback.

## Phase 6 — Local Providers

- Integrate Ollama.
- Integrate LM Studio.
- Integrate llama.cpp.
- Handle tool, context, and thinking differences.
- Test local unavailability without blocking remote providers.

Output: hybrid local/remote chain.

## Phase 7 — Observability and Benchmark

- Add structured route, retry, failover, and completion events.
- Create synthetic tool benchmark.
- Document result interpretation.
- Validate no log contains secrets.

Output: comparable candidates and diagnosable failures.

## Phase 8 — Hardening

- Run full suite.
- Perform manual test via Claude Code.
- Test cancellation, unavailability, and broken streams.
- Review limits, timeouts, and concurrency.
- Update SDDs with final decisions.

Output: first version candidate for daily use.

## Traceability Matrix

| Area | Requirements | Phase |
| --- | --- | --- |
| API | `API-*`, `PROTO-*` | 1–2 |
| Architecture | `ARCH-*` | 1–6 |
| Routing | `ROUTE-*` | 3 |
| Resilience | `RES-*` | 4 |
| Providers | `PROV-*`, `CFG-*` | 5–6 |
| Tools | `TOOL-*` | 3 |
| Streaming | `STREAM-*` | 2–4 |
| Security | `SEC-*` | all |
| Tests | `TEST-*` | all |
| Benchmark | `BENCH-*` | 7 |
| Observability | `OBS-*` | 7 |
| Change Engineering | `QUAL-*`, `CONTRACT-*`, `GATE-*` | 0 and all |

## Rules for Agents

Before implementing:

1. Read `CLAUDE.md`.
2. Read `spec/README.md`.
3. Read the SDD of the changed area and its dependencies.
4. List the requirement identifiers addressed.
5. Confirm no contradictory decision exists.

Upon completion, report changed files, logic, verification, and residual risks. A change contradicting the SDD must update the specification in the same work.