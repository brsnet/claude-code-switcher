# Supplementary Design Documents (SDDs)

This directory contains supplementary design documents that extend the core specifications with detailed requirements for specific subsystems.

## SDD Index

| ID | File | Description |
|----|------|-------------|
| SDD-09 | [09-logging-and-monitoring.md](09-logging-and-monitoring.md) | Structured logging requirements, external call/response logging, internal events, sensitive data protection, logging performance |
| SDD-10 | [10-metrics-token-time.md](10-metrics-token-time.md) | Token and time metrics collection per provider attempt, JSON Lines storage, resilience, security, derived metrics |
| SDD-11 | [11-free-providers.md](11-free-providers.md) | Free provider configuration (Groq, Gemini, Cerebras, Cloudflare), OpenRouter protection, adapter contract, observability, acceptance criteria |

## Relationship to Core Specs

These SDDs supplement the core specifications in `spec/`:

- SDD-09 extends [07-tests-observability-and-operations.md](../07-tests-observability-and-operations.md) with detailed logging requirements
- SDD-10 adds metrics collection as specified in [09-engineering-changes-and-quality-gates.md](../09-engineering-changes-and-quality-gates.md)
- SDD-11 details free provider integration per [05-providers-and-configuration.md](../05-providers-and-configuration.md)

## Requirement Identifiers

Each SDD uses its own identifier prefix:
- SDD-09: `LOG-*`
- SDD-10: `METRICAS-*` (legacy) / `METRICS-*`
- SDD-11: `FREE-*`

Identifiers are not renumbered to preserve traceability.