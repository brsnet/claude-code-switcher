# 07 — Testes, observabilidade e operação

## Estratégia de testes

### Unitários

- `TEST-001` — Resolução de nomes Opus, Sonnet e Haiku.
- `TEST-002` — Ordenação numérica de modelos NVIDIA com lacunas.
- `TEST-003` — Remoção estável de duplicatas.
- `TEST-004` — Filtro de ferramentas e `tool_choice`.
- `TEST-005` — Classificação de erros por status e mensagem.
- `TEST-006` — Conversão de eventos OpenAI-compatible para eventos internos.
- `TEST-007` — Redaction de todos os formatos de segredo conhecidos.

### Integração

- `TEST-008` — API Messages completa com provedor simulado.
- `TEST-009` — Retry seguido de sucesso.
- `TEST-010` — Failover antes do primeiro delta.
- `TEST-011` — Proibição de failover depois do primeiro delta.
- `TEST-012` — Cancelamento do cliente libera semáforo e conexão.
- `TEST-013` — Streaming Unicode e chamada de ferramenta fragmentada.
- `TEST-014` — Erro SSE terminal após início da resposta.

### Contrato por provedor

Cada adaptador deve executar o mesmo conjunto de contrato com respostas simuladas:

- texto simples;
- ferramenta válida;
- erro autenticado;
- rate limit;
- timeout;
- stream incompleto;
- fechamento correto do cliente.

### Teste real opcional

Testes que consomem API externa devem ser marcados e desativados por padrão. Nunca devem rodar em CI sem credenciais e autorização explícitas.

## Qualidade

Executar nesta ordem:

```powershell
uv run ruff format
uv run ruff check
uv run ty check
uv run pytest
```

- `TEST-015` — Nenhum `# type: ignore` ou `# ty: ignore`.
- `TEST-016` — Falha em qualquer verificação bloqueia a entrega.
- `TEST-017` — Alterações de comportamento incluem caso de regressão.

## Benchmark

O script de benchmark usa uma solicitação sintética com `Read`, no máximo 128 tokens, thinking desativado e timeout de 30 segundos.

Saída mínima por candidato:

```text
provider, model, http_status, first_event_ms, total_ms,
tool_call_valid, error_category, decision
```

- `BENCH-001` — Não ler arquivos reais do projeto.
- `BENCH-002` — Informar que a execução pode consumir créditos.
- `BENCH-003` — Não promover modelo apenas porque respondeu texto; validar ferramenta.
- `BENCH-004` — Registrar data, máquina e condição quente/fria para modelos locais.

## Logs

Eventos obrigatórios:

| Evento | Campos mínimos |
| --- | --- |
| `ROUTE` | request_id, logical_model |
| `ROUTE_CHAIN` | request_id, candidatos sanitizados |
| `API_REQUEST` | request_id, provider, model, tool_count |
| `ROUTE_RETRY` | request_id, candidate, attempt, reason, wait_ms |
| `ROUTE_FAILOVER` | request_id, from, to, reason |
| `PROVIDER_STREAM` | request_id, provider, first_event_ms |
| `PROVIDER_ERROR` | request_id, provider, category, status |
| `REQUEST_DONE` | request_id, result, total_ms |

- `OBS-001` — Logs não contêm chaves ou cabeçalhos.
- `OBS-002` — Toda linha operacional possui `request_id`.
- `OBS-003` — Métricas diferenciam retry de failover.
- `OBS-004` — Contagem de ferramentas permite confirmar a allowlist mínima.

## Runbook

### Inicialização manual

```powershell
cd D:\projetos\claude-code-switcher
uv run uvicorn server:app --host 0.0.0.0 --port 8082
```

### Verificação

1. Consultar `GET /health`.
2. Confirmar que as rotas foram carregadas sem segredos no log.
3. Enviar mensagem curta sem ferramentas.
4. Enviar mensagem sintética com `Read`.
5. Confirmar o candidato selecionado e o número de ferramentas.

### Diagnóstico rápido

| Sintoma | Verificação |
| --- | --- |
| `401` local | token do cliente e do servidor |
| `402` | saldo do provedor e próximo fallback |
| `404` externo | nome e disponibilidade do modelo |
| `429`/overloaded | retries, concorrência e fallback |
| mais de 10 minutos | timeout, modelo local frio, thinking e tool count |
| caracteres estranhos | decoder UTF-8, eventos cumulativos e conversão de delta |
| ações duplicadas | failover após início do stream |

### Encerramento

O usuário controla o processo. Não criar serviços, tarefas agendadas ou inicialização automática sem solicitação explícita.

