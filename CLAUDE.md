# Claude Code Switcher

## Identidade do projeto

Este projeto é um roteador local e independente para uso do Claude Code com diferentes provedores e modelos de inteligência artificial. A solução deve oferecer troca transparente de modelos, tolerância a falhas, streaming compatível e baixo custo operacional, preservando a experiência normal do Claude Code.

O projeto, sua documentação, suas decisões técnicas e seu código são de autoria do proprietário deste repositório. Não introduza referências, dependências documentais ou atribuições a projetos usados anteriormente como inspiração ou protótipo.

## Especificações de design

Antes de analisar, planejar ou alterar código, leia `spec/README.md` e os SDDs relacionados à área afetada. A pasta `spec` é a fonte de verdade para requisitos, contratos, estados, critérios de aceitação e ordem de implementação.

- Não implemente comportamento que contradiga um SDD.
- Se uma decisão precisar mudar, atualize o SDD correspondente no mesmo trabalho.
- Cite os identificadores de requisito atendidos ao resumir uma implementação.
- Preserve os identificadores existentes para manter a rastreabilidade.

## Objetivos

- Expor uma API local compatível com o protocolo Anthropic Messages.
- Permitir que os nomes lógicos `opus`, `sonnet` e `haiku` sejam roteados sem ficarem presos a um único modelo.
- Alternar automaticamente entre provedores e modelos quando houver indisponibilidade.
- Priorizar respostas rápidas e uso confiável de ferramentas.
- Reduzir o conjunto de ferramentas enviado aos modelos para diminuir tokens, latência e confusão.
- Suportar modelos locais e APIs externas na mesma instalação.
- Manter configuração sensível exclusivamente em variáveis de ambiente.

## Ambiente de desenvolvimento

- Sistema operacional principal: Windows com PowerShell.
- Python: 3.14.
- Gerenciador de ambiente e execução: `uv`.
- Servidor HTTP: FastAPI com Uvicorn.
- Nunca executar o projeto com o Python global quando houver um comando equivalente via `uv run`.
- O servidor é controlado pelo usuário. Não iniciar, encerrar ou reiniciar processos sem solicitação explícita.

Comando padrão de execução:

```powershell
uv run uvicorn server:app --host 0.0.0.0 --port 8082
```

Configuração do cliente:

```text
ANTHROPIC_BASE_URL=http://127.0.0.1:8082
ANTHROPIC_AUTH_TOKEN=<token-local>
```

O endereço base não deve terminar em `/v1`, pois o cliente adiciona o caminho do endpoint.

## Provedores suportados

O roteador deve trabalhar com os seguintes provedores:

- NVIDIA NIM
- OpenRouter
- DeepSeek
- Groq
- Google Gemini
- Cerebras Inference
- Cloudflare Workers AI
- Ollama
- LM Studio
- llama.cpp

Cada provedor precisa ser implementado como adaptador isolado e registrado em um catálogo central. Código compartilhado do protocolo Anthropic deve permanecer em módulos neutros, sem importações cruzadas entre provedores.

Prefixos de modelo:

| Provedor | Prefixo |
| --- | --- |
| NVIDIA NIM | `nvidia_nim/` |
| OpenRouter | `open_router/` |
| DeepSeek | `deepseek/` |
| Groq | `groq/` |
| Google Gemini | `gemini/` |
| Cerebras | `cerebras/` |
| Cloudflare Workers AI | `cloudflare/` |
| Ollama | `ollama/` |
| LM Studio | `lmstudio/` |
| llama.cpp | `llamacpp/` |

## Configuração por ambiente

Nunca grave chaves reais neste arquivo, no código, em testes, logs ou commits. Use apenas o arquivo `.env`, que deve permanecer ignorado pelo Git. O `.env.example` deve conter somente valores fictícios.

Variáveis esperadas:

```dotenv
# Credenciais
NVIDIA_API_KEY=
OPENROUTER_API_KEY=
DEEPSEEK_API_KEY=
GROQ_API_KEY=
GEMINI_API_KEY=
CEREBRAS_API_KEY=
CLOUDFLARE_API_TOKEN=
CLOUDFLARE_ACCOUNT_ID=

# Modelos NVIDIA; a numeração pode crescer sem limite fixo
NVIDIA_NIM_MODEL1=nvidia/nemotron-3-super-120b-a12b
NVIDIA_NIM_MODEL2=nvidia/nemotron-3-ultra-550b-a55b
NVIDIA_NIM_MODEL3=poolside/laguna-xs-2.1

# Compatibilidade com configuração antiga, se necessária
NVIDIA_NIM_MODEL=

# Outros modelos
OPENROUTER_MODEL=openrouter/free
DEEPSEEK_MODEL=deepseek-chat
OLLAMA_MODEL=qwen3.5:9b
GROQ_MODEL1=openai/gpt-oss-120b
GEMINI_MODEL1=gemini-3.8-flash
CEREBRAS_MODEL1=
CLOUDFLARE_MODEL1=@cf/openai/gpt-oss-120b

# Endpoints locais
OLLAMA_BASE_URL=http://localhost:11434/v1
LMSTUDIO_BASE_URL=http://localhost:1234/v1
LLAMACPP_BASE_URL=http://localhost:8080/v1

# Rotas lógicas, em ordem de prioridade
ROUTER_OPUS=nvidia_nim,open_router,ollama
ROUTER_SONNET=nvidia_nim,open_router,ollama
ROUTER_HAIKU=nvidia_nim,open_router,ollama

# Desempenho e ferramentas
TOOL_ALLOWLIST=Read,Edit,Write,Bash,Glob,Grep
ENABLE_THINKING=false
HTTP_READ_TIMEOUT=600
PROVIDER_MAX_CONCURRENCY=5

# Ajustes opcionais do Ollama para Haiku
HAIKU_LOCAL_NUM_CTX=
HAIKU_LOCAL_THINK=false
HAIKU_LOCAL_MAX_CONCURRENCY=
```

OpenRouter é sempre gratuito neste projeto. Aceitar somente `openrouter/free` ou modelos com
sufixo `:free`; nunca remover o sufixo nem substituir silenciosamente por variante paga.

Variáveis vazias ou sem uso devem ser removidas da configuração ativa. Não manter opções mortas apenas por compatibilidade, salvo quando a interface já estiver publicada e a migração precisar ser gradual.

## Catálogo de modelos NVIDIA

- Descobrir automaticamente `NVIDIA_NIM_MODEL1`, `NVIDIA_NIM_MODEL2`, até `NVIDIA_NIM_MODEL[N]`.
- Aceitar lacunas na numeração.
- Ordenar os modelos pelo índice numérico.
- Remover duplicatas preservando a primeira ocorrência.
- Manter suporte opcional a `NVIDIA_NIM_MODEL` como variável legada.
- Ao expandir `nvidia_nim` em uma rota, testar todos os modelos configurados na ordem declarada.
- Um modelo inválido não pode impedir o uso dos demais.

## Roteamento lógico

Os nomes recebidos do Claude Code devem ser tratados como categorias de capacidade, não como vínculo permanente com um provedor:

- Solicitações Opus usam `ROUTER_OPUS`.
- Solicitações Sonnet usam `ROUTER_SONNET`.
- Solicitações Haiku usam `ROUTER_HAIKU`.
- Um nome com prefixo explícito seleciona diretamente o provedor indicado.
- Cada item da rota pode representar um provedor inteiro ou um modelo específico.

O roteador deve gerar uma cadeia ordenada de candidatos e avançar somente quando a tentativa atual falhar antes de produzir conteúdo significativo.

## Retentativas e failover

Erros elegíveis para retentativa ou troca de candidato:

```text
402, 429, 500, 502, 503, 504, 529
```

Regras:

- Repetir erros transitórios usando espera exponencial com pequena variação aleatória.
- Respeitar limites de concorrência por provedor.
- Após esgotar as tentativas do candidato, seguir para o próximo modelo da cadeia.
- Fazer failover somente antes da emissão de texto ou chamada de ferramenta significativa.
- Depois que o streaming começar, nunca trocar silenciosamente de modelo, pois isso pode duplicar texto, comandos ou edições.
- Erros definitivos ocorridos após o início do streaming devem ser enviados como evento SSE válido.
- Uma falha de saldo `402` pode provocar failover, mas deve aparecer claramente nos logs.

## Política mínima de ferramentas

Por padrão, enviar apenas:

```text
Read, Edit, Write, Bash, Glob, Grep
```

Regras do filtro:

