> **Kairós Intelligence v2.7** | Stack: Evolution Go · OpenClaw · Paperclip · DeepSeek-V4 Flash · Gemini 3.1 · Redis · GraphRAG · Crawl4AI · Google TTS Journey
> Atualizado em 04/05/2026 — Arquitetura Híbrida + Resposta Multimodal Condicional.

# MANUAL DO SISTEMA
## Guia Completo para o Gestor
**Kairós Intelligence — Clínica [PLACEHOLDER]**

---

> **PARA QUEM É ESTE MANUAL**
>
> Este manual foi escrito para o gestor responsável por administrar o sistema
> no dia a dia. Você não precisa de conhecimento técnico para usar este guia.
> Tudo está explicado em linguagem simples, passo a passo.
>
> **Se algo der errado e não estiver neste manual, entre em contato
> com o suporte técnico pelo WhatsApp: [número do suporte]**

---

## ÍNDICE

1. Como o Sistema Funciona (visão geral)
2. Os 5 Agentes — O Que Cada Um Faz
3. Resposta Multimodal Condicional (Áudio e Texto)
4. O Que Você Gerencia Pelo Dashboard
5. O Que é Automático (não precisa fazer nada)
6. O Que Precisa de Suporte Técnico
7. Como Usar o Prometheus
8. Como Monitorar os Atendimentos
9. Como Atualizar Informações da Clínica
10. Como Fazer um Broadcast para Pacientes
11. Relatórios Automáticos
12. O Que Fazer em Cada Situação de Problema
13. Perguntas Frequentes do Gestor

---

## 1. COMO O SISTEMA FUNCIONA (VISÃO GERAL)

Imagine que você contratou 5 funcionários digitais que trabalham 24 horas por dia, 7 dias por semana, sem precisar de férias ou salário além do custo mensal do sistema.

**O que eles fazem:**

Um paciente manda mensagem no WhatsApp da clínica às 23h pedindo para marcar uma consulta. O sistema:
1. Reconhece quem é o paciente pelo número do celular
2. Verifica a agenda do médico solicitado
3. Confirma o horário disponível
4. Agenda no sistema da clínica
5. Manda confirmação para o paciente
6. Manda um aviso para a recepcionista no dia seguinte

E você? Não precisou fazer nada. Dormiu tranquilo.

**Um dia antes da consulta**, o sistema manda um lembrete automático para o paciente confirmar presença. Se o paciente não responder, o sistema tenta de novo 4 horas antes. Se ainda não responder, marca como "sem resposta" e avisa a recepcionista.

**No dia seguinte à consulta**, o sistema pergunta ao paciente como foi o atendimento. Se a nota for boa, manda automaticamente um link para avaliar a clínica no Google.

**Você**, o gestor, acompanha tudo isso pelo seu WhatsApp pessoal através do **Prometheus (Agente Prometheus)** — seu assistente particular que te informa, te alerta e executa ações no sistema quando você pede.

---

## 2. OS 5 AGENTES — O QUE CADA UM FAZ

### Prometheus (Agente Prometheus) (seu assistente pessoal)

**Quem usa:** Somente você, o gestor.
**Canal:** Seu WhatsApp pessoal.
**O que faz:** É sua interface com todo o sistema. Você conversa com ele como um assistente pessoal. Ele te informa, te alerta, executa ações e gera relatórios. Entende texto, áudio, imagem e documentos. Pode responder em voz quando você quiser.

**Exemplos do que você pode pedir:**
- *"Quantos agendamentos temos amanhã?"*
- *"Bloqueia a agenda do Dr. Carlos na sexta de tarde"*
- *"Manda um aviso para os pacientes de Cardiologia sobre o novo horário"*
- *"Como está a taxa de confirmação essa semana?"*

---

### Front-Desk (Agente 2) (recepcionista virtual)

**Quem usa:** Os pacientes da clínica.
**Canal:** WhatsApp Business da clínica (número comercial).
**O que faz:** Atende todos os pacientes 24/7. Agenda consultas, responde dúvidas, faz triagem, encaminha para humano quando necessário.

**Você não interage diretamente com ele**, mas pode monitorar as conversas pelo dashboard e pode pedir ao Prometheus para intervir em alguma conversa específica.

