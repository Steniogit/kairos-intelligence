# PRD — Kairós Intelligence
## Product Requirements Document v2.7.1
**Data:** 01/05/2026 | **Revisão:** 13/05/2026 | **Proprietário:** Stênio Alves de Souza Maia | **Status:** Pronto para Desenvolvimento

> **Nota de Revisão v2.7.1 (13/05/2026):**
> - Prometheus unificado para DeepSeek-V4 Flash (era Gemini 3.1 Pro)
> - Estrutura padronizada para `agents/[nome]/`
> - Evolution Go como gateway único (sem Bridge FastAPI separada)
> - Adicionado MAP.md (Segundo Cérebro) em cada agente

---

> **Kairós** (καιρός) — Do grego: o momento certo, a oportunidade precisa.
> Um ecossistema de IA que age no momento exato para o paciente certo,
> da forma certa.

---

## 1. VISÃO DO PRODUTO

O **Kairós Intelligence** é um ecossistema autônomo e multi-empresa (SaaS) voltado para automação de atendimento em clínicas médicas e veterinárias via WhatsApp, com integração nativa ao ERP Ademed. A solução combina agentes de IA, governança multi-tenant, automação de browser e comunicação proativa para eliminar no-show, reduzir custos operacionais e escalar sem aumento de equipe.

### 1.1 Objetivos Estratégicos

- **Eliminar no-show:** Meta de redução para abaixo de 10% via confirmação proativa em múltiplas etapas
- **Escalabilidade de holding:** Adicionar novas clínicas apenas com configuração — sem novo código
- **Custo operacional mínimo:** Estratégia de janela dinâmica reduz custo Meta em até 98%
- **Atendimento humanizado:** O paciente não percebe que está falando com IA

### 1.2 Público-Alvo

Clínicas médicas e veterinárias de pequeno e médio porte no Brasil com 50 a 300 atendimentos por dia.

---

## 2. ARQUITETURA DE INFRAESTRUTURA

### 2.1 Visão Geral

Todo o sistema roda em **Docker na mesma rede bridge interna** de um VPS Hostinger KVM 2, garantindo comunicação assíncrona entre containers com latência mínima.

```
┌─────────────────────────────────────────────────────────────┐
│                    VPS HOSTINGER KVM 2                       │
│                    Rede Docker: kairos-net                   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Evolution Go │  │  OpenClaw    │  │   Paperclip      │  │
│  │ (WhatsApp)   │  │  (Agentes)   │  │ (Governança)     │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                    │             │
│  ┌──────▼───────────────────────────────────────▼─────────┐ │
│  │                     Redis                               │ │
│  │         (Cache, Buffer 8s, Debounce, Filas)             │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  PostgreSQL  │  │   Neo4j /    │  │     MinIO        │  │
│  │ (Governança) │  │  ChromaDB    │  │  (Mídia/Docs)    │  │
│  │              │  │ (GraphRAG)   │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Serviços Docker

| Serviço | Imagem | Função | Porta Interna |
|---|---|---|---|
| Evolution Go | evolutionapi/evolution-go:latest | Gateway WhatsApp (Go) | 8080 |
| OpenClaw | openclaw/openclaw:latest | Framework de agentes | 18789 |
| Paperclip | paperclipai/paperclip:latest | Control Plane / Governança | 3000 |
| Redis | redis:7-alpine | Cache, buffer, filas | 6379 |
| PostgreSQL | postgres:15-alpine | Dados de governança | 5432 |
| Neo4j | neo4j:5-community | GraphRAG base conhecimento | 7474 |
| ChromaDB | chromadb/chroma:latest | Vetores de embedding | 8000 |
| MinIO | minio/minio:latest | Armazenamento de mídia | 9000 |

> **Nota Evolution Go:** Reescrito do zero em Go sobre a biblioteca whatsmeow.
> Usa 50-150MB de RAM por instância (vs 200-500MB da versão Node.js).
> Sub-second cold starts. Goroutine-based concurrency para milhares de
> conexões simultâneas. Requer apenas PostgreSQL (sem Redis adicional
> para sua própria operação). Docker-ready com Swagger em /swagger/index.html.

### 2.3 Rede e Comunicação

- Todos os serviços na mesma rede bridge `kairos-net`
- Comunicação interna por hostname do container (sem latência de rede externa)
- Apenas Evolution Go e Paperclip expostos externamente (via Tailscale)
- SSL via Certbot + Nginx reverse proxy
- Monitoramento: UptimeRobot (externo, gratuito)

---

## 3. MODELOS DE IA (LLMs)

| Uso | Modelo | Justificativa |
|---|---|---|
| Chat rápido (Agente 2) | DeepSeek-V4 Flash | Alta velocidade, baixo custo |
| Visão / OCR (documentos) | Gemini 3.1 Flash | Extração de RG e carteirinhas |
| Áudio / transcrição | Gemini 3.1 Flash | Transcrição de áudios WhatsApp |
| Raciocínio complexo (Master) | DeepSeek-V4 Flash | Unificação de modelo — mesmo custo/velocidade |
| Síntese de voz (respostas) | Google TTS | Voz do Agente Master |
| Fallback de emergência | GPT-4o Mini | Quando outros modelos falharem |

### 3.1 Cascata de Tokens (BYOK)

Sistema de fallback de chaves para evitar interrupção por quota excedida (erro 429):

```
Chave da clínica (quota individual)
        ↓ se erro 429
