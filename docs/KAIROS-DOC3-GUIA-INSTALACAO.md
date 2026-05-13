> **Kairós Intelligence v2.7** | Stack: Evolution Go · OpenClaw · Paperclip · DeepSeek-V4 Flash · Gemini 3.1 · Redis · GraphRAG · Crawl4AI · Google TTS Journey
> Atualizado em 04/05/2026 — Arquitetura Híbrida + Segundo Cérebro (kairos-brain).

# GUIA DE INSTALAÇÃO
## Passo a Passo Técnico — Do Zero ao Sistema em Produção
**Kairós Intelligence v2.7**

---

> **PRÉ-REQUISITOS**
>
> - Briefing do cliente preenchido (Documento 4)
> - Credenciais técnicas coletadas via formulário seguro
> - Número WhatsApp Business verificado na Meta
> - Acesso ao banco de dados da clínica
> - Conhecimento básico de terminal/linha de comando
> - Antigravity/Codex instalado (para geração do código)

---

## FASE 0 — PREPARAÇÃO

### 0.1 Checklist de credenciais antes de começar

Confirme que você tem em mãos:

☐ Token de acesso permanente da Meta
☐ Phone Number ID da Meta
☐ WhatsApp Business Account ID
☐ Chave API DeepSeek (chat/extração)
☐ Chave API Gemini (visão, áudio, TTS)
☐ Chave API Google Cloud TTS Journey (voz premium)
☐ Chave API Kairós Mestra (cascata BYOK)
☐ URL + login + senha do sistema Ademed
☐ Chave API SendGrid + email verificado
☐ Token Zenvia + número remetente
☐ Chave API OpenAI (fallback BYOK)
☐ Acesso ao repositório GitHub: `kairos-brain`

### 0.2 Clonar o repositório kairos-brain

O repositório `kairos-brain` é o **Segundo Cérebro** do Kairós Intelligence.
Contém todos os prompts, skills, configurações e scripts versionados.

```bash
# Clonar o repositório principal
git clone https://github.com/seu-usuario/kairos-brain.git

# Acessar o diretório
cd kairos-brain

# Verificar estrutura
ls -la
# Deve mostrar: MAP.md, README.md, VERSION.md, .env.example,
# docker-compose.yml, agents/, scripts/, logs/

# Copiar e configurar variáveis de ambiente
cp .env.example .env
nano .env  # Preencher com credenciais reais
```

### 0.3 Ferramentas necessárias na sua máquina local

```bash
# Verificar se tem Python 3.11+
python3 --version

# Verificar se tem Git
git --version

# Verificar se tem Docker
docker --version

# Verificar se tem SSH client
ssh --version
```

---

## FASE 1 — VPS HOSTINGER

### 1.1 Contratar o VPS

1. Acesse: hostinger.com.br
2. Menu: VPS Hosting → **KVM 2** (2 vCPU, 8GB RAM)
3. Sistema operacional: **Ubuntu 22.04 LTS**
4. Localização do servidor: **São Paulo, Brasil**
5. Conclua o pagamento

### 1.2 Configuração inicial do servidor

Acesse o terminal via painel da Hostinger (ou SSH):

```bash
# Atualizar o sistema
sudo apt update && sudo apt upgrade -y

# Instalar ferramentas essenciais
sudo apt install -y curl wget git ufw fail2ban

# Configurar firewall básico
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 18789  # OpenClaw gateway
sudo ufw allow 8000   # Evolution Go
sudo ufw enable

# Criar usuário dedicado para OpenClaw
sudo adduser openclaw
sudo usermod -aG sudo openclaw
```

### 1.3 Configurar SSH com chave (desabilitar senha)

Na sua máquina local:
```bash
# Gerar par de chaves SSH (se não tiver)
ssh-keygen -t ed25519 -C "openclaw-clinica"

# Copiar chave pública para o servidor
ssh-copy-id openclaw@[IP-DO-VPS]
```