---

### Manager (Agente 3) (acessa o sistema da clínica)

**Quem usa:** Os outros agentes internamente.
**Você não interage com ele diretamente.**
**O que faz:** Acessa o banco de dados e o sistema de agendamento da clínica. É o único agente com acesso às credenciais do sistema. Registra tudo que faz em um log de auditoria.

---

### Notificações (Agente 4) (comunicação proativa)

**Quem usa:** Roda automaticamente no fundo.
**Você não interage com ele diretamente.**
**O que faz:** Envia todos os lembretes automáticos — confirmação de consulta, lembretes, dicas de saúde, mensagem pós-consulta, pesquisa de satisfação (NPS), mensagens de aniversário, alerta de agenda vazia.

---

### Sincronizador (Agente 5) (atualização automática)

**Quem usa:** Roda sozinho a cada 30 minutos.
**Você não interage com ele diretamente.**
**O que faz:** Monitora o banco de dados da clínica. Se um médico novo for cadastrado ou sair, atualiza automaticamente as informações do Agente de Atendimento. Você recebe um aviso via Prometheus quando isso acontece.

---

## 3. RESPOSTA MULTIMODAL CONDICIONAL (ÁUDIO E TEXTO)

O Kairós Intelligence v2.7 adapta automaticamente o **formato da resposta** ao formato da entrada do paciente ou do gestor. Isso torna a experiência mais natural e fluída.

### Como Funciona

```
ENTRADA DO PACIENTE OU GESTOR
            ↓
  É uma mensagem de áudio?
     /              \
   SIM              NÃO
    ↓                 ↓
Gemini 3.1        DeepSeek-V4
Flash             Flash
transcreve        processa
o áudio           o texto
    ↓                 ↓
DeepSeek-V4       Formula
Flash formula     resposta
a resposta        em texto
    ↓                 ↓
Google Cloud      Resposta
TTS Journey       enviada
converte para     em texto
áudio
    ↓
Evolution Go
envia mensagem
de voz
```

**Regra simples:** Entrou áudio → sai áudio. Entrou texto → sai texto.

---

### Motor de Voz: Google Cloud TTS Journey

O sistema usa o motor **Google Cloud TTS Journey** para gerar respostas em voz. É o motor de mais alta qualidade do Google para português brasileiro, com naturalidade de fala muito superior aos motores padrão.

**Características do Journey:**
- Voz natural com entonação contextual (não é voz robótica)
- Pausas e respiração natural
- Velocidade adaptada ao conteúdo
- Suporte nativo a português do Brasil

**Quando é usado:**
- Respostas do **Prometheus** ao gestor quando ele manda áudio
- Respostas do **Front-Desk** ao paciente quando ele manda áudio
- Relatórios em voz sob demanda: *"Me manda esse relatório em áudio"*

---

### Para o Gestor (Prometheus)

Exemplos práticos do comportamento multimodal:

**Você manda áudio:**
*[áudio] "Quantos agendamentos temos amanhã?"*
→ Prometheus transcreve, processa, responde **em áudio** com voz Journey

**Você manda texto:**
*"Quantos agendamentos temos amanhã?"*
→ Prometheus responde **em texto**

**Você manda foto com texto:**
*[imagem de planilha] + "Resume esses dados"*
→ Gemini Vision analisa a imagem, responde **em texto**

**Você pede explicitamente:**
*"Me responde em áudio: como está o sistema hoje?"*
→ Prometheus responde em áudio mesmo que você tenha enviado texto

---

### Para o Paciente (Front-Desk)

**Paciente manda áudio:**
*[áudio] "Oi, queria marcar uma consulta pro Dr. Carlos"*
→ Gemini transcreve, DeepSeek processa, Google TTS Journey gera resposta em voz

**Paciente manda texto:**
*"Oi, queria marcar uma consulta"*
→ Bot responde em texto normalmente

**Nota:** O paciente não precisa saber nada disso. A experiência é natural — ele fala como prefere e o sistema acompanha.

---

### Configuração da Voz Journey

A voz Journey é configurada no briefing do cliente (Seção 3 do Documento de Onboarding). Cada clínica pode escolher:

