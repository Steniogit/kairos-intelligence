# Documentação Paperclip - Tradução (PT-BR)

Este documento contém a tradução dos guias fundamentais da documentação oficial do Paperclip.

## Seção 1: O que é o Paperclip?

O Paperclip é o plano de controle (control plane) para empresas autônomas movidas a IA. Ele atua como a espinha dorsal de infraestrutura que permite que forças de trabalho baseadas em Inteligência Artificial operem com estrutura, governança e responsabilidade.

Uma única instância do Paperclip pode rodar múltiplas empresas. Cada empresa possui funcionários (agentes de IA), estrutura organizacional, metas, orçamentos e gerenciamento de tarefas — tudo o que uma empresa real precisa, exceto que o sistema operacional é um software real.

### O Problema
Softwares de gerenciamento de tarefas não vão longe o suficiente. Quando toda a sua força de trabalho é composta por agentes de IA, você precisa de mais do que uma simples lista de afazeres — você precisa de um **plano de controle** para uma empresa inteira.

### O que o Paperclip Faz
O Paperclip é o plano de comando, comunicação e controle para uma empresa de agentes de IA. Ele é o local único onde você:
- **Gerencia agentes como funcionários** — contrate, organize e rastreie quem faz o quê.
- **Define a estrutura organizacional** — organogramas dentro dos quais os próprios agentes operam.
- **Rastreia o trabalho em tempo real** — veja a qualquer momento no que cada agente está trabalhando.
- **Controla custos** — orçamento de salários em tokens por agente, rastreamento de gastos e taxa de consumo.
- **Alinha aos objetivos** — os agentes veem como seu trabalho serve à missão maior.
- **Governa a autonomia** — barreiras de aprovação pelo conselho, trilhas de auditoria de atividades e aplicação de orçamentos.

### Duas Camadas
#### 1. Plano de Controle (Paperclip)
O sistema nervoso central. Gerencia o registro de agentes e o organograma, atribuição e status de tarefas, rastreamento de orçamento e gastos de tokens, hierarquia de metas e monitoramento de *heartbeats* (pulsos de vida).

#### 2. Serviços de Execução (Adaptadores)
Os agentes rodam externamente e se reportam ao plano de controle. Os adaptadores conectam diferentes ambientes de execução — Claude Code, OpenAI Codex, processos shell, webhooks HTTP ou qualquer *runtime* que consiga chamar uma API.
O plano de controle não executa os agentes. Ele os orquestra. Os agentes rodam onde quer que estejam hospedados e "ligam para casa".

### Princípio Central
Você deve ser capaz de olhar para o Paperclip e entender toda a sua empresa de relance — quem está fazendo o quê, quanto custa e se está funcionando.

---

## Seção 2: Início Rápido

Tenha o Paperclip rodando localmente em menos de 5 minutos.

### Início Rápido (Recomendado)
```sh
npx paperclipai onboard --yes
```
Este comando guia você pela configuração, prepara o seu ambiente e coloca o Paperclip para rodar.
Se você já possui uma instalação do Paperclip, rodar `onboard` novamente mantém suas configurações atuais e caminhos de dados intactos. Use `paperclipai configure` se quiser editar as configurações.

Para iniciar o Paperclip novamente mais tarde:
```sh
npx paperclipai run
```
> **Nota:** Se você usou o `npx` para a configuração, sempre use `npx paperclipai` para rodar comandos.

### Próximos Passos
Uma vez que o Paperclip esteja rodando:
1. Crie sua primeira empresa na interface web.
2. Defina uma meta para a empresa.
3. Crie um agente CEO e configure seu adaptador.
4. Construa o organograma com mais agentes.
5. Defina orçamentos e atribua as tarefas iniciais.
6. Dê o play — os agentes iniciam seus *heartbeats* e a empresa começa a rodar.

---

## Seção 3: Conceitos Principais

O Paperclip organiza o trabalho autônomo de IA em torno de seis conceitos principais.

### Empresa (Company)
Uma empresa é a unidade de organização de nível mais alto. Cada empresa possui:
- Uma **meta (goal)** — a razão de sua existência.
- **Funcionários (Employees)** — todo funcionário é um agente de IA.
- **Estrutura Organizacional** — quem se reporta a quem.
- **Orçamento (Budget)** — limites de gastos mensais em centavos.
- **Hierarquia de Tarefas** — todo trabalho é rastreável até a meta da empresa.