Chave Mestra Kairós (quota compartilhada)
        ↓ se erro 429
Chave de emergência (GPT-4o Mini)
        ↓ se erro 429
Mensagem automática de fallback + notificação Master
```

---

## 4. GOVERNANÇA E HIERARQUIA (PAPERCLIP)

### 4.1 Organograma

```
THE BOARD (Conselho)
└── Stênio — controle financeiro, estratégico e aprovações

THE CEO — PROMETHEUS (OpenClaw)
└── Agente mestre que supervisiona todas as clínicas
    Gera relatórios de ROI consolidados
    Recebe alertas críticos de qualquer clínica
    Controla limites de gastos por tenant

THE MANAGERS (por clínica)
└── Orquestradores lógicos por clínica
    Fazem a ponte com o Ademed via Playwright
    Gerenciam o GraphRAG específico de cada clínica
    Reportam ao Prometheus

THE FRONT-DESK (por clínica)
└── Agentes de atendimento final (WhatsApp)
    Interagem diretamente com pacientes
    Acionam os Managers para consultas e ações
```

### 4.2 Multi-Tenant

Cada clínica é um **tenant** isolado no Paperclip com:
- Budget de tokens próprio
- Instância Evolution Go própria (número WhatsApp separado)
- Base GraphRAG própria (Neo4j/ChromaDB)
- Variáveis de ambiente isoladas
- Logs e auditoria segregados

Adicionar nova clínica = configurar novo tenant no Paperclip. Sem novo código.

---

## 5. ARQUITETURA DOS AGENTES (5 AGENTES)

### 5.1 Agente 1 — Prometheus (Master/CEO)

**Responsabilidade:** Assistente pessoal do gestor (Stênio) e supervisor de todas as clínicas.

**Canal:** WhatsApp pessoal do gestor (número único, acesso restrito).

**Capacidades:**
- Multimodal: texto, voz (Gemini Audio), imagem (Gemini Vision), vídeo, documentos
- Resposta em voz via Google TTS quando solicitado
- Dashboard por linguagem natural para qualquer clínica
- Executa ações via Manager da clínica específica
- Orquestra broadcasts com validação automática das regras da Meta
- Monitoramento contínuo de todos os tenants
- Alerta de agenda vazia com sugestão de broadcast segmentado
- Monitoramento de custo de tokens por clínica (alerta se >20% acima do estimado)
- Intervém em conversas de qualquer Agente 2 quando necessário

**Monitoramento em 3 níveis:**
- 🔴 Urgente → notifica imediatamente (falha crítica, NPS baixo, erro 429 recorrente)
- 🟡 Aviso → relatório diário (anomalias, sugestões de fluxo)
- 🟢 Insight → relatório semanal (tendências, oportunidades)

**Relatórios automáticos:**
- Diário às 8h: agendamentos, confirmados, sem resposta, cancelamentos, NPS médio
- Semanal (segunda 8h): tendências, comparativos entre clínicas, gargalos
- Mensal (dia 1 às 8h): ROI consolidado, comparativo, sugestões estratégicas

**Fallback de LLM (3 camadas):**
1. Detecta falha → notifica gestor imediatamente
2. Mensagem automática pré-definida para pacientes
3. Após 15 min: tenta modelo alternativo na cascata BYOK

**Modelo:** DeepSeek-V4 Flash (unificado com Front-Desk — alta velocidade, baixo custo).

---

### 5.2 Agente 2 — Front-Desk (Atendimento)

**Responsabilidade:** Recepcionista virtual que atende pacientes via WhatsApp.

**Canal:** Evolution Go (instância por clínica).

**Processamento de mensagens:**
- **Buffer de 8 segundos (Redis):** Agrupa mensagens fragmentadas do usuário em uma única requisição ao LLM. Paciente que manda "oi" / "quero marcar" / "consulta com Dr. Carlos" em sequência rápida — o sistema aguarda 8 segundos, consolida e processa como uma mensagem só. Reduz custo de API e melhora experiência.
- **Denoising:** Extração de entidades relevantes para reduzir tokens e ruído no prompt.

**Identificação híbrida do paciente:**
1. Consulta GraphRAG pelo número de WhatsApp
2. Se encontrar → confirma só o nome: *"Olá! Você é o João?"*
3. Se não encontrar → pede CPF
4. Se CPF não encontrar → fluxo de paciente novo

**Fluxo de paciente novo (OCR):**
1. Consentimento LGPD (obrigatório antes de produção)
2. Solicita foto do documento (RG ou CNH)
3. **Gemini Vision** extrai: nome, CPF, nascimento, número do documento
4. Valida qualidade da imagem antes de processar
5. Pergunta: convênio ou particular?
6. Se convênio: solicita foto da carteirinha
7. **Gemini Vision** extrai: convênio, carteirinha, validade, plano
8. Manager valida convênio navegando no Ademed
9. Confirma dados com paciente antes de cadastrar
10. Manager cadastra no Ademed via Playwright
11. Manager faz upload dos documentos na seção Arquivos do Ademed
12. **REGRA LGPD:** Arquivos deletados do VPS imediatamente após upload confirmado

**Agendamento:**
- Paciente sugere médico e horário preferido
- Manager verifica disponibilidade no Ademed via Playwright
- Se disponível: confirma
- Se não disponível: negocia alternativas até encontrar horário que sirva
- Manager confirma no sistema via Playwright
- Mensagem de confirmação completa para o paciente
- Agente 4 notifica recepcionista

**Múltiplos agendamentos:** Lista todos ativos e pergunta sobre qual antes de qualquer ação.

**Cancelamento:** Direto no Ademed, sem aprovação do gestor.

**Reagendamento:** Máximo 2 vezes. Na 3ª → escala para recepcionista.

**Timeout:** 30 minutos sem resposta → encerra com mensagem amigável, limpa contexto Redis.

**Mensagens fora do escopo:** Redireciona com variação natural. Após 3 tentativas → handoff.

**Handoff humano:** Tenta 1 vez. Se não resolver → escala com contexto completo para recepcionista.

**Horário:** 24/7 sem restrição.

**Tom:** Humanizado, natural, nunca finge ser humano. Nome configurável por clínica. Português do Brasil com contrações naturais. Emojis com moderação.

**Modelo:** DeepSeek-V4 Flash (chat rápido, baixo custo). Gemini 3.1 Flash para processamento de imagens e áudio.

---

### 5.3 Agente 3 — Manager (Clínico)

**Responsabilidade:** Único ponto de contato com o sistema Ademed. Orquestrador lógico por clínica. Serviço compartilhado entre Agentes 2 e 4.

**MVP — Acesso exclusivo via browser (Playwright):**
Todas as operações — leitura e escrita — via navegação no Ademed.
Sem acesso direto ao banco de dados no MVP.

**Operações implementadas:**
- Buscar paciente por CPF (tela de pesquisa Ademed)
- Consultar histórico e agendamentos ativos
- Verificar horários disponíveis na agenda
- Validar convênios aceitos
- Cadastrar paciente novo (formulário Ademed)
- Upload de documentos (RG e Carteirinha) — salvar no sistema
- Criar agendamento
- Cancelar e reagendar
- Atualizar status (sem resposta, atendido, desmarcado)
- Criar Guia de Consulta
- Criar Guia SP/SADT
- Preencher Contratado Executante (Campo 9 Guia Consulta / Campo 29 SP/SADT)
- Verificação ANS (senha de autorização)
- Extrair lista de médicos ativos (para Agente 5)
- Extrair agendamentos do dia (para Agente 4)

**Nota técnica Ademed v2.02:**
- Mega-page com 2.415 elementos em `listaAgenda.php`
- Formulários são diálogos jQuery UI — sem URLs próprias
- Sessão PHP por cookie — manter contexto do browser entre operações
- Fila sequencial: UMA requisição de browser por vez
- Timeouts generosos: 15-20 segundos para navegação

**Log de ações (obrigatório):**
Toda ação registrada em `~/logs/agente3-actions.log`
Formato JSON: timestamp, operação, identificador (CPF mascarado), resultado, detalhe
Retenção: 90 dias. Nunca incluir dados de saúde.

**Fallback (Ademed fora do ar):**
1. Salva dados em `~/logs/agendamentos-pendentes.json`
2. Notifica recepcionista com todos os dados
3. Informa Agente 2 para avisar paciente

**Versão futura:** Adicionar leitura via SQLAlchemy quando volume justificar.

**Modelo:** DeepSeek-V4 Flash (tarefas estruturadas).

---

### 5.4 Agente 4 — Notificações (Proativo)

**Responsabilidade:** Toda comunicação proativa com pacientes ao longo do ciclo completo.

#### Ciclo Completo do Paciente

```
AGENDAMENTO CONFIRMADO
        ↓