- Criar uma cópia da requisição antes de alterar a lista de ferramentas.
- Preservar uma ferramenta exigida explicitamente em `tool_choice`, mesmo que ela não esteja na lista padrão.
- Remover ou limpar `tool_choice` quando nenhuma ferramenta compatível permanecer.
- Não enviar dezenas de ferramentas que o modelo não precisará usar.
- Adicionar ferramentas extras somente quando o trabalho realmente exigir.
- Considerar que ferramentas de pesquisa web ou subagentes não estarão disponíveis enquanto não forem incluídas ou exigidas explicitamente.

## Thinking e modelos locais

- O modo de raciocínio estendido fica desativado por padrão para priorizar velocidade e compatibilidade.
- O adaptador Ollama deve aceitar seleção automática ou ausência de ferramenta.
- Não presumir suporte do Ollama a ferramenta forçada, imagens ou extensões específicas sem teste do modelo ativo.
- Contexto, concorrência e thinking local podem ter configuração separada para a rota Haiku.
- Modelos locais lentos no primeiro carregamento podem ser mantidos como último fallback, nunca como primeira opção sem benchmark favorável.

## Streaming e compatibilidade

- Aceitar mensagens com papéis `system`, `user` e `assistant`, convertendo-as corretamente para o formato do provedor de destino.
- Produzir eventos SSE válidos e compatíveis com o Claude Code.
- O mecanismo de keepalive deve usar um único produtor para evitar conflito de contexto entre tarefas assíncronas.
- Clientes OpenAI-compatible devem ser encerrados com o método assíncrono realmente oferecido pela biblioteca instalada.
- Uma falha anterior ao primeiro conteúdo deve poder subir internamente para acionar o failover.
- Nunca devolver texto corrompido, fragmentos repetidos ou estruturas internas do provedor como resposta normal.

## Otimizações

- Ignorar geração de título quando ela não agrega valor à execução principal.
- Carregar e validar variáveis de ambiente uma única vez na inicialização.
- Usar acumulação em listas para montar strings durante loops.
- Evitar recursão em fluxos com profundidade variável.
- Manter prompts e esquemas de ferramentas pequenos.
- Não repetir leitura de arquivos ou descoberta de ferramentas sem necessidade.
- Medir tempo até o primeiro token, tempo total, validade da chamada de ferramenta e taxa de falha.

## Observabilidade

Os logs devem permitir reconstruir a decisão do roteador sem revelar prompts, conteúdo de arquivos
ou segredos. Observabilidade não pode alterar controle de fluxo, consumir um iterador, antecipar o
streaming nem transformar falha em sucesso.

Eventos obrigatórios:

- `ROUTE`: rota lógica escolhida.
- `ROUTE_CHAIN`: candidatos expandidos na ordem de tentativa.
- `API_REQUEST`: início da chamada ao provedor.
- `ROUTE_RETRY`: tentativa, motivo e espera antes da repetição.
- `ROUTE_FAILOVER`: motivo e próximo candidato.
- `PROVIDER_STREAM`: tempo até o primeiro evento significativo.
- `PROVIDER_ERROR`: erro normalizado.
- `REQUEST_DONE`: resultado final e duração total.

Campos mínimos por evento:

- `request_id` em toda linha operacional.
- `provider`, `model` e `candidate` quando houver tentativa externa.
- `attempt`, `status_code`, `category` e `duration_ms` quando aplicáveis.
- `tool_count`, nunca o esquema completo das ferramentas.
- `result` explícito: `success`, `error`, `cancelled` ou `stream_error`.

Regras:

- Usar logging estruturado através da API realmente suportada pelo backend. Com o `logging`
  padrão do Python, campos adicionais devem ser enviados por `extra={...}`.
- Cada tentativa deve produzir um evento de início e exatamente um resultado terminal.
- Diferenciar retry no mesmo candidato de failover para outro candidato.
- Registrar descarte de candidato com motivo; uma cadeia não vazia não pode terminar como
  “nenhum erro registrado” sem explicar por que nenhuma tentativa começou.
- Medir com relógio monotônico quando a duração for usada para diagnóstico.
- Capturar contagem real de tokens somente quando o provedor a informar. Não inventar zero como
  valor observado; usar ausência ou `null`.
- Sanitizar mensagens externas antes de registrá-las.
- Testar o logger real pelo menos uma vez; mocks sozinhos não validam compatibilidade da API.