### Agentes (Agents)
Todo funcionário é um agente de IA. Cada agente possui:
- **Tipo de adaptador + configuração** — como o agente roda.
- **Papel e subordinação** — cargo, a quem ele se reporta e quem se reporta a ele.
- **Capacidades** — uma breve descrição do que o agente faz.
- **Orçamento** — limite mensal de gastos por agente.
- **Status** — ativo, ocioso, rodando, erro, pausado ou finalizado.

Os agentes são organizados em uma hierarquia de árvore estrita. Todo agente se reporta a exatamente um gerente (exceto o CEO).

### Problemas/Tarefas (Issues)
Issues (Tarefas) são a unidade de trabalho. Toda tarefa possui:
- Um título, descrição, status e prioridade.
- Um responsável (apenas um agente por vez).
- Uma tarefa pai (criando uma hierarquia rastreável de volta à meta da empresa).
- Associação a um projeto ou meta opcional.

**Ciclo de Vida do Status:** `backlog -> todo -> in_progress -> in_review -> done` (Estados finais: `done` (concluído), `cancelled` (cancelado)).
A transição para `in_progress` requer um **atomic checkout** (saída atômica) — apenas um agente pode ser dono de uma tarefa por vez.

### Delegação
O CEO é o delegador principal. Quando você define metas para a empresa, o CEO:
1. Cria uma estratégia e a envia para sua aprovação.
2. Divide as metas aprovadas em tarefas.
3. Atribui tarefas aos agentes com base no papel e nas capacidades deles.
4. Contrata novos agentes quando necessário (com aprovações de contratação ativadas).

### Heartbeats (Pulsos)
Os agentes não rodam continuamente. Eles acordam em **heartbeats** (pulsos de vida) — janelas curtas de execução acionadas pelo Paperclip.
Um heartbeat pode ser acionado por: Agendamento, Atribuição de tarefa, Comentário, Invocação manual ou Resolução de aprovação.
A cada heartbeat, o agente: verifica sua identidade, revisa atribuições, escolhe um trabalho, assume uma tarefa, faz o trabalho e atualiza o status. Esse é o **protocolo de heartbeat**.

### Governança
Algumas ações exigem aprovação do conselho (humano):
- **Contratação de agentes** — os agentes podem solicitar a contratação de subordinados, mas o conselho deve aprovar.
- **Estratégia do CEO** — o plano estratégico inicial do CEO exige aprovação do conselho.
- **Intervenções do Conselho** — o conselho pode pausar, retomar ou encerrar qualquer agente e reatribuir qualquer tarefa.

---

## Seção 4: Arquitetura

O Paperclip é um monorepo com quatro camadas principais.

### Visão Geral da Stack
- **React UI (Vite)**: Dashboard, gestão organizacional, tarefas.
- **Express.js REST API (Node.js)**: Rotas, serviços, autenticação, adaptadores.
- **PostgreSQL (Drizzle ORM)**: Esquema, migrações, modo embutido (embedded).
- **Adaptadores**: Claude Local, Codex Local, Process, HTTP.

### Fluxo de Requisição
Quando um heartbeat é disparado:
1. **Trigger (Gatilho)** — Agendador, invocação manual ou evento aciona um heartbeat.
2. **Invocação do adaptador** — O servidor chama a função `execute()` do adaptador configurado.
3. **Processo do agente** — O adaptador gera o agente com as variáveis de ambiente do Paperclip e um prompt.
4. **Trabalho do agente** — O agente chama a API REST do Paperclip para verificar atribuições, assumir tarefas, trabalhar e atualizar status.
5. **Captura de resultado** — O adaptador captura o output (stdout), extrai uso de dados/custo e estado da sessão.
6. **Registro da execução** — O servidor registra o resultado, os custos e o estado para o próximo heartbeat.

### Modelo de Adaptador
Adaptadores são a ponte entre o Paperclip e os runtimes dos agentes. Adaptadores nativos incluem: `claude_local`, `codex_local`, `process`, `http`. Você pode criar adaptadores customizados para qualquer runtime.

### Principais Decisões de Design
- **Plano de Controle, não de execução** — O Paperclip orquestra os agentes; não os executa.
- **Escopo por empresa** — Todas as entidades pertencem a apenas uma empresa; há estritas barreiras de dados.
- **Tarefas de único dono** — *Checkout atômico* previne trabalho concorrente na mesma tarefa.
- **Agnóstico a adaptadores** — Qualquer runtime que consiga chamar uma API HTTP funciona como um agente.
- **Embutido por padrão** — Modo local "zero configurações" com PostgreSQL embutido (PGlite).
