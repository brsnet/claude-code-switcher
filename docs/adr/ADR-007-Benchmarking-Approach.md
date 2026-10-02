# ADR-007: Benchmarking Approach

## Status
Accepted

## Context
The system needs to evaluate provider/model performance to maintain quality in routing decisions while avoiding excessive costs from external API usage.

## Decision
Use a minimal benchmark with the synthetic Read tool, limiting responses to ~128 tokens, disabling thinking, and applying a 30-second timeout per model. Evaluate based on latency, HTTP status, and tool call validity. Maintain models in active routes only if they meet performance and correctness criteria.

## Consequences
- Provides consistent performance measurements across providers
- Limits costs from external API usage during testing
- Focuses on relevant metrics for routing decisions (speed, reliability)
- Requires regular re-benchmarking as models/providers change