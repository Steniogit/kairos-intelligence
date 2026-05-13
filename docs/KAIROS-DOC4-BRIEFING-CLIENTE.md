> **Kairós Intelligence v2.7** | Stack: Evolution Go · OpenClaw · Paperclip · DeepSeek-V4 Flash · Gemini 3.1 · Redis · GraphRAG · Crawl4AI · Google TTS Journey
> Atualizado em 04/05/2026 — Arquitetura Híbrida + Segundo Cérebro + Voz Journey.

# BRIEFING DE ONBOARDING — KAIRÓS INTELLIGENCE
## Formulário de Coleta de Informações v2.7
**Para ser preenchido pela clínica antes do início do projeto**

---

> **COMO USAR ESTE DOCUMENTO**
>
> Este briefing está dividido em **duas partes**:
>
> **PARTE 1 — Informações do Negócio** (preencher antes do desenvolvimento)
> São as informações que definem como o sistema vai funcionar para a sua clínica.
> Quanto mais detalhes você fornecer, mais inteligente e preciso será o seu assistente.
>
> **PARTE 2 — Credenciais Técnicas** (preencher antes de ir ao ar)
> São os acessos técnicos necessários para conectar o sistema ao seu WhatsApp,
> banco de dados e outros serviços.
>
> ⚠️ **IMPORTANTE:** Nunca envie senhas ou tokens por e-mail ou WhatsApp.
> As credenciais da Parte 2 serão coletadas por meio de um formulário
> criptografado seguro que será enviado separadamente.

---

# PARTE 1 — INFORMAÇÕES DO NEGÓCIO

---

## SEÇÃO 1 — IDENTIDADE DA CLÍNICA

**Nome fantasia da clínica:**
_____________________________________________

**Razão social:**
_____________________________________________

**CNPJ:**
_____________________________________________

**Endereço completo** (logradouro, número, complemento, bairro, cidade, CEP):
_____________________________________________
_____________________________________________

**Telefone fixo ou celular da recepção** (para emergências e fallback):
_____________________________________________

**Site da clínica** (se houver):
_____________________________________________

**E-mail de contato da clínica:**
_____________________________________________

---

## SEÇÃO 2 — REDES SOCIAIS E REPOSITÓRIO

*Estas informações serão usadas para planejar futuras integrações do sistema com suas redes sociais e para configurar o Segundo Cérebro no GitHub.*

| Rede Social | @ / Nome da Página | Link | Nível de Atividade |
|---|---|---|---|
| Instagram | | | ☐ Ativa ☐ Pouca ☐ Não tem |
| Facebook | | | ☐ Ativa ☐ Pouca ☐ Não tem |
| TikTok | | | ☐ Ativa ☐ Pouca ☐ Não tem |
| YouTube | | | ☐ Ativa ☐ Pouca ☐ Não tem |
| LinkedIn | | | ☐ Ativa ☐ Pouca ☐ Não tem |
| Outra: | | | ☐ Ativa ☐ Pouca ☐ Não tem |

**URL do repositório GitHub (kairos-brain) desta clínica:**
_____________________________________________

*(O repositório armazena todos os prompts, skills e configurações dos agentes desta clínica — o "Segundo Cérebro". Será criado pela equipe técnica durante o onboarding e compartilhado aqui para referência.)*

---

## SEÇÃO 3 — IDENTIDADE DO ASSISTENTE VIRTUAL

**Nome do assistente virtual** (como o bot vai se apresentar para os pacientes. Ex: Ana, Sofia, Carlos):
_____________________________________________

**Gênero do assistente:**
☐ Feminino  ☐ Masculino  ☐ Neutro

**Tom de comunicação com os pacientes:**
☐ Formal (senhor/senhora)
☐ Semi-formal (você, profissional mas acessível)
☐ Informal (você, descontraído, próximo)

**Como deve tratar os pacientes?**
☐ Pelo primeiro nome (ex: "Olá, João!")
☐ Por senhor/senhora (ex: "Olá, Sr. João!")
☐ Apenas "você" sem nome

**Palavras ou expressões que o assistente DEVE usar com frequência:**
_____________________________________________
_____________________________________________

**Palavras ou expressões que o assistente NUNCA deve usar:**
_____________________________________________
_____________________________________________

**Emojis:** ☐ Usar com moderação  ☐ Usar bastante  ☐ Não usar

