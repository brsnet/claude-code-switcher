# 05 — Providers and Configuration

## Configuration Contract

- `CFG-001` — `.env` contains local values and is never versioned.
- `CFG-002` — `.env.example` contains all supported variables without real credentials.
- `CFG-003` — Unknown variables do not alter behavior.
- `CFG-004` — Invalid values produce a message with the variable name, never its secret.
- `CFG-005` — URLs must use `http` or `https` and be normalized without duplicating `/v1`.
- `CFG-006` — Empty values are treated as absent.

## Providers

### NVIDIA NIM

- Credential: `NVIDIA_API_KEY`.
- Models: `NVIDIA_NIM_MODEL1...N` and optional legacy.
- OpenAI-compatible base.
- Must treat `Service temporarily overloaded` as transient failure even when external transport uses ambiguous HTTP response.

### OpenRouter

- Credential: `OPENROUTER_API_KEY`.
- Models: `OPENROUTER_MODEL` and `OPENROUTER_MODEL<N>`, restricted to `openrouter/free` or `:free` variants.
- OpenAI-compatible base.
- Optional identification headers must never contain secrets.
- Paid models are blocked locally to prevent accidental charges.

### Groq

- Credential: `GROQ_API_KEY`.
- Models: `GROQ_MODEL1...N`.
- OpenAI-compatible base: `https://api.groq.com/openai/v1`.
- Free limits and `429` handled by retry/failover.

### Gemini

- Credential: `GEMINI_API_KEY`.
- Models: `GEMINI_MODEL1...N`.
- OpenAI-compatible base: `https://generativelanguage.googleapis.com/v1beta/openai`.
- Advanced features outside OpenAI compatibility remain out of initial scope.

### Cerebras

- Credential: `CEREBRAS_API_KEY`.
- Models: `CEREBRAS_MODEL1...N`.
- OpenAI-compatible base: `https://api.cerebras.ai/v1`.
- Available context and models must be confirmed in dashboard before activation.

### Cloudflare Workers AI

- Credential: `CLOUDFLARE_API_TOKEN` and identifier `CLOUDFLARE_ACCOUNT_ID`.
- Models: `CLOUDFLARE_MODEL1...N`.
- URL derived from account ID, unless explicit `CLOUDFLARE_BASE_URL`.
- Free quota is limited and may return `429` after daily consumption.

### DeepSeek

- Credential: `DEEPSEEK_API_KEY`.
- Model: `DEEPSEEK_MODEL`.
- OpenAI-compatible base.
- `402` indicates insufficient balance and must trigger failover without repetitive retry.

### Ollama

- URL: `OLLAMA_BASE_URL`, default `http://localhost:11434/v1`.
- Model: `OLLAMA_MODEL`.
- Credential not required in standard local usage.
- Supported features depend on model; validate tools and context by benchmark.

### LM Studio

- URL: `LMSTUDIO_BASE_URL`.
- Configurable model.
- OpenAI compatibility does not imply full tool support; validate.

### llama.cpp

- URL: `LLAMACPP_BASE_URL`.
- Configurable model.
- Tool support depends on template and server compilation.

## Registration

- `PROV-001` — Registry maps prefix to adapter factory.
- `PROV-002` — Importing an adapter does not initiate network connection.
- `PROV-003` — Provider unavailable due to configuration does not block startup if not in active route.
- `PROV-004` — Provider in active route without sufficient configuration generates diagnostic at startup.
- `PROV-005` — Adapters reuse HTTP client when safe.
- `PROV-006` — Client is closed with the correct async method.

## Internal Model

```python
@dataclass(frozen=True)
class ModelCandidate:
    provider: str
    model: str


@dataclass(frozen=True)
class ProviderError:
    provider: str
    model: str
    status_code: int | None
    category: str
    retryable: bool
    safe_message: str
```

## Configuration Precedence

1. Provider/model-specific variable.
2. Logical route configuration.
3. Documented default value.

Do not infer credentials between providers. Do not use a NVIDIA key in OpenRouter nor reuse the client's local token.

## Startup Validation

- Local authentication key defined.
- At least one usable logical route.
- At least one candidate configured per required route.
- Timeouts and concurrency greater than zero.
- Allowlist without empty or duplicate names.
- Local endpoints with valid URL.

Critical failures block startup. Warnings for providers outside routes do not block the process.