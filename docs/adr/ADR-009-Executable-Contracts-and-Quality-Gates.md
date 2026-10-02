# ADR-009: Executable Contracts and Mandatory Quality Gates

## Status
Accepted

## Date
2026-10-01

## Deciders
project maintainer

## Context

The project has detailed requirements, but some exist only in documentation. Local changes have already introduced simple regressions — such as failing to execute candidates containing `/` and incorrectly using the logging API — without the delivery process blocking them.

The test suite also mixes automated tests with diagnostic scripts that access `.env`, print configuration, depend on a manually started server, or require undeclared packages. Additionally, Ruff and ty exclude test files broadly. Thus, running only part of the checks can produce a false indication of success.

The proxy sits at the boundary between Claude Code and heterogeneous providers. A regression in routing, tools, or streaming can cause loss of work, repetition of actions, and data exposure. Therefore, documentation without automated verification is insufficient for these areas.

## Decision

Adopt executable contracts and a single quality gate as a condition for completing changes.

1. Critical requirements will have identifiers linked to automated tests.
2. Unit, integration, and contract tests will be hermetic by default: no network, no real `.env`, no external server, and no credentials.
3. Real provider tests will be opt-in, marked, and executed only with explicit authorization.
4. Manual scripts will not use names collected by Pytest and will remain outside `tests/`.
5. Ruff and ty will verify production code and tests; exclusions will be specific and justified.
6. The canonical gate will execute formatting, lint, types, collection, and the full suite. Collection failure is a delivery failure.
7. Changes to routing, retry, failover, tools, or SSE will require a regression test at the affected architectural boundary, not just a test of the edited function.
8. The delivery will report commands executed and any verifications not performed. It will not be permitted to declare the suite passed when only a subset was executed.
9. The gate will be reproducible locally before being automated in CI.

## Options Considered

### Option A: Keep Manual Review and On-Demand Tests

| Dimension | Assessment |
| --- | --- |
| Complexity | Low |
| Initial Cost | Low |
| Regression Protection | Low |
| Diagnosis | Reactive |

**Pros:** No immediate migration.

**Cons:** The same errors can reappear; results depend on each agent's discipline; unsafe scripts remain mixed in the suite.

### Option B: Executable Contracts and Single Local Gate

| Dimension | Assessment |
| --- | --- |
| Complexity | Medium |
| Initial Cost | Medium |
| Regression Protection | High |
| Diagnosis | Early and reproducible |

**Pros:** Turns requirements into automatic protection; works offline; reduces false positives of completion; facilitates review.

**Cons:** Requires cleaning up existing tests and maintaining protocol fixtures.

### Option C: Adopt CI Immediately as Sole Guarantee

| Dimension | Assessment |
| --- | --- |
| Complexity | Medium/High |
| Initial Cost | High |
| Regression Protection | High after setup |
| Diagnosis | Late if local gate diverges |

**Pros:** Centralized blocking and execution history.

**Cons:** Does not by itself fix non-hermetic tests; creates platform dependency before the local gate is reliable.

## Trade-off Analysis

Option B delivers the greatest risk reduction without requiring external infrastructure. The local gate will be the canonical source and can be reused by CI later. The migration should be incremental: first prevent leakage and false collection; then expand lint and types; finally add coverage of critical contracts.

## Consequences

- Orchestration regressions now fail before manual execution.
- The `tests/` directory ceases to be used as a dumping ground for investigation scripts.
- Changes may require fixtures and additional tests, increasing initial cost and reducing subsequent diagnosis cost.
- Real provider tests remain possible but are clearly separated from the default gate.
- CI can execute exactly the same local gate, without a second definition of quality.

## Action Items

1. [ ] Sanitize or move diagnostic scripts currently collected as tests.
2. [ ] Remove reading and printing of credentials from all test artifacts.
3. [ ] Create settings fixtures isolated from the real `.env`.
4. [ ] Create parametrized contracts for all adapters.
5. [ ] Cover the retry/failover state machine and the stream start boundary.
6. [ ] Restrict Ruff and ty exclusions and gradually fix revealed errors.
7. [ ] Create a single local command for the quality gate.
8. [ ] Add CI only after the local gate is deterministic.