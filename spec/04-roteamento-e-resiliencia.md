# 04 — Roteamento e resiliência

## Resolução do modelo lógico

| Entrada do cliente | Rota |
| --- | --- |
| contém `opus` | `ROUTER_OPUS` |
| contém `sonnet` | `ROUTER_SONNET` |
| contém `haiku` | `ROUTER_HAIKU` |
| prefixo explícito | candidato indicado |
| desconhecida | erro de configuração claro |

- `ROUTE-001` — A comparação dos nomes lógicos deve ser normalizada e testada.
- `ROUTE-002` — Uma rota é uma lista ordenada separada por vírgulas.
- `ROUTE-003` — Entradas vazias são descartadas.
- `ROUTE-004` — Prefixos desconhecidos falham antes da chamada externa.

## Expansão de candidatos

Exemplo:

```dotenv
ROUTER_SONNET=nvidia_nim,open_router,ollama
NVIDIA_NIM_MODEL1=modelo-a
NVIDIA_NIM_MODEL2=modelo-b
OPENROUTER_MODEL=modelo-c
OLLAMA_MODEL=modelo-d
```

Resultado:

```text
nvidia_nim/modelo-a
nvidia_nim/modelo-b
open_router/modelo-c
ollama/modelo-d
```

- `ROUTE-005` — Descobrir todas as variáveis `NVIDIA_NIM_MODEL<N>`.
- `ROUTE-006` — Aceitar lacunas e ordenar numericamente, não alfabeticamente.
- `ROUTE-007` — Remover modelos duplicados preservando a primeira posição.
- `ROUTE-008` — Incluir `NVIDIA_NIM_MODEL` legado apenas conforme regra explícita de compatibilidade.
- `ROUTE-009` — Excluir provedores sem credencial ou endpoint exigido e registrar o motivo.
- `ROUTE-010` — Nunca modificar a configuração durante uma solicitação.

## Máquina de estados da tentativa

```text
RESOLVING
   |
   v
TRYING_CANDIDATE --> RETRY_WAIT --> TRYING_CANDIDATE
   |                       |
   | erro esgotado         | cancelamento
   v                       v
NEXT_CANDIDATE          CANCELLED
   |
   +--> TRYING_CANDIDATE
   |
   +--> FAILED

TRYING_CANDIDATE --> STREAMING --> COMPLETED
                           |
                           +--> STREAM_FAILED
```

- `RES-001` — A transição para `STREAMING` ocorre no primeiro evento significativo.
- `RES-002` — Em `STREAMING`, `NEXT_CANDIDATE` é proibido.
- `RES-003` — Keepalive, metadados internos e headers não contam como conteúdo significativo.
- `RES-004` — Texto, reasoning visível e início de chamada de ferramenta contam como conteúdo significativo.

## Política de retry

Status elegíveis:

```text
402, 429, 500, 502, 503, 504, 529
```

Classificação:

| Categoria | Retry no mesmo candidato | Failover |
| --- | --- | --- |
| timeout/conexão | sim | sim |
| `429`/sobrecarga | sim | sim |
| `5xx`/`529` | sim | sim |
| `402` saldo | não | sim |
| `401`/`403` | não | sim, se outro provedor puder funcionar |
| `400` requisição inválida | não | não, salvo incompatibilidade comprovadamente específica |
| cancelamento do cliente | não | não |

- `RES-005` — Backoff exponencial deve ter limite máximo e jitter.
- `RES-006` — A quantidade de tentativas precisa ser configurável e limitada.
- `RES-007` — `Retry-After`, quando válido, tem precedência dentro do limite configurado.
- `RES-008` — A soma de retries respeita o prazo total da solicitação.
- `RES-009` — Cada tentativa registra duração, candidato e resultado.

## Concorrência

- `RES-010` — Cada provedor possui semáforo próprio.
- `RES-011` — O padrão inicial é `PROVIDER_MAX_CONCURRENCY=5`.
- `RES-012` — Ollama/Haiku pode ter limite próprio.
- `RES-013` — Espera pelo semáforo deve respeitar cancelamento e timeout.

## Cenários de aceitação

1. Primeiro modelo retorna `429`; retry esgota; segundo modelo responde; cliente recebe somente a segunda resposta.
2. Primeiro modelo emite texto e depois retorna `500`; cliente recebe erro terminal; nenhum segundo modelo é chamado.
3. DeepSeek retorna `402`; OpenRouter é tentado sem retry inútil no DeepSeek.
4. Cliente cancela durante backoff; nenhuma tentativa adicional começa.
5. Duas entradas NVIDIA apontam ao mesmo modelo; apenas uma tentativa ocorre.

