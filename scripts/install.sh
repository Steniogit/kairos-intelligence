#!/bin/bash
# =============================================================
# Kairós Intelligence v2.7 — Instalação Inicial
# =============================================================
# Uso: ./scripts/install.sh
# Pré-requisitos: Ubuntu 22.04+ com acesso root/sudo
# =============================================================

set -euo pipefail

echo "[INFO] === Instalação — Kairós Intelligence v2.7 ==="
echo ""

# --- 1. Verificar sistema operacional ---
echo "[INFO] 1/6 — Verificando sistema..."
if ! grep -qi "ubuntu\|debian" /etc/os-release 2>/dev/null; then
    echo "[WARN] Sistema não é Ubuntu/Debian. Pode haver incompatibilidades."
fi

# --- 2. Instalar Docker ---
echo "[INFO] 2/6 — Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "[INFO] Instalando Docker..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    echo "[OK] Docker instalado. Faça logout/login para aplicar grupo docker."
else
    echo "[OK] Docker já instalado: $(docker --version)"
fi

# --- 3. Instalar Docker Compose ---
echo "[INFO] 3/6 — Verificando Docker Compose..."
if ! command -v docker compose &> /dev/null; then
    echo "[INFO] Instalando Docker Compose plugin..."
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
    echo "[OK] Docker Compose instalado."
else
    echo "[OK] Docker Compose já instalado."
fi

# --- 4. Configurar .env ---
echo "[INFO] 4/6 — Verificando .env..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "[INFO] Criando .env a partir de .env.example..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "[WARN] EDITE o arquivo .env com suas credenciais reais!"
    echo "       nano $PROJECT_DIR/.env"
else
    echo "[OK] .env já existe."
fi

# --- 5. Criar diretórios necessários ---
echo "[INFO] 5/6 — Criando diretórios..."
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/backups"

# --- 6. Permissões nos scripts ---
echo "[INFO] 6/6 — Configurando permissões..."
chmod +x "$PROJECT_DIR/scripts/"*.sh

echo ""
echo "[OK] === Instalação concluída ==="
echo ""
echo "Próximos passos:"
echo "  1. Edite .env com suas credenciais: nano .env"
echo "  2. Execute o deploy: ./scripts/deploy.sh"
echo "  3. Verifique a saúde: ./scripts/health-check.sh"
echo ""