- **Voz feminina Journey F** — tom acolhedor, indicado para clínicas médicas
- **Voz masculina Journey M** — tom profissional
- **Velocidade de fala** — normal, levemente mais lenta (para idosos), levemente mais rápida
- **Tom geral** — caloroso, profissional, neutro

Se não configurado, o padrão é **Journey F em velocidade normal**.

---

## 4. O QUE VOCÊ GERENCIA PELO DASHBOARD

O sistema tem dois painéis de controle acessíveis pelo navegador:

**Painel da Hostinger** (infraestrutura do servidor):
- Ligar e desligar o servidor
- Ver uso de CPU, memória e disco
- Acessar o terminal (se necessário)
- Gerenciar arquivos simples

**Painel do OpenClaw** (controle dos agentes):
- Ver todos os agentes e o status de cada um (online/offline)
- Monitorar conversas em andamento
- Ver histórico de mensagens
- Reiniciar um agente individualmente
- Gerenciar skills instaladas
- Ver cron jobs (automações agendadas)
- Ver logs de erros

### Como acessar os painéis:

**Hostinger:**
1. Acesse: hostinger.com.br
2. Faça login na sua conta
3. Clique em "VPS" → selecione o servidor da clínica

**OpenClaw:**
1. Abra o navegador
2. Acesse: http://[seu-ip-tailscale]:18789
3. Digite a senha do gateway

### O que você pode resolver sozinho pelo dashboard:

✅ Ver se os agentes estão funcionando
✅ Reiniciar um agente que travou
✅ Monitorar conversas ativas
✅ Ver logs de erro para entender o que aconteceu
✅ Editar textos simples no FAQ (via editor de arquivos da Hostinger)
✅ Verificar se o backup rodou

---

## 5. O QUE É AUTOMÁTICO (NÃO PRECISA FAZER NADA)

Estas ações acontecem sozinhas, sem nenhuma intervenção sua:

| Automação | Quando acontece | O que acontece |
|---|---|---|
| Atendimento de pacientes | 24/7, sempre | Front-Desk (Agente 2) responde automaticamente |
| Lembrete de consulta | 18h antes | Mensagem enviada ao paciente |
| Segundo lembrete | 4h antes (se sem resposta) | Segunda mensagem enviada |
| Status "sem resposta" | 1h antes (se sem resposta) | Recepcionista notificada |
| Mensagem pós-consulta | 24h após a consulta | Pergunta como o paciente está |
| Pesquisa NPS | Junto com pós-consulta | Avaliação de 1 a 5 estrelas |
| Link Google Maps | Se nota 4 ou 5 | Enviado automaticamente |
| Mensagem de aniversário | No dia do aniversário | Parabéns ao paciente |
| Dicas de saúde | A cada 3-4 dias (opt-in) | Para quem aceitou receber |
| Sincronização de médicos | A cada 30 minutos | Sincronizador (Agente 5) verifica mudanças |
| Backup do sistema | Todo dia às 4:30 | Arquivos salvos no GitHub |
| Atualização do OpenClaw | Todo dia às 4:00 | Sistema atualizado automaticamente |
| Auditoria de segurança | Todo domingo às 5:00 | Relatório enviado para o Prometheus |
| Relatório diário | Todo dia às 8:00 | Enviado para o seu WhatsApp |
| Relatório semanal | Toda segunda às 8:00 | Enviado para o seu WhatsApp |
| Relatório mensal | Todo dia 1º às 8:00 | Enviado para o seu WhatsApp |
| Monitoramento do servidor | A cada 5 minutos | UptimeRobot verifica se está online |

---

## 6. O QUE PRECISA DE SUPORTE TÉCNICO

Estas ações requerem intervenção do suporte técnico:

❌ Adicionar um novo fluxo de atendimento
❌ Criar uma nova integração (Instagram, Facebook, etc.)
❌ Mudar a lógica de agendamento
❌ Atualizar o sistema após mudança grande no sistema da clínica
❌ Configurar um segundo número de WhatsApp
❌ Resolver erros que o dashboard não explica
❌ Restaurar o sistema após uma falha grave

**Como acionar o suporte:**
WhatsApp: [número do suporte]
Horário: Segunda a sexta, 8h às 18h (Brasília)
Urgências fora do horário: [número de emergência]

