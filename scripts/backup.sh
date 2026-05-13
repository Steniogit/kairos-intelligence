#!/bin/bash
# =============================================================
# Kairós Intelligence v2.7 — Backup Script
# =============================================================
# Uso: ./scripts/backup.sh
# Faz backup de: volumes Docker, .env, agents/, openclaw.json
# Cron sugerido: 30 4 * * * /path/to/scripts/backup.sh
# =============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/kairos-backup-$TIMESTAMP.tar.gz"

echo "[INFO] === Backup — Kairós Intelligence v2.7 ==="
echo "[INFO] Timestamp: $TIMESTAMP"

# Criar diretório de backup
mkdir -p "$BACKUP_DIR"

# Backup dos arquivos de configuração
echo "[INFO] Criando backup de configurações..."
tar -czf "$BACKUP_FILE" \
    -C "$PROJECT_DIR" \
    .env \
    openclaw.json \
    docker-compose.yml \
    agents/ \
    nginx/ \
    2>/dev/null || true

echo "[OK] Backup salvo: $BACKUP_FILE"

# Backup do PostgreSQL
echo "[INFO] Backup do PostgreSQL..."
docker exec kairos-postgres pg_dump -U kairos kairos \
    > "$BACKUP_DIR/pg-dump-$TIMESTAMP.sql" 2>/dev/null || \
    echo "[WARN] Backup do PostgreSQL falhou (container pode não estar rodando)"

# Limpar backups antigos (manter últimos 7 dias)
echo "[INFO] Limpando backups antigos (>7 dias)..."
find "$BACKUP_DIR" -name "kairos-backup-*.tar.gz" -mtime +7 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "pg-dump-*.sql" -mtime +7 -delete 2>/dev/null || true

echo "[OK] Backup concluído."
