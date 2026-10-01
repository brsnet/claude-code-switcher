# 08 — Plano de implementação

## Estratégia

Implementar por fatias verticais pequenas. Cada fase precisa terminar com testes passando antes da próxima. Não conectar APIs pagas até que o mesmo fluxo funcione com provedores simulados.

## Fase 1 — Fundação

- Criar projeto Python 3.14 com `uv`.
- Configurar FastAPI, Uvicorn, Ruff, ty e pytest.
- Criar settings imutáveis e redaction de segredos.
- Implementar `GET /health` e autenticação local.
- Adicionar testes de startup e autenticação.

Saída: servidor local seguro, ainda sem inferência.

## Fase 2 — Protocolo e provedor simulado

- Definir modelos internos de solicitação, candidato, evento e erro.
- Implementar normalização Anthropic e serialização SSE.
- Criar adaptador simulado com texto, ferramenta e falhas controladas.
- Testar Unicode, cancelamento e fechamento do stream.

Saída: `POST /v1/messages` validado sem custo externo.

## Fase 3 — Roteamento

- Resolver Opus, Sonnet e Haiku.
- Implementar prefixos explícitos.
- Expandir modelos NVIDIA numerados.
- Remover duplicatas e candidatos não configurados.
- Implementar filtro mínimo de ferramentas.

Saída: cadeia determinística e requisição reduzida.

## Fase 4 — Resiliência

- Adicionar semáforos por provedor.
- Implementar retry com backoff, jitter e `Retry-After`.
- Criar máquina de estados da tentativa.
- Bloquear failover após conteúdo significativo.
- Propagar erro SSE terminal.

Saída: failover seguro coberto por testes de integração.

## Fase 5 — Provedores remotos

- Criar base OpenAI-compatible.
- Integrar NVIDIA NIM.
- Integrar OpenRouter.
- Integrar DeepSeek.
- Validar fechamento assíncrono e normalização de erros.

Saída: rotas externas funcionais com fallback.

## Fase 6 — Provedores locais

- Integrar Ollama.
- Integrar LM Studio.
- Integrar llama.cpp.
- Tratar diferenças de ferramentas, contexto e thinking.
- Testar indisponibilidade local sem bloquear provedores remotos.

Saída: cadeia híbrida local/remota.

## Fase 7 — Observabilidade e benchmark

- Adicionar eventos estruturados de rota, retry, failover e conclusão.
- Criar benchmark sintético de ferramenta.
- Documentar interpretação dos resultados.
- Validar que nenhum log contém segredo.

Saída: candidatos comparáveis e falhas diagnosticáveis.

## Fase 8 — Endurecimento

- Executar suíte completa.
- Realizar teste manual pelo Claude Code.
- Testar cancelamento, indisponibilidade e streams quebrados.
- Revisar limites, timeouts e concorrência.
- Atualizar SDDs com decisões finais.

Saída: primeira versão candidata a uso diário.

## Matriz de rastreabilidade

| Área | Requisitos | Fase |
| --- | --- | --- |
| API | `API-*`, `PROTO-*` | 1–2 |
| Arquitetura | `ARCH-*` | 1–6 |
| Roteamento | `ROUTE-*` | 3 |
| Resiliência | `RES-*` | 4 |
| Provedores | `PROV-*`, `CFG-*` | 5–6 |
| Ferramentas | `TOOL-*` | 3 |
| Streaming | `STREAM-*` | 2–4 |
| Segurança | `SEC-*` | todas |
| Testes | `TEST-*` | todas |
| Benchmark | `BENCH-*` | 7 |
| Observabilidade | `OBS-*` | 7 |

## Regras para agentes

Antes de implementar:

1. Ler `CLAUDE.md`.
2. Ler `spec/README.md`.
3. Ler o SDD da área alterada e suas dependências.
4. Listar os identificadores de requisito atendidos.
5. Confirmar que não existe decisão contraditória.

Ao concluir, informar arquivos alterados, lógica, verificação e riscos residuais. Uma mudança que contradiga o SDD deve atualizar a especificação no mesmo trabalho.
