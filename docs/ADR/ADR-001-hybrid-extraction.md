# ADR-001: Arquitetura Híbrida de Extração (Crawl4AI + Playwright)

## Status
Aceita

## Contexto
O ERP Ademed é uma aplicação web PHP sem API REST pública. Precisamos ler e escrever dados para automação de agendamentos, cadastros e consultas. Existiam duas abordagens:

1. **SQL Direto:** Acessar o banco MySQL do Ademed diretamente.
2. **Automação de Interface:** Usar navegador headless para interagir com a interface web.

A abordagem SQL foi descartada porque:
- Risco de corromper dados (tabelas com lógica de negócio no PHP)
- Sem documentação do schema
- Atualizações do Ademed podem quebrar queries
- Fere os termos de uso do sistema

## Decisão
Adotamos **Arquitetura Híbrida** com dois mecanismos:

### Crawl4AI (Leitura — 80% das operações)
- Extrai dados via CSS selectors do HTML renderizado
- Reutiliza sessão PHP (PHPSESSID) obtida pelo Playwright
- Tempo de resposta: ~1 segundo
- Casos: busca de pacientes, disponibilidade, lista de médicos

### Playwright (Escrita — 20% das operações)
- Controle completo do navegador headless (Chromium)
- Executa JavaScript do Ademed (necessário para formulários e cálculos)
- Tempo de resposta: ~5 segundos
- Casos: criação de agendamento, cadastro de paciente, upload de documentos

### Sessão Compartilhada
- Playwright faz login e obtém `PHPSESSID`
- Crawl4AI reutiliza o cookie para leituras rápidas
- Re-login automático se sessão expirar

## Consequências

### Positivas
- Não depende de acesso ao banco de dados
- Respeita a lógica de negócio do Ademed
- Leituras são rápidas (Crawl4AI)
- Compatível com atualizações do Ademed (desde que HTML não mude drasticamente)

### Negativas
- Seletores CSS podem quebrar com atualizações do Ademed
- Escrita é mais lenta (~5s por operação)
- Necessita container Chromium rodando (2GB+ RAM)
- Manutenção: seletores precisam ser validados periodicamente

### Riscos Mitigados
- **Seletor quebrado:** Retry com timeout estendido + notificação ao gestor
- **Sessão expirada:** Re-login automático via Playwright
- **Ademed fora do ar:** Fila de pendentes + retry no próximo ciclo

---

*ADR-001 — Aceita em 2026-05-13 — Kairós Intelligence v2.7*
