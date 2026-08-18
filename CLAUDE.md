# CLAUDE.md — Guia de Desenvolvimento & Arquitetura Kairós Intelligence

## 📌 Visão Geral do Projeto
**Kairós Intelligence** é um ecossistema de inteligência artificial clínica e atendimento médico multicanal voltado para clínicas e hospitais. O sistema une orquestração multi-agente via WhatsApp (OpenClaw + Evolution Go), base de conhecimento médico (GraphRAG + ChromaDB + Neo4j) e um módulo clínico completo de telemedicina e apoio à consulta (FastAPI + React).

---

## 🏗️ Arquitetura & Microsserviços

| Serviço | Porta / Host | Descrição / Tecnologias |
|---------|--------------|-------------------------|
| **dashboard** | `3001` (Nginx) | Frontend SPA em React + Vite. Roteia `/api/` para Paperclip, `/clinical-api/` para Clinical e `/storage/` para MinIO. |
| **clinical** | `3100` (FastAPI) | Módulo clínico: gestão de pacientes, transcrição ao vivo, geração SOAP, upload e consulta de exames/anexos. |
| **paperclip** | `3000` (FastAPI) | Base de conhecimento médico, ingestão RAG e indexação vetorial/grafos. |
| **kairos-postgres** | `5432` | Banco relacional PostgreSQL com suporte multi-tenant (schemas separados por clínica) e extensão `unaccent`. |
| **kairos-minio** | `9000` / `9001` | Armazenamento de objetos S3 (PDFs, exames de imagem, áudios e relatórios). |
| **kairos-chromadb** | `8000` | Banco vetorial para embeddings e busca semântica. |
| **kairos-neo4j** | `7474` / `7687` | Banco de grafos para relacionamentos clínicos e ontologias médicas. |
| **kairos-redis** | `6379` | Cache e fila de buffer para mensageria. |
| **evolution-go** | `8080` | Gateway de conexão WhatsApp API. |

---

## 🚀 Comandos de Desenvolvimento & Deploy

### 1. Build e Reinicialização de Serviços (Docker Compose)
```bash
cd /root/kairos-intelligence

# Rebuild e subida de serviço específico
docker compose up --build -d dashboard
docker compose up --build -d clinical
docker compose up --build -d paperclip

# Subir todos os serviços em background
docker compose up -d

# Status dos containers
docker ps --format "table {{.Names}}	{{.Status}}	{{.Ports}}"
```

### 2. Frontend (Dashboard)
```bash
cd /root/kairos-intelligence/dashboard

# Instalação de dependências
npm ci

# Build de produção (Vite)
npm run build
```

### 3. Backend (Clinical / Paperclip)
```bash
# Executar script de migração no banco de dados via container clinical
docker exec -i kairos-clinical python3 - < meu_script_migracao.py

# Verificação de logs em tempo real
docker logs -f --tail 100 kairos-clinical
docker logs -f --tail 100 kairos-dashboard
```

---

## 🗄️ Padrões de Banco de Dados & Multi-Tenancy

1. **Multi-Tenancy por Schema:**
   - Cada clínica/tenant possui seu schema isolado no PostgreSQL (ex: `clinica-demo`).
   - Toda rota no backend deve recuperar o slug da clínica (`get_tenant_slug(request)`) e definir o `search_path`:
     ```python
     with engine.connect() as conn:
         conn.execute(text(f"SET search_path TO '{tenant_slug}', public"))
         # queries aqui...
     ```

2. **Busca de Pacientes Sem Acentos:**
   - A extensão `unaccent` está ativa no banco.
   - Sempre utilize `unaccent(name) ILIKE unaccent(:q_name)` para buscas flexíveis e insensíveis a maiúsculas/minúsculas e acentuações.

3. **Tabela `patient_files`:**
   - Armazena metadados de arquivos vinculados a `patients(id)`:
     ```sql
     CREATE TABLE IF NOT EXISTS patient_files (
         id SERIAL PRIMARY KEY,
         patient_id INTEGER REFERENCES patients(id) ON DELETE CASCADE,
         file_name VARCHAR(255) NOT NULL,
         file_type VARCHAR(50) DEFAULT 'outro',
         mime_type VARCHAR(100),
         file_size INTEGER,
         storage_key VARCHAR(500) NOT NULL,
         description TEXT DEFAULT '',
         uploaded_by VARCHAR(200) DEFAULT '',
         created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
     );
     ```

---

## 📂 Armazenamento de Arquivos & Proxy MinIO

3. **Upload de Documentos para Biblioteca de Conhecimentos:**
   - Endpoint: `POST /api/v1/quarantine/suggest`
   - Suporta upload multi-formato (`.pdf, .docx, .doc, .txt, .rtf, .md, .csv, .xlsx, .json, .tsv`) até 50MB.
   - Extração automática de texto via `pypdf` e `python-docx` para alimentar o Grafo de Conhecimento e a Curadoria Central.
   - Endpoint de visualização: `GET /api/v1/quarantine/{item_id}/file` (presigned URL proxied via `/storage/`).

1. **Upload:**
   - Endpoint: `POST /api/v1/patients/{patient_id}/files`
   - O arquivo é enviado diretamente ao bucket MinIO (`kairos-media`) com chave `{tenant_slug}/patients/{patient_id}/{uuid}.ext`.
   - Limite configurado no Nginx: `client_max_body_size 50M;`.

2. **Download / Visualização:**
   - Endpoint: `GET /api/v1/patients/files/{file_id}/download`
   - Gera uma presigned URL temporária.
   - O backend substitui `http://kairos-minio:9000` por `/storage/` para que o navegador acesse via proxy reverso do Nginx de forma transparente e segura.

---

## 🎨 Padrões de Interface & Frontend

- **Formatação de Datas:** Sempre exibir e processar datas de nascimento no formato brasileiro `DD/MM/AAAA` (utilizar helper `formatDateBR` na UI).
- **Máscaras de Input:** Utilizar formatação de CPF (`000.000.000-00`) nos inputs de cadastro rápido de pacientes.
- **Nomenclaturas Padronizadas:**
  - *"Atendimento Médico"* (em substituição a Consulta Médica)
  - *"Admed IA"* (IA clínica de apoio diagnóstico)
  - *"Assistente de IA"* (chat de protocolo e base de conhecimento)
