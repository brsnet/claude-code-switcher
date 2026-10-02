# 07 — Tests, Observability, and Operations

## Test Strategy

### Unit Tests

- `TEST-001` — Resolution of Opus, Sonnet, and Haiku names.
- `TEST-002` — Numeric ordering of NVIDIA models with gaps.
- `TEST-003` — Stable duplicate removal.
- `TEST-004` — Tool filtering and `tool_choice`.
- `TEST-005` — Error classification by status and message.
- `TEST-006` — Conversion of OpenAI-compatible events to internal events.
- `TEST-007` — Redaction of all known secret formats.

### Integration Tests

- `TEST-008` — Complete Messages API with simulated provider.
- `TEST-009` — Retry followed by success.
- `TEST-010` — Failover before first delta.
- `TEST-011` — Failover prohibition after first delta.
- `TEST-012` — Client cancellation releases semaphore and connection.
- `TEST-013` — Streaming Unicode and fragmented tool call.
- `TEST-014` — Terminal SSE error after response start.

### Provider Contract Tests

Each adapter must execute the same contract test suite with simulated responses:

- simple text;
- valid tool;
- auth error;
- rate limit;
- timeout;
- incomplete stream;
- correct client closure.

### Optional Real Tests

- `QUAL-006` — Must use `external` marker and be disabled by default.
- `QUAL-007` — Require explicit enable variable and user authorization.
- `QUAL-008` — Must limit cost, tokens, and duration.
- `QUAL-009` — Real results do not replace simulated contracts.

### Manual Scripts

- `QUAL-010` — Stay in `scripts/`, not in `tests/`.
- `QUAL-011` — Don't start with `test_`.
- `QUAL-012` — Inform preconditions and effects before executing.
- `QUAL-013` — Outputs apply redaction and don't enumerate secret variables.

Automated tests must use synthetic settings and simulated providers. Complete rules are in `09-engineering-changes-and-quality-gates.md`.

## Quality

Execute in this order:

```powershell
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest --collect-only -q
uv run pytest -q -m "not external"
```

- `TEST-015` — No `# type: ignore` or `# ty: ignore`.
- `TEST-016` — Failure in any check blocks delivery.
- `TEST-017` — Behavior changes include regression case.
- `TEST-018` — Default suite does not access network, local server, or real `.env`.
- `TEST-019` — Collection failure blocks delivery.
- `TEST-020` — Instrumentation tests run real backend at least once, beyond mocks.

## Benchmark

The benchmark script uses a synthetic request with `Read`, max 128 tokens, thinking disabled, and 30-second timeout.

Minimum output per candidate:

```text
provider, model, http_status, first_event_ms, total_ms,
tool_call_valid, error_category, decision
```

- `BENCH-001` — Do not read real project files.
- `BENCH-002` — Warn that execution may consume credits.
- `BENCH-003` — Do not promote model just because it responded text; validate tool.
- `BENCH-004` — Record date, machine, and hot/cold condition for local models.

## Logs

Required events:

| Event | Minimum Fields |
| --- | --- |
| `ROUTE` | request_id, logical_model |
| `ROUTE_CHAIN` | request_id, sanitized candidates |
| `API_REQUEST` | request_id, provider, model, tool_count |
| `ROUTE_RETRY` | request_id, candidate, attempt, reason, wait_ms |
| `ROUTE_FAILOVER` | request_id, from, to, reason |
| `PROVIDER_STREAM` | request_id, provider, first_event_ms |
| `PROVIDER_ERROR` | request_id, provider, category, status |
| `REQUEST_DONE` | request_id, result, total_ms |

- `OBS-001` — Logs contain no keys or headers.
- `OBS-002` — Every operational line has `request_id`.
- `OBS-003` — Metrics differentiate retry from failover.
- `OBS-004` — Tool count allows confirming minimum allowlist.

## Runbook

### Manual Startup

```powershell
cd D:\projetos\claude-code-switcher
uv run uvicorn server:app --host 0.0.0.0 --port 8082
```

### Verification

1. Query `GET /health`.
2. Confirm routes loaded without secrets in log.
3. Send short message without tools.
4. Send synthetic message with `Read`.
5. Confirm selected candidate and tool count.

### Quick Diagnosis

| Symptom | Check |
| --- | --- |
| `401` local | client and server token |
| `402` | provider balance and next fallback |
| `404` external | model name and availability |
| `429`/overloaded | retries, concurrency, and fallback |
| over 10 minutes | timeout, cold local model, thinking, and tool count |
| strange characters | UTF-8 decoder, cumulative events, and delta conversion |
| duplicate actions | failover after stream start |

### Shutdown

The user controls the process. Do not create services, scheduled tasks, or automatic startup without explicit request.