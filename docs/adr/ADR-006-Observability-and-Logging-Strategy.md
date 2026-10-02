# ADR-006: Observability and Logging Strategy

## Status
Accepted

## Context
The system needs to provide sufficient observability for debugging and monitoring without compromising security by logging sensitive information. Based on specifications, we need to log external calls with model, provider, URL, and response details including tokens used and total time.

## Decision
Log events including ROUTE, ROUTE_CHAIN, API_REQUEST (with model, provider, endpoint URL), provider-specific streams, ROUTE_FAILOVER, and provider errors. For each external call, log the model name, provider identifier, request URL, and on response include tokens used (input+output) and total latency. Never log tokens, authorization headers, or contents of private files as sensitive data; however, aggregated token counts and timing are safe for observability. Use structured logging (e.g., JSON) to enable request tracing and correlation.

## Consequences
- Enables debugging and monitoring of request flows with full visibility into external API usage
- Provides clear audit trail for routing decisions, failures, and performance metrics
- Allows tracking of token consumption and latency per provider/model for cost and performance analysis
- Requires consistent logging implementation across all components to maintain correlation
- Prevents accidental exposure of sensitive data in logs while exposing necessary operational metrics