#!/bin/bash
# Cria a database 'paperclip' no PostgreSQL compartilhado
# Executado automaticamente pelo docker-entrypoint-initdb.d
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE paperclip;
    GRANT ALL PRIVILEGES ON DATABASE paperclip TO $POSTGRES_USER;
EOSQL

echo "✅ Database 'paperclip' criada com sucesso."
