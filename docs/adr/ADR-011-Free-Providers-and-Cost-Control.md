# ADR-011: Free Providers and Preventive Cost Control

## Status
Accepted

## Date
2026-10-01

## Deciders
project maintainer

## Context

The switcher needs to increase availability without turning failover into unexpected charges. Groq, Gemini, Cerebras, and Cloudflare Workers AI offer free tiers or limited quotas with OpenAI-compatible interfaces. OpenRouter offers free models but also exposes paid models through the same API and key.

Free policies, limits, and catalogs change without notice. The application must not confuse "has a free tier" with "free without limits" and must not silently select a paid model.

## Decision

1. Integrate Groq, Gemini, Cerebras, and Cloudflare via thin adapters over the shared OpenAI-compatible base.
2. Allow `MODEL1...MODEL[N]` for each new provider, with numeric ordering and deduplication.
3. Keep credentials, models, and endpoints independent per provider.
4. Restrict OpenRouter to `openrouter/free` or identifiers ending in `:free`.
5. Ignore non-free OpenRouter models in configuration and use `openrouter/free` as a safe fallback. An explicit paid route must fail locally before the external call.
6. Do not assert a model is suitable for Claude Code until it passes the tool calling contract.
7. Treat `429`, unavailability, and catalog changes as normal failover conditions.
8. Display provider, model, retry, failover, and result in human and structured logs.

## Options Considered

### Option A: One Full Specific Adapter Per Provider

| Dimension | Assessment |
| --- | --- |
| Complexity | High |
| Isolation | High |
| Maintenance | High |
| Delivery Speed | Low |

### Option B: Thin Adapters Over OpenAI-Compatible

| Dimension | Assessment |
| --- | --- |
| Complexity | Low |
| Reuse | High |
| Maintenance | Low |
| Specific Limitations | Require per-provider contract tests |

### Option C: Use Only OpenRouter as Aggregator

| Dimension | Assessment |
| --- | --- |
| Complexity | Very Low |
| Independence | Low |
| Common Unavailability Risk | High |
| Cost Control | Depends on external route |

## Trade-off Analysis

Option B preserves independence between services and reuses conversion, streaming, and error handling already tested. Specifics will be added only when a contract test demonstrates necessity. The OpenRouter restriction reduces flexibility but eliminates accidental paid selection.

## Consequences

- More candidates can absorb `429` and unavailability.
- Route order now also influences free quotas.
- A valid key doesn't guarantee capacity; limits must be observed in logs.
- Models may disappear and must be replaced in `.env` without code changes.
- Paid OpenRouter requires a future explicit architectural decision; it cannot be enabled by mistake.

## Action Items

1. [x] Register adapters for the four providers.
2. [x] Add numbered configuration and endpoints.
3. [x] Block non-free OpenRouter models.
4. [x] Cover registration, routing, configuration, and logs with tests.
5. [ ] Execute real benchmark after user fills in each key.
6. [ ] Periodically review free models and limits.