---

## 7. COMO USAR O PROMETHEUS

### Acessando o Prometheus

O Prometheus está no seu **WhatsApp pessoal**. O número salvo como contato é o número do WhatsApp Business da clínica. Você conversa com ele normalmente, como faria com qualquer pessoa.

### Tipos de mensagem que ele entende

**Texto:** Digite normalmente.

**Áudio:** Grave um áudio no WhatsApp. Ele transcreve e responde.
*Exemplo: [áudio] "Quantos pacientes cancelaram essa semana?"*

**Imagem:** Mande uma foto com uma pergunta.
*Exemplo: Foto de um documento → "O que está escrito nesse papel?"*

**Documento:** Mande um PDF ou planilha com uma instrução.
*Exemplo: Planilha de agendamentos → "Resume os dados dessa planilha"*

### Comandos úteis do dia a dia

**Ver agendamentos:**
*"Quantos agendamentos temos hoje?"*
*"Quem tem consulta amanhã com o Dr. Carlos?"*
*"Quais pacientes não confirmaram para sexta?"*

**Gerenciar agenda:**
*"Bloqueia a agenda de todos os médicos na quinta-feira"*
*"Qual o próximo horário disponível com a Dra. Ana?"*
*"Adiciona um horário extra para o Dr. Carlos na quarta às 14h"*

**Enviar comunicados:**
*"Avisa todos os pacientes que a clínica vai fechar mais cedo sexta"*
*"Manda uma mensagem para os pacientes de Cardiologia sobre o novo protocolo"*

**Ver relatórios sob demanda:**
*"Me dá um resumo dos últimos 7 dias"*
*"Qual foi a taxa de comparecimento esse mês?"*
*"Quais médicos tiveram mais cancelamentos?"*

**Pedir resposta em voz:**
*"Me responde em áudio: como está o sistema hoje?"*

**Verificar saúde do sistema:**
*"Qual versão está rodando?"*
*"Todos os agentes estão funcionando?"*

---

## 8. COMO MONITORAR OS ATENDIMENTOS

### Pelo Dashboard do OpenClaw

1. Acesse o painel do OpenClaw no navegador
2. Clique em "Conversations" (Conversas)
3. Você verá todas as conversas ativas e recentes
4. Clique em qualquer conversa para ler o histórico completo
5. Se quiser intervir: peça ao Prometheus para assumir ou mandar uma mensagem específica

### Pelo Prometheus (mais simples)

*"Tem algum paciente esperando atendimento humano agora?"*
*"Me mostra as últimas 5 conversas que foram escaladas para a recepcionista"*
*"Quantas conversas ativas tem agora?"*

### Alertas Automáticos

O Prometheus te manda uma mensagem automaticamente quando:
- Um paciente pede para falar com humano
- Um agente trava ou cai
- A taxa de erro sobe acima de 20%
- O custo de API está acima do esperado
- Um médico foi atualizado no sistema (Sincronizador (Agente 5) detectou)
- Um paciente deu nota baixa no NPS

---

## 9. COMO ATUALIZAR INFORMAÇÕES DA CLÍNICA

### Atualizações simples (você mesmo pode fazer)

**Editar o FAQ:**
1. Acesse o painel da Hostinger
2. Clique em "File Manager" (Gerenciador de arquivos)
3. Navegue até: `/home/openclaw/workspace-atendimento/SOUL.md`
4. Clique em "Edit" (Editar)
5. Encontre a seção "FAQ"
6. Faça a alteração
7. Salve o arquivo
8. Peça ao Prometheus: *"Reinicia o Agente de Atendimento"*

**Alterar horário de funcionamento:**
Mesmo processo — edite a seção "Horário de Funcionamento" no SOUL.md.

### Atualizações automáticas (sem fazer nada)

**Novos médicos ou mudança de horário:** O Sincronizador (Agente 5) detecta automaticamente e atualiza. Você recebe um aviso via Prometheus.

### Atualizações que precisam de suporte técnico

- Adicionar nova especialidade com FAQ específico
- Mudar o nome ou tom do assistente
- Adicionar novas dicas de saúde (requer revisão médica)
- Mudar a política de cancelamento

