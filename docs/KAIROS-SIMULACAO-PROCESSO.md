> **Kairós Intelligence v2.7** | Stack: Evolution Go · OpenClaw · Paperclip · DeepSeek-V4 Flash · Gemini 3.1 · Redis · GraphRAG · Crawl4AI · Google TTS Journey
> Atualizado em 04/05/2026 — Arquitetura Híbrida + Resposta Multimodal Condicional.

# SIMULAÇÃO DO PROCESSO COMPLETO
## Kairós Intelligence v2.7
**Do primeiro contato do paciente até o pós-atendimento**

---

> **COMO LER ESTE DOCUMENTO**
>
> 📱 = Mensagem no WhatsApp do paciente
> 🤖 = Ação do Front-Desk (Agente 2) (Atendimento)
> 🔧 = Ação do Manager (Agente 3) (Clínico) — invisível para o paciente
> 📋 = Ação do Notificações (Agente 4) (Notificações)
> 👑 = Ação do Prometheus (Agente Prometheus) (Prometheus) — visível só para o gestor
> 🔄 = Ação do Sincronizador (Agente 5) (Sincronizador) — roda em background
> 👩‍💼 = Recepcionista humana
> 👨‍💼 = Gestor (você)

---

# CENÁRIO A — PACIENTE RECORRENTE AGENDANDO CONSULTA

---

## ETAPA 1 — PRIMEIRO CONTATO E IDENTIFICAÇÃO

```
📱 Paciente (João Silva):
"Oi, boa tarde! Queria marcar uma consulta"

🤖 Front-Desk (Agente 2):
"Olá! Boa tarde 😊 Sou a Ana, assistente virtual
da Clínica Clínica [PLACEHOLDER]. Fico feliz em te ajudar!

Para eu te identificar no sistema, pode me
informar seu CPF?"

📱 Paciente:
"123.456.789-00"

🔧 Manager (Agente 3):
[Consulta banco de dados via SQL]
SELECT * FROM pacientes WHERE cpf_pac = '123.456.789-00'
→ ENCONTROU: João Silva, Cardiologia habitual,
  Dr. Carlos Mendes, Unimed Plano Essencial

🤖 Front-Desk (Agente 2):
"Encontrei seu cadastro 😊
Você é o João Silva, correto?"

📱 Paciente:
"Sim, isso mesmo!"

🔧 Manager (Agente 3):
[Puxa histórico completo]
- Última consulta: 15/03/2026 — Cardiologia — Dr. Carlos
- Agendamentos ativos: nenhum
- Retorno indicado: sim, em 45 dias (vence em 29/04/2026)
- Convênio: Unimed — Plano Essencial — válido até 12/2026
```

---

## ETAPA 2 — AGENDAMENTO

```
🤖 Front-Desk (Agente 2):
"Perfeito, João! Vi que sua última consulta foi
com o Dr. Carlos Mendes em Cardiologia.

Quer agendar um retorno com ele, ou prefere
outro médico ou especialidade?"

📱 Paciente:
"Quero marcar com o Dr. Carlos mesmo.
Pode ser quinta-feira de manhã?"

🔧 Manager (Agente 3):
[Consulta banco de dados]
SELECT hora_agenda FROM agenda
WHERE id_profissional = [id_dr_carlos]
AND data_agenda = '24/04/2026'
AND situacao NOT IN ('MARCADO','ATENDIDO','BLOQUEADO')
→ Horários disponíveis: 08:00, 09:00, 11:00

🤖 Front-Desk (Agente 2):
"Na quinta-feira com o Dr. Carlos temos
disponível:

🕗 08:00
🕘 09:00
🕚 11:00

Qual prefere?"

📱 Paciente:
"09:00 está ótimo!"

🤖 Front-Desk (Agente 2):
"Perfeito! Posso confirmar:

📅 Quinta-feira, 24/04/2026
🕘 09:00
👨‍⚕️ Dr. Carlos Mendes — Cardiologia
💳 Unimed — Plano Essencial

Confirma? ✅ SIM ❌ NÃO"

📱 Paciente:
"✅ SIM"

🔧 Manager (Agente 3):
[Abre browser — Playwright]
1. Login no ADMED (se sessão expirada)
2. Navega para listaAgenda.php
3. Clica em célula 09:00 da agenda do Dr. Carlos
4. Preenche formulário:
   - Paciente: João Silva (busca por CPF)
   - Data: 24/04/2026
   - Hora: 09:00
   - Convênio: Unimed
   - Situação: MARCADO
5. Clica em Gravar
6. Captura número do agendamento: #12847
→ LOG: [2026-04-22 14:35:01] AGENDAMENTO 123.***.***.00 sucesso agendamento: 12847

🤖 Front-Desk (Agente 2):
"✅ Consulta agendada com sucesso!

👤 Paciente: João Silva
📅 Data: 24/04/2026 (quinta-feira)
🕘 Horário: 09:00
👨‍⚕️ Médico: Dr. Carlos Mendes
🏥 Especialidade: Cardiologia
💳 Convênio: Unimed — Plano Essencial

📍 Endereço: [endereço da clínica]
📋 Documentos: Carteirinha do convênio e RG
⚠️ Chegue 15 minutos antes.

Antes de finalizar — você gostaria de receber
dicas de saúde relacionadas à Cardiologia
enquanto aguarda a consulta?

💚 Sim, quero receber!
🚫 Não, obrigado"

📱 Paciente:
"💚 Sim, quero receber!"

🔧 Manager (Agente 3):
[Atualiza banco]
UPDATE pacientes SET recebe_dicas = 1
WHERE cpf_pac = '123.456.789-00'

📋 Notificações (Agente 4):
[Registra cron jobs para este agendamento]
- Dicas de saúde: a cada 3-4 dias (opt-in ativo)
- Lembrete: calcular janela dinâmica
- Orientações pré-consulta: 23/04 às 18:00 (1 dia antes)
- Pós-consulta: 25/04 às 09:00 (24h após)
- NPS: junto com pós-consulta

👩‍💼 Notificação para recepcionista (WhatsApp):
"📋 Novo agendamento para revisão:
👤 João Silva
📅 24/04/2026 às 09:00
👨‍⚕️ Dr. Carlos Mendes — Cardiologia
💳 Unimed — Plano Essencial
📱 (61) 99999-9999
Agendamento #12847 ✅"
```