**Qual é o principal diferencial da clínica que o assistente deve destacar naturalmente?**
_____________________________________________
_____________________________________________

**Existe alguma situação que frequentemente gera conflito ou reclamação de pacientes?**
(Ex: demora no atendimento, dificuldade para remarcar, etc.)
_____________________________________________
_____________________________________________

---

### Configuração de Voz (Google Cloud TTS Journey)

*O sistema usa o motor Journey — o mais natural do Google para português brasileiro — para responder em áudio quando o paciente ou gestor enviar mensagens de voz.*

**Preferência de voz Journey:**
☐ **Journey F** — Voz feminina, tom acolhedor (recomendado para clínicas médicas)
☐ **Journey M** — Voz masculina, tom profissional
☐ Sem preferência (padrão: Journey F)

**Velocidade de fala preferida:**
☐ Normal (padrão)
☐ Levemente mais lenta (recomendado para clínicas com pacientes idosos)
☐ Levemente mais rápida

**Tom geral da voz:**
☐ Caloroso e acolhedor
☐ Profissional e objetivo
☐ Neutro (padrão)

**O assistente deve responder em áudio somente quando o paciente mandar áudio?**
☐ Sim, apenas se o paciente mandar áudio (padrão)
☐ Sempre em texto, independente da entrada
☐ Sempre em áudio, independente da entrada

---

## SEÇÃO 4 — EQUIPE MÉDICA

*Preencha uma linha por médico. Adicione mais linhas conforme necessário.*

| Nome completo | Especialidade | CRM | Dias de atendimento | Horário | Convênios individuais (se diferente da clínica) |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |

**Existe algum médico que não deve ter agendamentos via bot sem autorização prévia?**
☐ Não  ☐ Sim — Qual(is)? _____________________________________________

---

## SEÇÃO 5 — CONVÊNIOS E VALORES

**A clínica aceita convênios?**
☐ Sim  ☐ Não  ☐ Apenas alguns médicos aceitam

**Liste todos os convênios aceitos pela clínica:**

| Convênio | Planos aceitos | Planos NÃO aceitos |
|---|---|---|
| | | |
| | | |
| | | |
| | | |
| | | |
| | | |
| | | |
| | | |

**Valor da consulta particular por especialidade:**

| Especialidade | Valor (R$) |
|---|---|
| | |
| | |
| | |
| | |
| | |

**A clínica aceita pagamento de quais formas?**
☐ PIX  ☐ Cartão de crédito  ☐ Cartão de débito  ☐ Dinheiro  ☐ Outro: _______

---

## SEÇÃO 6 — FUNCIONAMENTO DA CLÍNICA

**Horário de funcionamento:**

| Dia | Abre | Fecha | Funciona? |
|---|---|---|---|
| Segunda-feira | | | ☐ Sim ☐ Não |
| Terça-feira | | | ☐ Sim ☐ Não |
| Quarta-feira | | | ☐ Sim ☐ Não |
| Quinta-feira | | | ☐ Sim ☐ Não |
| Sexta-feira | | | ☐ Sim ☐ Não |
| Sábado | | | ☐ Sim ☐ Não |
| Domingo | | | ☐ Sim ☐ Não |
| Feriados | | | ☐ Sim ☐ Não |

**Tempo médio de duração de consulta por especialidade:**

| Especialidade | Duração (minutos) |
|---|---|
| | |
| | |
| | |

**A clínica tem estacionamento?**
☐ Sim, gratuito  ☐ Sim, pago  ☐ Não  ☐ Tem nas proximidades — onde? _________

**Como chegar de transporte público?**
_____________________________________________

**Referências de localização** (pontos de referência próximos):
_____________________________________________

**Documentos obrigatórios na PRIMEIRA consulta:**
☐ RG ou CNH  ☐ Carteirinha do convênio  ☐ Pedido médico  ☐ Outro: _________

**Documentos obrigatórios no RETORNO:**
_____________________________________________

**Política de cancelamento** (quantas horas de antecedência? Tem multa?):
_____________________________________________

**Política de reagendamento:**
_____________________________________________

**O que acontece se o paciente chegar sem consulta marcada?**
_____________________________________________

**Como a clínica trata urgências/emergências?**
_____________________________________________

**A clínica faz retorno? Em quais condições?**
_____________________________________________

---

## SEÇÃO 7 — FLUXO DE ATENDIMENTO E EQUIPE

