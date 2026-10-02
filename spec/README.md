# SDD — Claude Code Switcher

## Purpose

This folder contains the system design specification. It is the source of truth for implementation, tests, and architectural review of the Claude Code Switcher.

The `CLAUDE.md` defines global principles and boundaries. These SDDs detail expected behavior. In case of conflict, stop implementation, record the divergence, and correct the documentation before proceeding.

## Specification Files

### Core Specifications (spec/)

| File | Description |
|------|-------------|
| [01-vision-and-scope.md](01-vision-and-scope.md) | Problem statement, solution overview, functional and non-functional goals, actors, success criteria |
| [02-architecture.md](02-architecture.md) | System architecture, component breakdown, directory structure, architectural decisions, invariants |
| [03-api-and-protocol.md](03-api-and-protocol.md) | HTTP endpoints, authentication, message roles, SSE streaming protocol, error handling |
| [04-routing-and-resilience.md](04-routing-and-resilience.md) | Logical model resolution, candidate expansion, attempt state machine, retry policy, concurrency |
| [05-providers-and-configuration.md](05-providers-and-configuration.md) | Provider configurations, registration, internal models, startup validation |
| [06-tools-streaming-and-security.md](06-tools-streaming-and-security.md) | Tool filtering, tool call conversion, streaming integrity, security requirements, threat model |
| [07-tests-observability-and-operations.md](07-tests-observability-and-operations.md) | Test strategy, quality gates, benchmark, logging events, runbook |
| [08-implementation-plan.md](08-implementation-plan.md) | Phased implementation plan, traceability matrix, agent rules |
| [09-engineering-changes-and-quality-gates.md](09-engineering-changes-and-quality-gates.md) | Change engineering principles, validation artifacts, contract pyramid, canonical gate |
| [10-logging-and-monitoring.md](10-logging-and-monitoring.md) | Structured logging requirements, external call/response logging, internal events, sensitive data protection |
| [11-metrics-token-time.md](11-metrics-token-time.md) | Token and time metrics collection, storage format, resilience, security, derived metrics |
| [12-free-providers.md](12-free-providers.md) | Free provider configuration, OpenRouter protection, adapter contract, observability, acceptance criteria |

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