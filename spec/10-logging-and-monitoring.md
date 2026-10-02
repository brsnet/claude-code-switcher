# 10 — Logging and Monitoring

## Overview

This specification details the logging and monitoring requirements for the Claude Code Switcher, focusing on capturing essential information for observability, debugging, and performance analysis while maintaining security by not exposing sensitive data.

## Functional Requirements

### LOG-001 — External Call Logging

The system MUST log all calls made to external AI providers, including:
- Requested model name (e.g., opus, sonnet, haiku, or provider-specific name)
- Provider identifier (e.g., nvidia_nim, open_router, ollama)
- Complete endpoint URL called
- HTTP method and relevant headers (excluding authorization)
- Request payload (size, not sensitive content)

### LOG-002 — Response Logging

For each logged external call, the system MUST log in the response:
- HTTP status code
- Tokens used (input + output, when available)
- Total latency (from request to complete response receipt)
- Response size
- Indicator if streaming was used

### LOG-003 — Internal Event Logging

The system MUST log relevant internal events for tracing:
- ROUTE: Logical route chosen (opus/sonnet/haiku)
- ROUTE_CHAIN: Complete sequence of providers/models attempted
- ROUTE_FAILOVER: Failover reason and next candidate attempted
- Provider-specific events: Stream start/end, provider errors
- Validation and internal processing errors

### LOG-004 — Structured Logging Format

All log entries MUST follow a structured format (JSON) to facilitate:
- Query and aggregation in monitoring systems
- Correlation of events related to the same request
- Automated analysis of patterns and metrics

Each log entry MUST include:
- Timestamp with timezone
- Log level (DEBUG, INFO, WARN, ERROR)
- Request correlation ID
- Event type (per LOG-001 to LOG-003)
- Event-specific fields

### LOG-005 — Sensitive Data Protection

The system MUST ensure no sensitive data is logged:
- Authorization tokens (Bearer, API keys)
- Content of private files read via Read tool
- Prompt content containing personal or confidential data
- Any data marked as sensitive by the client

### LOG-006 — Logging Performance

The logging mechanism MUST be asynchronous and non-blocking to avoid significant impact on response latency.

## Derived Metrics

From the registered logs, the system MUST enable calculation of:
- Success rate by provider/model
- Latency distribution (p50, p95, p99)
- Average token consumption by call type
- Estimated cost by provider (when applicable)
- Cache efficiency (when implemented)