[Se opt-in de dicas]
Dicas de saúde personalizadas
(a cada 3-4 dias, pelo GraphRAG)
        ↓
ORIENTAÇÕES PRÉ-CONSULTA ESPECÍFICAS
(jejum, documentos, preparo por especialidade)
Enviadas junto com o lembrete
        ↓
LEMBRETE DE CONFIRMAÇÃO (janela dinâmica)
        ↓
SEGUNDO LEMBRETE (4h antes, se sem resposta)
        ↓
[Se 1h antes sem resposta]
STATUS "SEM RESPOSTA" NO ADEMED
+ Notificação recepcionista
        ↓
CONSULTA ACONTECE
        ↓
PÓS-CONSULTA (24h depois)
+ NPS (1-5 estrelas)
        ↓
[NPS 4-5] Link Google Maps
[NPS 1-3] Notificação urgente ao Prometheus
        ↓
[Médico indicou retorno]
Oferta de agendamento de retorno
        ↓
[Paciente quer lembrete]
Cron job para X dias antes da data
```

#### Fluxo de Confirmação em Dupla Etapa

**D-1 (Véspera — Janela Dinâmica):**
- Calcula dinamicamente o melhor momento dentro da janela de 22h ativa
- Se janela aberta → envio gratuito
- Se janela fechada → cascata: Email (SendGrid) → SMS (Zenvia) → Template Meta

**D-0 (08:00h — Varredura Matinal):**
- O Manager navega no Ademed e varre todos os agendamentos do dia sem confirmação
- Para cada um: nova tentativa de contato
- Se responder → janela renovada → segundo lembrete gratuito

**H-4 (4 horas antes):**
- Tentativa final
- Se silêncio → Manager atualiza status "Sem resposta" no Ademed
- Acionamento automático do transbordo humano para a recepcionista

#### Filtro Circadiano

Mensagens **nunca** são enviadas entre 22h e 07h.
Se o vencimento da janela de 22h cair na madrugada:
- O sistema antecipa o envio para o último horário comercial anterior (antes das 22h)
- Garante que o paciente recebe a mensagem em horário adequado

#### Estratégia de Janela Dinâmica (Minimizar Custo Meta)

```python
# Lógica do Agente 4
def calcular_horario_lembrete(janela_fecha, hora_consulta):

    # Aplicar filtro circadiano
    if janela_fecha.hour < 7:
        janela_fecha = dia_anterior_22h()

    # Lembrete 1h antes da janela fechar (dentro da janela = grátis)
    lembrete = janela_fecha - timedelta(hours=1)

    # Garante pelo menos 4h antes da consulta
    if lembrete > hora_consulta - timedelta(hours=4):
        # Envia via cascata paga
        return hora_consulta - timedelta(hours=18), "template_pago"

    return lembrete, "gratuito"
