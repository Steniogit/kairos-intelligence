> **Kairós Intelligence v2.7.1** | Stack: Evolution Go · OpenClaw · DeepSeek-V4 Flash · Gemini 3.1 · Redis · Crawl4AI · Playwright · Google TTS Journey
> Atualizado em 13/05/2026 — Revisão: modelo unificado, agents/*, sem Bridge FastAPI.

> **Nota de Revisão v2.7.1 (13/05/2026):**
> - Prometheus e Front-Desk unificados para DeepSeek-V4 Flash
> - Removido prefixo `anthropic/` dos modelos (usar `deepseek/`)
> - Estrutura `workspace-*` → `agents/[nome]/`
> - Bridge FastAPI removida (Evolution Go já faz tudo)
> - Adicionado MAP.md em cada agente

# PROMPT PARA O GOOGLE ANTIGRAVITY
## Briefing Completo — Kairós Intelligence v2.7

---

> **INSTRUÇÕES DE USO**
>
> Cole este prompt no painel Agent Manager do Antigravity/Codex.
> Use o modo **Agent-Assisted Development**.
>
> ⚠️ **REGRA HUMAN-IN-THE-LOOP (OBRIGATÓRIA):**
> O Prometheus (e o Antigravity ao construir o sistema) DEVE apresentar
> cada ação planejada e aguardar aprovação explícita ("Y" ou "sim") antes
> de executar QUALQUER comando no servidor, criar arquivo ou modificar
> configuração. Nunca executar em modo automático sem confirmação.
>
> Após a geração, use o Guia de Instalação (Documento 3) para o deploy no VPS.

---

## PROMPT PRINCIPAL

```
Você vai construir um sistema completo de atendimento automatizado via WhatsApp
para clínicas médicas, baseado em múltiplos agentes de IA orquestrados pelo OpenClaw.

Leia TODO este briefing antes de escrever qualquer código. Entenda a arquitetura
completa primeiro. Só então comece a gerar os arquivos na ordem especificada.

Peça minha aprovação antes de executar qualquer comando ou criar qualquer arquivo.
Explique o que vai fazer antes de fazer.

=============================================================
PARTE 1 — VISÃO GERAL DO SISTEMA
=============================================================

NOME DO SISTEMA: Kairós Intelligence v2.7
LINGUAGEM: Python 3.11+ e Go
PLATAFORMA DE AGENTES: OpenClaw
GOVERNANÇA MULTI-TENANT: Paperclip
CANAL DE COMUNICAÇÃO: Evolution Go (evolutionapi/evolution-go:latest)
CACHE E BUFFER: Redis 7
BANCO DE GOVERNANÇA: PostgreSQL 15
BASE DE CONHECIMENTO: Neo4j 5 + ChromaDB (GraphRAG por clínica)
SEGUNDO CÉREBRO: GitHub kairos-brain (prompts e skills versionados)
MODELO CHAT/EXTRAÇÃO: DeepSeek-V4 Flash
MODELO VISÃO/OCR/ÁUDIO/TTS: Gemini 3.1 Flash
MODELO COMPLEXO (Prometheus): DeepSeek-V4 Flash
VOZ PREMIUM: Google Cloud TTS Journey
MODELO FALLBACK: GPT-4o Mini (cascata BYOK)
LEITURA ERP: Crawl4AI (80% mais rápido)
ESCRITA ERP: Playwright (garante JavaScript do Ademed)

REGRA HUMAN-IN-THE-LOOP (NUNCA VIOLAR):
Antes de executar QUALQUER comando no servidor, criar arquivo ou
modificar configuração, o sistema DEVE:
1. Apresentar exatamente o que vai fazer e por quê
2. Aguardar aprovação explícita do gestor: "Y", "sim", "pode", "ok"
3. Só então executar
Se o gestor responder "N", "não", "cancela" → abortar completamente.
Esta regra se aplica ao Antigravity durante a construção E ao
Prometheus em produção quando executar ações no servidor.

O SISTEMA TEM 5 AGENTES E RODA EM DOCKER:

SERVIÇOS DOCKER (mesma rede bridge kairos-net):
- Evolution Go: gateway WhatsApp (evolutionapi/evolution-go:latest)
- OpenClaw: framework de agentes (openclaw/openclaw:latest)
- Paperclip: governança multi-tenant (paperclipai/paperclip:latest)
- Redis 7: cache, buffer 8s, filas (redis:7-alpine)
- PostgreSQL 15: dados de governança (postgres:15-alpine)
- Neo4j 5: GraphRAG base de conhecimento (neo4j:5-community)
- ChromaDB: vetores de embedding (chromadb/chroma:latest)
- MinIO: armazenamento de mídia (minio/minio:latest)

Gerar docker-compose.yml completo com todos esses serviços
na mesma rede bridge interna kairos-net.
Comunicação entre containers por hostname (sem latência externa).

OS 5 AGENTES:

1. PROMETHEUS — Assistente pessoal do gestor (ex-Master)
2. FRONT-DESK — Recepcionista virtual para pacientes (ex-Atendimento)
3. MANAGER — Arquitetura Híbrida: Crawl4AI (leitura) + Playwright (escrita) no Ademed
4. NOTIFICAÇÕES — Comunicação proativa ao longo do ciclo do paciente
5. SINCRONIZADOR — Mantém SOUL.md sincronizado via Crawl4AI no Ademed

INSTRUÇÃO PARA CRIAR ESTRUTURA MAP.md:
Em cada diretório de agente, criar um arquivo MAP.md com:
- O que é este agente/componente (2-3 linhas)
- Lista de arquivos e seus propósitos
- Dependências (quem depende de quem)
- Regras críticas
- Histórico de mudanças relevantes

Esta MAP.md serve como bússola de contexto — qualquer IA ou
desenvolvedor que abrir este diretório deve conseguir entender
o componente lendo apenas o MAP.md.

=============================================================
PARTE 2 — AGENTE 1: MASTER
=============================================================

SOUL.md do Prometheus deve conter:

IDENTIDADE:
- Nome: Assistente Prometheus
- É o sócio digital do gestor
- Nunca expõe ao paciente — uso exclusivo do gestor

CAPACIDADES:
- Multimodal: texto, voz (Gemini Audio), imagem (Gemini Vision), vídeo (extrai áudio), PDF, Excel, Word
- Resposta em voz via Google TTS quando solicitado
- Interface com Agentes 2, 3, 4 e 5
- Dashboard por linguagem natural
- Executa ações no sistema via Manager (Agente 3)
- Orquestra broadcasts com validação automática regras Meta
- Monitora saúde de todos os agentes continuamente
- Alerta de agenda vazia com sugestão de broadcast segmentado
- Monitora custo de API (alerta se >20% acima do estimado)
- Monitoramento em 3 níveis: Urgente (imediato), Aviso (relatório diário), Insight (semanal)

RELATÓRIOS AUTOMÁTICOS:
- Diário às 8h: agendamentos, confirmados, sem resposta, cancelamentos, NPS médio, destaque
- Semanal toda segunda às 8h: tendências, comparativos, gargalos, sugestões
- Mensal dia 1 às 8h: consolidado, comparativo, sugestões estratégicas

FALLBACK LLM (3 camadas):
1. Detecta falha → notifica gestor imediatamente
2. Mensagem automática pré-definida para pacientes (sem depender de IA)
3. Após 15 min: tenta GPT-4o Mini (cascata BYOK)

MODELO: DeepSeek-V4 Flash (sempre — sem downgrade)

=============================================================
PARTE 3 — AGENTE 2: ATENDIMENTO
=============================================================

SOUL.md do Atendimento deve conter:

IDENTIDADE:
- Nome: [PLACEHOLDER: definido pelo cliente no briefing]
- Tom: humanizado, natural, nunca finge ser humano
- Idioma: Português do Brasil com contrações naturais
- Emojis: com moderação

IDENTIFICAÇÃO HÍBRIDA DO PACIENTE:
1. Consulta banco pelo número de WhatsApp
2. Se encontrar → confirma só o nome: "Olá! Você é [nome]?"
3. Se não encontrar → pede CPF
4. Se CPF não encontrar → fluxo de paciente novo

FLUXO PACIENTE NOVO:
1. Consentimento LGPD [PLACEHOLDER: implementar antes da produção]
2. Solicita foto do documento (RG ou CNH)
3. Gemini Vision extrai: nome, CPF, data de nascimento, número do documento
4. Valida qualidade da imagem antes de processar
5. Pergunta: convênio ou particular?
6. Se convênio: solicita foto da carteirinha
7. Gemini Vision extrai: convênio, número da carteira, validade, plano
8. Manager (Agente 3) valida convênio no banco em tempo real
9. Se aceito: confirma dados com paciente
10. Se não aceito: informa e oferece particular com valor
11. Manager (Agente 3) cadastra no sistema via browser
12. REGRA CRÍTICA: após extrair dados de qualquer imagem, descarte IMEDIATAMENTE.
    Nunca armazene, nunca logue, nunca referencie em contextos futuros.

AGENDAMENTO:
- Paciente sugere médico e horário preferido
- Manager (Agente 3) verifica disponibilidade no banco
- Se disponível: confirma
- Se não disponível: busca e negocia alternativas até encontrar horário que sirva
- Manager (Agente 3) confirma no sistema via browser
- Mensagem de confirmação completa para o paciente
- Notificações (Agente 4) notifica recepcionista

MENSAGEM DE CONFIRMAÇÃO (template):
"✅ Consulta agendada com sucesso!
👤 Paciente: [nome]
📅 Data: [data]
🕙 Horário: [hora]
👨‍⚕️ Médico: [nome do médico]
🏥 Especialidade: [especialidade]
💳 Convênio: [convênio ou Particular]
📍 Endereço: [PLACEHOLDER]
📋 Documentos necessários: [PLACEHOLDER]
⚠️ Chegue 15 minutos antes.
Qualquer dúvida, é só chamar! 😊"

MÚLTIPLOS AGENDAMENTOS:
Quando paciente tem mais de um agendamento ativo, lista todos e pergunta sobre qual está falando antes de qualquer ação.

CANCELAMENTO:
Direto no sistema via Manager (Agente 3), sem aprovação do gestor.

REAGENDAMENTO:
Máximo 2 vezes. Na 3ª tentativa → escala para recepcionista com histórico completo.

TIMEOUT:
30 minutos sem resposta → encerra com mensagem amigável, limpa contexto.

MENSAGENS FORA DO ESCOPO:
Redireciona com variação natural (nunca repete a mesma frase).
Após 3 tentativas fora do escopo → escala para recepcionista.

HANDOFF HUMANO:
Tenta responder uma vez. Se não conseguir → escala com contexto completo da conversa.

BROADCAST COMO ENTRADA:
Consulta contexto no MEMORY.md ao receber resposta de broadcast ativo.
Contexto expira em 48h.

BOT 24/7: sem restrição de horário.

MODELO: DeepSeek-V4 Flash (unificado)
- 100% das mensagens de chat → DeepSeek-V4 Flash
- Imagens e áudio → Gemini 3.1 Flash
- Prompt Caching: ativo para o SOUL.md

=============================================================
PARTE 4 — AGENTE 3: MANAGER (CLÍNICO) — ARQUITETURA HÍBRIDA
=============================================================

SOUL.md do Manager deve conter:

RESPONSABILIDADE:
Único ponto de contato com o sistema ADMED da clínica.
Serviço compartilhado entre Agentes 2 e 4.
NENHUM outro agente acessa o sistema.

ARQUITETURA HÍBRIDA v2.7:
- LEITURA → Crawl4AI (80% mais rápido que Playwright puro)
- ESCRITA → Playwright (garante execução correta do JavaScript do ADMED)
- SESSÃO COMPARTILHADA via cookie PHPSESSID
  * Playwright SEMPRE inicia a sessão (login)
  * Crawl4AI reutiliza o PHPSESSID existente
  * NUNCA criar sessão paralela no ADMED

OPERAÇÕES DE LEITURA (Crawl4AI):
- Buscar paciente por CPF (tela de pesquisa ADMED)
- Consultar histórico e agendamentos ativos
- Verificar horários disponíveis na agenda
- Validar convênios aceitos
- Extrair lista de médicos ativos (para Sincronizador)
- Extrair agendamentos do dia (para Notificações)

OPERAÇÕES DE ESCRITA (Playwright):
- Cadastrar paciente novo (formulário ADMED)
- Upload de documentos (RG e Carteirinha) — salvar no sistema
- Criar agendamento
- Cancelar e reagendar
- Atualizar status (sem resposta, atendido)
- Criar Guia de Consulta e Guia SP/SADT
- Preencher Contratado Executante (Campo 9/29)
- Verificação ANS (senha de autorização)

REFERÊNCIA: Usar KAIROS-SKILL-ADMED-v2.7.md como guia técnico completo.
Copiar INTEGRALMENTE como agents/manager/skills/admed/SKILL.md.

LOG DE AÇÕES (OBRIGATÓRIO):
Toda ação executada deve ser registrada em: ~/logs/agente3-actions.log
Formato JSON: timestamp, operacao, identificador (CPF mascarado), resultado, detalhe
Retenção: 90 dias
Nunca incluir dados de saúde no log — apenas ações e IDs.

FILA DE EXECUÇÃO:
Processar UMA requisição de browser por vez (fila sequencial).
Sem paralelismo — o ADMED não suporta múltiplas sessões simultâneas.

SEGURANÇA — IMAGENS DE DOCUMENTOS:
Após fazer upload de RG e Carteirinha no ADMED:
- Deletar o arquivo local imediatamente
- Nunca armazenar em disco além do necessário para o upload
- Nunca logar conteúdo das imagens

FALLBACK (ADMED fora do ar):
1. Salva dados do paciente em ~/logs/agendamentos-pendentes.json
2. Notifica recepcionista com todos os dados para processamento manual
3. Informa Front-Desk (Agente 2) para avisar paciente sobre instabilidade

CREDENCIAIS:
- Login e senha do ADMED isolados no workspace do Manager (Agente 3)
- Carregadas de variáveis de ambiente SISTEMA_URL, SISTEMA_USER, SISTEMA_PASS
- Nunca escritas em código

VERSÃO FUTURA:
Quando volume justificar, adicionar leitura via SQLAlchemy.
Escrita continuará sempre via browser.

MODELO: DeepSeek-V4 Flash

=============================================================
PARTE 5 — AGENTE 4: NOTIFICAÇÕES
=============================================================

SOUL.md do Agente de Notificações deve conter:

CICLO COMPLETO DO PACIENTE (ordem cronológica):

1. DICAS DE SAÚDE (opt-in):
   - Apenas para quem aceitou receber
   - Frequência: 1 a cada 3-4 dias
   - Personalizadas por especialidade e histórico
   - Sempre com pergunta aberta no final para renovar janela
   - Conteúdo vem da base de conhecimento do briefing

2. ORIENTAÇÕES PRÉ-CONSULTA:
   - Enviadas junto com o lembrete de confirmação
   - Específicas por especialidade (jejum, documentos, preparo)
   - Vêm do briefing do cliente

3. LEMBRETE DE CONFIRMAÇÃO (dinâmico):
   - ESTRATÉGIA DE JANELA DINÂMICA:
     * Monitora janela de 24h de cada paciente continuamente
     * Calcula o melhor momento para enviar dentro da janela ativa
     * Se janela aberta: envia gratuitamente
     * Se janela fechada: cascata Email (SendGrid) → SMS (Zenvia) → Template Meta
   - Mensagem inclui pergunta aberta no final para renovar janela

4. SEGUNDO LEMBRETE (se sem resposta):
   - Enviado 4h antes da consulta
   - Dentro da nova janela (aberta pela resposta ao primeiro lembrete)
   - Se janela fechada: cascata de fallback

5. SEM RESPOSTA (1h antes):
   - Manager (Agente 3) atualiza status no sistema: "Sem resposta"
   - Notifica recepcionista com detalhes da consulta

6. NOTIFICAÇÃO DE AGENDAMENTO (para recepcionista):
   - Após cada agendamento confirmado
   - Contém: nome do paciente, data, hora, médico, convênio, WhatsApp do paciente

7. PÓS-CONSULTA (24h após):
   - "Como você está após a consulta com [médico]?"
   - Pergunta simples com resposta fácil

8. PESQUISA NPS (junto com pós-consulta):
   - Avaliação de 1 a 5 estrelas
   - Se 4-5 estrelas: envia link do Google Maps automaticamente
   - Se 1-3 estrelas: notificação URGENTE para o Prometheus

9. RETORNO (híbrido):
   - Se médico indicou retorno: oferece agendamento na mensagem pós-consulta
   - Se Sincronizador (Agente 5) detectar "retorno indicado" no banco: aciona cron job para X dias antes
   - Se paciente pedir lembrete: cria cron job na data solicitada

10. ANIVERSÁRIO:
    - Monitora datas de nascimento no banco
    - Manda mensagem humanizada no dia do aniversário
    - Abre janela gratuitamente

BROADCAST (funcionalidade do Front-Desk (Agente 2), cron jobs gerenciados pelo Notificações (Agente 4)):
- Notificações (Agente 4) gerencia os cron jobs de follow-up de campanhas ativas

FALLBACK CASCATA (quando janela fechada):
1. Email via SendGrid com link direto para WhatsApp (grátis)
2. SMS via Zenvia com link direto para WhatsApp (~R$0,09)
3. Template Meta apenas se email e SMS falharem (~R$0,20)

OPT-IN DE DICAS:
- Perguntado no momento do agendamento pelo Front-Desk (Agente 2)
- Registrado no banco via Manager (Agente 3)
- Opt-out processado imediatamente quando solicitado

MODELO: DeepSeek-V4 Flash com Prompt Caching para templates recorrentes.

=============================================================
PARTE 6 — AGENTE 5: SINCRONIZADOR
=============================================================

SOUL.md do Sincronizador deve conter:

EXECUÇÃO: Cron job a cada 30 minutos.

PROCESSO (via browser — sem banco de dados):
1. Navega para tela de profissionais no ADMED via Playwright
2. Extrai lista atual de médicos ativos com especialidades
3. Lê seção de médicos do SOUL.md do Front-Desk (Agente 2)
4. Compara os dois
5. Se há diferença:
   a. Atualiza SOUL.md automaticamente (DeepSeek reformula naturalmente)
   b. Reinicia o Front-Desk (Agente 2)
   c. Notifica Prometheus (informativo, sem pedir permissão)
6. Se não há diferença: aguarda próximo ciclo

REFERÊNCIA: Usar função extrair_lista_medicos() da SKILL-ADMED-AGENTE3.md

CUSTO: Zero quando não há mudança. ~2 chamadas de API apenas quando detecta diferença.

VERSÃO FUTURA: Substituir navegação browser por query SQL direta — mais rápido.

MODELO: DeepSeek-V4 Flash (somente quando há mudança).

=============================================================
PARTE 7 — OPENCLAW.JSON
=============================================================

Gere o arquivo openclaw.json completo com:

agents:
  - id: prometheus
    workspace: ~/agents/prometheus
    model: deepseek/deepseek-chat
    channels:
      whatsapp:
        allowFrom: ["[PLACEHOLDER: número do gestor]"]

  - id: front-desk
    workspace: ~/agents/front-desk
    model: deepseek/deepseek-chat
    channels:
      whatsapp:
        allowFrom: ["*"]

  - id: manager
    workspace: ~/agents/manager
    model: internal
    internal_only: true

  - id: notifications
    workspace: ~/agents/notifications
    model: internal
    internal_only: true

  - id: synchronizer
    workspace: ~/agents/synchronizer
    model: internal
    internal_only: true

fallback:
  models:
    - deepseek/deepseek-chat
    - openai/gpt-4o-mini

cron jobs a incluir:
  - Backup Diário: todo dia às 4:30
  - Relatório Diário: todo dia às 8:00
  - Relatório Semanal: toda segunda às 8:00
  - Relatório Mensal: todo dia 1 às 8:00
  - Sincronizador: a cada 30 minutos

=============================================================
PARTE 8 — REMOVIDA (Bridge FastAPI)
=============================================================

NOTA: A Bridge FastAPI foi REMOVIDA na v2.7.1.
O Evolution Go já possui integração direta com webhooks da Meta
e API REST completa. Não é necessário um intermediário.

=============================================================
PARTE 9 — SKILLS DO OPENCLAW
=============================================================

Gere os seguintes arquivos SKILL.md:

SKILL 1: Google TTS (síntese de voz)
Localização: workspace-master/skills/google-tts/SKILL.md
Funcionalidade:
- Converte texto em áudio usando Google Cloud TTS
- Idioma: pt-BR, voz feminina natural
- Salva arquivo .mp3 temporário
- Envia via WhatsApp como mensagem de voz
- Deleta o arquivo após envio

SKILL 2: Gemini Audio Transcription (transcrição de áudio)
Localização: workspace-master/skills/whisper/SKILL.md
Funcionalidade:
- Recebe arquivo .ogg do WhatsApp
- Chama API Gemini Audio da OpenAI
- Retorna texto transcrito
- Usado automaticamente quando gestor envia áudio

SKILL 3: ADMED Browser Operations (operações no sistema ADMED)
Localização: workspace-clinico/skills/admed/SKILL.md
Conteúdo: COPIAR INTEGRALMENTE o arquivo SKILL-ADMED-AGENTE3.md fornecido.
Este arquivo já contém o código Playwright completo para todos os processos.
NÃO reescrever — copiar como está.

SKILL 4: Regras Meta API (validação de broadcast)
Localização: workspace-master/skills/meta-regras/SKILL.md
Conteúdo: resumo das principais regras da Meta WhatsApp Business API:
- Janela de 24h: livre para responder, pago para iniciar
- Templates: categorias utilidade e marketing e seus custos
- Rate limit: 1.000/dia conta nova, sobe gradualmente
- Opt-out: obrigatório processar imediatamente
- Conteúdo proibido
- Como verificar limite atual pelo Prometheus

SKILL 5: SendGrid Email (fallback)
Localização: workspace-notificacoes/skills/sendgrid/SKILL.md
Funcionalidade:
- Envia email com link direto para WhatsApp
- Template HTML responsivo
- Assunto: "Confirmação de consulta — [nome da clínica]"
- Corpo: dados da consulta + botão "Confirmar pelo WhatsApp"

SKILL 6: Zenvia SMS (fallback)
Localização: workspace-notificacoes/skills/zenvia/SKILL.md
Funcionalidade:
- Envia SMS com link encurtado para WhatsApp
- Texto máximo de 160 caracteres
- Formato: "Olá [nome]! Sua consulta é [data]. Confirme: [link]"

=============================================================
PARTE 10 — SCRIPTS
=============================================================

SCRIPT 1: scripts/deploy.sh
Faz o deploy completo:
- Copia todos os arquivos para os lugares certos
- Configura variáveis de ambiente
- Instala skills
- Configura cron jobs
- Inicia serviços
- Roda smoke tests
- Exibe resultado final

SCRIPT 2: scripts/rollback.sh
Reverte para a versão anterior:
- Identifica último commit anterior no GitHub
- Baixa os arquivos da versão anterior
- Substitui os arquivos atuais
- Reinicia os agentes
- Roda smoke tests
- Exibe resultado

SCRIPT 3: scripts/smoke-test.sh
Testa se todos os serviços estão funcionando:
- Ping Claude API
- Ping Evolution Go /health
- Login no ADMED via browser (testa acesso ao sistema)
- Status dos 5 agentes
- Ping webhook Meta
- Exibe resultado com ✅ ou ❌ para cada item

SCRIPT 4: scripts/test-fluxos.py
Testa os fluxos principais:
- test_paciente_recorrente()
- test_paciente_novo()
- test_agendamento_completo()
- test_timeout_conversa()
- test_fallback_sistema()
- test_fallback_claude_api()
- test_handoff_recepcionista()
Usa números de teste da Meta (não envia para pacientes reais)

SCRIPT 5: scripts/run-tests.sh
Roda todos os testes em sequência:
- smoke-test.sh
- test-fluxos.py
- Exibe relatório consolidado

SCRIPT 6: scripts/install.sh
Instalação completa do zero (usado no Disaster Recovery):
- Instala dependências (Node.js, Python, Docker)
- Instala OpenClaw
- Cria estrutura de diretórios
- Configura variáveis de ambiente
- Clona o repositório
- Executa deploy.sh
- Exibe resultado

SCRIPT 7: scripts/backup.sh
Backup diário:
- Verifica se há segredos nos arquivos (API keys, senhas)
- Substitui segredos por placeholders
- Faz commit e push para o GitHub privado
- Mantém últimos 30 backups
- Remove backups antigos

SCRIPT 8: scripts/test-db-connection.py
Testa a conexão com o banco de dados:
- Tenta conectar com as credenciais do .env
- Lista as tabelas encontradas
- Faz uma query de teste em cada tabela esperada
- Exibe resultado

=============================================================
PARTE 11 — ARQUIVOS DE DOCUMENTAÇÃO
=============================================================

ARQUIVO: VERSION.md
```
# Versão do Sistema

## v1.0.0 — [data de hoje]
Lançamento inicial
- 5 agentes configurados e operacionais
- WhatsApp Business API conectada
- Fluxo completo de agendamento
- Notificações com estratégia de janela dinâmica
- Sistema de backup e monitoramento ativo
```

ARQUIVO: README.md
Documentação técnica resumida:
- Visão geral do sistema
- Estrutura de diretórios
- Como fazer deploy
- Como executar testes
- Como fazer rollback
- Contato do suporte

ARQUIVO: .env.example
Template com TODAS as variáveis de ambiente necessárias, sem os valores reais.
Cada variável deve ter um comentário explicando para que serve.

=============================================================
PARTE 12 — ORDEM DE CONSTRUÇÃO
=============================================================

Construa os arquivos NESTA ORDEM EXATA. Peça minha aprovação após cada grupo:

GRUPO 1 — Estrutura base:
1. .env.example
2. VERSION.md
3. README.md

GRUPO 2 — Configuração OpenClaw:
4. openclaw.json
5. workspace-master/SOUL.md
6. workspace-master/MEMORY.md
7. workspace-atendimento/SOUL.md
8. workspace-atendimento/MEMORY.md
9. workspace-clinico/SOUL.md
10. workspace-clinico/MEMORY.md
11. workspace-notificacoes/SOUL.md
12. workspace-notificacoes/MEMORY.md
13. workspace-sincronizador/SOUL.md

GRUPO 3 — Skills:
14. workspace-master/skills/google-tts/SKILL.md
15. workspace-master/skills/whisper/SKILL.md
16. workspace-clinico/skills/admed/SKILL.md (copiar SKILL-ADMED-AGENTE3.md)
17. workspace-master/skills/meta-regras/SKILL.md
18. workspace-notificacoes/skills/sendgrid/SKILL.md
19. workspace-notificacoes/skills/zenvia/SKILL.md

GRUPO 4 — Evolution Go:
20. bridge/main.py
21. bridge/requirements.txt
22. bridge/Dockerfile
23. bridge/docker-compose.yml

GRUPO 5 — Scripts:
24. scripts/deploy.sh
25. scripts/rollback.sh
26. scripts/smoke-test.sh
27. scripts/test-fluxos.py
28. scripts/run-tests.sh
29. scripts/install.sh
30. scripts/backup.sh

=============================================================
PARTE 13 — PLACEHOLDERS E REGRAS GERAIS
=============================================================

PLACEHOLDERS (deixe marcados claramente no código):
- [PLACEHOLDER: nome do assistente virtual] — vem do briefing do cliente
- [PLACEHOLDER: número do gestor] — número WhatsApp pessoal com DDD e código do país
- [PLACEHOLDER: número da recepcionista] — idem
- [PLACEHOLDER: endereço da clínica] — vem do briefing
- [PLACEHOLDER: telefone de emergência] — vem do briefing
- [PLACEHOLDER: link Google Maps] — vem do briefing
- [PLACEHOLDER: especialidades e médicos] — vem do briefing
- [PLACEHOLDER: convênios aceitos] — vem do briefing
- [PLACEHOLDER: FAQ da clínica] — vem do briefing
- [PLACEHOLDER: dicas de saúde por especialidade] — vem do briefing (validadas por médico)
- [PLACEHOLDER: orientações pré-consulta] — vem do briefing

REGRAS GERAIS DE CODIFICAÇÃO:
1. Nunca escrever credenciais no código — sempre usar variáveis de ambiente
2. Sempre usar queries parametrizadas no banco (sem SQL injection)
3. Sempre tratar erros com try/catch e logar em ~/logs/
4. Imagens de documentos: processar e descartar imediatamente após extração
5. Logs do Manager (Agente 3): sem dados de saúde, apenas ações executadas
6. Comentários em português do Brasil em todos os arquivos
7. Cada arquivo deve ter um cabeçalho explicando sua função
8. Scripts shell: sempre com `set -e` para parar em caso de erro

SEGURANÇA:
- Nenhum agente compartilha credenciais com outro
- Manager (Agente 3): acesso restrito ao banco com usuário de permissões mínimas
- Gateway OpenClaw: apenas localhost e Tailscale
- Imagens: descarte imediato após uso

=============================================================
PARTE 14 — ESTRUTURA DE DIRETÓRIOS FINAL
=============================================================

Ao terminar, a estrutura deve ser:

projeto/
├── README.md
├── VERSION.md
├── .env.example
├── openclaw.json
├── bridge/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
├── workspace-master/
│   ├── SOUL.md
│   ├── MEMORY.md
│   └── skills/
│       ├── google-tts/SKILL.md
│       ├── whisper/SKILL.md
│       └── meta-regras/SKILL.md
├── workspace-atendimento/
│   ├── SOUL.md
│   └── MEMORY.md
├── workspace-clinico/
│   ├── SOUL.md
│   ├── MEMORY.md
│   └── skills/
│       └── banco-dados/SKILL.md
├── workspace-notificacoes/
│   ├── SOUL.md
│   ├── MEMORY.md
│   └── skills/
│       ├── sendgrid/SKILL.md
│       └── zenvia/SKILL.md
├── workspace-sincronizador/
│   └── SOUL.md
└── scripts/
    ├── deploy.sh
    ├── rollback.sh
    ├── smoke-test.sh
    ├── test-fluxos.py
    ├── run-tests.sh
    ├── install.sh
    ├── backup.sh
    └── test-db-connection.py

=============================================================
PARTE 15 — VERIFICAÇÃO FINAL
=============================================================

Após gerar todos os arquivos, execute a verificação final:

1. Confirme que todos os 31 arquivos foram gerados
2. Confirme que nenhum arquivo tem credenciais reais (apenas placeholders)
3. Confirme que todos os scripts têm permissão de execução (chmod +x)
4. Confirme que o .env.example tem TODAS as variáveis necessárias
5. Confirme que os SOUL.md de todos os agentes têm os placeholders claramente marcados
6. Execute: ~/scripts/smoke-test.sh (após o deploy no VPS)
7. Exiba um relatório final com: arquivos gerados, placeholders pendentes, próximos passos

=============================================================
PODE COMEÇAR.

Lembre-se: peça minha aprovação antes de cada grupo de arquivos.
Explique o que vai fazer antes de fazer.
Se tiver dúvidas sobre algum comportamento, pergunte antes de implementar.
```

---

## CHECKLIST PÓS-GERAÇÃO

Após o Antigravity/Codex terminar, verifique:

☐ 31 arquivos gerados na estrutura correta
☐ Nenhuma credencial real nos arquivos (só placeholders)
☐ Todos os scripts com chmod +x
☐ .env.example completo com todas as variáveis
☐ Todos os SOUL.md com placeholders claramente marcados
☐ Evolution Go testada localmente
☐ Smoke tests passando no VPS após deploy

---

## PRÓXIMOS PASSOS APÓS A GERAÇÃO

1. Revisar cada arquivo gerado
2. Preencher os placeholders com os dados do briefing do cliente
3. Seguir o Guia de Instalação (Documento 3) para o deploy
4. Executar os testes de fluxo completos
5. Implementar o consentimento LGPD antes de ir ao ar
6. Treinar o gestor conforme o Manual do Sistema (Documento 2)

---

*Prompt do Antigravity/Codex v1.0 — Abril 2026*
*Kairós Intelligence para Clínicas*