No servidor:
```bash
# Desabilitar autenticação por senha
sudo nano /etc/ssh/sshd_config
# Alterar: PasswordAuthentication no
sudo systemctl restart ssh
```

⚠️ **Guarde a chave SSH privada em local seguro offline (pen drive).**
**Esta é sua chave de acesso de emergência.**

### 1.4 Instalar Node.js 24

```bash
# Via NodeSource
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt install -y nodejs

# Verificar
node --version  # deve mostrar v24.x.x
npm --version
```

### 1.5 Instalar Docker

```bash
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker openclaw

# Fazer logout e login novamente para aplicar o grupo
exit
# reconectar via SSH
```

### 1.6 Instalar Python 3.11

```bash
sudo apt install -y python3.11 python3.11-pip python3.11-venv
python3.11 --version
```

### 1.7 Configurar domínio e SSL

1. No painel da Hostinger: aponte um subdomínio para o IP do VPS
   - Exemplo: `bot.suaclinica.com.br` → IP do VPS
2. Instalar Certbot:
```bash
sudo apt install -y certbot
sudo certbot certonly --standalone -d bot.suaclinica.com.br
```

---

## FASE 2 — TAILSCALE (REDE PRIVADA) + DEPENDÊNCIAS DE EXTRAÇÃO

### 2.1 Instalar Tailscale no VPS

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Acesse o link exibido no terminal para autenticar.

### 2.2 Instalar na sua máquina local

Acesse: https://tailscale.com/download
Instale para o seu sistema operacional e faça login com a mesma conta.

### 2.3 Verificar conexão

```bash
# No VPS, verificar IP Tailscale
tailscale ip -4
# Anote este IP — você vai precisar para acessar o OpenClaw remotamente
```

### 2.4 Instalar dependências da Arquitetura Híbrida (Crawl4AI + Playwright)

A v2.7 usa **Crawl4AI** para leitura rápida e **Playwright** para escrita no Ademed.
Ambas as dependências precisam ser instaladas no VPS.

```bash
# Ativar ambiente virtual Python (recomendado)
python3.11 -m venv ~/kairos-venv
source ~/kairos-venv/bin/activate

# Instalar Crawl4AI e Playwright juntos
pip install crawl4ai playwright

# Instalar o browser Chromium para o Playwright
playwright install chromium

# Verificar instalações
python3 -c "import crawl4ai; print('Crawl4AI OK')"
python3 -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"

# Instalar dependências do sistema necessárias para o Chromium
playwright install-deps chromium
```

> **Por que Chromium especificamente?**
> O Chromium é o menor dos browsers suportados pelo Playwright (~200MB vs ~500MB do Firefox).
> Suficiente para todas as operações no ADMED v2.02.

### 2.5 Testar acesso ao Ademed (Playwright)

```bash
# Teste básico de login no Ademed
python3 scripts/test-admed-login.py
```

Saída esperada:
```
✅ Playwright: OK
✅ Crawl4AI: OK
✅ Login no Ademed: OK
✅ Sessão PHPSESSID: [valor do cookie]
✅ Compartilhamento de sessão: OK
```

---

## FASE 3 — CONFIGURAR META BUSINESS API

### 3.1 Criar app no Meta for Developers

1. Acesse: developers.facebook.com
2. Clique em "Meus Apps" → "Criar App"
3. Tipo: **Business**
4. Preencha nome e e-mail de contato
5. Na página do app: adicione o produto **WhatsApp**

### 3.2 Configurar número de telefone

1. Em WhatsApp → Configuração:
2. Clique em "Adicionar número de telefone"
3. Siga o processo de verificação com o número da clínica
4. Anote: **Phone Number ID** e **WhatsApp Business Account ID**

### 3.3 Gerar token permanente

1. Em Configurações → Avançado → Tokens de acesso do sistema
2. Crie um "Usuário do sistema" com permissão de administrador
3. Gere o token → **copie e guarde em local seguro**

### 3.4 Configurar webhook

A URL do webhook será configurada após a Evolution Go estar no ar (Fase 5).