---

## 10. COMO FAZER UM BROADCAST PARA PACIENTES

Broadcast é uma mensagem enviada para vários pacientes ao mesmo tempo.

### Como pedir ao Prometheus

Você simplesmente fala o que quer enviar e para quem:

*"Avisa todos os pacientes que a clínica vai estar fechada na sexta dia 25 por feriado"*

*"Manda uma mensagem para os pacientes de Cardiologia informando que o Dr. Carlos tem novos horários disponíveis na manhã de quinta"*

*"Envia um lembrete para todos os pacientes que têm consulta essa semana para confirmar presença"*

### O que o Prometheus faz automaticamente

1. Verifica as regras do WhatsApp (para não arriscar o número ser bloqueado)
2. Filtra os pacientes corretos
3. Verifica se tem template aprovado para o tipo de mensagem
4. Te pede confirmação antes de enviar
5. Dispara as mensagens
6. Te reporta quantas foram enviadas e quantas responderam

### Regras importantes

⚠️ **Nunca peça ao Prometheus para enviar mensagens em massa sem ele verificar as regras primeiro.** O Prometheus sabe quando pode e quando não pode enviar, e vai te explicar caso não seja possível.

⚠️ **Pacientes que pediram para sair da lista nunca recebem broadcasts.** Isso é automático e obrigatório por lei.

---

## 11. RELATÓRIOS AUTOMÁTICOS

### Relatório Diário (todo dia às 8h)

Você recebe automaticamente no seu WhatsApp:

```
📋 Resumo de [data]

✅ Agendamentos realizados: [número]
❌ Cancelamentos: [número]
⚠️ Sem resposta: [número]
🆕 Novos pacientes cadastrados: [número]
⏱️ Tempo médio de atendimento: [minutos]
⭐ NPS médio do dia: [nota]

💡 Destaque do dia: [observação do Prometheus]

🔔 Alertas: [se houver]
```

### Relatório Semanal (toda segunda às 8h)

Inclui comparativo com a semana anterior, tendências e sugestões do Prometheus.

### Relatório Mensal (todo dia 1º às 8h)

Visão consolidada do mês, comparativo com mês anterior e sugestões estratégicas.

### Relatórios Sob Demanda

Peça ao Prometheus a qualquer momento:
*"Me dá um relatório dos últimos 30 dias"*
*"Qual médico teve mais agendamentos em março?"*
*"Me mostra a evolução do NPS nos últimos 3 meses"*

---

## 12. O QUE FAZER EM CADA SITUAÇÃO DE PROBLEMA

### Situação 1: Um paciente reclamou que o bot não respondeu

1. Peça ao Prometheus: *"O paciente [nome] mandou mensagem hoje às [hora]. O que aconteceu?"*
2. O Prometheus vai verificar os logs e te explicar
3. Se foi erro do sistema: acione o suporte técnico
4. Se foi timeout (paciente demorou mais de 30 min): é comportamento normal, peça à recepcionista para entrar em contato manualmente

### Situação 2: O bot deu uma informação errada para um paciente

1. Acione a recepcionista para corrigir com o paciente por ligação
2. Anote qual foi a informação errada
3. Acesse o SOUL.md e corrija a informação (veja Seção 8)
4. Se for algo mais complexo: acione o suporte técnico

### Situação 3: O sistema está lento ou não responde

1. Peça ao Prometheus: *"O sistema está funcionando normalmente?"*
2. Se o Prometheus não responder em 5 minutos: acesse o painel da Hostinger
3. Verifique se o servidor está online
4. Se o servidor estiver online mas lento: acesse o OpenClaw e reinicie os agentes
5. Se não conseguir resolver: acione o suporte técnico urgente

### Situação 4: Muitos pacientes não estão recebendo confirmação de consulta

1. Verifique pelo Prometheus: *"Quantas notificações foram enviadas hoje?"*
2. Acesse o painel do OpenClaw → Cron Jobs → verifique se o Notificações (Agente 4) está ativo
3. Se estiver inativo: reinicie o Notificações (Agente 4) pelo dashboard
4. Se o problema persistir: acione o suporte técnico

### Situação 5: Um médico saiu da clínica mas ainda aparece no bot

