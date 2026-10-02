# 06 — Tools, Streaming, and Security

## Tool Filtering

Default allowlist:

```text
Read, Edit, Write, Bash, Glob, Grep
```

- `TOOL-001` — Compare tool names exactly, respecting protocol-defined capitalization.
- `TOOL-002` — Copy the request before filtering.
- `TOOL-003` — Preserve relative order of accepted tools.
- `TOOL-004` — Remove duplicates by name.
- `TOOL-005` — Preserve tool explicitly forced by `tool_choice`.
- `TOOL-006` — If forced tool doesn't exist in the request, return validation error.
- `TOOL-007` — If no tools remain, remove incompatible `tool_choice` configuration.
- `TOOL-008` — Log only counts and non-sensitive names.

## Tool Call Conversion

- `TOOL-009` — Accumulate fragmented JSON arguments until forming a valid document.
- `TOOL-010` — Do not execute tools in the proxy; only transport the call.
- `TOOL-011` — Preserve call identifier between request and result.
- `TOOL-012` — Incomplete argument at end of stream generates explicit terminal error.
- `TOOL-013` — Requests with explicit intent to modify files or execute commands must require a structured tool call; text merely simulating actions is not valid execution.

## Streaming Integrity

- `STREAM-001` — A single producer writes events for each response.
- `STREAM-002` — Keepalive is coordinated by the same pipeline, without accessing another task's logging context.
- `STREAM-003` — Deltas are validated before serialization.
- `STREAM-004` — Invalid characters are rejected or replaced in a controlled manner; never emit broken UTF-8 bytes.
- `STREAM-005` — Provider internal marker fragments don't appear as normal text.
- `STREAM-006` — Don't repeat deltas when converting cumulative events.
- `STREAM-007` — Client closure interrupts reading, retry, and keepalive.

## Corrupted Response Prevention

Tests must cover:

- Unicode text and Portuguese with accents;
- Tool JSON split in the middle of a multibyte character;
- Cumulative event received twice;
- Reasoning separate from final text;
- Error in the middle of a tool call;
- Termination without final marker;
- Unknown external event.

## Security

- `SEC-001` — Credentials loaded only from environment or future secure mechanism.
- `SEC-002` — Use constant-time comparison for the local token.
- `SEC-003` — Apply redaction to `Authorization`, `api-key`, `x-api-key`, `nvapi-*`, `sk-*`, and sensitive parameters.
- `SEC-004` — Do not log full body by default.
- `SEC-005` — Limit request size to avoid uncontrolled memory consumption.
- `SEC-006` — Validate configured endpoints and document SSRF risk when URLs are externally controlled.
- `SEC-007` — Restrict bind to user-requested address; recommend loopback when network access not needed.
- `SEC-008` — Never execute model content in the proxy process.
- `SEC-009` — Treat keys exposed in conversation or screenshot as compromised and recommend rotation.

## Summarized Threat Model

| Threat | Mitigation |
| --- | --- |
| Key leak in log | central redaction and tests |
| Unauthorized client | required local token |
| Duplicate response from failover | lock after first significant content |
| Malformed tool JSON | incremental validation and terminal error |
| Malicious local endpoint | explicit configuration and URL validation |
| Excessive external consumption | timeout, retry limit, and controlled benchmark |