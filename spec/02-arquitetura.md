# 02 — Arquitetura

## Visão geral

```text
Claude Code
    |
    | Anthropic Messages + SSE
    v
API FastAPI
    |
    +--> normalização de entrada
    +--> filtro de ferramentas
    +--> resolução da rota
    v
Orquestrador de tentativas
    |
    +--> limite de concorrência
    +--> retry com backoff
    +--> failover pré-stream
    v
Registro de provedores
    |
    +--> NVIDIA NIM
    +--> OpenRouter
    +--> DeepSeek
    +--> Ollama
    +--> LM Studio
    +--> llama.cpp
    v
Normalização de eventos --> SSE --> Claude Code
```

## Componentes

### Camada HTTP

- `ARCH-001` — Validar autenticação local, corpo, tipos e limites básicos.
- `ARCH-002` — Não conter regras específicas de provedor.
- `ARCH-003` — Converter exceções anteriores ao streaming em resposta HTTP adequada.
- `ARCH-004` — Depois de abrir o streaming, converter erro terminal em evento SSE válido.

### Configuração

- `ARCH-005` — Ler o ambiente uma vez na inicialização.
- `ARCH-006` — Validar tipos, URLs e valores obrigatórios antes de aceitar tráfego.
- `ARCH-007` — Expor configuração imutável aos demais componentes.
- `ARCH-008` — Nunca fornecer valor secreto em representação textual ou log.

### Roteador de modelos

- `ARCH-009` — Transformar o nome solicitado em uma lista ordenada de candidatos.
- `ARCH-010` — Expandir entradas de provedor em seus modelos configurados.
- `ARCH-011` — Remover candidatos duplicados preservando ordem.
- `ARCH-012` — Não realizar chamadas de rede.

### Orquestrador

- `ARCH-013` — Ser o único responsável por retry, failover e ciclo de vida da tentativa.
- `ARCH-014` — Registrar resultado de cada candidato.
- `ARCH-015` — Controlar o ponto após o qual failover é proibido.

### Adaptadores

- `ARCH-016` — Implementar uma interface comum para preparar e transmitir a resposta.
- `ARCH-017` — Isolar particularidades do SDK, URL, autenticação e formato externo.
- `ARCH-018` — Normalizar erros sem apagar status e mensagem úteis.
- `ARCH-019` — Não importar implementação de outro provedor.

### Núcleo Anthropic

- `ARCH-020` — Conter modelos, eventos e conversões compartilhadas do protocolo.
- `ARCH-021` — Não depender de FastAPI nem de SDK específico.

## Interface conceitual do adaptador

```python
class ProviderAdapter(Protocol):
    name: str

    async def stream(
        self,
        request: NormalizedRequest,
        candidate: ModelCandidate,
    ) -> AsyncIterator[NormalizedEvent]: ...
```

O adaptador devolve eventos normalizados. A serialização Anthropic/SSE pertence ao núcleo, evitando implementações divergentes por provedor.

## Estrutura de diretórios alvo

```text
server.py
api/
  routes.py
  services.py
  model_router.py
config/
  settings.py
core/
  anthropic/
    models.py
    normalize.py
    stream_response.py
  errors.py
providers/
  base.py
  registry.py
  openai_compat.py
  rate_limit.py
  nvidia_nim/
  openrouter/
  deepseek/
  ollama/
  lmstudio/
  llamacpp/
scripts/
  benchmark_model_tools.py
tests/
spec/
```

## Decisões arquiteturais

| Decisão | Escolha | Consequência |
| --- | --- | --- |
| Contrato interno | Eventos normalizados | Adaptadores menores e streaming consistente |
| Configuração | Ambiente validado no startup | Erros aparecem cedo |
| Failover | Somente antes de conteúdo significativo | Evita ações duplicadas |
| Ferramentas | Allowlist mínima | Menos tokens, com menor disponibilidade de ferramentas opcionais |
| Provedores OpenAI | Base compatível compartilhada | Reuso sem acoplamento entre adaptadores |
| Servidor | FastAPI/Uvicorn | Boa integração assíncrona e SSE |

## Invariantes

1. Uma solicitação possui no máximo um candidato que tenha emitido conteúdo significativo.
2. Toda conexão externa é encerrada, inclusive em cancelamento.
3. A ordem dos candidatos é estável.
4. A requisição original não é alterada pelo filtro de ferramentas.
5. Eventos externos nunca são repassados sem validação e normalização.

