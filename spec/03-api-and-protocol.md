# 03 — API and Protocol

## Endpoints

### `POST /v1/messages`

Main endpoint compatible with Anthropic Messages. Must also accept additional query parameters used by the client, such as `beta=true`, without altering message semantics.

- `API-001` — Accept requests with and without streaming when supported by the first version.
- `API-002` — Accept `system` as a top-level field and messages with valid roles.
- `API-003` — Preserve message order and content blocks.
- `API-004` — Accept tools and `tool_choice`.
- `API-005` — Generate a `request_id` for correlation.
- `API-006` — Ignore unknown fields only when the protocol allows; otherwise, respond with a clear validation error.

Minimal example:

```json
{
  "model": "claude-sonnet",
  "max_tokens": 512,
  "stream": true,
  "system": "Respond objectively.",
  "messages": [
    {"role": "user", "content": "Read the file README.md"}
  ],
  "tools": [
    {
      "name": "Read",
      "description": "Reads a file",
      "input_schema": {
        "type": "object",
        "properties": {"file_path": {"type": "string"}},
        "required": ["file_path"]
      }
    }
  ]
}
```

### `GET /health`

- `API-007` — Respond without querying external providers.
- `API-008` — Report process state and version, without secrets.
- `API-009` — Do not claim all providers are healthy without explicit probing.

Suggested response:

```json
{
  "status": "ok",
  "service": "claude-code-switcher",
  "version": "0.1.0"
}
```

## Local Authentication

- `API-010` — Compare received token with `ANTHROPIC_AUTH_TOKEN` using secure comparison.
- `API-011` — Return `401` for missing or invalid token.
- `API-012` — Never forward the local token to providers.

## Roles and Messages

- `PROTO-001` — Accepted roles in input: `system`, `user`, and `assistant`.
- `PROTO-002` — When destination doesn't accept `system` inside `messages`, convert it to the appropriate field.
- `PROTO-003` — Tool result blocks must maintain their identifiers.
- `PROTO-004` — Invalid sequences must produce a local error, not an opaque provider error.

## SSE Streaming

The conceptual event order must follow the Anthropic protocol:

```text
message_start
content_block_start
content_block_delta ...
content_block_stop
message_delta
message_stop
```

- `PROTO-005` — Each frame ends with an empty line.
- `PROTO-006` — JSON must be valid UTF-8.
- `PROTO-007` — Text and tool deltas cannot be mixed in the same block.
- `PROTO-008` — Tool call identifier remains stable.
- `PROTO-009` — Client cancellation cancels the external call and releases resources.
- `PROTO-010` — Keepalive cannot create a second concurrent producer for the same stream.

## Errors

Before streaming, use appropriate HTTP status. After streaming, emit error event and close connection.

Normalized internal format:

```json
{
  "request_id": "req_...",
  "provider": "nvidia_nim",
  "model": "model",
  "status_code": 429,
  "category": "rate_limit",
  "retryable": true,
  "message": "sanitized message"
}
```

- `PROTO-011` — Preserve original HTTP code when known.
- `PROTO-012` — Remove keys, signed URLs, and headers from message.
- `PROTO-013` — Do not transform terminal error into empty success response.