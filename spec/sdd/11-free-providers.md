# SDD 11 — Free Providers and Cost Protection

## Scope

This document defines configuration, routing, and acceptance for Groq, Gemini, Cerebras, Cloudflare Workers AI, and Free OpenRouter.

## Configuration Requirements

- `FREE-001` — Each provider has its own credential; keys are never reused.
- `FREE-002` — Groq uses `GROQ_API_KEY`, `GROQ_MODEL<N>`, and `GROQ_BASE_URL`.
- `FREE-003` — Gemini uses `GEMINI_API_KEY`, `GEMINI_MODEL<N>`, and `GEMINI_BASE_URL`.
- `FREE-004` — Cerebras uses `CEREBRAS_API_KEY`, `CEREBRAS_MODEL<N>`, and `CEREBRAS_BASE_URL`.
- `FREE-005` — Cloudflare uses `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_MODEL<N>`, and derived or explicit URL.
- `FREE-006` — Numbered models accept gaps, are ordered numerically, and don't repeat.
- `FREE-007` — Empty fields mean provider not configured, never shared credential.

## OpenRouter Protection

- `FREE-008` — Only `openrouter/free` and models ending in `:free` are accepted.
- `FREE-009` — A legacy paid model in `.env` is discarded and replaced with `openrouter/free`.
- `FREE-010` — An explicit route to a non-free OpenRouter model fails before network call.
- `FREE-011` — Code does not remove `:free` nor automatically swap to a paid variant.

## Adapter Contract

The four providers reuse `OpenAICompatibleAdapter` and must preserve:
- system/user/assistant messages;
- tools and tool results;
- SSE streaming;
- timeout and HTTP classification;
- fragmented tool calls;
- narrative simulation blocking when tool is required.

- `FREE-012` — Provider specifics only enter the specific adapter after a contract test.
- `FREE-013` — Declared OpenAI compatibility does not replace real tool benchmarking.

## Observability

For every candidate, the terminal must show:

```text
ROUTE: request_id=... claude_model='...' -> provider=groq model='...'
PROVIDER_REQUEST: request_id=... provider=groq model='...' attempt=1
PROVIDER_STREAM: request_id=... provider=groq model='...' first_event_ms=...
REQUEST_DONE: request_id=... provider=groq model='...' result=success total_ms=...
```

- `FREE-014` — The above contract applies to Groq, Gemini, Cerebras, Cloudflare, and OpenRouter.
- `FREE-015` — `429` logs provider/model and produces retry or failover per stream state.
- `FREE-016` — Logs contain no key, prompt, file content, or header.
- `FREE-017` — Human message contains provider/model; `extra` keeps the same fields.

## Acceptance Criteria

1. All adapters are registered without initiating network during import.
2. Each provider expands all its numbered models in the correct order.
3. Paid OpenRouter is impossible via configuration and explicit route.
4. Simulated tests confirm visible logs for each provider.
5. Opt-in external benchmark confirms a valid tool call before activating the candidate in the route.
6. Failure or free limit of one service does not prevent the next candidate.