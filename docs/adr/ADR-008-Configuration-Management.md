# ADR-008: Configuration Management

## Status
Accepted

## Context
The system requires configuration for provider credentials, model selections, routing preferences, and operational parameters while maintaining security of sensitive information.

## Decision
Keep all sensitive configuration exclusively in environment variables loaded from .env file. Load and validate configuration once at startup. Remove unused variables from active configuration. Maintain .env.example with sample values (no real credentials).

## Consequences
- Prevents accidental commitment of sensitive credentials
- Ensures consistent configuration validation
- Simplifies deployment across different environments
- Requires discipline to never commit real credentials to version control