### 3.5 Rate limit — informação importante

Conta nova começa com **1.000 conversas únicas por dia** que você inicia.
O limite sobe automaticamente:
- Após 7 dias com bom uso: 10.000/dia
- Após 30 dias: 100.000/dia

Para uma clínica com até 200 atendimentos/dia, o limite inicial é suficiente.
Monitore pelo Meta Business Manager: WhatsApp Manager → Insights → Limites.

---

## FASE 4 — INSTALAR E CONFIGURAR O OPENCLAW

### 4.1 Instalar OpenClaw

```bash
# Mudar para o usuário openclaw
su - openclaw

# Instalar OpenClaw globalmente
npm i -g openclaw@latest

# Verificar instalação
openclaw --version
```

### 4.2 Criar estrutura de diretórios

```bash
mkdir -p ~/.openclaw
mkdir -p ~/workspace-master
mkdir -p ~/workspace-atendimento
mkdir -p ~/workspace-clinico
mkdir -p ~/workspace-notificacoes
mkdir -p ~/workspace-sincronizador
mkdir -p ~/openclaw-backups
mkdir -p ~/logs
```

### 4.3 Configurar variáveis de ambiente

```bash
# Criar arquivo de variáveis de ambiente
nano ~/.openclaw/.env
```

Adicione (substituindo pelos valores reais):
```env
# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI (fallback)
OPENAI_API_KEY=sk-...

# Meta WhatsApp
META_TOKEN=...
META_PHONE_NUMBER_ID=...
META_BUSINESS_ACCOUNT_ID=...
META_WEBHOOK_VERIFY_TOKEN=escolha-uma-senha-aleatoria

# Google TTS
GOOGLE_APPLICATION_CREDENTIALS=/home/openclaw/.gcp/credentials.json

# SendGrid
SENDGRID_API_KEY=SG....
SENDGRID_FROM_EMAIL=bot@suaclinica.com.br

# Zenvia
ZENVIA_TOKEN=...
ZENVIA_FROM_NUMBER=...

# Sistema da clínica (browser via Playwright)
SISTEMA_URL=https://admedsistemas.com.br/demo
SISTEMA_USER=STENIO
SISTEMA_PASS=...
SISTEMA_UNIDADE=DEMO

# OpenClaw gateway
OPENCLAW_GATEWAY_PASSWORD=escolha-uma-senha-forte

# Recepcionista (notificações)
RECEPCIONISTA_WHATSAPP=+5561999999999
```

### 4.4 Implantar os arquivos gerados pelo Antigravity/Codex

```bash
# Clonar o repositório gerado pelo Antigravity/Codex
git clone https://github.com/[seu-usuario]/[nome-do-repo].git ~/projeto

# Copiar configuração principal
cp ~/projeto/openclaw.json ~/.openclaw/openclaw.json

# Copiar workspaces dos agentes
cp ~/projeto/workspaces/master/* ~/workspace-master/
cp ~/projeto/workspaces/atendimento/* ~/workspace-atendimento/
cp ~/projeto/workspaces/clinico/* ~/workspace-clinico/
cp ~/projeto/workspaces/notificacoes/* ~/workspace-notificacoes/
cp ~/projeto/workspaces/sincronizador/* ~/workspace-sincronizador/

# Copiar scripts
cp ~/projeto/scripts/* ~/scripts/
chmod +x ~/scripts/*.sh
```

### 4.5 Executar onboarding do OpenClaw

```bash
openclaw onboard --install-daemon
```

Durante o onboarding:
- Modelo: `anthropic/DeepSeek-V4 Flash`
- **NÃO conecte nenhum canal ainda** — a Evolution Go faz isso
- **NÃO instale skills agora** — serão instaladas pelo script de deploy

### 4.6 Verificar instalação

```bash
openclaw doctor
openclaw sandbox explain
openclaw status
```

---

## FASE 5 — BRIDGE FASTAPI

A Evolution Go é o serviço intermediário entre a Meta e o OpenClaw.

