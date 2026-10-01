# 06 — Ferramentas, streaming e segurança

## Filtro de ferramentas

Allowlist padrão:

```text
Read, Edit, Write, Bash, Glob, Grep
```

- `TOOL-001` — Comparar nomes de ferramenta exatamente, respeitando capitalização definida pelo protocolo.
- `TOOL-002` — Copiar a requisição antes de filtrar.
- `TOOL-003` — Preservar ordem relativa das ferramentas aceitas.
- `TOOL-004` — Remover duplicatas pelo nome.
- `TOOL-005` — Preservar ferramenta explicitamente forçada por `tool_choice`.
- `TOOL-006` — Se a ferramenta forçada não existir na solicitação, devolver erro de validação.
- `TOOL-007` — Se nenhuma ferramenta restar, remover configuração incompatível de `tool_choice`.
- `TOOL-008` — Registrar apenas contagens e nomes não sensíveis.

## Conversão de chamadas de ferramenta

- `TOOL-009` — Acumular argumentos JSON fragmentados até formar documento válido.
- `TOOL-010` — Não executar ferramentas no proxy; apenas transportar a chamada.
- `TOOL-011` — Preservar o identificador da chamada entre request e resultado.
- `TOOL-012` — Argumento incompleto ao fim do stream gera erro terminal explícito.

## Integridade do streaming

- `STREAM-001` — Um único produtor escreve eventos para cada resposta.
- `STREAM-002` — Keepalive é coordenado pelo mesmo pipeline, sem acessar contexto de logging de outra tarefa.
- `STREAM-003` — Deltas são validados antes da serialização.
- `STREAM-004` — Caracteres inválidos são rejeitados ou substituídos de forma controlada; nunca emitir bytes UTF-8 quebrados.
- `STREAM-005` — Fragmentos de marcadores internos do provedor não aparecem como texto normal.
- `STREAM-006` — Não repetir deltas ao converter eventos cumulativos.
- `STREAM-007` — O fechamento do cliente interrompe leitura, retry e keepalive.

## Prevenção de respostas corrompidas

Testes devem cobrir:

- texto Unicode e português com acentos;
- JSON de ferramenta dividido no meio de caractere multibyte;
- evento cumulativo recebido duas vezes;
- reasoning separado de texto final;
- erro no meio de uma chamada de ferramenta;
- encerramento sem marcador final;
- evento externo desconhecido.

## Segurança

- `SEC-001` — Credenciais são carregadas somente de ambiente ou mecanismo seguro futuro.
- `SEC-002` — Usar comparação de tempo constante para o token local.
- `SEC-003` — Aplicar redaction a `Authorization`, `api-key`, `x-api-key`, `nvapi-*`, `sk-*` e parâmetros sensíveis.
- `SEC-004` — Não registrar corpo integral por padrão.
- `SEC-005` — Limitar tamanho da requisição para evitar consumo descontrolado de memória.
- `SEC-006` — Validar endpoints configurados e documentar o risco de SSRF quando URLs forem controladas externamente.
- `SEC-007` — Restringir o bind ao endereço solicitado pelo usuário; recomendar loopback quando acesso de rede não for necessário.
- `SEC-008` — Nunca executar conteúdo de modelo no processo do proxy.
- `SEC-009` — Tratar chaves expostas em conversa ou captura de tela como comprometidas e recomendar rotação.

## Modelo de ameaça resumido

| Ameaça | Mitigação |
| --- | --- |
| Vazamento de chave em log | redaction central e testes |
| Cliente não autorizado | token local obrigatório |
| Resposta duplicada por failover | trava após primeiro conteúdo significativo |
| JSON de ferramenta malformado | validação incremental e erro terminal |
| Endpoint local malicioso | configuração explícita e validação de URL |
| Excesso de consumo externo | timeout, limite de retry e benchmark controlado |