**Nome e WhatsApp da recepcionista responsável** (receberá notificações de agendamentos e handoffs):
Nome: _____________________________________________
WhatsApp: _____________________________________________

**Existe mais de uma recepcionista?**
☐ Não  ☐ Sim — todas devem receber notificações? ☐ Sim ☐ Não (só a responsável)

**Qual o horário de atendimento da recepção humana?**
_____________________________________________

**Fora do horário da recepção, o bot deve:**
☐ Continuar agendando normalmente
☐ Informar que a confirmação virá no próximo dia útil
☐ Outro: _____________________________________________

**Existe algum procedimento que o bot NUNCA deve agendar sem aprovação humana?**
☐ Não  ☐ Sim — Qual(is)? _____________________________________________

**Nome do responsável pelo tratamento de dados (LGPD):**
_____________________________________________

**E-mail do responsável pelos dados (LGPD):**
_____________________________________________

---

## SEÇÃO 8 — BASE DE CONHECIMENTO

*Esta é a seção mais importante do briefing.*
*Quanto mais detalhes você fornecer, mais inteligente e preciso será seu assistente.*
*Reserve pelo menos 30 minutos para preencher esta seção com calma.*

---

### 8A — FAQ UNIVERSAL (já incluído no sistema)

*Estas perguntas já vêm pré-configuradas. Informe as respostas específicas da sua clínica:*

**"Como faço para agendar uma consulta?"**
_____________________________________________

**"Posso cancelar ou remarcar pelo WhatsApp?"**
_____________________________________________

**"Quanto tempo antes devo chegar?"**
_____________________________________________

**"Como funciona o atendimento por convênio?"**
_____________________________________________

**"E se eu precisar de atendimento urgente?"**
_____________________________________________

**"Vocês fazem retorno? Como funciona?"**
_____________________________________________

**"Quais documentos devo trazer?"**
_____________________________________________

**"Como funciona a lista de espera?"**
_____________________________________________

---

### 8B — FAQ ESPECÍFICO DA CLÍNICA

*Liste aqui as perguntas que chegam todo dia na sua recepção.*
*Use as palavras exatas que seus pacientes usam.*
*Mínimo de 15 perguntas e respostas.*

| Pergunta (como o paciente pergunta) | Resposta (como a clínica responde) |
|---|---|
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |
| | |

---

### 8C — DICAS DE SAÚDE POR ESPECIALIDADE

*O sistema enviará dicas de saúde personalizadas para pacientes que optarem por recebê-las.*
*⚠️ OBRIGATÓRIO: Todo o conteúdo desta seção deve ser revisado e aprovado*
*por um médico da clínica antes de ser ativado.*

*Para cada especialidade, forneça pelo menos 5 dicas de saúde relevantes:*

**Especialidade: ___________________________**

Dica 1: _____________________________________________
Dica 2: _____________________________________________
Dica 3: _____________________________________________
Dica 4: _____________________________________________
Dica 5: _____________________________________________

**Especialidade: ___________________________**

Dica 1: _____________________________________________
Dica 2: _____________________________________________
Dica 3: _____________________________________________
Dica 4: _____________________________________________
Dica 5: _____________________________________________

**Especialidade: ___________________________**

Dica 1: _____________________________________________
Dica 2: _____________________________________________
Dica 3: _____________________________________________
Dica 4: _____________________________________________
Dica 5: _____________________________________________

---

### 8D — ORIENTAÇÕES PRÉ-CONSULTA POR ESPECIALIDADE

*O sistema enviará orientações específicas junto com o lembrete de confirmação.*
*Exemplos: jejum, documentos específicos, preparo especial.*

| Especialidade | Orientações pré-consulta |
|---|---|
| | |
| | |
| | |
| | |
| | |

---

### 8E — SITUAÇÕES ESPECIAIS

**A clínica tem alguma especialidade com fila de espera longa?**
☐ Não  ☐ Sim — Qual? _____________ Tempo médio de espera: _____________

**Existe alguma informação sensível que o bot NUNCA deve mencionar?**
(Ex: valores de procedimentos específicos, situações administrativas internas)
_____________________________________________

**Existe algum médico que os pacientes frequentemente perguntam mas que não atende mais?**
_____________________________________________

**Mensagem de boas-vindas personalizada** (o que a clínica quer dizer no primeiro contato):
_____________________________________________
_____________________________________________

