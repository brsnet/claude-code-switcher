# ADR-009: Contratos executáveis e quality gates obrigatórios

**Status:** Accepted
**Date:** 2026-10-01
**Deciders:** mantenedor do projeto

## Context

O projeto possui requisitos detalhados, porém parte deles existe apenas em documentação.
Alterações locais já introduziram regressões simples — como deixar de executar candidatos que
contêm `/` e usar incorretamente a API de logging — sem que o processo de entrega as bloqueasse.

A suíte também mistura testes automatizados com scripts de diagnóstico que acessam `.env`,
imprimem configuração, dependem de um servidor ativo ou requerem pacotes não declarados. Além
disso, Ruff e ty excluem arquivos de teste de forma ampla. Dessa forma, executar apenas uma parte
das verificações pode produzir uma falsa indicação de sucesso.

O proxy está na fronteira entre o Claude Code e provedores heterogêneos. Uma regressão em
roteamento, ferramentas ou streaming pode causar perda de trabalho, repetição de ações e exposição
de dados. Portanto, documentação sem verificação automatizada não é suficiente para essas áreas.

## Decision

Adotar contratos executáveis e um quality gate único como condição para concluir alterações.

1. Requisitos críticos terão identificadores ligados a testes automatizados.
2. Testes unitários, de integração e de contrato serão herméticos por padrão: sem rede, sem `.env`
   real, sem servidor externo e sem credenciais.
3. Testes reais de provedores serão opt-in, marcados e executados apenas com autorização.
4. Scripts manuais não poderão usar nomes coletados pelo Pytest e ficarão fora de `tests/`.
5. Ruff e ty verificarão código de produção e testes; exclusões serão específicas e justificadas.
6. O gate canônico executará formatação, lint, tipos, coleta e suíte completa. Falha de coleta é
   falha da entrega.
7. Mudanças em roteamento, retry, failover, ferramentas ou SSE exigirão teste de regressão no
   limite arquitetural afetado, não somente teste da função editada.
8. A entrega informará comandos executados e eventuais verificações não realizadas. Não será
   permitido declarar a suíte aprovada quando apenas um subconjunto tiver sido executado.
9. O gate será reproduzível localmente antes de ser automatizado em CI.

## Options Considered

### Option A: Manter revisão manual e testes sob demanda

| Dimension | Assessment |
| --- | --- |
| Complexity | Baixa |
| Custo inicial | Baixo |
| Proteção contra regressão | Baixa |
| Diagnóstico | Reativo |

**Pros:** nenhuma migração imediata.

**Cons:** os mesmos erros podem reaparecer; resultados dependem da disciplina de cada agente;
scripts inseguros continuam misturados à suíte.

### Option B: Contratos executáveis e gate local único

| Dimension | Assessment |
| --- | --- |
| Complexity | Média |
| Custo inicial | Médio |
| Proteção contra regressão | Alta |
| Diagnóstico | Precoce e reproduzível |

**Pros:** transforma requisitos em proteção automática; funciona offline; reduz falsos positivos de
conclusão; facilita revisão.

**Cons:** exige sanear testes existentes e manter fixtures de protocolo.

### Option C: Adotar CI imediatamente como única garantia

| Dimension | Assessment |
| --- | --- |
| Complexity | Média/alta |
| Custo inicial | Alto |
| Proteção contra regressão | Alta após configuração |
| Diagnóstico | Tardio se o gate local divergir |

**Pros:** bloqueio centralizado e histórico de execuções.

**Cons:** não resolve por si só testes não herméticos; cria dependência da plataforma antes de o
gate local estar confiável.

## Trade-off Analysis

A opção B entrega a maior redução de risco sem exigir infraestrutura externa. O gate local será a
fonte canônica e poderá ser reutilizado por CI posteriormente. A migração deve ser incremental:
primeiro impedir vazamento e falsa coleta; depois ampliar lint e tipos; por fim adicionar cobertura
de contratos críticos.

## Consequences

- Regressões de orquestração passam a falhar antes da execução manual.
- O diretório `tests/` deixa de ser usado como depósito de scripts de investigação.
- Alterações podem exigir fixtures e testes adicionais, aumentando o custo inicial e reduzindo o
  custo de diagnóstico posterior.
- Testes reais de provedores continuam possíveis, mas ficam claramente separados do gate padrão.
- CI poderá executar exatamente o mesmo gate local, sem uma segunda definição de qualidade.

## Action Items

1. [ ] Sanear ou mover scripts de diagnóstico atualmente coletados como testes.
2. [ ] Remover leitura e impressão de credenciais de todos os artefatos de teste.
3. [ ] Criar fixtures de settings isoladas do `.env` real.
4. [ ] Criar contratos parametrizados para todos os adaptadores.
5. [ ] Cobrir a máquina de estados de retry/failover e o limite de início do stream.
6. [ ] Restringir exclusões de Ruff e ty e corrigir os erros revelados gradualmente.
7. [ ] Criar um comando local único para o quality gate.
8. [ ] Adicionar CI somente depois que o gate local for determinístico.

