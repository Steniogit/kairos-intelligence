#!/bin/bash
# =============================================================
# Kairós Intelligence v2.7.1 — Script de Deploy (Hostinger VPS)
# =============================================================
set -e

DEPLOY_DIR="/docker/kairos-intelligence"
REPO_URL="https://github.com/Steniogit/kairos-intelligence.git"

echo "================================================"
echo "  Kairós Intelligence v2.7.1 — Deploy"
echo "================================================"

# 1. Criar diretório de deploy
echo "[1/6] Criando diretório de deploy..."
mkdir -p "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# 2. Clonar ou atualizar repositório
if [ -d ".git" ]; then
    echo "[2/6] Atualizando repositório..."
    git pull origin main
else
    echo "[2/6] Clonando repositório..."
    cd /docker
    rm -rf kairos-intelligence
    git clone "$REPO_URL" kairos-intelligence
    cd kairos-intelligence
fi

# 3. Copiar .env de produção
echo "[3/6] Configurando variáveis de ambiente..."
if [ ! -f ".env" ]; then
    cp .env.production .env
    echo "    → .env criado a partir de .env.production"
    echo "    → ATENÇÃO: Edite o .env com suas credenciais reais!"
else
    echo "    → .env já existe, mantendo configuração atual"
fi

# 4. Gerar senhas automáticas para credenciais não preenchidas
echo "[4/6] Gerando credenciais seguras..."
generate_secret() {
    openssl rand -base64 32 | tr -d '/+=' | head -c 32
}

# Substituir placeholders por senhas reais (apenas se ainda forem placeholders)
sed -i "s/GERE_UM_TOKEN_SEGURO_AQUI/$(generate_secret)/g" .env
sed -i "s/GERE_UMA_API_KEY_SEGURA/$(generate_secret)/g" .env
sed -i "s/GERE_UMA_SENHA_SEGURA_POSTGRES/$(generate_secret)/g" .env
sed -i "s/GERE_UMA_SENHA_SEGURA_NEO4J/$(generate_secret)/g" .env
sed -i "s/GERE_UM_TOKEN_SEGURO_CHROMA/$(generate_secret)/g" .env
sed -i "s/GERE_UM_SECRET_SEGURO_PAPERCLIP/$(generate_secret)/g" .env
sed -i "s/GERE_UMA_SENHA_SEGURA_MINIO/$(generate_secret)/g" .env
echo "    → Credenciais geradas automaticamente"

# 5. Criar script de init do PostgreSQL para o Paperclip
echo "[5/6] Configurando banco de dados..."
mkdir -p scripts
cat > scripts/init-paperclip-db.sh << 'INITDB'
#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE paperclip;
    GRANT ALL PRIVILEGES ON DATABASE paperclip TO $POSTGRES_USER;
EOSQL
INITDB
chmod +x scripts/init-paperclip-db.sh

# 6. Subir containers
echo "[6/6] Subindo containers..."
docker compose up -d

echo ""
echo "================================================"
echo "  Deploy concluído!"
echo "================================================"
echo ""
echo "URLs de acesso:"
echo "  🔧 OpenClaw:  https://kairos.$(grep TRAEFIK_HOST .env | cut -d= -f2)"
echo "  📋 Paperclip: https://paperclip.$(grep TRAEFIK_HOST .env | cut -d= -f2)"
echo "  📱 Evolution: https://evolution.$(grep TRAEFIK_HOST .env | cut -d= -f2)"
echo "  🔗 Neo4j:     https://neo4j.$(grep TRAEFIK_HOST .env | cut -d= -f2)"
echo ""
echo "⚠️  IMPORTANTE: Edite o .env com suas API keys reais:"
echo "    nano $DEPLOY_DIR/.env"
echo ""
echo "Depois de editar, reinicie:"
echo "    cd $DEPLOY_DIR && docker compose restart"
echo ""