### 5.1 Instalar dependências

```bash
cd ~/projeto/bridge

python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5.2 Iniciar com Docker

```bash
cd ~/projeto/bridge
docker-compose up -d

# Verificar se está rodando
docker ps
curl http://localhost:8000/health
```

### 5.3 Configurar webhook na Meta

Agora que a Bridge está no ar, configure o webhook:

1. No painel Meta for Developers: WhatsApp → Configuração → Webhook
2. URL de callback: `https://bot.suaclinica.com.br/webhook/whatsapp`
3. Token de verificação: o valor de `META_WEBHOOK_VERIFY_TOKEN` do seu .env
4. Clique em "Verificar e salvar"
5. Assine os campos: `messages`

### 5.4 Testar o webhook

```bash
# Envie uma mensagem de teste para o número da clínica pelo seu celular
# Verifique os logs da Bridge:
docker logs bridge_fastapi -f
```

---

## FASE 6 — SERVIÇOS DE VOZ E COMUNICAÇÃO

### 6.1 Google TTS

1. Acesse: console.cloud.google.com
2. Crie um projeto ou selecione um existente
3. Ative a API: Cloud Text-to-Speech API
4. Crie uma conta de serviço e baixe as credenciais JSON
5. Salve em: `/home/openclaw/.gcp/credentials.json`
6. Defina a variável de ambiente (já configurada no .env)

### 6.2 Gemini Audio

Já incluído na chave API da OpenAI. Nenhuma configuração adicional necessária.

### 6.3 SendGrid

1. Acesse: sendgrid.com → crie uma conta gratuita
2. Vá em Settings → API Keys → Create API Key
3. Verificar o e-mail remetente: Settings → Sender Authentication
4. Adicione a chave e o e-mail no .env

### 6.4 Zenvia

1. Acesse: zenvia.com → crie uma conta
2. Gere um token de API no painel
3. Configure o número remetente
4. Adicione ao .env

---

## FASE 7 — UPROTIME ROBOT (MONITORAMENTO)

### 7.1 Criar conta

1. Acesse: uptimerobot.com → crie conta gratuita

### 7.2 Adicionar monitor

1. Clique em "Add New Monitor"
2. Tipo: HTTP(s)
3. URL: `https://bot.suaclinica.com.br/health`
4. Intervalo: 5 minutos
5. Alertas: e-mail + SMS (configure seu número)

⚠️ **Configure isso ANTES de qualquer outra coisa.** Se o servidor cair, você precisa saber antes dos pacientes.

---

## FASE 8 — ACESSO AO SISTEMA DA CLÍNICA (ADMED)

### Nota sobre o MVP

No MVP, o Manager (Agente 3) acessa o ADMED exclusivamente via browser (Playwright).
**Não há configuração de banco de dados necessária.**

Apenas as credenciais de login do ADMED precisam ser configuradas no `.env`:

```env
SISTEMA_URL=https://admedsistemas.com.br/demo
SISTEMA_USER=STENIO
SISTEMA_PASS=sua-senha
SISTEMA_UNIDADE=DEMO
```

### Verificar acesso ao ADMED

```bash
# Testar login no ADMED via Playwright
python3 scripts/test-admed-login.py
```

Saída esperada:
```
✅ Login no ADMED: OK
✅ Sessão ativa: OK
✅ Página da agenda carregada: OK
```

### Versão futura — Banco de dados direto

Quando o volume justificar maior velocidade, configure um usuário
SQL dedicado com permissões de leitura apenas. Consulte o suporte
técnico para esse procedimento.

---

## FASE 9 — DEPLOY COMPLETO

### 9.1 Executar script de deploy

```bash
chmod +x ~/scripts/deploy.sh
~/scripts/deploy.sh
```

O script executa:
1. ✅ Copia todos os arquivos para os lugares certos
2. ✅ Configura variáveis de ambiente
3. ✅ Instala skills do OpenClaw
4. ✅ Configura cron jobs (backup, update, auditoria, sincronizador)
5. ✅ Inicia todos os serviços
6. ✅ Roda smoke tests

