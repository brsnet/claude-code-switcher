# ADR-005: Streaming Implementation

## Status
Accepted

## Context
The system must support streaming responses compatible with the Claude Code client while handling provider-specific streaming formats.

## Decision
Accept messages with system/user/assistant roles and convert them appropriately for each provider. Produce valid SSE events compatible with Claude Code. Use a single keepalive producer to avoid context conflicts between asynchronous tasks.

## Consequences
- Maintains compatibility with existing Claude Code clients
- Handles provider-specific streaming format differences
- Prevents race conditions in keepalive implementations
- Requires proper SSE formatting and error handling during streams