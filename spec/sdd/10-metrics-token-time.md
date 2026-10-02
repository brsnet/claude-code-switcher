# SDD 10 — Token and Time Metrics

## Overview

This specification details the mechanism for collecting and storing performance and token consumption metrics for each external provider call attempt. The goal is to enable post-fact analysis of efficiency, costs, and usage trends.

## Functional Requirements

### METRICAS-001 — Per-Attempt Metrics Collection

For each provider call attempt (regardless of success or failure), the system MUST collect and store:
- Attempt timestamp (ISO 8601 with timezone)
- Request correlation identifier (request_id)
- Provider name (e.g., nvidia_nim, open_router, ollama)
- Concrete model name called (e.g., nvidia/nemotron-3-super-120b-a12b)
- Input token count (input_tokens) when available in provider response
- Output token count (output_tokens) when available in provider response
- Total token count (input + output) when both are available
- Attempt duration in milliseconds (using monotonic clock)
- Success indicator (boolean: True if attempt received HTTP 2xx and produced valid response, False otherwise)
- Error category (when failed, per existing classification: rate_limit, auth_error, not_found, internal_error, etc.)

### METRICAS-002 — Metrics Storage

Collected metrics MUST be stored in append-only format, one line per attempt, in a configurable text file. Each line MUST be a valid JSON object containing all fields above. The system MUST allow configuring:
- Storage file path (default: ./data/metrics.jsonl)
- Flush interval (in seconds, default: 5) to ensure data is written to disk with reasonable frequency without excessively impacting performance.

### METRICAS-003 — Storage Resilience

Metrics storage failures (e.g., disk full, insufficient permissions) MUST NOT affect normal request processing. The system MUST continue operating normally, logging only a warning in the operations log (not a critical error) when a metric cannot be written.

### METRICAS-004 — Metrics Security

No sensitive data MUST be stored in metrics:
- Authorization tokens (Bearer, API keys)
- Prompt content or user messages
- Content of files read via Read tool
- Complete request or response headers
- Any data that could allow reconstruction of confidential information

### METRICAS-005 — Availability for Analysis

The storage format MUST be simple and widely supported by analysis tools (e.g., jq, pandas, pandas.read_json with lines=True). Each line MUST be a self-contained JSON object.

## Derived Metrics

From stored metrics, it is possible to calculate (via post-processing):
- Success rate by provider/model
- Latency distribution (p50, p95, p99) by provider/model
- Average input and output token consumption by call type
- Estimated cost by provider (when token prices are available)
- Relative efficiency between providers for the same task type
- Usage trends over time

## Recommended Implementation

- Create a new module `api.metrics` with function `record_attempt(metrics_dict)` that writes a JSON line to the configured file.
- In `api.services.RequestHandler._try_provider`, after obtaining the attempt result (success or exception), extract necessary data and call `record_attempt`.
- Use `time.monotonic()` to measure duration accurately.
- Extract input tokens from the `request` (approximate count based on character count or using lightweight tokenizer if available, but preferably use the actual count provided by the provider in the response; if not available, record as null).
- Extract output tokens from the `usage` field of the JSON response of OpenAI-compatible providers when available.
- Ensure the write function is fast and non-blocking (consider using in-memory queue and background write if necessary, but for expected volume, synchronous append with configurable flush is sufficient).
- Configure default metrics file path as relative to project directory: `./data/metrics.jsonl`.
- Create the `data/` directory if it doesn't exist at startup.