```

#### Dicas de Saúde (Opt-in)

- Perguntado no momento do agendamento pelo Agente 2
- Armazenado no GraphRAG do paciente
- Personalizadas por especialidade da consulta via GraphRAG
- Frequência: 1 a cada 3-4 dias
- **Sempre com pergunta aberta no final** para renovar a janela
- Conteúdo validado por médico antes de ativar em produção
- Opt-out processado imediatamente quando solicitado

#### Pós-Consulta e NPS

- 24h após a consulta: *"Como você está após a consulta com Dr. Carlos?"*
- Pesquisa NPS (1-5 estrelas)
- Nota 4-5 → link automático Google Maps
- Nota 1-3 → notificação urgente ao Prometheus

#### Retorno (Híbrido)

- Se médico indicou retorno: oferece agendamento na mensagem pós-consulta
- Se paciente pedir lembrete: cria cron job para X dias antes
- Se Manager detectar "retorno indicado" no Ademed: aciona cron job automaticamente

#### Aniversários

- Manager extrai datas de nascimento do Ademed periodicamente
- Mensagem humanizada no dia do aniversário
- Abre janela gratuitamente

**Modelo:** DeepSeek-V4 Flash com prompt caching para templates recorrentes.

---

### 5.5 Agente 5 — Sincronizador

**Responsabilidade:** Manter o SOUL.md/contexto do Agente 2 sincronizado com os médicos cadastrados no Ademed.

**Execução:** Cron job a cada 30 minutos.

**Processo (via browser — sem banco):**
1. Navega para tela de profissionais no Ademed via Playwright
2. Extrai lista atual de médicos ativos com especialidades
3. Compara com o contexto atual do Agente 2
4. Se há diferença:
   - Atualiza automaticamente (DeepSeek reformula naturalmente)
   - Reinicia o Agente 2 para carregar as mudanças
   - Notifica Prometheus (informativo, sem pedir permissão)
5. Se não há diferença: aguarda próximo ciclo

**Custo:** Zero quando não há mudança. ~2 chamadas de API apenas quando detecta diferença.

**Versão futura:** Query SQL direta — mais rápido que browser.

**Modelo:** DeepSeek-V4 Flash (somente quando há mudança).

---

## 6. FLUXO DE INTEGRAÇÃO E LATÊNCIA

```
Paciente envia mensagem
        ↓
