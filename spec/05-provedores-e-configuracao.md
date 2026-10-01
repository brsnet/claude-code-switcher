# 05 — Provedores e configuração

## Contrato de configuração

- `CFG-001` — `.env` contém valores locais e nunca é versionado.
- `CFG-002` — `.env.example` contém todas as variáveis suportadas sem credenciais reais.
- `CFG-003` — Variáveis desconhecidas não alteram o comportamento.
- `CFG-004` — Valores inválidos produzem mensagem com o nome da variável, nunca com seu segredo.
- `CFG-005` — URLs devem usar `http` ou `https` e ser normalizadas sem duplicar `/v1`.
- `CFG-006` — Variáveis vazias são tratadas como ausentes.

## Provedores

### NVIDIA NIM

- Credencial: `NVIDIA_API_KEY`.
- Modelos: `NVIDIA_NIM_MODEL1...N` e legado opcional.
- Base compatível com OpenAI.
- Deve tratar `Service temporarily overloaded` como falha transitória mesmo quando o transporte externo usar resposta HTTP ambígua.

### OpenRouter

- Credencial: `OPENROUTER_API_KEY`.
- Modelo: `OPENROUTER_MODEL`.
- Base compatível com OpenAI.
- Cabeçalhos opcionais de identificação nunca devem conter segredo.

### DeepSeek

- Credencial: `DEEPSEEK_API_KEY`.
- Modelo: `DEEPSEEK_MODEL`.
- Base compatível com OpenAI.
- `402` indica saldo insuficiente e deve provocar failover sem retry repetitivo.

### Ollama

- URL: `OLLAMA_BASE_URL`, padrão `http://localhost:11434/v1`.
- Modelo: `OLLAMA_MODEL`.
- Credencial não é exigida no uso local padrão.
- Recursos suportados dependem do modelo; validar ferramentas e contexto por benchmark.

### LM Studio

- URL: `LMSTUDIO_BASE_URL`.
- Modelo configurável.
- Compatibilidade OpenAI não implica suporte completo a ferramentas; validar.

### llama.cpp

- URL: `LLAMACPP_BASE_URL`.
- Modelo configurável.
- O suporte a ferramentas depende do template e da compilação do servidor.

## Registro

- `PROV-001` — O registro mapeia prefixo para fábrica de adaptador.
- `PROV-002` — Importar um adaptador não inicia conexão de rede.
- `PROV-003` — Provedor indisponível por configuração não impede o startup se não estiver em rota ativa.
- `PROV-004` — Provedor em rota ativa sem configuração suficiente gera diagnóstico no startup.
- `PROV-005` — Adaptadores reutilizam cliente HTTP quando seguro.
- `PROV-006` — O cliente é encerrado com o método assíncrono correto.

## Modelo interno

```python
@dataclass(frozen=True)
class ModelCandidate:
    provider: str
    model: str

@dataclass(frozen=True)
class ProviderError:
    provider: str
    model: str
    status_code: int | None
    category: str
    retryable: bool
    safe_message: str
```

## Precedência de configuração

1. Variável específica do provedor/modelo.
2. Configuração da rota lógica.
3. Valor padrão documentado.

Não inferir credenciais entre provedores. Não usar uma chave NVIDIA em OpenRouter nem reutilizar o token local do cliente.

## Validação de startup

- Chave local de autenticação definida.
- Ao menos uma rota lógica utilizável.
- Ao menos um candidato configurado por rota necessária.
- Timeouts e concorrência maiores que zero.
- Allowlist sem nomes vazios ou duplicados.
- Endpoints locais com URL válida.

Falhas críticas impedem o startup. Avisos de provedores fora das rotas não impedem o processo.

