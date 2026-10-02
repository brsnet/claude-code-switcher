# 09 — Engenharia de mudanças e quality gates

## Objetivo

Impedir que alterações aparentemente concluídas introduzam regressões em roteamento, ferramentas,
streaming, segurança ou observabilidade. Este capítulo define como uma mudança é especificada,
testada e aceita.

## Princípios

- `QUAL-001` — Documentação normativa deve possuir teste correspondente quando o comportamento
  for observável por código.
- `QUAL-002` — Uma alteração não está pronta se qualquer etapa do gate canônico falhar ou não for
  executada sem justificativa explícita.
- `QUAL-003` — Sucesso de testes focados não substitui a suíte completa.
- `QUAL-004` — Falha durante coleta de testes é falha da suíte, nunca dependência opcional implícita.
- `QUAL-005` — Código gerado ou alterado por agentes segue o mesmo gate do código humano.

## Classificação dos artefatos de validação

### Testes automatizados

Ficam em `tests/`, são coletados pelo Pytest e devem:

- ser determinísticos;
- funcionar sem rede;
- usar configuração sintética;
- nunca ler o `.env` real;
- nunca imprimir segredos, nem parcialmente;
- não depender de um servidor iniciado manualmente;
- declarar toda dependência necessária no projeto.

### Testes reais de provedor

- `QUAL-006` — Devem usar marcador `external` e ficar desativados por padrão.
- `QUAL-007` — Exigem variável explícita de habilitação e autorização do usuário.
- `QUAL-008` — Devem limitar custo, tokens e duração.
- `QUAL-009` — Resultados reais não substituem contratos simulados.

### Scripts manuais

- `QUAL-010` — Ficam em `scripts/`, não em `tests/`.
- `QUAL-011` — Não começam com `test_`.
- `QUAL-012` — Informam pré-condições e efeitos antes de executar.
- `QUAL-013` — Saídas aplicam redaction e não enumeram variáveis secretas.

## Pirâmide de contratos

| Camada | Responsabilidade | Exemplos obrigatórios |
| --- | --- | --- |
| Unidade | Regra local pura | normalização, expansão, classificação de erro |
| Componente | Limite entre módulos | roteador → candidato; adaptador → evento normalizado |
| Integração | Fluxo interno completo | API → orquestrador → provedor simulado → SSE |
| Regressão | Defeito já observado | candidato com `/`; tool call fragmentada; Unicode |
| Externo opt-in | Compatibilidade real | NVIDIA, OpenRouter, DeepSeek, Ollama |

## Contratos críticos

### Roteamento e orquestração

- `CONTRACT-001` — Todo candidato retornado pelo roteador é tentado ou possui motivo explícito e
  testado para ser ignorado.
- `CONTRACT-002` — Candidatos `provider/model` e tokens somente de provedor seguem o mesmo fluxo
  após a resolução do modelo.
- `CONTRACT-003` — `attempted_candidates` corresponde exatamente às chamadas iniciadas.
- `CONTRACT-004` — Lista resolvida não vazia nunca termina como “nenhum erro registrado” sem que
  uma razão de descarte seja registrada.
- `CONTRACT-005` — Retry e failover são testados separadamente.

### Streaming e ferramentas

- `CONTRACT-006` — O primeiro evento significativo sela o candidato e proíbe failover.
- `CONTRACT-007` — Argumentos fragmentados de ferramenta resultam em JSON válido ou erro
  normalizado, nunca execução parcial.
- `CONTRACT-008` — Texto narrando uma ação não substitui chamada de ferramenta estruturada quando
  uma ferramenta é obrigatória.
- `CONTRACT-009` — Cada stream termina uma única vez com sequência SSE válida.

### Observabilidade

- `CONTRACT-010` — Logging estruturado usa a API suportada pelo backend configurado.
- `CONTRACT-011` — Cada tentativa produz início e exatamente um resultado: sucesso, erro ou
  cancelamento.
- `CONTRACT-012` — Campos sensíveis são bloqueados por testes de redaction.
- `CONTRACT-013` — Instrumentação não muda controle de fluxo, ordem de candidatos ou conteúdo.

## Matriz de impacto obrigatória

Antes de implementar, registrar no plano da mudança:

| Pergunta | Evidência esperada |
| --- | --- |
| Qual requisito muda? | identificadores SDD/ADR |
| Qual limite arquitetural é afetado? | módulo chamador e chamado |
| Qual regressão pode surgir? | cenário de falha |
| Qual teste falhava antes? | nome do teste de regressão |
| A mudança toca streaming? | estado antes/depois do primeiro evento |
| A mudança toca segredo/rede? | estratégia de isolamento |

## Gate canônico

O gate local deve executar, nesta ordem:

```powershell
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest --collect-only -q
uv run pytest -q -m "not external"
```

- `GATE-001` — Todos os comandos terminam com código zero.
- `GATE-002` — A coleta não executa chamadas HTTP nem lê credenciais.
- `GATE-003` — O conjunto de arquivos verificados não exclui `tests/` globalmente.
- `GATE-004` — Exclusões são específicas, documentadas e temporárias.
- `GATE-005` — O relatório final diferencia suíte focada, suíte completa e teste externo.
- `GATE-006` — Formatação corretiva não faz parte da verificação; mudanças de formato devem ser
  revisáveis antes do gate.

## Fluxo obrigatório de mudança

1. Reproduzir o defeito ou definir o cenário de aceitação.
2. Identificar os requisitos e limites afetados.
3. Adicionar um teste que falha pela causa correta.
4. Implementar a menor correção completa.
5. Executar testes focados.
6. Executar o gate canônico completo.
7. Revisar o diff por segredos, código morto e mudanças não relacionadas.
8. Informar verificações executadas e riscos residuais.

## Política de adoção incremental

### Etapa A — tornar a suíte confiável

- separar scripts manuais;
- eliminar leituras do `.env` em testes;
- declarar dependências ou remover testes obsoletos;
- garantir coleta limpa.

### Etapa B — cobrir contratos críticos

- adicionar provedor simulado reutilizável;
- criar testes parametrizados de adaptadores;
- testar estados de retry, failover e streaming;
- vincular regressões aos identificadores `CONTRACT-*`.

### Etapa C — ampliar análise estática

- remover exclusão global de testes do Ruff;
- incluir testes no ty quando as incompatibilidades atuais forem saneadas;
- proibir novas exclusões amplas.

### Etapa D — automatizar

- criar comando único local;
- executar o mesmo comando em CI;
- bloquear integração quando o gate falhar.

## Critérios de aceitação desta política

1. `pytest --collect-only` funciona sem pacote opcional nem servidor ativo.
2. Nenhum teste lê ou imprime chaves reais.
3. A regressão de candidatos `provider/model` é coberta.
4. Instrumentação de logging possui teste que executa o logger real.
5. O gate completo pode ser repetido duas vezes com o mesmo resultado.