### 9.2 Verificar saúde completa

```bash
~/scripts/smoke-test.sh
```

Saída esperada:
```
✅ Claude API: OK
✅ Banco de dados: OK
✅ Evolution Go: OK
✅ Paperclip (Control Plane): OK
✅ Prometheus (Agente Prometheus): ONLINE
✅ Agente Atendimento: ONLINE
✅ Agente Clínico: ONLINE
✅ Agente Notificações: ONLINE
✅ Agente Sincronizador: ONLINE
✅ Meta webhook: VERIFICADO
✅ Google TTS: OK
✅ SendGrid: OK
✅ Tailscale: CONECTADO

🎉 Sistema 100% operacional!
```

---

## FASE 10 — TESTES PRÉ-PRODUÇÃO

### 10.1 Executar testes de fluxo completos

```bash
~/scripts/run-tests.sh
```

### 10.2 Testes manuais obrigatórios

Execute cada teste e confirme o resultado esperado:

**Teste 1: Paciente recorrente**
- Use um número cadastrado no sistema
- Envie "oi" para o WhatsApp Business
- ✅ Esperado: bot reconhece pelo número e confirma nome

**Teste 2: Paciente novo**
- Use um número não cadastrado
- Envie "oi" e siga o fluxo
- Envie uma foto de documento de teste
- ✅ Esperado: bot extrai dados e pede confirmação

**Teste 3: Agendamento completo**
- Solicite agendamento com médico e horário
- ✅ Esperado: bot verifica disponibilidade, agenda e confirma

**Teste 4: Timeout**
- Inicie uma conversa e não responda por 30 minutos
- ✅ Esperado: bot encerra com mensagem amigável

**Teste 5: Fallback do sistema**
- Desconecte temporariamente o acesso ao banco
- Tente agendar pelo bot
- ✅ Esperado: bot avisa instabilidade e notifica recepcionista

**Teste 6: Handoff**
- Faça uma pergunta que o bot não sabe responder duas vezes
- ✅ Esperado: bot escala para recepcionista na segunda tentativa

**Teste 7: Prometheus (Agente Prometheus)**
- Envie mensagem de texto para o Prometheus
- Envie áudio para o Prometheus
- ✅ Esperado: respostas corretas em ambos os formatos

**Teste 8: Broadcast**
- Peça ao Prometheus para enviar uma mensagem de teste para 1 paciente
- ✅ Esperado: Prometheus valida, confirma com você e envia

**Teste 9: Fallback Claude API**
- Temporariamente invalide a chave API do Claude no .env
- Envie mensagem para o bot
- ✅ Esperado: mensagem automática de fallback enviada ao paciente
- Restaure a chave e verifique que o sistema volta ao normal

**Teste 10: Isolamento de imagens**
- No Front-Desk (Agente 2): verifique nos logs que imagens não são armazenadas após processamento

---

## FASE 11 — CONFIGURAÇÕES FINAIS DE PRODUÇÃO

### 11.1 LGPD (OBRIGATÓRIO antes de pacientes reais)

☐ Termo de consentimento implementado no fluxo do Front-Desk (Agente 2)
☐ DPA (Data Processing Agreement) assinado com o cliente
☐ Política de privacidade da clínica publicada e linkada
☐ Mecanismo de opt-out funcionando e testado

⚠️ **Não libere para pacientes reais sem esta etapa concluída.**

### 11.2 Verificações finais

```bash
# Verificar versão do sistema
cat ~/projeto/VERSION.md

# Verificar cron jobs ativos
openclaw cron list

# Verificar backup configurado
ls ~/openclaw-backups/

# Verificar UptimeRobot monitorando
# (verificar no painel uptimerobot.com)
```

### 11.3 Configurar acesso de emergência ao VPS

