#!/bin/bash
# =============================================================
# Kairós Intelligence v2.7 — Health Check
# =============================================================
# Uso: ./scripts/health-check.sh
# Verifica: containers rodando, portas acessíveis, logs sem erro
# =============================================================

set -euo pipefail

ERRORS=0

echo "[INFO] === Health Check — Kairós Intelligence v2.7 ==="
echo ""

# --- Verificar containers ---
echo "[INFO] Verificando containers..."

SERVICES=("kairos-evolution" "kairos-openclaw" "kairos-redis" "kairos-postgres" "kairos-minio" "kairos-nginx")

for svc in "${SERVICES[@]}"; do
    STATUS=$(docker inspect -f '{{.State.Status}}' "$svc" 2>/dev/null || echo "not_found")
    if [ "$STATUS" = "running" ]; then
        echo "  [OK] $svc — running"
    else
        echo "  [!] $svc — $STATUS"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# --- Verificar portas ---
echo "[INFO] Verificando portas..."

check_port() {
    local name=$1
    local port=$2
    if nc -z localhost "$port" 2>/dev/null || curl -s -o /dev/null -w "" "http://localhost:$port" 2>/dev/null; then
        echo "  [OK] $name — porta $port acessível"
    else
        echo "  [!] $name — porta $port INACESSÍVEL"
        ERRORS=$((ERRORS + 1))
    fi
}

check_port "Evolution Go" 8080
check_port "OpenClaw" 18789
check_port "Redis" 6379
check_port "PostgreSQL" 5432
check_port "MinIO" 9000
check_port "Nginx" 80

echo ""

# --- Verificar Nginx health endpoint ---
echo "[INFO] Verificando endpoint /health..."
HEALTH_RESPONSE=$(curl -s http://localhost/health 2>/dev/null || echo "failed")
if echo "$HEALTH_RESPONSE" | grep -q "ok" 2>/dev/null; then
    echo "  [OK] /health retornou OK"
else
    echo "  [!] /health falhou: $HEALTH_RESPONSE"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# --- Verificar logs recentes por erros ---
echo "[INFO] Verificando logs por erros críticos..."
for svc in "${SERVICES[@]}"; do
    ERROR_COUNT=$(docker logs --since=5m "$svc" 2>&1 | grep -ciE "(fatal|panic|critical)" || true)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "  [!] $svc — $ERROR_COUNT erros críticos nos últimos 5 min"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# --- Resultado ---
if [ $ERRORS -eq 0 ]; then
    echo "[OK] === Todos os serviços saudáveis ==="
    exit 0
else
    echo "[!] === $ERRORS problemas detectados ==="
    exit 1
fi
