#!/bin/bash
# =============================================================
# Kairós Intelligence v2.7 — Deploy Script
# =============================================================
# Uso: ./scripts/deploy.sh
# Segue: skill deployment-procedures (5 fases)
# =============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "[INFO] === Kairós Intelligence — Deploy v2.7 ==="
echo "[INFO] Timestamp: $TIMESTAMP"
echo ""

# --- FASE 1: PREPARE ---
echo "[INFO] Fase 1/5: Verificando pré-requisitos..."

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "[!] ERRO: Arquivo .env não encontrado."
    echo "[!] Copie .env.example para .env e preencha."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "[!] ERRO: Docker não instalado."
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo "[!] ERRO: Docker Compose não instalado."
    exit 1
fi

echo "[OK] Pré-requisitos verificados."

# --- FASE 2: BACKUP ---
echo ""
echo "[INFO] Fase 2/5: Criando backup..."
"$SCRIPT_DIR/backup.sh" || echo "[WARN] Backup falhou, continuando..."

# --- FASE 3: DEPLOY ---
echo ""
echo "[INFO] Fase 3/5: Executando deploy..."

cd "$PROJECT_DIR"

# Pull das imagens mais recentes
echo "[INFO] Baixando imagens atualizadas..."
docker compose pull

# Rebuild e restart
echo "[INFO] Reiniciando serviços..."
docker compose up -d --force-recreate --remove-orphans

echo "[OK] Serviços iniciados."

# --- FASE 4: VERIFY ---
echo ""
echo "[INFO] Fase 4/5: Verificando saúde dos serviços..."
sleep 10  # Aguarda startup

"$SCRIPT_DIR/health-check.sh"
HEALTH_EXIT=$?

# --- FASE 5: CONFIRM ou ROLLBACK ---
echo ""
if [ $HEALTH_EXIT -eq 0 ]; then
    echo "[OK] === Deploy concluído com sucesso! ==="
    echo "[INFO] Versão: $(cat $PROJECT_DIR/VERSION.md)"
    echo "[INFO] Timestamp: $TIMESTAMP"
    echo ""
    echo "[INFO] Monitore os logs com: docker compose logs -f"
else
    echo "[!] === FALHA NO HEALTH CHECK ==="
    echo "[!] Considere executar rollback: ./scripts/rollback.sh"
    exit 1
fi
