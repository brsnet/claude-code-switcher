# 01 — Visão e escopo

## Problema

O Claude Code normalmente seleciona modelos por nomes lógicos, mas diferentes ambientes podem exigir modelos locais, APIs externas, fallback por indisponibilidade e controle de custo. O sistema precisa intermediar essas solicitações sem obrigar o cliente a conhecer detalhes de cada provedor.

## Solução

O Claude Code Switcher será um proxy HTTP local compatível com Anthropic Messages. Ele receberá uma solicitação, normalizará o conteúdo, filtrará ferramentas, resolverá uma cadeia de candidatos e transmitirá a resposta do provedor escolhido no formato esperado pelo cliente.

## Metas funcionais

- `SCOPE-001` — Expor uma API local compatível com o endpoint de mensagens usado pelo Claude Code.
- `SCOPE-002` — Mapear `opus`, `sonnet` e `haiku` para rotas configuráveis.
- `SCOPE-003` — Suportar NVIDIA NIM, OpenRouter, DeepSeek, Ollama, LM Studio e llama.cpp.
- `SCOPE-004` — Tentar mais de um modelo NVIDIA configurado por variáveis numeradas.
- `SCOPE-005` — Executar retentativas e failover sem duplicar conteúdo ou ferramentas.
- `SCOPE-006` — Restringir ferramentas ao conjunto mínimo configurado.
- `SCOPE-007` — Emitir streaming SSE válido.
- `SCOPE-008` — Oferecer health check, logs estruturados e benchmark de candidatos.

## Metas não funcionais

- `NFR-001` — Tempo adicional do proxy antes da chamada externa menor que 100 ms no caminho normal.
- `NFR-002` — Nenhuma credencial em logs, respostas, documentação ou exceções.
- `NFR-003` — Comportamento determinístico para a mesma configuração de rotas.
- `NFR-004` — Falha de um provedor não pode indisponibilizar candidatos saudáveis.
- `NFR-005` — O sistema deve funcionar no Windows com PowerShell, Python 3.14 e `uv`.
- `NFR-006` — Toda operação assíncrona deve liberar conexões e tarefas ao terminar.

## Fora do escopo inicial

- Interface gráfica.
- Armazenamento de conversas.
- Gerenciamento de cobrança dos provedores.
- Alteração automática de `.env` em produção.
- Balanceamento baseado em custo em tempo real.
- Garantia de recursos não oferecidos pelo modelo, como visão ou ferramenta forçada.
- Execução automática do servidor sem autorização do usuário.

## Atores

- **Claude Code:** cliente que envia mensagens e ferramentas.
- **Usuário:** configura modelos, inicia o servidor e avalia resultados.
- **Roteador:** resolve candidatos e coordena tentativas.
- **Adaptador:** traduz requisições e respostas de um provedor.
- **Provedor:** serviço local ou remoto que executa inferência.

## Critérios de sucesso

- Uma solicitação compatível produz resposta válida pelo primeiro candidato saudável.
- Um erro elegível antes do primeiro conteúdo avança para o próximo candidato.
- Uma falha depois do início do conteúdo termina a resposta sem segunda execução silenciosa.
- O modelo recebe apenas as ferramentas necessárias.
- Um benchmark identifica modelos lentos, inválidos ou incapazes de chamar ferramentas.