Nunca registrar credenciais, cabeçalhos de autorização, corpo integral da requisição, prompt,
resultado de ferramenta ou conteúdo de arquivos privados. Uma sondagem `HEAD /api/hello`
respondendo `404` pode ser apenas uma verificação do cliente e não caracteriza falha do roteador.

## Benchmark de modelos

Manter um teste pequeno e reproduzível para cada modelo candidato:

- Usar somente a ferramenta sintética `Read`.
- Não enviar código real do projeto.
- Limitar a resposta a aproximadamente 128 tokens.
- Desativar thinking.
- Aplicar limite de 30 segundos por modelo.
- Registrar latência, status HTTP e validade da chamada de ferramenta.
- Alertar que APIs externas podem consumir créditos.

Critério de permanência na rota ativa:

- Responder dentro do limite esperado.
- Emitir uma chamada de ferramenta válida quando solicitada.
- Não retornar caracteres corrompidos ou texto sem coerência.
- Não falhar de forma persistente por modelo inexistente, autorização ou saldo.

Resultados de referência obtidos durante a construção inicial, sujeitos a nova medição:

| Candidato | Resultado observado | Decisão inicial |
| --- | --- | --- |
| Nemotron Super 120B | sobrecarga temporária em uma execução | manter como primário com fallback |
| Nemotron Ultra 550B | ferramenta válida em cerca de 2,9 s | manter |
| Laguna XS 2.1 | ferramenta válida em cerca de 1,2 s | manter |
| OpenRouter DeepSeek | ferramenta válida em cerca de 1,7 s | manter |
| DeepSeek direto | saldo insuficiente (`402`) | excluir da rota até regularização |
| GLM 5.3 testado | modelo inexistente (`404`) | remover |
| Kimi K3 testado | acima de 30 s | remover |
| Ollama Qwen local | acima de 30 s no teste frio | manter apenas como fallback final |

Esses números não são garantias. Repetir o benchmark após mudanças de modelo, hardware, rede ou provedor.

## Estrutura recomendada

```text
api/
  model_router.py       # catálogo, rotas, expansão e filtro de ferramentas
  services.py           # execução, streaming, retentativas e failover
config/
  settings.py           # leitura e validação das variáveis de ambiente
core/
  anthropic/            # protocolo Anthropic compartilhado
providers/
  registry.py           # registro central de adaptadores
  openai_compat.py      # base para APIs compatíveis com OpenAI
  anthropic_messages.py # conversões do protocolo
  rate_limit.py         # concorrência e espera
  ollama/               # comportamento específico do Ollama
scripts/
  benchmark_model_tools.py
tests/
```

## Princípios de engenharia

- Corrigir a causa raiz, não apenas o sintoma.
- Preferir a implementação mais simples que preserve confiabilidade.
- Evitar duplicação e extrair comportamento comum para módulos neutros.
- Preferir composição a cópia de código.
- Encapsular estado interno com métodos públicos apropriados.
- Manter configurações específicas dentro do adaptador correspondente.
- Remover código morto, opções antigas e valores fixos desnecessários.
- Usar nomes independentes de plataforma em módulos compartilhados.
- Concluir migrações no mesmo trabalho, removendo atalhos obsoletos quando seguro.
- Não adicionar `# type: ignore` ou `# ty: ignore`; corrigir o tipo na origem.

## Contratos e estratégia de testes

Aplicar `spec/09-engenharia-de-mudancas-e-quality-gates.md` e o ADR-009. Requisitos críticos não
podem existir apenas como texto: devem possuir contratos automatizados no limite arquitetural em
que a regressão seria observada.

### Regras para testes automatizados

- Manter em `tests/` somente testes coletáveis, determinísticos e sem efeitos externos.
- Não acessar rede, servidor iniciado manualmente ou `.env` real na suíte padrão.
- Não ler, imprimir ou comparar credenciais reais, nem parcialmente.
- Usar settings sintéticas, `monkeypatch`, fixtures e provedores simulados.
- Marcar testes reais de provedor como `external`; eles ficam desativados por padrão e exigem
  autorização explícita porque podem consumir créditos.
- Colocar verificações e utilitários manuais em `scripts/`, sem prefixo `test_`.
- Tratar falha na coleta do Pytest como falha da entrega.
- Não usar mocks para esconder o comportamento que está sendo validado. Para logging, SSE e
  serialização, incluir ao menos um teste com a implementação real do limite correspondente.

### Contratos obrigatórios por área

