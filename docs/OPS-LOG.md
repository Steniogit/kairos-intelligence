# Kairós Intelligence — Operações de Infraestrutura

## 2026-05-29 — Correção de Acessibilidade dos Painéis

### Problema
Os painéis de controle do Evolution Go e Paperclip não estavam acessíveis externamente via HTTPS na VPS Hostinger.

### Causa Raiz
1. **Isolamento de rede Docker**: O Traefik (reverse proxy) estava na rede `host`, enquanto os containers Kairós estavam na rede bridge `kairos-net`. O Traefik descobria os containers via Docker socket (labels corretas), mas não conseguia rotear tráfego porque não compartilhava a mesma rede.
2. **Container conflitante**: Existia um segundo Paperclip (`paperclip-nvpa-paperclip-1`) instalado via catálogo Hostinger que conflitava com o `kairos-paperclip` e gerava erros de certificado SSL.

### Correções Aplicadas
1. Conectado Traefik à rede `kairos-net` via `docker network connect`
2. Recriados containers `evolution-go`, `openclaw`, `paperclip`, `dashboard` com `--force-recreate`
3. Removido container `paperclip-nvpa-paperclip-1` e sua rede `paperclip-nvpa_default`

### Verificação
Todos os testes passaram com HTTP 200:

| Serviço | Interno | Externo (HTTPS) |
|---------|---------|-----------------|
| Evolution Go | ✅ 200 | ✅ 200 |
| Paperclip | ✅ 200 | ✅ 200 |
| OpenClaw | — | ✅ 200 |
| Dashboard | — | ✅ 200 |

### URLs de Acesso
- Evolution Go: https://evolution.srv1652132.hstgr.cloud
- Paperclip: https://paperclip.srv1652132.hstgr.cloud
- OpenClaw: https://kairos.srv1652132.hstgr.cloud
- Dashboard: https://dashboard.srv1652132.hstgr.cloud
- Paperclip Swagger: https://paperclip.srv1652132.hstgr.cloud/docs