---

## ETAPA 3 — DICAS DE SAÚDE (OPT-IN ATIVO)

```
[3 dias depois — 22/04 às 10:00]

📋 Notificações (Agente 4):
[Verifica janela de 24h]
→ Janela aberta (João respondeu ontem) → envio GRATUITO

📱 Paciente recebe:
"João, você sabia que monitorar a pressão
arterial em casa pode ajudar muito no
acompanhamento cardiológico? 🫀

O ideal é medir sempre no mesmo horário,
com 5 minutos de repouso antes.

Essa dica foi útil?
👍 Sim!   👎 Já sabia"

📱 Paciente:
"👍 Sim!"

📋 Notificações (Agente 4):
[Registra resposta — janela renovada por mais 24h]
[Agenda próxima dica para 26/04]
```

---

## ETAPA 4 — ORIENTAÇÕES PRÉ-CONSULTA E LEMBRETE

```
[23/04 às 16:00 — 18h antes da consulta]

📋 Notificações (Agente 4):
[Calcula janela dinâmica]
→ Última resposta: 22/04 às 10:30
→ Janela fecha: 23/04 às 10:30
→ Janela FECHADA — usa cascata de fallback

[Cascata de fallback]
1. Verifica se tem e-mail → sim: joao@email.com
2. Envia e-mail via SendGrid:
   "Sua consulta é amanhã! Confirme presença →
   [botão que abre WhatsApp]"

📱 João clica no link do e-mail → abre WhatsApp:
"Confirmar consulta amanhã"
→ João envia a mensagem → JANELA ABERTA ✅

🤖 Front-Desk (Agente 2):
[Processa mensagem de confirmação]
"João! Sua consulta é amanhã 😊

📅 24/04/2026 às 09:00
👨‍⚕️ Dr. Carlos Mendes — Cardiologia

⚠️ Orientações para sua consulta:
• Traga carteirinha do convênio e RG
• Traga exames anteriores se tiver
• Jejum não é necessário para esta consulta
• Chegue 15 minutos antes

Você confirma presença?
✅ SIM — Confirmo!
❌ NÃO — Preciso remarcar"

📱 Paciente:
"✅ SIM — Confirmo!"

🔧 Manager (Agente 3):
[Atualiza banco — status confirmado]
UPDATE agenda SET conf = 'SIM'
WHERE id_agenda = 12847

📋 Notificações (Agente 4):
[Janela aberta pela confirmação — agenda 2º lembrete gratuito]
[Cron: 24/04 às 05:00 — lembrete de 4h antes]
```

---

## ETAPA 5 — DIA DA CONSULTA

