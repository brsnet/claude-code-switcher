# ADR-002: Provider Adapter Pattern

## Status
Accepted

## Context
The system needs to support multiple AI providers (NVIDIA NIM, OpenRouter, DeepSeek, Ollama, LM Studio, llama.cpp) each with different APIs and response formats.

## Decision
Implement each provider as an isolated adapter registered in a central registry. Use a shared OpenAI-compatible base for providers that support it, while maintaining neutral modules for Anthropic protocol conversions.

## Consequences
- Providers are loosely coupled and can be developed independently
- Shared code is centralized in neutral modules
- Adding new providers requires only implementing the adapter interface
- Clear separation between protocol handling and provider-specific logic