Evolution Go recebe e dispara webhook
        ↓
Redis Buffer (8 segundos)
Agrupa mensagens fragmentadas em uma requisição
        ↓
OpenClaw recebe mensagem consolidada
        ↓
Paperclip verifica budget do tenant
Consulta Redis para estado da conversa
        ↓
Agente 2 processa com DeepSeek-V4 Flash
Consulta GraphRAG (Neo4j/ChromaDB) para contexto
        ↓
Se precisar de ação no Ademed:
Aciona Agente 3 (Manager) via Playwright
        ↓
Agente 2 formula resposta
        ↓
Evolution Go envia resposta ao paciente
        ↓
Redis atualiza estado da conversa
Paperclip registra consumo de tokens
```

---

## 7. INTEGRAÇÃO COM O ADEMED v2.02

### 7.1 Abordagem MVP

Acesso **exclusivo via browser (Playwright)**. Todas as operações — leitura e escrita — são feitas navegando pelas telas do sistema.

Sem acesso direto ao banco de dados no MVP. Versão futura adiciona leitura via SQLAlchemy.

### 7.2 Processos Implementados

**Fase 1 — Identificação:**
- Busca por número WhatsApp no GraphRAG
- Busca por CPF no Ademed (tela de pesquisa)

**Fase 2 — Cadastro e Agendamento:**
- Cadastro completo com todos os campos: nome, CPF, nascimento, RG, CEP (auto-complete ViaCEP), e-mail, celular, convênio, plano, validade
- Upload de RG e Carteirinha na seção Arquivos do Ademed
- Criação de agendamento na grade de agenda
- Verificação de disponibilidade de horários

**Fase 3 — Atendimento:**
- Localizar agendamento e alterar para ATENDIDO
- Criar Guia de Consulta com todos os campos TISS
- Criar Guia SP/SADT com todos os campos TISS
- Preencher Contratado Executante (Campo 9 / Campo 29)
- Verificação ANS e senha de autorização
- Vínculo automático guia ↔ agendamento

### 7.3 Nota Técnica Crítica

O Ademed v2.02 usa uma mega-page jQuery UI com 2.415 elementos. Todos os formulários são diálogos sobrepostos sem URL própria. O Playwright deve:
- Manter contexto do browser para preservar sessão PHP
- Usar `waitForLoadState("networkidle")` com timeouts de 15-20s
- Processar uma requisição de browser por vez (fila sequencial)
- Detectar e renovar sessão expirada automaticamente

### 7.4 SKILL do Ademed

A skill técnica completa (código Playwright para todos os processos) está documentada em `SKILL-ADMED-AGENTE3.md`. O Agente 3 deve consultar essa skill antes de qualquer operação no Ademed.

---

## 8. BASE DE CONHECIMENTO (GRAPHRAG)

### 8.1 Arquitetura

Cada clínica tem sua própria base vetorial no Neo4j/ChromaDB contendo:
- FAQ específico da clínica (perguntas e respostas reais)
- Informações de médicos, especialidades e horários
- Histórico de atendimento por paciente
- Dicas de saúde validadas por especialidade
- Orientações pré-consulta por procedimento
- Protocolos específicos da clínica

### 8.2 Vantagem sobre FAQ Estático

O GraphRAG permite que o agente encontre respostas por similaridade semântica, não apenas por palavras-chave exatas. Pergunta *"precisa em jejum?"* encontra a resposta de *"é necessário jejum para exame de sangue?"* mesmo com palavras diferentes.

### 8.3 Alimentação do GraphRAG

- **Setup inicial:** Preenchido com dados do Briefing do Cliente (Documento 4)
- **Histórico de pacientes:** Sincronizado automaticamente pelo Agente 3
- **Dicas de saúde:** Adicionadas manualmente após validação médica
- **FAQ:** Atualizado via dashboard do Paperclip pelo gestor

---

## 9. GESTÃO DA JANELA DE 24H (META)

### 9.1 Estratégia Completa

O custo da Meta existe apenas quando **você inicia** a conversa fora da janela de 24h. A estratégia do Kairós mantém a janela sempre aberta para minimizar esse custo.

**Regra 1 — Perguntas abertas em toda mensagem:**
Toda mensagem proativa termina com uma pergunta simples (Sim/Não ou escolha binária). Qualquer resposta do paciente reabre a janela gratuitamente.

**Regra 2 — Filtro Circadiano:**
Nunca enviar entre 22h-07h. Se o vencimento cair na madrugada, antecipa para antes das 22h do dia anterior.

**Regra 3 — Janela dinâmica:**
Calcular o melhor momento para enviar dentro da janela disponível em vez de horários fixos.

**Regra 4 — Dicas de saúde como renovação:**
Para agendamentos com muita antecedência, enviar dica de saúde 1-2 dias antes de mensagem importante para abrir/renovar a janela.

**Regra 5 — Cascata de fallback quando janela fechada:**
Email (SendGrid) → SMS (Zenvia) → Template Meta (pago)

### 9.2 Estimativa de Custo Meta

| Estratégia | Custo/mês (100 pac/dia) |
|---|---|
| Sem otimização | R$ 900 |
| Com janela dinâmica + perguntas abertas | R$ 50-80 |
| Com dicas de saúde opt-in | R$ 15-30 |

---

## 10. BROADCAST INTELIGENTE

### 10.1 Fluxo

O gestor fala com o Prometheus (texto ou áudio):
*"Avisa os pacientes de Cardiologia que o Dr. Carlos abriu novos horários"*

**Prometheus:**
1. Valida regras da Meta automaticamente (template aprovado? limite diário? janela disponível?)
2. Consulta Agente 3: lista segmentada de pacientes de Cardiologia
3. Registra contexto da campanha no Redis (expira em 48h)
4. Aciona Agente 2 para disparar individualmente
5. Reporta: entregues, responderam, agendamentos gerados

**Pacientes que respondem:** Agente 2 atende contextualizado com a oferta específica.

### 10.2 Opt-out

Resposta com "PARAR", "Não quero mais", "Me tire da lista" → Agente 2 processa, Agente 3 atualiza no Ademed, Agente 4 registra no GraphRAG. Nunca mais recebe broadcast.

---

## 11. SEGURANÇA E LGPD

### 11.1 Dados Sensíveis

- **Imagens de documentos:** Processadas pelo Gemini Vision e descartadas do VPS imediatamente após upload confirmado no Ademed. Nunca armazenadas além do necessário.
- **Dados de saúde:** Tratados como categoria especial pela LGPD. Nunca logados.
- **CPF nos logs:** Sempre mascarado (123.***.***-00).
- **Credenciais:** Sempre em variáveis de ambiente, nunca em código.

### 11.2 Isolamento Multi-Tenant

- Cada clínica tem credenciais próprias isoladas
- Dados de uma clínica nunca acessíveis por outra
- Logs segregados por tenant no Paperclip
- Budget de tokens independente por clínica

### 11.3 Transbordo Humano

Gatilhos automáticos para transferência ao humano:
- Paciente solicita explicitamente
- 2 tentativas do bot sem resolver
- 3 mensagens fora do escopo em sequência
- NPS 1-3 estrelas (Prometheus notificado)
- Erro crítico no sistema

### 11.4 LGPD — Conformidade

- Consentimento explícito: obrigatório antes de ir para produção
- Termo de Processamento de Dados (DPA): assinado com cada clínica
- Opt-out de comunicações: processado imediatamente
- Retenção de dados: conforme política de cada clínica
- Responsável pelos dados: definido no briefing do cliente
- **ATENÇÃO:** Sistema não deve ser liberado para pacientes reais sem LGPD implementada

---

## 12. PROCESSO DE ONBOARDING DO CLIENTE

### 12.1 Dados Coletados Antes do Desenvolvimento

Para personalizar o sistema de cada clínica:

**Seção 1 — Identidade da Clínica:** Nome fantasia, razão social, CNPJ, endereço, telefone, site, redes sociais (Instagram, Facebook, TikTok, LinkedIn — para futuras integrações)

**Seção 2 — Identidade do Agente:** Nome do assistente virtual, tom (formal/informal), forma de tratamento, palavras a usar/evitar, diferencial da clínica

**Seção 3 — Equipe Médica:** Lista de médicos com especialidade, CRM, dias e horários de atendimento

**Seção 4 — Convênios e Valores:** Lista completa de convênios aceitos, planos por convênio, valores de consulta particular por especialidade

**Seção 5 — Funcionamento:** Horários, tempo médio por consulta, política de cancelamento, documentos exigidos, estacionamento, como chegar

**Seção 6 — Fluxo de Atendimento:** WhatsApp da recepcionista responsável, quem recebe handoffs, horário de atendimento humano

**Seção 7 — Base de Conhecimento:** FAQ específico (mínimo 15 perguntas reais), orientações pré-consulta por especialidade, dicas de saúde por especialidade (validadas por médico)

**Seção 8 — Google Maps:** Link do perfil para NPS positivo

**Seção 9 — Redes Sociais:** Perfis para futuras integrações

### 12.2 Credenciais Técnicas (Antes da Produção)

Coletadas via formulário criptografado seguro (Bitwarden Send ou equivalente):
- Número WhatsApp Business (conectado ao Evolution Go)
- Login e senha do Ademed (usuário dedicado)
- Chave API do modelo de IA (DeepSeek/Gemini)
- Chave API Google TTS
- Chave API SendGrid + e-mail verificado
- Token Zenvia + número remetente
- Telefone da recepcionista para fallback

### 12.3 Processo de Treinamento

**Dia 1:** Videochamada de 1h — tour pelo Paperclip e Prometheus, como monitorar atendimentos, como fazer broadcast, como interpretar relatórios

**Dias 2-15:** Acompanhamento prioritário — suporte via WhatsApp, check-in nos dias 3, 7 e 15

**Após dia 15:** Suporte padrão em horário comercial

---

## 13. SLA (SERVICE LEVEL AGREEMENT)

| Métrica | Compromisso |
|---|---|
| Uptime do sistema | 99% (~7h de downtime/mês) |
| Tempo de resposta do bot | < 5 segundos em condições normais |
| Incidentes críticos | Resposta em 2h em horário comercial |
| Backup | Diário, retenção de 30 dias |
| Restauração após disaster | < 3 horas |
| Suporte | WhatsApp direto, horário comercial |
| Atualizações | Comunicadas 24h antes, fora do horário de pico |
| Cancelamento | 30 dias de aviso. Dados exportados em 15 dias. |

---

## 14. DISASTER RECOVERY

### 14.1 Meta: Sistema restaurado em menos de 3 horas

### 14.2 O Que É Salvo no GitHub

- Configurações de todos os agentes (SOUL.md/contextos)
- Código da Bridge/integração
- Scripts de deploy, rollback e testes
- Versão do sistema (VERSION.md)
- Documentação técnica

### 14.3 O Que Não É Salvo no GitHub

- Variáveis de ambiente e credenciais (armazenadas offline)
- Logs de conversas
- Dados de pacientes

### 14.4 Processo de Restauração

1. Provisionar novo VPS Hostinger KVM 2 (15 min)
2. Clonar repositório GitHub (5 min)
3. Restaurar `.env` do documento de emergência offline (10 min)
4. Rodar `./scripts/install.sh` (30 min)
5. Reconectar instâncias Evolution Go (QR Code) (20 min)
6. Executar smoke tests (10 min)
7. Validar funcionamento com mensagem de teste (10 min)

### 14.5 Acesso de Emergência

Se WhatsApp pessoal for perdido (acesso ao Prometheus):
- Acesso via SSH com chave de emergência offline
- Dashboard do Paperclip via Tailscale

---

## 15. VERSIONAMENTO

### 15.1 Convenção

```
v MAJOR.MINOR.PATCH