```
[24/04 às 05:00 — 4h antes]

📋 Notificações (Agente 4):
[Janela aberta — envio GRATUITO]

📱 Paciente recebe:
"Bom dia, João! 🌅
Sua consulta com o Dr. Carlos é hoje às 09:00.

Tudo confirmado? Qualquer dúvida é só chamar! 😊"

📱 Paciente:
"Bom dia! Confirmado, obrigado!"

[09:00 — Paciente chega na clínica]

👩‍💼 Recepcionista:
Localiza agendamento #12847 no ADMED

[O Manager (Agente 3) pode ser acionado pelo Prometheus
para realizar as etapas de atendimento:]

🔧 Manager (Agente 3) (acionado via Prometheus):
[Abre browser — Playwright]
1. Localiza agendamento #12847
2. Altera #situacao → ATENDIDO
3. Clica em botão "Fatura"
4. Preenche Guia de Consulta:
   - Tipo: CONSULTA
   - Convênio: Unimed
   - Matrícula: 0012345678
   - Tipo Atendimento: 04-Consulta
   - Tipo Consulta: Segmento (retorno)
   - Regime: Ambulatorial
   - Caráter: Eletiva
5. Seleciona Profissional Executante: Dr. Carlos Mendes
6. Seleciona Empresa Executante: Clínica [PLACEHOLDER] (Contratado Executante)
   → Campo 9 da Guia Consulta preenchido ✅
7. Preenche procedimento (código TUSS)
8. Clica em Gravar Fatura
9. Guia #G-2847 criada e vinculada ao agendamento ✅
→ LOG: [2026-04-24 09:15:22] CRIAR_GUIA 12847 sucesso guia: G-2847

👑 Prometheus notifica gestor:
"✅ Guia G-2847 criada
Paciente: João Silva
Agendamento #12847 — Dr. Carlos
Tipo: Guia Consulta (Segmento)
Contratado Executante: Clínica [PLACEHOLDER] ✅"
```

---

## ETAPA 6 — PÓS-CONSULTA E NPS

```
[25/04 às 09:00 — 24h após a consulta]

📋 Notificações (Agente 4):
[Janela verificada — usa e-mail se fechada, senão envia direto]

📱 Paciente recebe:
"Olá, João! Passando para saber como você
está após a consulta com o Dr. Carlos ontem 😊

Ficou alguma dúvida sobre as orientações médicas?
👍 Estou bem, obrigado!
❓ Tenho uma dúvida"

📱 Paciente:
"👍 Estou bem, obrigado!"

📋 Notificações (Agente 4):
[Dispara NPS]

📱 Paciente recebe:
"Que ótimo! 🎉
Como você avalia o atendimento na Clínica [PLACEHOLDER]?

⭐ 1   ⭐⭐ 2   ⭐⭐⭐ 3   ⭐⭐⭐⭐ 4   ⭐⭐⭐⭐⭐ 5"

📱 Paciente:
"⭐⭐⭐⭐⭐ 5"

📋 Notificações (Agente 4):
[Nota 5 → envia link Google Maps automaticamente]

📱 Paciente recebe:
"Muito obrigado pelo feedback, João! 🙏
Se quiser compartilhar sua experiência,
sua avaliação faz muita diferença para
outras pessoas encontrarem nossa clínica:

⭐ Avaliar no Google: [link]"

👑 Prometheus registra NPS:
NPS do dia: 5.0 ⭐ (1 avaliação)
→ Entra no relatório diário de amanhã

[Dr. Carlos indicou retorno em 30 dias]

📋 Notificações (Agente 4):
"João, o Dr. Carlos recomendou um retorno
em aproximadamente 30 dias.

Quer que eu já deixe agendado para você?
📅 Sim, pode agendar!
⏰ Me lembra mais perto da data"

📱 Paciente:
"⏰ Me lembra mais perto da data"

📋 Notificações (Agente 4):
[Cria cron job: 20/05/2026 — lembrete de retorno]
```

---

# CENÁRIO B — PACIENTE NOVO

---

## ETAPA 1 — IDENTIFICAÇÃO E CONSENTIMENTO

```
📱 Paciente (Maria Souza — nova):
"Olá! Quero marcar uma consulta"

🤖 Front-Desk (Agente 2):
"Olá! Seja bem-vinda 😊 Sou a Ana, assistente
virtual da Clínica Clínica [PLACEHOLDER]!

Para começar, preciso do seu CPF."

📱 Maria:
"456.789.123-00"

🔧 Manager (Agente 3):
[Consulta banco]
→ NÃO ENCONTRADO

🤖 Front-Desk (Agente 2):
"Não encontrei seu cadastro em nosso sistema.
Vamos fazer seu cadastro agora mesmo — é rápido!

[PLACEHOLDER: Termo de consentimento LGPD]
Você concorda com nossa política de privacidade?
✅ SIM — concordo
❌ NÃO — não concordo"

📱 Maria:
"✅ SIM"
```

---

## ETAPA 2 — COLETA DE DOCUMENTOS