Documente em local físico seguro (papel):
- IP do VPS
- IP do Tailscale do VPS
- Caminho da chave SSH de emergência
- Senha do gateway OpenClaw
- Contato do suporte técnico

---

## FASE 12 — MANUTENÇÃO

### 12.1 Processo de atualização

Sempre que precisar atualizar o sistema:

```bash
# 1. Gerar arquivos atualizados com o Antigravity/Codex
# 2. Atualizar VERSION.md
# 3. Commit no GitHub
git add .
git commit -m "v1.1.0: Adicionado Dr. Paulo, Ortopedia"
git push

# 4. Smoke tests locais
~/scripts/smoke-test.sh

# 5. Deploy no VPS
~/scripts/deploy.sh

# 6. Smoke tests no VPS
~/scripts/smoke-test.sh

# 7. Se falhar: rollback
~/scripts/rollback.sh
```

### 12.2 Rollback de emergência

```bash
~/scripts/rollback.sh
```

O script restaura automaticamente a versão anterior do GitHub.

### 12.3 Backup manual

```bash
~/scripts/backup.sh
```

### 12.4 Atualização do OpenClaw

```bash
npm update -g openclaw
openclaw doctor
```

*(Ocorre automaticamente todo dia às 4h via cron job)*

---

## DISASTER RECOVERY — RESTAURAÇÃO COMPLETA

**Meta: sistema restaurado em menos de 3 horas.**

### Quando usar este procedimento

- VPS completamente perdido (disco corrompido, problema grave)
- Dados corrompidos sem possibilidade de recuperação

### Passo a passo

**Passo 1 (15 min): Provisionar novo VPS**
- Contratar novo VPS Hostinger KVM 2 com Ubuntu 22.04
- Anotar o novo IP

**Passo 2 (30 min): Instalação base**
- Executar Fases 1 e 2 deste guia (VPS + Tailscale)

**Passo 3 (10 min): Restaurar código**
```bash
git clone https://github.com/[seu-usuario]/[nome-do-repo].git ~/projeto
```

**Passo 4 (15 min): Restaurar credenciais**
- Pegar o documento físico de emergência
- Recriar o arquivo `~/.openclaw/.env` com todas as credenciais

**Passo 5 (30 min): Executar instalação completa**
```bash
~/projeto/scripts/install.sh
```

**Passo 6 (20 min): Reconectar WhatsApp**
- Atualizar a URL do webhook na Meta para o novo IP/domínio

**Passo 7 (20 min): Testes**
```bash
~/scripts/smoke-test.sh
```

**Total estimado: 2 a 3 horas**

---

## REFERÊNCIAS RÁPIDAS

### Comandos úteis do dia a dia

```bash
# Status de todos os agentes
openclaw status

# Ver logs em tempo real
openclaw logs --follow

# Reiniciar um agente específico
openclaw restart [nome-do-agente]

# Ver cron jobs ativos
openclaw cron list

# Executar smoke tests
~/scripts/smoke-test.sh

# Ver versão atual
cat ~/projeto/VERSION.md

# Ver logs da Bridge
docker logs bridge_fastapi --tail 100

# Ver uso de recursos do servidor
htop
df -h
```

### Portas utilizadas

| Serviço | Porta |
|---|---|
| Paperclip (Control Plane) | 18789 |
| Evolution Go | 8000 |
| SSH | 22 |
| Tailscale | (automático) |

### Arquivos importantes

| Arquivo | Localização |
|---|---|
| Configuração OpenClaw | `~/.openclaw/openclaw.json` |
| Variáveis de ambiente | `~/.openclaw/.env` |
| SOUL.md Prometheus | `~/workspace-master/SOUL.md` |
| SOUL.md Atendimento | `~/workspace-atendimento/SOUL.md` |
| Log do Manager (Agente 3) | `~/logs/agente3-actions.log` |
| Backups | `~/openclaw-backups/` |
| Versão do sistema | `~/projeto/VERSION.md` |

---

*Guia de Instalação v1.0 — Abril 2026*
*Kairós Intelligence para Clínicas*
