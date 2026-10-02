# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for the Claude Code Switcher. Each ADR documents a significant architectural decision, its context, and consequences.

## ADR Index

| ID | Title | Area | Status |
|----|-------|------|--------|
| [ADR-001](ADR-001-Model-Router-Architecture.md) | Model Router Architecture | Routing | Accepted |
| [ADR-002](ADR-002-Provider-Adapter-Pattern.md) | Provider Adapter Pattern | Providers | Accepted |
| [ADR-003](ADR-003-Tool-Filtering-Policy.md) | Tool Filtering Policy | Tools | Accepted |
| [ADR-004](ADR-004-Routing-Logic-and-Failover-Mechanisms.md) | Routing Logic and Failover Mechanisms | Routing/Resilience | Accepted |
| [ADR-005](ADR-005-Streaming-Implementation.md) | Streaming Implementation | Streaming | Accepted |
| [ADR-006](ADR-006-Observability-and-Logging-Strategy.md) | Observability and Logging Strategy | Observability | Accepted |
| [ADR-007](ADR-007-Benchmarking-Approach.md) | Benchmarking Approach | Testing/Benchmark | Accepted |
| [ADR-008](ADR-008-Configuration-Management.md) | Configuration Management | Configuration | Accepted |
| [ADR-009](ADR-009-Executable-Contracts-and-Quality-Gates.md) | Executable Contracts and Quality Gates | Quality/Testing | Accepted |
| [ADR-010](ADR-010-Metrics-for-Token-and-Time-Collection.md) | Metrics for Token and Time Collection | Metrics | Accepted |
| [ADR-011](ADR-011-Free-Providers-and-Cost-Control.md) | Free Providers and Cost Control | Providers/Cost | Accepted |

## By Category

### Routing & Resilience
- ADR-001: Model Router Architecture
- ADR-004: Routing Logic and Failover Mechanisms

### Providers & Adapters
- ADR-002: Provider Adapter Pattern
- ADR-011: Free Providers and Cost Control

### Tools & Streaming
- ADR-003: Tool Filtering Policy
- ADR-005: Streaming Implementation

### Observability & Quality
- ADR-006: Observability and Logging Strategy
- ADR-007: Benchmarking Approach
- ADR-009: Executable Contracts and Quality Gates
- ADR-010: Metrics for Token and Time Collection

### Configuration
- ADR-008: Configuration Management

## ADR Format

Each ADR follows this structure:
- **Status**: Accepted/Proposed/Deprecated
- **Context**: The problem being addressed
- **Decision**: The chosen solution
- **Consequences**: Trade-offs and implications
- **Options Considered** (when applicable): Alternatives evaluated