```
🤖 Front-Desk (Agente 2):
"Ótimo! Para agilizar seu cadastro, por favor
envie uma foto do seu documento de identificação
(RG ou CNH) 📸"

📱 Maria envia foto do RG

🔧 Manager (Agente 3):
[Gemini Vision processa a imagem]
Extrai:
- Nome: Maria Aparecida Souza
- CPF: 456.789.123-00
- Data nascimento: 22/07/1990
- RG: 9876543
- Órgão expedidor: SSP-DF
→ Imagem descartada imediatamente após extração ✅

🤖 Front-Desk (Agente 2):
"Vai utilizar convênio ou será particular?"

📱 Maria:
"Convênio — tenho Hapvida"

🤖 Front-Desk (Agente 2):
"Perfeito! Pode enviar uma foto da sua
carteirinha do Hapvida? 📸"

📱 Maria envia foto da carteirinha

🔧 Manager (Agente 3):
[Gemini Vision processa]
Extrai:
- Convênio: Hapvida
- Número: 123456789
- Validade: 06/2027
- Plano: Nacional Plus
→ Imagem descartada imediatamente ✅

🔧 Manager (Agente 3):
[Verifica convênio no banco]
SELECT * FROM convenios WHERE nome_convenio LIKE '%Hapvida%'
→ ENCONTRADO — Hapvida aceito ✅

🤖 Front-Desk (Agente 2):
"Ótimo! Aceitamos o Hapvida 😊

Confirmando seus dados antes de cadastrar:

👤 Nome: Maria Aparecida Souza
📋 CPF: 456.789.123-00
🎂 Nascimento: 22/07/1990
💳 Convênio: Hapvida — Nacional Plus
📄 Carteira: 123456789 (válida até 06/2027)

Está correto? ✅ SIM ✏️ Corrigir"

📱 Maria:
"✅ SIM"
```

---

## ETAPA 3 — DADOS COMPLEMENTARES

```
🤖 Front-Desk (Agente 2):
"Preciso de mais alguns dados rapidinho:

📮 Qual seu CEP?"

📱 Maria:
"70040-010"

🤖 Front-Desk (Agente 2):
"📧 E seu e-mail?"

📱 Maria:
"maria@email.com"

🤖 Front-Desk (Agente 2):
"Perfeito! Seu celular para contato
é o mesmo número do WhatsApp?
✅ Sim, é esse mesmo
📱 Não, tenho outro"

📱 Maria:
"✅ Sim, é esse mesmo"
```

---

## ETAPA 4 — CADASTRO NO SISTEMA

```
🔧 Manager (Agente 3):
[Abre browser — Playwright]
1. Navega para formPesquisaPaciente.php
2. Clica em "Novo"
3. Preenche formulário:
   - #nome_pac: Maria Aparecida Souza
   - #nasci: 22/07/1990
   - #cpf_pac: 456.789.123-00
   - #rg: 9876543
   - #cep: 70040-010
     → Aguarda auto-complete ViaCEP (2 seg)
     → Endereço preenchido automaticamente ✅
   - #email: maria@email.com
   - #cel: 61988888888
   - Convênio: Hapvida (busca modal)
   - #plano_pac: Nacional Plus
   - #val_pac: 06/2027
4. Clica em Gravar
5. Captura ID: #pac-5891
→ LOG: [2026-04-22 15:10:33] CADASTRO_PACIENTE 456.***.***-00 sucesso id: 5891

[Upload de documentos]
6. Clica em "Arquivos" no cadastro
7. Upload: rg_maria.jpg → confirmado → arquivo local deletado ✅
8. Upload: carteirinha_maria.jpg → confirmado → arquivo local deletado ✅
→ LOG: [2026-04-22 15:11:05] UPLOAD_RG 5891 sucesso
→ LOG: [2026-04-22 15:11:18] UPLOAD_CARTEIRINHA 5891 sucesso

🤖 Front-Desk (Agente 2):
"Cadastro realizado com sucesso! ✅
Agora vamos agendar sua consulta.

Qual especialidade você precisa?"
```

---

## ETAPA 5 — AGENDAMENTO (MESMO FLUXO DO CENÁRIO A)

```
[Continua igual ao Cenário A — Etapa 2]

📱 Maria:
"Clínico Geral"

🤖 Front-Desk (Agente 2):
"Temos os seguintes médicos disponíveis
em Clínico Geral:

👨‍⚕️ Dr. Paulo Ferreira
👩‍⚕️ Dra. Ana Lima

Prefere algum deles ou tanto faz?"

[... continua fluxo de agendamento ...]
```

---

# CENÁRIO C — CANCELAMENTO E REAGENDAMENTO

---

