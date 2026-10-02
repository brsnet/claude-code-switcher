# SDD — Claude Code Switcher

## Finalidade

Esta pasta contém a especificação de design do sistema. Ela é a fonte de verdade para implementação, testes e revisão arquitetural do Claude Code Switcher.

O `CLAUDE.md` define princípios e limites globais. Estes SDDs detalham o comportamento esperado. Em caso de conflito, interrompa a implementação, registre a divergência e corrija a documentação antes de prosseguir.

## Ordem de leitura

1. [01-visao-e-escopo.md](01-visao-e-escopo.md)
2. [02-arquitetura.md](02-arquitetura.md)
3. [03-api-e-protocolo.md](03-api-e-protocolo.md)
4. [04-roteamento-e-resiliencia.md](04-roteamento-e-resiliencia.md)
5. [05-provedores-e-configuracao.md](05-provedores-e-configuracao.md)
6. [06-ferramentas-streaming-e-seguranca.md](06-ferramentas-streaming-e-seguranca.md)
7. [07-testes-observabilidade-e-operacao.md](07-testes-observabilidade-e-operacao.md)
8. [08-plano-de-implementacao.md](08-plano-de-implementacao.md)
9. [09-engenharia-de-mudancas-e-quality-gates.md](09-engenharia-de-mudancas-e-quality-gates.md)

## Estado dos requisitos

- `OBRIGATÓRIO`: necessário para a primeira versão funcional.
- `RECOMENDADO`: pode ser adiado, mas a decisão deve ser registrada.
- `FUTURO`: fora do escopo inicial.

Os identificadores de requisito não devem ser renumerados. Requisitos removidos devem ser marcados como obsoletos para preservar a rastreabilidade.

## Definição de pronto

Uma funcionalidade está pronta quando:

- atende aos requisitos associados;
- possui testes automatizados de sucesso e falha;
- não expõe credenciais;
- preserva a semântica do streaming;
- passa por `ruff`, `ty` e `pytest`;
- passa pela coleta e pelo gate canônico definido em
  [09-engenharia-de-mudancas-e-quality-gates.md](09-engenharia-de-mudancas-e-quality-gates.md);
- atualiza o SDD quando introduz uma nova decisão.

