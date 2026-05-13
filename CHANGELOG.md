# Changelog

Todas as mudanças notáveis do projeto serão documentadas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).

## [2.7.0] - 2026-05-13

### Adicionado
- Arquitetura Híbrida: Crawl4AI (leitura) + Playwright (escrita) para ERP Ademed
- Resposta Multimodal Condicional (áudio → áudio, texto → texto)
- Google Cloud TTS Journey para respostas em voz
- Segundo Cérebro (MAP.md) em cada agente
- Human-in-the-loop para Prometheus (aguarda confirmação antes de executar)
- Buffer de 8 segundos no Redis para agregação de mensagens
- Sincronizador (Agente 5) com scan a cada 30 minutos via Crawl4AI
- Cascata de fallback para notificações (WhatsApp → Email → SMS → Template pago)
- Filtro circadiano para notificações (respeita horários)
- Mascaramento de CPF em logs (LGPD)
- Descarte imediato de imagens após upload no Ademed (LGPD)

### Mudanças em relação a v2.0
- Prometheus e Front-Desk usam DeepSeek-V4 Flash (unificação de modelo)
- Evolution Go como gateway único (sem Bridge FastAPI separada)
- Estrutura de diretórios padronizada: `agents/[nome]/`
- Documentação completa: PRD, Manual, Guia de Instalação, Briefing, Simulação

---

*Kairós Intelligence — Proprietário: Stênio Alves de Souza Maia*