```
📱 Paciente (João Silva):
"Oi, preciso cancelar minha consulta de quinta"

🔧 Manager (Agente 3):
[Consulta banco]
SELECT * FROM agenda
WHERE id_paciente = [id_joao]
AND situacao = 'MARCADO'
→ Encontrou 2 agendamentos:
  1. #12847 — Dr. Carlos — 24/04 09:00 — Cardiologia
  2. #12901 — Dr. Paulo — 26/04 14:00 — Clínico Geral

🤖 Front-Desk (Agente 2):
"João, encontrei 2 consultas agendadas:

1️⃣ Dr. Carlos Mendes — Cardiologia
   📅 24/04/2026 às 09:00

2️⃣ Dr. Paulo Ferreira — Clínico Geral
   📅 26/04/2026 às 14:00

Qual delas você quer cancelar?"

📱 João:
"A de quinta, o Dr. Carlos"

🤖 Front-Desk (Agente 2):
"Vou cancelar a consulta com o Dr. Carlos
no dia 24/04 às 09:00.

Confirma o cancelamento?
✅ SIM — cancelar
❌ NÃO — manter"

📱 João:
"✅ SIM"

🔧 Manager (Agente 3):
[Abre browser — Playwright]
1. Localiza agendamento #12847
2. Altera #situacao → DESMARCADO
3. Grava
→ LOG: [2026-04-23 08:22:11] CANCELAMENTO 12847 sucesso

🤖 Front-Desk (Agente 2):
"Consulta cancelada ✅

Quer remarcar para outro dia com
o Dr. Carlos?
📅 Sim, remarcar
🚫 Não por enquanto"

📱 João:
"📅 Sim, remarcar"

[Contador: 1ª remarcação — máximo 2]

[... continua fluxo de agendamento ...]
```

---

# CENÁRIO D — HANDOFF PARA HUMANO

---

```
📱 Paciente:
"Preciso saber se meu convênio cobre
cirurgia de hérnia de disco com o Dr. Carlos"

🤖 Front-Desk (Agente 2):
[Tenta responder — informação não está no FAQ]
"Para procedimentos cirúrgicos, a cobertura
depende do seu plano específico e da
autorização prévia do convênio.

Posso verificar as informações básicas, mas
para uma resposta precisa sobre cirurgia,
nossa equipe pode te ajudar melhor.

Quer que eu te conecte com nossa recepcionista?"

📱 Paciente:
"Sim, por favor"

🤖 Front-Desk (Agente 2):
[Escala para humano]
"Vou chamar nossa equipe agora! 😊
Em breve alguém entrará em contato."

👩‍💼 Recepcionista recebe (WhatsApp):
"🔔 Handoff — Paciente aguardando

👤 João Silva
📱 (61) 99999-9999
💳 Unimed — Plano Essencial

❓ Pergunta: Cobertura de cirurgia de
hérnia de disco pelo convênio com Dr. Carlos

📋 Contexto da conversa:
[histórico das últimas 5 mensagens]"
```

---

# CENÁRIO E — NOTIFICAÇÃO SEM RESPOSTA

---

```
[24/04 às 05:00 — lembrete 4h antes]
[Paciente não respondeu o lembrete de 18h]

📋 Notificações (Agente 4):
[Verifica janela → fechada]
[Cascata: e-mail → sem abertura em 2h → SMS]

📱 Paciente recebe SMS:
"Clínica [PLACEHOLDER]: Sua consulta é HOJE às 09:00
com Dr. Carlos. Confirme: [link]"

[09:00 — 1h antes — ainda sem resposta]

📋 Notificações (Agente 4):
🔧 Manager (Agente 3) atualiza status no ADMED:
UPDATE agenda SET obs = 'SEM RESPOSTA'
WHERE id_agenda = 12847

👩‍💼 Recepcionista recebe:
"⚠️ SEM RESPOSTA

👤 João Silva
📅 Hoje às 09:00 — Dr. Carlos
📱 (61) 99999-9999

Paciente não confirmou presença.
Recomendamos contato telefônico."

👑 Prometheus notifica gestor:
"⚠️ 2 pacientes sem resposta hoje:
• João Silva — 09:00 Dr. Carlos
• Ana Costa — 10:30 Dra. Paula
Recepcionista foi notificada."
```

---

# CENÁRIO F — BROADCAST DO GESTOR

---

```
👨‍💼 Gestor manda áudio para o Prometheus:
[áudio] "Ana, avisa os pacientes de Cardiologia
que o Dr. Carlos abriu novos horários
nas manhãs de quinta-feira"

👑 Prometheus:
[Gemini Audio transcreve o áudio]
[Valida regras da Meta]
→ Verificou: template de marketing aprovado ✅
→ Dentro do limite diário ✅
→ 47 pacientes de Cardiologia no banco

"Entendido! Vou disparar para 47 pacientes
de Cardiologia.

Mensagem que será enviada:
'Olá [nome]! O Dr. Carlos Mendes abriu
novos horários nas manhãs de quinta-feira.
Quer aproveitar? Responda esta mensagem
que te ajudo a agendar! 😊'

Confirma o envio?
✅ SIM   ❌ NÃO"

👨‍💼 Gestor:
"✅ SIM"

👑 Prometheus:
[Registra contexto no MEMORY.md do Front-Desk (Agente 2)]
[Aciona Front-Desk (Agente 2) para disparar]

🤖 Front-Desk (Agente 2):
[Dispara mensagem individualmente para 47 pacientes]

[Pacientes que respondem → Front-Desk (Agente 2) atende
contextualizado com a oferta de horários]

👑 Prometheus reporta (30 min depois):
"📊 Broadcast concluído:
✅ Enviadas: 47
📖 Abertas: 31 (66%)
💬 Responderam: 18 (38%)
📅 Agendamentos gerados: 12"
```

