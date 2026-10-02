# ADR-004: Routing Logic and Failover Mechanisms

## Status
Accepted

## Context
The system needs to handle provider failures gracefully and automatically switch to alternative providers when the primary choice fails.

## Decision
Generate an ordered chain of candidates from the routing lists and attempt each in sequence. Only failover before producing significant content (text or tool calls). Retry transient errors (402, 429, 500, 502, 503, 504, 529) with exponential backoff before moving to the next candidate.

## Consequences
- Provides automatic failover when providers experience issues
- Prevents mid-stream provider switching which could corrupt responses
- Distributes load across providers based on priority ordering
- Requires proper error classification to distinguish transient from permanent failures