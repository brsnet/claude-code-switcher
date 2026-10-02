# SDD — Claude Code Switcher

## Purpose

This folder contains the system design specification. It is the source of truth for implementation, tests, and architectural review of the Claude Code Switcher.

The `CLAUDE.md` defines global principles and boundaries. These SDDs detail expected behavior. In case of conflict, stop implementation, record the divergence, and correct the documentation before proceeding.

## Reading Order

1. [01-vision-and-scope.md](01-vision-and-scope.md)
2. [02-architecture.md](02-architecture.md)
3. [03-api-and-protocol.md](03-api-and-protocol.md)
4. [04-routing-and-resilience.md](04-routing-and-resilience.md)
5. [05-providers-and-configuration.md](05-providers-and-configuration.md)
6. [06-tools-streaming-and-security.md](06-tools-streaming-and-security.md)
7. [07-tests-observability-and-operations.md](07-tests-observability-and-operations.md)
8. [08-implementation-plan.md](08-implementation-plan.md)
9. [09-engineering-changes-and-quality-gates.md](09-engineering-changes-and-quality-gates.md)
10. [SDD 10 — Metrics for Token and Time](sdd/10-metrics-token-time.md)
11. [SDD 11 — Free Providers](sdd/11-free-providers.md)

## Requirement Status

- `MANDATORY`: required for the first functional version.
- `RECOMMENDED`: may be deferred, but the decision must be recorded.
- `FUTURE`: out of initial scope.

Requirement identifiers must not be renumbered. Removed requirements must be marked as obsolete to preserve traceability.

## Definition of Done

A feature is done when:

- it meets the associated requirements;
- has automated success and failure tests;
- does not expose credentials;
- preserves streaming semantics;
- passes `ruff`, `ty`, and `pytest`;
- passes collection and the canonical gate defined in
  [09-engineering-changes-and-quality-gates.md](09-engineering-changes-and-quality-gates.md);
- updates the SDD when introducing a new decision.