- **Roteamento:** todo candidato resolvido é tentado ou descartado com motivo explícito; formatos
  `provider/model` e somente `provider` convergem para o mesmo fluxo de execução.
- **Retry e failover:** testar separadamente repetição no mesmo candidato, avanço para o próximo e
  proibição de failover após o primeiro evento significativo.
- **Ferramentas:** validar chamadas estruturadas, argumentos JSON fragmentados, `tool_choice` e
  ausência de texto que simule execução.
- **Streaming:** validar ordem dos eventos, índices, Unicode, término único, cancelamento e erro
  terminal depois de iniciado o stream.
- **Observabilidade:** confirmar correlação por `request_id`, um resultado por tentativa, redaction
  e ausência de mudança no comportamento instrumentado.
- **Configuração:** isolar o ambiente do processo e cobrir valores ausentes, inválidos, duplicados e
  numerados com lacunas.

Todo defeito corrigido deve ganhar um teste de regressão que falhe pela causa original. Testar
somente a função editada não é suficiente quando a falha acontece na integração entre módulos.

## Fluxo obrigatório para alterações

1. Ler `spec/README.md`, o SDD da área e ADRs relacionados.
2. Reproduzir o defeito ou definir um cenário de aceitação observável.
3. Registrar os identificadores de requisitos atendidos e os limites entre módulos afetados.
4. Identificar a causa raiz e o risco de regressão; não corrigir apenas a mensagem de erro.
5. Adicionar um teste de regressão que falhe pela causa correta antes da implementação.
6. Planejar e implementar a menor alteração completa, preservando mudanças não relacionadas.
7. Executar primeiro os testes focados para obter retorno rápido.
8. Executar o gate canônico completo; testes focados não substituem a suíte.
9. Revisar o diff procurando segredos, código morto, exclusões amplas e alterações acidentais.
10. Conferir logs, streaming e liberação de recursos quando essas áreas forem afetadas.
11. Atualizar SDD e ADR no mesmo trabalho quando a decisão ou o comportamento mudar.
12. Documentar o que foi verificado e os riscos residuais sem afirmar sucesso parcial como total.

Antes de implementar, responder internamente:

- Qual requisito muda?
- Qual módulo chama e qual módulo é chamado?
- Qual cenário falhava antes?
- A mudança toca o ponto de início do streaming?
- A mudança acessa rede, segredo ou estado global?
- Qual teste impedirá a recorrência?

Gate canônico, executado nesta ordem:

```powershell
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest --collect-only -q
uv run pytest -q -m "not external"
```

Todas as etapas devem terminar com código zero. Não executar correção automática de formatação como
substituto da verificação. Não reduzir o escopo do gate para fazê-lo passar. Uma exclusão temporária
deve ser específica, justificada e acompanhada de ação de remoção.

Se a dívida existente impedir o gate completo, informar claramente:

- qual comando falhou;
- se a falha já existia ou foi introduzida pela mudança;
- quais testes focados passaram;
- qual trabalho ainda é necessário.

Nunca declarar “todos os testes passaram” quando a coleta falhou, uma dependência estava ausente ou
somente um subconjunto foi executado.

## Segurança

- Tratar qualquer chave publicada em terminal, conversa, captura de tela ou log como comprometida e substituí-la no provedor.
- Não copiar segredos para documentação, exemplos, fixtures ou mensagens de erro.
- Validar URLs locais e externas antes de enviar dados.
- Não executar comandos destrutivos ou alterações externas sem autorização explícita.
- Não iniciar o servidor automaticamente quando o usuário preferir controlá-lo.

## Restrições do projeto

- Não criar vínculo técnico ou documental com o protótipo anteriormente utilizado.
- Não mencionar repositórios de terceiros como origem deste projeto.
- Não prender `opus`, `sonnet` ou `haiku` a um único modelo.
- Não alternar de provedor depois que conteúdo significativo já foi emitido.
- Não aumentar a lista de ferramentas sem necessidade comprovada.
- Não mascarar erros de autenticação, saldo ou limite como sucesso.
- Não afirmar que um modelo funciona sem validar resposta e uso de ferramenta.

## Padrão de entrega dos agentes

Toda entrega técnica deve terminar com:

- `[Arquivos alterados]`
- `[Lógica alterada]`
- `[Método de verificação]`
- `[Riscos residuais]`

Se não houver riscos residuais conhecidos, declarar explicitamente `nenhum`.
