#!/bin/bash
# =============================================================
# Kairós Intelligence v2.7 — Smoke Test
# =============================================================
# Uso: ./scripts/smoke-test.sh
# Testes pós-deploy para validar funcionalidade básica
# =============================================================

set -euo pipefail

ERRORS=0

echo "[INFO] === Smoke Test — Kairós Intelligence v2.7 ==="
echo ""

# --- 1. Evolution Go API ---
echo "[INFO] Teste 1: Evolution Go API..."
EVOLUTION_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "apikey: ${EVOLUTION_API_KEY:-test}" \
    http://localhost:8080/instance/fetchInstances 2>/dev/null || echo "000")

if [ "$EVOLUTION_RESPONSE" = "200" ] || [ "$EVOLUTION_RESPONSE" = "401" ]; then
    echo "  [OK] Evolution Go respondendo (HTTP $EVOLUTION_RESPONSE)"
else
    echo "  [!] Evolution Go não respondeu (HTTP $EVOLUTION_RESPONSE)"
    ERRORS=$((ERRORS + 1))
fi

# --- 2. OpenClaw WebSocket ---
echo "[INFO] Teste 2: OpenClaw Control Plane..."
OPENCLAW_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    http://localhost:18789/ 2>/dev/null || echo "000")

if [ "$OPENCLAW_RESPONSE" != "000" ]; then
    echo "  [OK] OpenClaw respondendo (HTTP $OPENCLAW_RESPONSE)"
else
    echo "  [!] OpenClaw não respondeu"
    ERRORS=$((ERRORS + 1))
fi

# --- 3. Redis PING ---
echo "[INFO] Teste 3: Redis PING..."
REDIS_PONG=$(docker exec kairos-redis redis-cli PING 2>/dev/null || echo "FAIL")
if [ "$REDIS_PONG" = "PONG" ]; then
    echo "  [OK] Redis respondendo PONG"
else
    echo "  [!] Redis não respondeu ($REDIS_PONG)"
    ERRORS=$((ERRORS + 1))
fi

# --- 4. PostgreSQL ---
echo "[INFO] Teste 4: PostgreSQL..."
PG_RESULT=$(docker exec kairos-postgres pg_isready 2>/dev/null || echo "FAIL")
if echo "$PG_RESULT" | grep -q "accepting connections"; then
    echo "  [OK] PostgreSQL aceitando conexões"
else
    echo "  [!] PostgreSQL não está pronto ($PG_RESULT)"
    ERRORS=$((ERRORS + 1))
fi

# --- 5. MinIO ---
echo "[INFO] Teste 5: MinIO..."
MINIO_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    http://localhost:9000/minio/health/live 2>/dev/null || echo "000")

if [ "$MINIO_RESPONSE" = "200" ]; then
    echo "  [OK] MinIO saudável"
else
    echo "  [!] MinIO não respondeu (HTTP $MINIO_RESPONSE)"
    ERRORS=$((ERRORS + 1))
fi

# --- 6. Nginx Health ---
echo "[INFO] Teste 6: Nginx /health..."
NGINX_RESPONSE=$(curl -s http://localhost/health 2>/dev/null || echo "FAIL")
if echo "$NGINX_RESPONSE" | grep -q "ok"; then
    echo "  [OK] Nginx /health OK"
else
    echo "  [!] Nginx /health falhou ($NGINX_RESPONSE)"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# --- Resultado ---
if [ $ERRORS -eq 0 ]; then
    echo "[OK] === Todos os smoke tests passaram (6/6) ==="
    exit 0
else
    PASSED=$((6 - ERRORS))
    echo "[!] === $PASSED/6 testes passaram, $ERRORS falharam ==="
    exit 1
fi