---

# CENÁRIO G — ANIVERSÁRIO DO PACIENTE

---

```
[22/07/2026 — aniversário de Maria Souza]

📋 Notificações (Agente 4):
[Detecta aniversário no banco]
[Janela verificada → fechada → usa e-mail para abrir]

📱 Maria recebe:
"Feliz aniversário, Maria! 🎂🎉

Toda a equipe da Clínica [PLACEHOLDER] deseja um
dia muito especial e muita saúde!

Cuide-se bem 😊"

📱 Maria:
"Obrigada, que fofo! 🥰"

📋 Notificações (Agente 4):
[Janela aberta — anota para próxima comunicação]
```

---

# CENÁRIO H — MASTER EM AÇÃO (GESTOR)

---

```
👨‍💼 Gestor manda para o Prometheus:
"Quantos agendamentos temos amanhã?"

👑 Prometheus:
[Aciona Manager (Agente 3) — consulta banco]
SELECT COUNT(*), situacao FROM agenda
WHERE data_agenda = '23/04/2026'
GROUP BY situacao

→ Resultado:
"📋 Amanhã — 23/04/2026:

✅ Confirmados: 18
⏳ Aguardando confirmação: 7
❌ Cancelados hoje: 2
👤 Pacientes novos: 3

Por médico:
👨‍⚕️ Dr. Carlos: 12 consultas
👩‍⚕️ Dra. Ana: 8 consultas
👨‍⚕️ Dr. Paulo: 7 consultas

⚠️ Atenção: Dr. Carlos tem 3 pacientes
sem confirmação para as 08:00, 09:00 e 10:00.
Quer que eu notifique a recepcionista?"

👨‍💼 Gestor:
"Sim, notifica"

👑 Prometheus:
[Notifica recepcionista com lista dos 3 pacientes]
"✅ Recepcionista notificada com
os 3 pacientes pendentes."
```

---

# CENÁRIO I — AGENTE 5 (SINCRONIZADOR) EM AÇÃO

---

```
[Clínica cadastra novo médico no ADMED]
Dr. Roberto Alves — Neurologia — terças e quintas

[30 minutos depois]

🔄 Sincronizador (Agente 5):
[Executa query no banco]
SELECT nome_prof, especialidade FROM profissionais WHERE ativo = 1
→ Detectou: Dr. Roberto Alves (Neurologia) — não está no SOUL.md

[Atualiza SOUL.md do Front-Desk (Agente 2) automaticamente]
[Reinicia Front-Desk (Agente 2)]

👑 Prometheus notifica gestor:
"🔄 Sincronização automática realizada:

✅ Novo médico detectado no sistema:
👨‍⚕️ Dr. Roberto Alves — Neurologia
📅 Atende: terças e quintas

O Agente de Atendimento foi atualizado
automaticamente e já pode agendar consultas
com o Dr. Roberto."
```

---

# RELATÓRIOS AUTOMÁTICOS

---

## Relatório Diário (todo dia às 8h)

```
👑 Prometheus envia para o gestor:

"📋 Resumo de ontem — 22/04/2026

✅ Agendamentos realizados: 28
❌ Cancelamentos: 3
⚠️ Sem resposta: 2
🆕 Pacientes novos cadastrados: 5
⏱️ Tempo médio de atendimento: 4 min
⭐ NPS médio: 4.8

💡 Destaque do dia:
18 pacientes aceitaram opt-in de dicas de saúde.

🔔 Alerta:
Dr. Carlos tem apenas 3 horários vagos
na próxima semana. Agenda quase cheia!

📊 Por médico:
👨‍⚕️ Dr. Carlos: 12 atendimentos
👩‍⚕️ Dra. Ana: 9 atendimentos
👨‍⚕️ Dr. Paulo: 7 atendimentos"
```

---

# CHECKLIST DE PROCESSOS COBERTOS

## Identificação
☐ Paciente recorrente — identificação por WhatsApp
☐ Paciente recorrente — identificação por CPF
☐ Paciente novo — não encontrado no sistema

