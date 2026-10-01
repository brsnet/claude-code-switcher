# 03 — API e protocolo

## Endpoints

### `POST /v1/messages`

Endpoint principal compatível com Anthropic Messages. Deve aceitar também parâmetros de consulta adicionais usados pelo cliente, como `beta=true`, sem alterar a semântica da mensagem.

- `API-001` — Aceitar requisições com e sem streaming quando suportado pela primeira versão.
- `API-002` — Aceitar `system` como campo superior e mensagens com papéis válidos.
- `API-003` — Preservar a ordem das mensagens e dos blocos de conteúdo.
- `API-004` — Aceitar ferramentas e `tool_choice`.
- `API-005` — Gerar um `request_id` para correlação.
- `API-006` — Ignorar campos desconhecidos somente quando o protocolo permitir; caso contrário, responder erro de validação claro.

Exemplo mínimo:

```json
{
  "model": "claude-sonnet",
  "max_tokens": 512,
  "stream": true,
  "system": "Responda de forma objetiva.",
  "messages": [
    {"role": "user", "content": "Leia o arquivo README.md"}
  ],
  "tools": [
    {
      "name": "Read",
      "description": "Lê um arquivo",
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

- `API-007` — Responder sem consultar provedores externos.
- `API-008` — Informar estado do processo e versão, sem segredos.
- `API-009` — Não afirmar que todos os provedores estão saudáveis sem sondagem explícita.

Resposta sugerida:

```json
{
  "status": "ok",
  "service": "claude-code-switcher",
  "version": "0.1.0"
}
```

## Autenticação local

- `API-010` — Comparar o token recebido com `ANTHROPIC_AUTH_TOKEN` usando comparação segura.
- `API-011` — Retornar `401` para token ausente ou inválido.
- `API-012` — Nunca encaminhar o token local a provedores.

## Papéis e mensagens

- `PROTO-001` — Papéis aceitos na entrada: `system`, `user` e `assistant`.
- `PROTO-002` — Quando o destino não aceitar `system` dentro de `messages`, convertê-lo para o campo adequado.
- `PROTO-003` — Blocos de resultado de ferramenta devem manter seus identificadores.
- `PROTO-004` — Sequências inválidas devem produzir erro local, não erro opaco do provedor.

## Streaming SSE

A ordem conceitual dos eventos deve seguir o protocolo Anthropic:

```text
message_start
content_block_start
content_block_delta ...
content_block_stop
message_delta
message_stop
```

- `PROTO-005` — Cada frame termina com uma linha vazia.
- `PROTO-006` — JSON deve ser UTF-8 válido.
- `PROTO-007` — Deltas de texto e de ferramenta não podem ser misturados no mesmo bloco.
- `PROTO-008` — O identificador de chamada de ferramenta permanece estável.
- `PROTO-009` — Cancelamento do cliente cancela a chamada externa e libera recursos.
- `PROTO-010` — Keepalive não pode criar um segundo produtor concorrente para o mesmo stream.

## Erros

Antes do streaming, usar status HTTP adequado. Depois do streaming, emitir evento de erro e finalizar a conexão.

Formato interno normalizado:

```json
{
  "request_id": "req_...",
  "provider": "nvidia_nim",
  "model": "modelo",
  "status_code": 429,
  "category": "rate_limit",
  "retryable": true,
  "message": "mensagem sanitizada"
}
```

- `PROTO-011` — Preservar código HTTP original quando conhecido.
- `PROTO-012` — Remover chaves, URLs assinadas e cabeçalhos da mensagem.
- `PROTO-013` — Não transformar erro terminal em resposta de sucesso vazia.

