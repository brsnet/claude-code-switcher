# ADR-001: Model Router Architecture

## Status
Accepted

## Context
The system needs to route requests to different AI providers based on logical model names (opus, sonnet, haiku) while maintaining flexibility to switch between providers and models.

## Decision
Implement a model router that treats logical model names as capability categories rather than fixed bindings to specific models. The router will use priority-based provider lists (ROUTER_OPUS, ROUTER_SONNET, ROUTER_HAIKU) to determine the order of provider attempts.

## Consequences
- Enables transparent switching between providers and models
- Provides failover capability when providers become unavailable
- Maintains compatibility with Claude Code's expected model names
- Requires careful management of routing lists to ensure appropriate model selection