## Cadastro
☐ Coleta de documentos via foto (RG + Carteirinha)
☐ Extração via Gemini Vision
☐ Validação do convênio no banco
☐ Convênio não aceito — oferta de particular
☐ Confirmação dos dados com o paciente
☐ Cadastro no ADMED (browser)
☐ Upload de documentos no ADMED
☐ Coleta de CEP, e-mail e celular
☐ Consentimento LGPD [versão futura]

## Agendamento
☐ Paciente sugere médico e horário
☐ Verificação de disponibilidade no banco
☐ Negociação de horários alternativos
☐ Múltiplos agendamentos do mesmo paciente
☐ Confirmação e gravação no ADMED
☐ Notificação para recepcionista

## Cancelamento e Reagendamento
☐ Cancelamento direto no ADMED
☐ Reagendamento (máx 2x)
☐ 3ª remarcação → escala para recepcionista

## Notificações
☐ Dicas de saúde (opt-in, janela dinâmica)
☐ Orientações pré-consulta específicas
☐ Lembrete de confirmação (18h — dinâmico)
☐ Segundo lembrete (4h — dentro da janela)
☐ Fallback: e-mail → SMS → template Meta
☐ Status "Sem resposta" no ADMED
☐ Notificação para recepcionista (sem resposta)

## Atendimento (dia da consulta)
☐ Alterar status para ATENDIDO no ADMED
☐ Criar Guia de Consulta
☐ Criar Guia SP/SADT
☐ Preencher Contratado Executante (Campo 9/29)
☐ Verificação ANS (senha de autorização)
☐ Vincular guia ao agendamento

## Pós-consulta
☐ Mensagem pós-consulta (24h depois)
☐ Pesquisa NPS (1 a 5 estrelas)
☐ Link Google Maps (nota 4-5)
☐ Notificação urgente ao Prometheus (nota 1-3)
☐ Oferta de agendamento de retorno
☐ Cron job de lembrete de retorno

## Comunicação Proativa
☐ Broadcast com validação de regras Meta
☐ Opt-out de broadcast
☐ Mensagem de aniversário
☐ Alerta de agenda vazia → sugestão de broadcast

## Prometheus (Gestor)
☐ Dashboard por linguagem natural
☐ Resposta em texto e voz (Google TTS)
☐ Multimodal: texto, áudio, imagem, documento
☐ Bloqueio de agenda via comando
☐ Intervenção em conversas do Front-Desk (Agente 2)
☐ Relatório diário automático (8h)
☐ Relatório semanal automático (segunda 8h)
☐ Relatório mensal automático (dia 1 às 8h)
☐ Alerta de custo de API acima do esperado

## Situações de Erro
☐ Sistema ADMED fora do ar (Opção C — fila pendente)
☐ LLM fora do ar (3 camadas de fallback BYOK)
☐ Sessão ADMED expirada (renovação automática — Playwright e Crawl4AI)
☐ Handoff para recepcionista (1 tentativa, depois escala)
☐ Mensagens fora do escopo (3x → escala)
☐ Timeout de 30 minutos sem resposta

## Infraestrutura
☐ Sincronização automática de médicos (Sincronizador — Crawl4AI)
☐ Backup diário (4:30am)
☐ Auto-update OpenClaw (4:00am)
☐ Auditoria de segurança semanal
☐ Monitoramento de uptime (UptimeRobot)
☐ Log de todas as ações do Manager (Agente 3)

## v2.7 — Novidades
☐ Leitura no Ademed via Crawl4AI (80% mais rápido)
☐ Resposta multimodal condicional (áudio → voz Journey, texto → texto)
☐ Segundo Cérebro (MAP.md em cada agente)
☐ Human-in-the-loop (Prometheus aguarda "Y" antes de executar)
☐ Voz Journey configurada por clínica

---

# CENÁRIO J — ENTRADA DE ÁUDIO (v2.7)

*Fluxo de teste da Resposta Multimodal Condicional*

---

## Paciente envia áudio para agendar consulta

