# ADR-006: Observability and Logging Strategy

## Status
Accepted

## Context
The system needs to provide sufficient observability for debugging and monitoring without compromising security by logging sensitive information.

## Decision
Log events including ROUTE, ROUTE_CHAIN, API_REQUEST, provider-specific streams, ROUTE_FAILOVER, and provider errors. Never log tokens, authorization headers, or contents of private files. Use structured logging to enable request tracing.

## Consequences
- Enables debugging and monitoring of request flows
- Prevents accidental exposure of sensitive data in logs
- Provides clear audit trail for routing decisions and failures
- Requires consistent logging implementation across all components