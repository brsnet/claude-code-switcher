# ADR-003: Tool Filtering Policy

## Status
Accepted

## Context
To reduce token usage, latency, and confusion, the system needs to limit the tools sent to models while still supporting required functionality.

## Decision
By default, send only the essential tools: Read, Edit, Write, Bash, Glob, Grep. Preserve tools explicitly required in tool_choice even if not in the default list. Clear tool_choice when no compatible tools remain after filtering.

## Consequences
- Reduces token consumption and improves response times
- Minimizes confusion for models by limiting available tools
- Ensures required tools are never filtered out when explicitly needed
- Requires careful validation of tool_choice handling