MAJOR → mudança grande de arquitetura
MINOR → nova funcionalidade
PATCH → correção ou ajuste pequeno
```

### 15.2 Processo de Atualização

1. Antigravity gera arquivos atualizados
2. Atualiza `VERSION.md`
3. Commit no GitHub
4. Smoke tests locais
5. Deploy no VPS: `./scripts/deploy.sh`
6. Smoke tests no VPS
7. Se falhar: `./scripts/rollback.sh`

---

## 16. TESTES

### 16.1 Smoke Tests (2 minutos — antes de qualquer deploy)

- Ping LLMs (DeepSeek, Gemini)
- Login no Ademed via Playwright
- Status dos 5 agentes no OpenClaw
- Ping Evolution Go /health
- Ping Redis
- Ping Paperclip

### 16.2 Testes de Fluxo (10 minutos — antes de produção)

- Paciente recorrente: identificação + histórico via Ademed
- Paciente novo: OCR + cadastro + upload
- Agendamento completo: verifica disponibilidade + confirma no Ademed
- Buffer 8 segundos: mensagens fragmentadas consolidadas
- Timeout 30 minutos: encerramento correto
- Fallback Ademed fora do ar: fila pendente + notificação
- Fallback LLM: cascata BYOK + mensagem automática
- Handoff: escala para recepcionista corretamente
- Guia de consulta: criação + vínculo ao agendamento
- NPS positivo: link Google Maps enviado automaticamente

---

## 17. ESTIMATIVA DE CUSTO OPERACIONAL

*Por clínica, volume de 100 atendimentos/dia*

| Item | Custo Mensal |
|---|---|
| VPS Hostinger KVM 2 | R$ 50,00 |
| DeepSeek-V4 Flash (chat) | R$ 40,00 |
| Gemini 3.1 Flash (OCR/áudio) | R$ 30,00 |
| Gemini 3.1 Pro (Prometheus) | R$ 20,00 |
| Meta Cloud API (com otimização) | R$ 50,00 |
| Evolution Go | R$ 0,00 (open source) |
| SendGrid (email fallback) | R$ 0,00 (gratuito até 100/dia) |
| SMS Zenvia (fallback) | R$ 20,00 |
| Google TTS (voz Prometheus) | R$ 0,00 (gratuito até 1M chars) |
| Domínio/SSL | R$ 3,50 |
| **TOTAL** | **~R$ 213/mês** |

> Comparativo: Custo original (antes das otimizações) era ~R$1.263/mês.
> Redução de **83%** mantendo todas as funcionalidades.

### 17.1 Precificação Sugerida

| Plano | Perfil | Preço/mês | Margem |
|---|---|---|---|
| Starter | Clínica pequena, até 50 atend/dia | R$ 800 | ~73% |
| Pro | Clínica média, até 150 atend/dia | R$ 1.500 | ~86% |
| Enterprise | Clínica grande, multi-médico | R$ 2.500 | ~91% |
| Setup único | Implementação e onboarding | R$ 2.000 | ~100% |

---

## 18. PLANO DE ROLLOUT

| Fase | Descrição | Entregável |
|---|---|---|
| Fase 1 | VPS Hostinger + rede Docker + Tailscale + SSL | Infraestrutura ativa |
| Fase 2 | Evolution Go + instâncias WhatsApp por clínica | Canal WhatsApp funcionando |
| Fase 3 | OpenClaw + 5 agentes + SKILL Ademed | Agentes criados e testados |
| Fase 4 | Paperclip + governança multi-tenant | Control Plane ativo |
| Fase 5 | GraphRAG + base de conhecimento | Conhecimento da clínica carregado |
| Fase 6 | Redis + buffer + debounce | Performance otimizada |
| Fase 7 | Testes completos de latência e transbordo | Sistema validado |
| Fase 8 | LGPD + consentimento + DPA | Conformidade legal |
| Fase 9 | Go-live com pacientes reais | Produção |

---

## 19. ROADMAP — VERSÕES FUTURAS

| Funcionalidade | Versão |
|---|---|
| LGPD — consentimento completo | v1.1 |
| Leitura direta do banco Ademed (SQLAlchemy) | v1.2 |
| Integração Instagram DM | v2.0 |
| Integração Facebook Messenger | v2.0 |
| Múltiplas unidades por clínica | v2.0 |
| Dashboard visual web (além do Paperclip) | v2.0 |
| Regras de cancelamento configuráveis por clínica | v1.1 |
| Integração veterinária (Agropet) | v1.5 |
| App mobile para gestor | v3.0 |

---

## 20. ARQUIVOS DO PROJETO

### 20.1 Documentação

| Arquivo | Descrição |
|---|---|
| `PRD-Kairos-Intelligence.md` | Este documento |
| `DOC2-MANUAL-SISTEMA.md` | Manual para o gestor leigo |
| `DOC3-GUIA-INSTALACAO.md` | Instalação técnica passo a passo |
| `DOC4-BRIEFING-CLIENTE.md` | Formulário de onboarding da clínica |
| `DOC5-PROMPT-ANTIGRAVITY.md` | Briefing para o agente construir o sistema |
| `SKILL-ADMED-AGENTE3.md` | Código Playwright para operação do Ademed |
| `PLANO-IMPLEMENTACAO.md` | Cronograma de implementação |
| `SIMULACAO-PROCESSO.md` | Simulação visual de todos os fluxos |

### 20.2 Arquivos Gerados pelo Antigravity

```
kairos-intelligence/
├── README.md
├── VERSION.md
├── .env.example
├── docker-compose.yml          ← todos os 8 serviços
├── docker-compose.override.yml ← overrides de dev
├── nginx/
│   └── nginx.conf
├── agents/
│   ├── prometheus/
│   │   ├── SOUL.md
│   │   └── MEMORY.md
│   ├── front-desk/
│   │   ├── SOUL.md
│   │   └── MEMORY.md
│   ├── manager/
│   │   ├── SOUL.md
│   │   ├── MEMORY.md
│   │   └── skills/
│   │       └── admed/SKILL.md
│   ├── notifications/
│   │   ├── SOUL.md
│   │   └── MEMORY.md
│   └── synchronizer/
│       └── SOUL.md
├── openclaw.json
├── scripts/
│   ├── deploy.sh
│   ├── rollback.sh
│   ├── smoke-test.sh
│   ├── test-fluxos.py
│   ├── run-tests.sh
│   ├── install.sh
│   └── backup.sh
└── logs/
    └── .gitkeep
```

---

*PRD Kairós Intelligence v2.7 — 01/05/2026*
*Proprietário: Stênio Alves de Souza Maia*
*Status: Pronto para Desenvolvimento*