**Mensagem de encerramento** (quando a conversa é concluída com sucesso):
_____________________________________________

**Mensagem de fallback** (quando o sistema estiver temporariamente indisponível):
_____________________________________________

---

## SEÇÃO 9 — LINK DO GOOGLE MAPS

*Usado para enviar automaticamente aos pacientes que derem nota alta no NPS.*

**Link do perfil da clínica no Google Maps:**
_____________________________________________

*(Para encontrar: acesse seu perfil no Google, clique em "Peça avaliações" e copie o link)*

---

# PARTE 2 — CREDENCIAIS TÉCNICAS

*⚠️ Esta parte deve ser preenchida APENAS no formulário criptografado seguro.*
*Nunca envie estas informações por e-mail, WhatsApp ou qualquer outro canal não criptografado.*
*O formulário seguro será enviado separadamente antes da fase de produção.*

---

*A seguir está a lista do que será solicitado no formulário seguro, para você se preparar:*

### O Que Será Solicitado

**WhatsApp Business API (Meta):**
- Número de telefone do WhatsApp Business (com DDD e código do país: +55...)
- Phone Number ID (obtido no Meta for Developers)
- WhatsApp Business Account ID
- Token de acesso permanente

**Banco de Dados da Clínica:**
- Tipo de banco (MySQL, PostgreSQL, SQL Server, Firebird, outro)
- Host do banco de dados (endereço IP ou hostname)
- Porta
- Nome do banco de dados
- Usuário dedicado para o sistema (a ser criado antes da produção)
- Senha do usuário dedicado
- Estrutura básica das tabelas de agenda, médicos, pacientes e convênios

**Sistema de Agendamento (acesso browser):**
- URL de acesso ao sistema
- Login e senha de um usuário dedicado para o sistema
  *(recomendamos criar um usuário específico com permissões limitadas)*

**Claude API (Anthropic):**
- Chave de API (API Key)

**Google TTS:**
- Chave de API do Google Cloud

**SendGrid (e-mail de fallback):**
- Chave de API
- E-mail remetente verificado

**Zenvia (SMS de fallback):**
- Token de API
- Número remetente

**OpenAI (fallback de emergência — opcional):**
- Chave de API

---

# TERMOS DE SERVIÇO BÁSICOS (SLA)

Ao contratar o sistema, a clínica concorda com os seguintes termos:

**Uptime garantido:** 99% de disponibilidade mensal (~7h de manutenção/mês permitidas)

**Incidentes críticos:** Resposta em até 2 horas em horário comercial (segunda a sexta, 8h às 18h, horário de Brasília)

**Backup:** Diário, com retenção de 30 dias

**Tempo de resposta do bot:** Menos de 10 segundos em condições normais de operação

**Suporte:** Via WhatsApp direto com a equipe técnica

**Atualizações:** Comunicadas com no mínimo 24h de antecedência, realizadas preferencialmente fora do horário de pico (após as 22h)

**LGPD:** A clínica é responsável pelo tratamento de dados de seus pacientes. O sistema é um processador de dados. O contrato de processamento de dados (DPA) será assinado separadamente antes da produção.

**Cancelamento:** Aviso prévio de 30 dias. Dados exportados e entregues à clínica em até 15 dias após o cancelamento.

---

# CHECKLIST DE ENTREGA

*A ser preenchido pela equipe técnica antes de liberar o sistema:*

☐ SOUL.md de todos os agentes configurado com dados da clínica
☐ Base de conhecimento (FAQ) carregada e testada
☐ Dicas de saúde aprovadas por médico e configuradas
☐ Orientações pré-consulta configuradas por especialidade
☐ WhatsApp Business conectado e testado
☐ Banco de dados conectado e queries testadas
☐ Browser (sistema da clínica) testado com usuário dedicado
☐ Evolution Go rodando e webhook verificado
☐ Todos os 5 agentes operacionais
☐ Smoke tests passando
☐ Testes de fluxo completos realizados
☐ Recepcionista treinada no dashboard
☐ Gestor treinado no Prometheus (Agente Prometheus)
☐ UptimeRobot configurado
☐ Backup automático configurado e testado
☐ LGPD: consentimento implementado *(obrigatório antes de produção)*
☐ Termo de processamento de dados (DPA) assinado

---

*Briefing v1.0 — Kairós Intelligence para Clínicas*
*Abril 2026*