```
📱 Paciente (Maria Souza) envia áudio:
[áudio 8 segundos]
"Oi, boa tarde! Queria marcar uma consulta
com o Dr. Carlos para essa semana se possível"

🤖 Front-Desk (Evolution Go recebe .ogg):
[Detecta: entrada = ÁUDIO]
[Gemini 3.1 Flash transcreve]:
→ "Oi, boa tarde! Queria marcar uma consulta
   com o Dr. Carlos para essa semana se possível"

[DeepSeek-V4 Flash processa a transcrição]
[Formula resposta em texto]
→ "Olá, Maria! Boa tarde 😊 Vou verificar
   os horários do Dr. Carlos essa semana..."

[Gemini 3.1 Flash TTS / Google Cloud TTS Journey]
[Converte resposta para áudio .ogg]
[Voz: Journey F, tom acolhedor, velocidade normal]

📱 Paciente recebe MENSAGEM DE VOZ:
[áudio] "Olá, Maria! Boa tarde. Vou verificar
os horários do Dr. Carlos essa semana..."

🔧 Manager (Agente 3) — Crawl4AI (leitura rápida):
[Crawl4AI busca disponibilidade do Dr. Carlos]
→ ~1 segundo (vs ~5s anterior com Playwright)
→ Horários disponíveis: terça 10h, quarta 14h, quinta 9h

🤖 Front-Desk gera resposta em texto:
"Terça 10h, quarta 14h ou quinta 9h.
Qual prefere?"

[Google Cloud TTS Journey converte para áudio]

📱 Paciente recebe VOZ:
[áudio] "Tenho disponível terça às dez,
quarta às duas da tarde, ou quinta às nove.
Qual horário você prefere?"

📱 Paciente responde (texto desta vez):
"Quinta às 9h!"

🤖 Front-Desk:
[Detecta: entrada = TEXTO]
[Responde em TEXTO — sem converter para áudio]
"Perfeito! Confirmando:
📅 Quinta-feira, [data]
🕘 09:00
👨‍⚕️ Dr. Carlos Mendes
Confirma? ✅ SIM ❌ NÃO"

📱 Paciente:
"✅ SIM"

🔧 Manager (Agente 3) — Playwright (escrita):
[Cria agendamento no ADMED via Playwright]
→ Necessário JavaScript do ADMED para grade de agenda
→ Agendamento #12948 criado ✅

🤖 Front-Desk (resposta em TEXTO — entrada foi texto):
"✅ Consulta agendada!
📅 Quinta, [data] às 09:00
👨‍⚕️ Dr. Carlos Mendes — Cardiologia
💳 Unimed — Plano Essencial
📍 [endereço]
Chegue 15 minutos antes 😊"
```

---

## Gestor envia áudio para o Prometheus

```
👨‍💼 Gestor envia áudio para o Prometheus:
[áudio 12 segundos]
"Prometheus, quantos agendamentos temos
amanhã e qual a taxa de confirmação
dessa semana?"

👑 Prometheus:
[Detecta: entrada = ÁUDIO]
[Gemini 3.1 Flash transcreve o áudio]
→ "Quantos agendamentos temos amanhã e
   qual a taxa de confirmação dessa semana?"

[Aciona Manager para consultar via Crawl4AI]

🔧 Manager — Crawl4AI:
[Extrai agendamentos de amanhã]
→ ~1 segundo
→ 23 agendamentos: 19 confirmados, 3 sem resposta, 1 cancelado

[Extrai dados da semana para taxa de confirmação]
→ ~2 segundos
→ Taxa de confirmação: 87% (vs 72% semana anterior)

[Gemini 3.1 Pro formula análise]
[Google Cloud TTS Journey converte para áudio]
[Voz: Journey M, tom profissional]

👑 Prometheus envia VOZ ao gestor:
[áudio] "Amanhã temos 23 agendamentos:
19 confirmados, 3 ainda sem resposta —
vou monitorar — e 1 cancelamento.
A taxa de confirmação dessa semana chegou a
87%, acima dos 72% da semana passada.
Quer que eu notifique a recepcionista
sobre os 3 sem resposta?"

👨‍💼 Gestor (responde em texto):
"Sim, pode notificar"

👑 Prometheus:
[Detecta: entrada = TEXTO → responde em TEXTO]
"✅ Recepcionista notificada com os 3 pacientes
sem confirmação para amanhã."

[Aciona Agente 4 para notificar recepcionista]
```

---

## Exceções e Tratamentos Mantidos

```
EXCEÇÃO 1: Qualidade de áudio ruim
        ↓
Gemini não consegue transcrever com confiança
        ↓
Front-Desk responde em texto:
"Desculpe, não consegui entender bem o áudio.
Pode repetir ou digitar sua mensagem?"

EXCEÇÃO 2: Falha do Google TTS Journey
        ↓
Sistema tenta Google TTS padrão como fallback
        ↓
Se também falhar: responde em texto
        ↓
Log de erro + notificação ao Prometheus

EXCEÇÃO 3: Áudio muito longo (>2 min)
        ↓
Gemini transcreve normalmente
        ↓
DeepSeek processa e resume
        ↓
Resposta em voz com duração proporcional ao conteúdo

EXCEÇÃO 4: Paciente manda áudio fora do escopo
        ↓
Gemini transcreve
        ↓
DeepSeek identifica fora do escopo
        ↓
Front-Desk redireciona (em voz, espelhando a entrada):
[áudio] "Entendi! Mas por aqui só consigo
te ajudar com assuntos da clínica.
Posso te ajudar com alguma consulta?"
```

---

*Simulação de Processo v2.7 — Maio 2026*
*Kairós Intelligence*
*Proprietário: Stênio Alves de Souza Maia*
