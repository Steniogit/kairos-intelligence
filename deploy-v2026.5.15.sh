#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Kairós Intelligence — Script de Deploy v2026.5.15
# Executa na VPS (rede estável de datacenter)
# ═══════════════════════════════════════════════════════════

set -e

echo "╔══════════════════════════════════════════╗"
echo "║  Kairós Intelligence — Deploy v2026.5.15 ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# 1. Pull das imagens atualizadas
echo "🔄 [1/4] Puxando imagem OpenClaw v2026.5.15..."
docker compose pull openclaw
echo "✅ Imagem atualizada!"
echo ""

# 2. Rebuild do Paperclip (backend com novos endpoints)
echo "🔨 [2/4] Rebuild do Paperclip (novos endpoints de telemetria)..."
docker compose build paperclip
echo "✅ Paperclip reconstruído!"
echo ""

# 3. Rebuild do Dashboard (nova seção Reasoning Health)
echo "🎨 [3/4] Rebuild do Dashboard (Reasoning Health)..."
docker compose build dashboard
echo "✅ Dashboard reconstruído!"
echo ""

# 4. Restart dos serviços afetados
echo "🚀 [4/4] Reiniciando serviços..."
docker compose up -d openclaw paperclip dashboard
echo ""

# Validação
echo "═══════════════════════════════════════════"
echo "📋 Status dos containers:"
docker compose ps openclaw paperclip dashboard
echo ""
echo "🔍 Verificando versão do OpenClaw..."
docker compose exec openclaw openclaw --version 2>/dev/null || echo "  (verificar manualmente)"
echo ""
echo "🏥 Verificando endpoint de Reasoning Health..."
sleep 3
curl -s http://localhost:3000/api/system/reasoning-health | python3 -m json.tool 2>/dev/null || echo "  Aguardando Paperclip inicializar..."
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅ Deploy concluído com sucesso!        ║"
echo "╚══════════════════════════════════════════╝"