1. Certifique-se de que o médico foi desativado no sistema da clínica
2. Aguarde até 30 minutos — o Sincronizador (Agente 5) vai detectar automaticamente
3. Se depois de 30 minutos ainda aparecer: peça ao Prometheus: *"Reinicia o Sincronizador"*
4. Se persistir: acione o suporte técnico

### Situação 6: O WhatsApp da clínica foi bloqueado pela Meta

⚠️ **Situação grave — acione o suporte técnico imediatamente**

Enquanto aguarda:
- Avise a recepcionista para atender manualmente pelo telefone
- Não tente reconectar o WhatsApp sozinho — pode piorar a situação

### Situação 7: O servidor caiu (UptimeRobot enviou alerta)

1. Acesse o painel da Hostinger
2. Verifique o status do VPS
3. Se estiver parado: clique em "Iniciar"
4. Aguarde 2-3 minutos e verifique se voltou
5. Se não voltar: acione o suporte técnico

---

## 13. PERGUNTAS FREQUENTES DO GESTOR

**P: Posso usar o Prometheus de outro celular?**
R: Não. O Prometheus está vinculado ao seu número de WhatsApp pessoal. Por segurança, apenas você tem acesso.

**P: E se eu trocar de celular?**
R: O WhatsApp migra junto com você. O Prometheus continuará funcionando normalmente.

**P: Posso pedir ao Prometheus para responder por um paciente?**
R: Sim! Diga ao Prometheus: *"Manda uma mensagem para o paciente João Silva dizendo que a recepcionista vai entrar em contato amanhã de manhã"*

**P: O bot pode errar e agendar no horário errado?**
R: O bot consulta a agenda em tempo real antes de confirmar. Mas por segurança, a recepcionista recebe uma notificação de cada agendamento para revisar.

**P: O que acontece com os dados dos pacientes?**
R: Os dados ficam no sistema da clínica (como sempre). O bot acessa apenas para consultar e agendar. Imagens de documentos são apagadas imediatamente após o uso.

**P: Os pacientes sabem que estão falando com um bot?**
R: Sim. O assistente se apresenta como assistente virtual, nunca finge ser humano. Mas conversa de forma natural e humanizada.

**P: Posso mudar o nome do assistente?**
R: Sim, mas isso precisa de suporte técnico. Avise com antecedência.

**P: E se o paciente insistir em falar com humano?**
R: O bot encaminha para a recepcionista, que recebe a notificação com todo o contexto da conversa.

**P: Quantos pacientes o sistema consegue atender ao mesmo tempo?**
R: Entre 5 e 15 conversas simultâneas sem degradação. Para clínicas com volume maior, entre em contato para avaliar a infraestrutura necessária.

**P: O sistema funciona no feriado?**
R: Sim, 24/7. Mas você pode configurar mensagens específicas para feriados — acione o suporte técnico.

**P: Como sei se o sistema está custando mais do que o esperado?**
R: O Prometheus monitora o custo automaticamente e te alerta se estiver 20% acima do normal.

---

## PROCESSO DE ONBOARDING DO GESTOR

Ao receber o sistema, você passará por este processo de treinamento:

**Dia 1 — Videochamada de treinamento (1 hora)**
- Tour pelo dashboard da Hostinger e OpenClaw
- Como usar o Prometheus (Agente Prometheus) (texto, voz, imagem)
- Como monitorar atendimentos
- Como atualizar o FAQ
- Como fazer um broadcast
- Como interpretar os relatórios

**Dias 2 a 15 — Período de acompanhamento**
- Suporte prioritário via WhatsApp para qualquer dúvida
- Check-in diário nos primeiros 3 dias
- Check-in semanal nos dias 7 e 15

**Após o dia 15 — Suporte padrão**
- WhatsApp disponível em horário comercial
- Resposta em até 2 horas para questões não urgentes

**Material de apoio:**
- Este manual (sempre atualizado)
- Vídeos gravados dos fluxos principais (enviados por WhatsApp)
- Acesso ao suporte técnico pelo WhatsApp

---

*Manual do Sistema v2.7 — Abril 2026*
*Kairós Intelligence para Clínicas*
*Para suporte: [número do suporte]*
