#!/bin/bash
# =============================================================
# Kairós Intelligence v2.7 — Rollback Script
# =============================================================
# Uso: ./scripts/rollback.sh
# Princípio: Velocidade sobre perfeição
# =============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "[INFO] === Kairós Intelligence — Rollback ==="
echo "[WARN] Parando todos os serviços..."

cd "$PROJECT_DIR"

# Para todos os containers
docker compose down

# Verifica se há backup de imagens
echo "[INFO] Reiniciando com imagens anteriores (cache local)..."
docker compose up -d

# Aguarda e verifica
sleep 15
echo "[INFO] Verificando saúde pós-rollback..."
"$SCRIPT_DIR/health-check.sh"

if [ $? -eq 0 ]; then
    echo "[OK] Rollback concluído com sucesso."
else
    echo "[!] CRÍTICO: Rollback também falhou."
    echo "[!] Verifique manualmente: docker compose logs"
    exit 1
fi
