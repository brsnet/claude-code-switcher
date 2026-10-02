# ADR-010: Metrics for Token and Time Collection

## Status
Accepted

## Context

The system needs to collect and store metrics about token consumption and execution time for each provider attempt to enable performance analysis, cost estimation, and optimization decisions.

## Decision

Implement a metrics collection system that:

1. Records metrics for each provider attempt (both successful and failed)
2. Stores metrics in an append-only JSON Lines file for simplicity and performance
3. Collects: timestamp, request_id, provider, model, input_tokens, output_tokens, total_tokens, duration_ms, success, error_category
4. Makes metrics collection non-blocking and resilient to storage failures
5. Configures storage path and flush interval via environment variables
6. Creates the storage directory automatically if it doesn't exist

## Consequences

- Enables post-fact analysis of provider performance and cost
- Provides data for benchmarking and optimization decisions
- Adds minimal overhead to each request (microseconds for collection, milliseconds only if disk write blocks)
- Requires disk space for metrics storage (can be managed with rotation in future)
- Does not affect core routing, streaming, or failover logic
- Storage failures are logged as warnings but don't interrupt request processing