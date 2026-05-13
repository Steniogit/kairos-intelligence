# Kairós Intelligence v2.7

> Ecossistema de atendimento inteligente para clínicas médicas via WhatsApp.

**Stack:** Evolution Go · OpenClaw · DeepSeek-V4 Flash · Gemini 3.1 · Redis · Crawl4AI · Playwright · Google TTS Journey

---

## Quick Start

```bash
# 1. Clone o repositório
git clone git@github.com:Steniogit/kairos-intelligence.git
cd kairos-intelligence

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 3. Suba os serviços
docker compose up -d

# 4. Verifique a saúde do sistema
./scripts/health-check.sh
```

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                    WhatsApp (Meta)                   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Evolution Go (Gateway)                  │
│              Porta 8080 · kairos-net                 │
└──────────────────────┬──────────────────────────────┘
                       │ webhook
┌──────────────────────▼──────────────────────────────┐
│         OpenClaw (Orquestrador de Agentes)           │
│              Porta 18789 · kairos-net                │
├─────────────────────────────────────────────────────┤
│  Prometheus   │  Front-Desk  │  Manager (Agente 3)  │
│  (Agente 1)   │  (Agente 2)  │  Crawl4AI+Playwright │
│  Gestor       │  Pacientes   │  ERP Ademed          │
├───────────────┴──────────────┴──────────────────────┤
│  Notificações (Agente 4)  │  Sincronizador (Ag. 5)  │
│  Lembretes · NPS · Dicas  │  Sync médicos 30min     │
└─────────────────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  Serviços de Suporte                 │
│  Redis (Buffer 8s) · PostgreSQL · MinIO (Mídia)     │
└─────────────────────────────────────────────────────┘
```

## Agentes

| Agente | Função | Modelo |
|--------|--------|--------|
| **Prometheus** | Assistente do gestor (dashboard, relatórios, comandos) | DeepSeek-V4 Flash |
| **Front-Desk** | Recepcionista virtual 24/7 (agendamento, triagem) | DeepSeek-V4 Flash |
| **Manager** | Acessa ERP Ademed (leitura Crawl4AI, escrita Playwright) | Interno |
| **Notificações** | Lembretes, NPS, dicas de saúde, aniversários | Cron-based |
| **Sincronizador** | Sync de médicos e horários a cada 30min | Cron-based |

## Documentação

| Documento | Descrição |
|-----------|-----------|
| [PRD v2.7](docs/KAIROS-PRD-v2.7.md) | Requisitos completos do sistema |
| [Manual do Sistema](docs/KAIROS-DOC2-MANUAL-SISTEMA.md) | Guia para o gestor |
| [Guia de Instalação](docs/KAIROS-DOC3-GUIA-INSTALACAO.md) | Deploy passo-a-passo |
| [Briefing do Cliente](docs/KAIROS-DOC4-BRIEFING-CLIENTE.md) | Formulário de onboarding |
| [Prompt Antigravity](docs/KAIROS-DOC5-PROMPT-ANTIGRAVITY.md) | Briefing para IA construir |
| [Simulação de Processo](docs/KAIROS-SIMULACAO-PROCESSO.md) | Cenários A-J completos |

## Configuração

| Variável | Descrição |
|----------|-----------|
| `EVOLUTION_API_KEY` | Chave da Evolution Go |
| `DEEPSEEK_API_KEY` | API key DeepSeek |
| `GEMINI_API_KEY` | API key Google Gemini |
| `ADEMED_USER` | Usuário do ERP Ademed |
| `ADEMED_PASS` | Senha do ERP Ademed |

Veja `.env.example` para a lista completa.

## Scripts

| Script | Descrição |
|--------|-----------|
| `scripts/install.sh` | Instalação inicial no VPS |
| `scripts/deploy.sh` | Deploy com verificação |
| `scripts/rollback.sh` | Rollback para versão anterior |
| `scripts/smoke-test.sh` | Testes pós-deploy |
| `scripts/backup.sh` | Backup diário |
| `scripts/health-check.sh` | Health check de todos os serviços |

## Licença

Proprietário — Uso exclusivo autorizado.

---

*Kairós Intelligence v2.7 — Maio 2026*
*Proprietário: Stênio Alves de Souza Maia*
