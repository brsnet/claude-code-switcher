# 09 — Change Engineering and Quality Gates

## Objective

Prevent apparently completed changes from introducing regressions in routing, tools, streaming, security, or observability. This chapter defines how a change is specified, tested, and accepted.

## Principles

- `QUAL-001` — Normative documentation must have a corresponding test when the behavior is observable by code.
- `QUAL-002` — A change is not ready if any canonical gate step fails or is not executed without explicit justification.
- `QUAL-003` — Focused test success does not replace the full suite.
- `QUAL-004` — Failure during test collection is a suite failure, never an implicit optional dependency.
- `QUAL-005` — Code generated or modified by agents follows the same gate as human code.

## Validation Artifact Classification

### Automated Tests

Located in `tests/`, collected by Pytest, and must:

- be deterministic;
- work without network;
- use synthetic configuration;
- never read the real `.env`;
- never print secrets, even partially;
- not depend on a manually started server;
- declare all necessary dependencies in the project.

### Real Provider Tests

- `QUAL-006` — Must use `external` marker and be disabled by default.
- `QUAL-007` — Require explicit enable variable and user authorization.
- `QUAL-008` — Must limit cost, tokens, and duration.
- `QUAL-009` — Real results do not replace simulated contracts.

### Manual Scripts

- `QUAL-010` — Stay in `scripts/`, not in `tests/`.
- `QUAL-011` — Don't start with `test_`.
- `QUAL-012` — Inform preconditions and effects before executing.
- `QUAL-013` — Outputs apply redaction and don't enumerate secret variables.

## Contract Pyramid

| Layer | Responsibility | Mandatory Examples |
| --- | --- | --- |
| Unit | Pure local rule | normalization, expansion, error classification |
| Component | Module boundary | router → candidate; adapter → normalized event |
| Integration | Full internal flow | API → orchestrator → simulated provider → SSE |
| Regression | Observed defect | candidate with `/`; fragmented tool call; Unicode |
| External opt-in | Real compatibility | NVIDIA, OpenRouter, DeepSeek, Ollama |

## Critical Contracts

### Routing and Orchestration

- `CONTRACT-001` — Every candidate returned by the router is attempted or has an explicit, tested reason to be ignored.
- `CONTRACT-002` — `provider/model` candidates and provider-only tokens follow the same flow after model resolution.
- `CONTRACT-003` — `attempted_candidates` exactly matches initiated calls.
- `CONTRACT-004` — Non-empty resolved list never ends as "no error recorded" without a discard reason being logged.
- `CONTRACT-005` — Retry and failover are tested separately.

### Streaming and Tools

- `CONTRACT-006` — The first significant event seals the candidate and prohibits failover.
- `CONTRACT-007` — Fragmented tool arguments result in valid JSON or normalized error, never partial execution.
- `CONTRACT-008` — Text narrating an action does not replace a structured tool call when a tool is mandatory.
- `CONTRACT-009` — Each stream ends exactly once with a valid SSE sequence.

### Observability

- `CONTRACT-010` — Structured logging uses the API supported by the configured backend.
- `CONTRACT-011` — Each attempt produces a start and exactly one result: success, error, or cancellation.
- `CONTRACT-012` — Sensitive fields are blocked by redaction tests.
- `CONTRACT-013` — Instrumentation does not change flow control, candidate order, or content.

## Mandatory Impact Matrix

Before implementing, record in the change plan:

| Question | Expected Evidence |
| --- | --- |
| Which requirement changes? | SDD/ADR identifiers |
| Which architectural boundary is affected? | caller and callee module |
| Which regression can arise? | failure scenario |
| Which test failed before? | regression test name |
| Does the change touch streaming? | state before/after first event |
| Does the change touch secret/network? | isolation strategy |

## Canonical Gate

The local gate must execute, in this order:

```powershell
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest --collect-only -q
uv run pytest -q -m "not external"
```

- `GATE-001` — All commands exit with code zero.
- `GATE-002` — Collection does not execute HTTP calls or read credentials.
- `GATE-003` — Verified file set does not globally exclude `tests/`.
- `GATE-004` — Exclusions are specific, documented, and temporary.
- `GATE-005` — Final report differentiates focused suite, full suite, and external test.
- `GATE-006` — Corrective formatting is not part of verification; format changes must be reviewable before the gate.

## Mandatory Change Flow

1. Reproduce the defect or define the acceptance scenario.
2. Identify affected requirements and boundaries.
3. Add a test that fails for the correct cause.
4. Implement the smallest complete fix.
5. Run focused tests.
6. Run the full canonical gate.
7. Review diff for secrets, dead code, and unrelated changes.
8. Report executed verifications and residual risks.

## Incremental Adoption Policy

### Stage A — Make the Suite Reliable

- separate manual scripts;
- eliminate `.env` reads in tests;
- declare dependencies or remove obsolete tests;
- ensure clean collection.

### Stage B — Cover Critical Contracts

- add reusable simulated provider;
- create parametrized adapter tests;
- test retry, failover, and streaming states;
- link regressions to `CONTRACT-*` identifiers.

### Stage C — Expand Static Analysis

- remove global test exclusion from Ruff;
- include tests in ty when current incompatibilities are sanitized;
- prohibit new broad exclusions.

### Stage D — Automate

- create single local command;
- execute the same command in CI;
- block integration when gate fails.

## Acceptance Criteria for This Policy

1. `pytest --collect-only` works without optional package or active server.
2. No test reads or prints real keys.
3. Regression of `provider/model` candidates is covered.
4. Logging instrumentation has a test running the real logger.
5. The full gate can be repeated twice with the same result.