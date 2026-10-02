# 09 — Logging e Monitoramento

## Visão geral
Este especificação detalha os requisitos de logging e monitoramento do Claude Code Switcher, focando na captura de informações essenciais para observabilidade, depuração e análise de desempenho, mantendo a segurança ao não expor dados sensíveis.

## Requisitos funcionais

### LOG-001 — Registro de chamadas externas
O sistema MUST registrar todas as chamadas feitas a provedores externos de IA, incluindo:
- Nome do modelo solicitado (ex: opus, sonnet, haiku ou nome específico do provedor)
- Identificador do provedor (ex: nvidia_nim, open_router, ollama)
- URL completa do endpoint chamado
- Método HTTP e headers relevantes (exceto autorização)
- Payload da requisição (tamanho, não conteúdo sensível)

### LOG-002 — Registro de respostas
Para cada chamada externa registrada, o sistema MUST registrar na resposta:
- Código de status HTTP
- Tokens utilizados (input + output, quando disponível)
- Tempo total de latência (do request ao recebimento da resposta completa)
- Tamanho da resposta
- Indicador se streaming foi utilizado

### LOG-003 — Registro de eventos internos
O sistema MUST registrar eventos internos relevantes para rastreamento:
- ROUTE: Rota lógica escolhida (opus/sonnet/haiku)
- ROUTE_CHAIN: Sequência completa de provedores/modelos tentados
- ROUTE_FAILOVER: Motivo do failover e próximo candidato tentado
- Provider-specific events: Início/fim de streaming, erros do provedor
- Erros de validação e processamento interno

### LOG-004 — Formato de logging estruturado
Todas as entradas de log MUST seguir um formato estruturado (JSON) para facilitar:
- Consulta e agregação em sistemas de monitoramento
- Correlação de eventos relacionados à mesma requisição
- Análise automatizada de padrões e métricas
Cada entrada de log MUST incluir:
- Timestamp com timezone
- Nível de log (DEBUG, INFO, WARN, ERROR)
- ID de correlação da requisição
- Tipo de evento (conforme LOG-001 a LOG-003)
- Campos específicos do tipo de evento

### LOG-005 — Proteção de dados sensíveis
O sistema MUST garantir que nenhum dado sensível seja registrado:
- Tokens de autorização (Bearer, API keys)
- Conteúdo de arquivos privados lidos via ferramenta Read
- Conteúdo de prompts contendo dados pessoais ou confidenciais
- Qualquer dado marcado como sensível pelo cliente

### LOG-006 — Performance do logging
O mecanismo de logging MUST ser assíncrono e não bloqueante para evitar impacto significativo na latência das respostas.

## Métricas derivadas
A partir dos logs registrados, o sistema MUST permitir o cálculo de:
- Taxa de sucesso por provedor/modelo
- Distribuição de latência (p50, p95, p99)
- Consumo médio de tokens por tipo de chamada
- Custo estimado por provedor (quando aplicável)
- Eficiência do cache (quando implementado)