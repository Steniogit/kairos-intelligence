"""
Kairos Intelligence — Clinical Module API
Servico dedicado para o Modulo Clinico Avancado.
Separado do Paperclip (Control Plane) por responsabilidade unica.
"""

import os
import json
import logging
import tempfile
from datetime import datetime
from typing import Optional

import neo4j.time

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, WebSocket, WebSocketDisconnect, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from neo4j import GraphDatabase
from minio import Minio
from minio.error import S3Error
import io
import uuid as uuid_lib
from pathlib import Path

# ─── Logging ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kairos-clinical")

# ─── App ─────────────────────────────────────────────────
app = FastAPI(
    title="Kairos Clinical API",
    version="1.0.0",
    description="Modulo Clinico Avancado — SOAP, GraphRAG, Copiloto"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    tenant_slug = request.headers.get("X-Tenant-Slug")
    if tenant_slug and request.url.path.startswith("/api/v1/"):
        request.state.tenant_slug = tenant_slug
    response = await call_next(request)
    return response

def get_tenant_slug(request: Request):
    x_tenant_slug = request.headers.get("X-Tenant-Slug")
    if not x_tenant_slug:
        x_tenant_slug = request.query_params.get("tenant_slug")
    if not x_tenant_slug:
        raise HTTPException(status_code=400, detail="X-Tenant-Slug header or tenant_slug query param required")
    return x_tenant_slug

def get_tenant_db(tenant_slug: str = Depends(get_tenant_slug)):
    conn = engine.connect()
    try:
        conn.execute(text(f"SET search_path TO '{tenant_slug}', public"))
        yield conn
    finally:
        conn.close()

# ─── Database Connections ────────────────────────────────
PG_USER = os.getenv("POSTGRES_USER", "kairos_user")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "")
PG_DB = os.getenv("POSTGRES_DB", "kairos")
PG_HOST = os.getenv("POSTGRES_HOST", "kairos-postgres")
DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:5432/{PG_DB}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://kairos-neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "")

def _serialize_neo4j(obj):
    """Convert neo4j native types to JSON-serializable Python types."""
    if isinstance(obj, dict):
        return {k: _serialize_neo4j(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_neo4j(i) for i in obj]
    elif isinstance(obj, (neo4j.time.DateTime, neo4j.time.Date)):
        return str(obj)
    elif isinstance(obj, neo4j.time.Time):
        return str(obj)
    elif isinstance(obj, neo4j.time.Duration):
        return str(obj)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
        return [_serialize_neo4j(i) for i in obj]
    return obj


neo4j_driver = None
try:
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    logger.info("Neo4j driver initialized")
except Exception as e:
    logger.error(f"Neo4j connection failed: {e}")

CHROMA_HOST = os.getenv("CHROMA_HOST", "kairos-chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
CHROMA_TOKEN = os.getenv("CHROMA_AUTH_TOKEN", "")



# ─── MinIO (S3) ──────────────────────────────────────────
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "kairos-minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "kairos-media")

minio_client = None
try:
    if MINIO_ACCESS_KEY:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )
        if not minio_client.bucket_exists(MINIO_BUCKET):
            minio_client.make_bucket(MINIO_BUCKET)
        logger.info(f"MinIO connected: {MINIO_ENDPOINT}/{MINIO_BUCKET}")
except Exception as e:
    logger.warning(f"MinIO not available: {e}")
    minio_client = None

# ═══════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Verifica saude de todas as conexoes."""
    status = {"service": "kairos-clinical", "version": "1.0.0"}

    # Postgres
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["postgres"] = "online"
    except Exception:
        status["postgres"] = "offline"

    # Neo4j
    try:
        if neo4j_driver:
            with neo4j_driver.session() as session:
                session.run("RETURN 1")
            status["neo4j"] = "online"
        else:
            status["neo4j"] = "not_configured"
    except Exception:
        status["neo4j"] = "offline"

    return status


# ═══════════════════════════════════════════════════════════
# Admin — Provisionamento Multi-Tenant
# ═══════════════════════════════════════════════════════════

@app.post("/api/v1/admin/provision/{tenant_slug}")
async def provision_tenant(tenant_slug: str):
    """Provisiona a infraestrutura para um novo tenant (schema e tabelas basicas)."""
    # Protecao basica: permitir apenas caracteres alfanumericos e hifens no slug
    import re
    if not re.match(r"^[a-z0-9\-]+$", tenant_slug):
        raise HTTPException(status_code=400, detail="Slug invalido")

    try:
        with engine.connect() as conn:
            # Cria schema se nao existir
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS \"{tenant_slug}\""))
            
            # Muda search_path
            conn.execute(text(f"SET search_path TO \"{tenant_slug}\""))
            
            # Cria tabela knowledge_quarantine especifica do tenant
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge_quarantine (
                    id SERIAL PRIMARY KEY,
                    source_url TEXT NOT NULL,
                    source_type VARCHAR(20) DEFAULT 'url',
                    raw_text TEXT,
                    entities_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    relationships_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                    graph_cypher TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    reviewed_by VARCHAR(100),
                    reviewer_notes TEXT,
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    reviewed_at TIMESTAMP WITHOUT TIME ZONE
                );
            """))

            # Tabela de pacientes
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS patients (
                    id SERIAL PRIMARY KEY,
                    cpf VARCHAR(14) UNIQUE NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    sex VARCHAR(1) DEFAULT 'N',
                    birth_date DATE,
                    phone VARCHAR(20),
                    email VARCHAR(200),
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
            """))

                        # Tabela de arquivos de pacientes
            conn.execute(text("""
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
            """))

            # Tabela de consultas (historico)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS consultations (
                    id SERIAL PRIMARY KEY,
                    patient_id INTEGER REFERENCES patients(id),
                    doctor_name VARCHAR(200),
                    doctor_crm VARCHAR(20),
                    transcript TEXT,
                    soap_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    documents_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                    duration_seconds INTEGER DEFAULT 0,
                    status VARCHAR(20) DEFAULT 'completed',
                    started_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    ended_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
            """))
            conn.commit()
        return {"status": "provisioned", "tenant_slug": tenant_slug}
    except Exception as e:
        logger.error(f"Erro ao provisionar tenant {tenant_slug}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════
# GraphRAG — Consultas ao Grafo Medico
# ═══════════════════════════════════════════════════════════

@app.get("/api/v1/graph/patient/{cpf}")
async def get_patient_graph(cpf: str, tenant_slug: str = Depends(get_tenant_slug)):
    """Busca paciente e todo o seu contexto no grafo."""
    if not neo4j_driver:
        raise HTTPException(status_code=503, detail="Neo4j nao disponivel")

    with neo4j_driver.session() as session:
        result = session.run(f"""
            MATCH (p:Patient:{tenant_slug} {{cpf: $cpf}})
            OPTIONAL MATCH (p)-[:HAS_CONDITION]->(c:Condition:{tenant_slug})
            OPTIONAL MATCH (p)-[:ATTENDED_BY]->(d:Doctor:{tenant_slug})
            OPTIONAL MATCH (p)<-[:BELONGS_TO]-(s:Session:{tenant_slug})
            RETURN p, collect(DISTINCT c) as conditions,
                   collect(DISTINCT d) as doctors,
                   collect(DISTINCT s) as sessions
        """, cpf=cpf)

        record = result.single()
        if not record:
            return {"found": False, "cpf": cpf}

        patient = _serialize_neo4j(dict(record["p"]))
        conditions = [_serialize_neo4j(dict(c)) for c in record["conditions"]]
        doctors = [_serialize_neo4j(dict(d)) for d in record["doctors"]]
        sessions = [_serialize_neo4j(dict(s)) for s in record["sessions"]]

        return {
            "found": True,
            "patient": patient,
            "conditions": conditions,
            "doctors": doctors,
            "sessions_count": len(sessions)
        }


@app.post("/api/v1/graph/patient")
async def create_patient_node(data: dict, tenant_slug: str = Depends(get_tenant_slug)):
    """Cria ou atualiza no de paciente no grafo."""
    if not neo4j_driver:
        raise HTTPException(status_code=503, detail="Neo4j nao disponivel")

    cpf = data.get("cpf")
    if not cpf:
        raise HTTPException(status_code=400, detail="CPF obrigatorio")

    with neo4j_driver.session() as session:
        session.run(f"""
            MERGE (p:Patient:{tenant_slug} {{cpf: $cpf}})
            SET p.name = $name,
                p.phone = $phone,
                p.birth_date = $birth_date,
                p.updated_at = datetime()
        """, cpf=cpf,
             name=data.get("name", ""),
             phone=data.get("phone", ""),
             birth_date=data.get("birth_date", ""))

    return {"status": "ok", "cpf": cpf}


@app.get("/api/v1/graph/search")
async def search_graph(query: str, limit: int = 10, tenant_slug: str = Depends(get_tenant_slug)):
    """Busca full-text no grafo (pacientes, condicoes, medicamentos)."""
    if not neo4j_driver:
        raise HTTPException(status_code=503, detail="Neo4j nao disponivel")

    results = []
    with neo4j_driver.session() as session:
        # Busca por nome de paciente
        patients = session.run(f"""
            MATCH (p:Patient:{tenant_slug})
            WHERE toLower(p.name) CONTAINS toLower($search_term)
            RETURN 'Patient' as type, p.name as name, p.cpf as id
            LIMIT $max_results
        """, search_term=query, max_results=limit)
        for r in patients:
            results.append(dict(r))

        # Busca por condicao medica
        conditions = session.run(f"""
            MATCH (c:Condition:{tenant_slug})
            WHERE toLower(c.name) CONTAINS toLower($search_term)
            RETURN 'Condition' as type, c.name as name, c.cid10 as id
            LIMIT $max_results
        """, search_term=query, max_results=limit)
        for r in conditions:
            results.append(dict(r))

        # Busca por medicamento
        drugs = session.run(f"""
            MATCH (d:Drug:{tenant_slug})
            WHERE toLower(d.name) CONTAINS toLower($search_term)
            RETURN 'Drug' as type, d.name as name, d.name as id
            LIMIT $max_results
        """, search_term=query, max_results=limit)
        for r in drugs:
            results.append(dict(r))

    return {"query": query, "results": results}



def extract_text_from_file_bytes(filename: str, file_bytes: bytes) -> str:
    """Extrai texto limpo de arquivos PDF, DOCX, TXT, etc."""
    ext = Path(filename).suffix.lower()
    text_content = ""
    try:
        if ext == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(file_bytes))
                pages_text = []
                for page in reader.pages[:50]:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t)
                text_content = "\n\n".join(pages_text)
            except Exception as e:
                logger.warning(f"pypdf extraction error: {e}")
        elif ext in [".docx", ".doc"]:
            try:
                import docx
                doc = docx.Document(io.BytesIO(file_bytes))
                text_content = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            except Exception as e:
                logger.warning(f"docx extraction error: {e}")
        elif ext in [".txt", ".md", ".csv", ".json", ".rtf", ".tsv"]:
            try:
                text_content = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                text_content = file_bytes.decode("latin-1", errors="ignore")
        else:
            text_content = file_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Error extracting text from {filename}: {e}")
        text_content = ""
    return text_content

# ═══════════════════════════════════════════════════════════
# Quarentena de Conhecimento
# ═══════════════════════════════════════════════════════════

class QuarantineEntry(BaseModel):
    source_url: str
    source_type: str = "url"
    raw_text: Optional[str] = None
    entities_json: dict = {}
    relationships_json: list = []
    graph_cypher: Optional[str] = None
    submitted_by: Optional[str] = ""

class RejectPayload(BaseModel):
    reviewer: Optional[str] = "admin"
    notes: Optional[str] = ""


@app.get("/api/v1/quarantine")
async def list_quarantine(status: str = "all", limit: int = 100, conn = Depends(get_tenant_db)):
    """Lista itens na quarentena de conhecimento com suporte a arquivos anexos."""
    if status == "all" or not status:
        result = conn.execute(
            text("""
                SELECT id, source_url, source_type, raw_text, entities_json,
                       relationships_json, graph_cypher, status, submitted_by,
                       reviewer_notes, reviewed_by, reviewed_at, storage_key,
                       file_name, mime_type, file_size, created_at
                FROM knowledge_quarantine
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"limit": limit}
        )
    else:
        result = conn.execute(
            text("""
                SELECT id, source_url, source_type, raw_text, entities_json,
                       relationships_json, graph_cypher, status, submitted_by,
                       reviewer_notes, reviewed_by, reviewed_at, storage_key,
                       file_name, mime_type, file_size, created_at
                FROM knowledge_quarantine
                WHERE status = :status
                ORDER BY created_at DESC
                LIMIT :limit
            """),
            {"status": status, "limit": limit}
        )
    items = [dict(row._mapping) for row in result]
    for item in items:
        if item.get("created_at"):
            item["created_at"] = item["created_at"].isoformat()
        if item.get("reviewed_at"):
            item["reviewed_at"] = item["reviewed_at"].isoformat()
        
        ent = item.get("entities_json")
        entities_list = ent if isinstance(ent, list) else (ent.get("entities", []) if isinstance(ent, dict) else [])
        rels = item.get("relationships_json") or []
        cypher_lines = [l.strip() for l in (item.get("graph_cypher") or "").splitlines() if l.strip()]
        
        item["extracted_data"] = {
            "entities": entities_list,
            "relationships": rels,
            "cypher_queries": cypher_lines
        }
    return {"items": items, "count": len(items)}


@app.post("/api/v1/quarantine/suggest")
async def suggest_knowledge(
    request: Request,
    title: str = Form(""),
    source_type: str = Form("protocolo"),
    source_url: str = Form(""),
    content_text: str = Form(""),
    notes: str = Form(""),
    file: Optional[UploadFile] = File(None),
    conn = Depends(get_tenant_db)
):
    """Permite que médicos enviem sugestões com links, textos ou arquivos anexados (PDF, DOCX, TXT, etc)."""
    tenant_slug = get_tenant_slug(request)
    submitted_by = "Médico"
    try:
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            from jose import jwt
            token_data = jwt.decode(auth[7:], options={"verify_signature": False})
            submitted_by = f"{token_data.get('name', 'Médico')} (CRM: {token_data.get('crm', 'N/I')})"
    except Exception:
        pass

    storage_key = ""
    original_filename = ""
    mime_type = ""
    file_size = 0
    extracted_text = ""

    if file and file.filename:
        original_filename = file.filename
        file_bytes = await file.read()
        file_size = len(file_bytes)
        mime_type = file.content_type or "application/octet-stream"

        # Upload para MinIO
        if minio_client:
            ext = Path(original_filename).suffix.lower()
            storage_key = f"{tenant_slug}/knowledge/{uuid_lib.uuid4().hex}{ext}"
            try:
                minio_client.put_object(
                    MINIO_BUCKET,
                    storage_key,
                    io.BytesIO(file_bytes),
                    length=file_size,
                    content_type=mime_type
                )
            except Exception as e:
                logger.error(f"Erro ao salvar arquivo no MinIO: {e}")

        # Extrair texto do arquivo
        extracted_text = extract_text_from_file_bytes(original_filename, file_bytes)

    display_title = (title or original_filename or source_url or "Sugestão Médica").strip()
    raw = (content_text or extracted_text or notes or "").strip()

    row = conn.execute(
        text("""
            INSERT INTO knowledge_quarantine
            (source_url, source_type, raw_text, status, submitted_by, storage_key, file_name, mime_type, file_size, created_at)
            VALUES (:url, :type, :raw, 'pending', :submitted_by, :storage_key, :file_name, :mime_type, :file_size, NOW())
            RETURNING id, created_at
        """),
        {
            "url": display_title,
            "type": source_type or "protocolo",
            "raw": raw,
            "submitted_by": submitted_by,
            "storage_key": storage_key,
            "file_name": original_filename,
            "mime_type": mime_type,
            "file_size": file_size,
        }
    ).fetchone()
    conn.commit()
    return {
        "status": "queued",
        "id": row[0],
        "file_name": original_filename,
        "created_at": str(row[1])
    }


@app.get("/api/v1/quarantine/{item_id}/file")
async def get_quarantine_file_url(item_id: int, request: Request, conn = Depends(get_tenant_db)):
    """Gera URL assinada para visualização/download do arquivo anexo de conhecimento."""
    if not minio_client:
        raise HTTPException(status_code=503, detail="Armazenamento MinIO não disponível")
    
    row = conn.execute(
        text("SELECT storage_key, file_name, mime_type FROM knowledge_quarantine WHERE id = :id"),
        {"id": item_id}
    ).fetchone()
    
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado nesta sugestão")
    
    from datetime import timedelta
    url = minio_client.presigned_get_object(
        MINIO_BUCKET,
        row[0],
        expires=timedelta(hours=2),
    )
    proxied_url = url.replace("http://kairos-minio:9000", "/storage").replace("http://127.0.0.1:9000", "/storage").replace("http://localhost:9000", "/storage")
    return {
        "url": proxied_url,
        "file_name": row[1],
        "mime_type": row[2]
    }


@app.post("/api/v1/quarantine")
async def add_to_quarantine(entry: QuarantineEntry, conn = Depends(get_tenant_db)):
    """Adiciona um novo item a quarentena para revisao."""
    try:
        conn.execute(
            text("""
                INSERT INTO knowledge_quarantine
                (source_url, source_type, raw_text, entities_json, relationships_json, graph_cypher, submitted_by)
                VALUES (:url, :type, :raw, :entities, :rels, :cypher, :submitted_by)
            """),
            {
                "url": entry.source_url,
                "type": entry.source_type,
                "raw": entry.raw_text,
                "entities": json.dumps(entry.entities_json),
                "rels": json.dumps(entry.relationships_json),
                "cypher": entry.graph_cypher,
                "submitted_by": entry.submitted_by or "Sistema"
            }
        )
        conn.commit()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erro ao adicionar na quarentena: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Erro interno do banco")


@app.post("/api/v1/quarantine/{item_id}/approve")
async def approve_quarantine(item_id: int, reviewer: str = "admin", conn = Depends(get_tenant_db), tenant_slug: str = Depends(get_tenant_slug)):
    """Aprova um item da quarentena e ingere no grafo Neo4j global."""
    if not neo4j_driver:
        raise HTTPException(status_code=503, detail="Neo4j nao disponivel")

    try:
        result = conn.execute(
            text("SELECT * FROM knowledge_quarantine WHERE id = :id"),
            {"id": item_id}
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Item nao encontrado")

        row_dict = dict(row._mapping)
        cypher_lines = (row_dict.get("graph_cypher") or "").splitlines()

        if cypher_lines:
            with neo4j_driver.session() as session:
                for line in cypher_lines:
                    cypher = line.strip()
                    if cypher:
                        session.run(cypher)
                logger.info(f"Quarantine #{item_id} merged into Neo4j")
        
        conn.execute(
            text("""
                UPDATE knowledge_quarantine
                SET status = 'approved', reviewed_by = :reviewer,
                    reviewed_at = NOW()
                WHERE id = :id
            """),
            {"id": item_id, "reviewer": reviewer}
        )
        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao executar Cypher no Neo4j: {str(e)}"
        )

    return {"status": "approved", "id": item_id}


@app.post("/api/v1/quarantine/{item_id}/reject")
async def reject_quarantine(
    item_id: int, 
    data: Optional[RejectPayload] = None, 
    reviewer: str = "admin", 
    notes: str = "", 
    conn = Depends(get_tenant_db)
):
    """Rejeita um item da quarentena salvando o motivo/justificativa."""
    rev = (data.reviewer if data and data.reviewer else reviewer) or "admin"
    reason = (data.notes if data and data.notes else notes) or "Nao aprovado pela curadoria central."
    try:
        conn.execute(
            text("""
                UPDATE knowledge_quarantine
                SET status = 'rejected', reviewed_by = :reviewer,
                    reviewer_notes = :notes, reviewed_at = NOW()
                WHERE id = :id
            """),
            {"id": item_id, "reviewer": rev, "notes": reason}
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Erro ao rejeitar item")
    return {"status": "rejected", "id": item_id, "notes": reason}


# ═══════════════════════════════════════════════════════════
# SOAP — Estruturação de Consultas Médicas (Fase 2)
# ═══════════════════════════════════════════════════════════

from soap_pipeline import process_audio_to_soap, process_text_to_soap

AUDIO_MIME_MAP = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
    ".webm": "audio/webm",
    ".flac": "audio/flac",
}


@app.post("/api/v1/clinical/soap")
async def soap_from_audio(audio: UploadFile = File(...), tenant_slug: str = Depends(get_tenant_slug)):
    """Recebe audio de consulta, envia ao Gemini Flash, retorna JSON SOAP.
    LGPD: Audio salvo em tmpfs (RAM), apagado imediatamente apos processamento."""

    # Detectar MIME type
    from pathlib import Path
    ext = Path(audio.filename or "audio.wav").suffix.lower()
    mime_type = AUDIO_MIME_MAP.get(ext, "audio/wav")

    # Ler bytes do audio
    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Arquivo de audio vazio")
    if len(audio_bytes) > 25 * 1024 * 1024:  # 25MB limit
        raise HTTPException(status_code=413, detail="Audio excede 25MB")

    logger.info(f"SOAP request: {audio.filename} ({len(audio_bytes)} bytes, {mime_type})")

    result = await process_audio_to_soap(audio_bytes, audio.filename or "audio.wav", mime_type, neo4j_driver=neo4j_driver, tenant_slug=tenant_slug)
    return result


class TextTranscription(BaseModel):
    text: str = Field(..., description="Transcricao bruta da consulta medica")


@app.post("/api/v1/clinical/soap/text")
async def soap_from_text(data: TextTranscription, tenant_slug: str = Depends(get_tenant_slug)):
    """Recebe texto de transcricao pronto e gera SOAP via Gemini 2.5."""
    try:
        result = await process_text_to_soap(data.text, neo4j_driver=neo4j_driver, tenant_slug=tenant_slug)
        return result
    except Exception as e:
        logger.error(f"Erro no pipeline SOAP de texto: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ═══════════════════════════════════════════════════════════
# Curador Científico — Ingestão de Conhecimento (Fase 3)
# ═══════════════════════════════════════════════════════════

from curator_pipeline import ingest_url, fetch_url_content


class IngestRequest(BaseModel):
    url: str = Field(..., description="URL da fonte medica (bula, protocolo, artigo)")
    auto_quarantine: bool = Field(default=True, description="Enviar automaticamente para quarentena")
    source_type: str = Field(default="url", description="Tipo da fonte")


@app.post("/api/v1/clinical/ingest")
async def ingest_medical_source(data: IngestRequest, conn = Depends(get_tenant_db), tenant_slug: str = Depends(get_tenant_slug)):
    """Ingere uma URL medica: raspa conteudo, extrai entidades via Gemini,
    gera Cypher queries e opcionalmente envia para quarentena."""

    logger.info(f"Ingest request: {data.url}")

    result = await ingest_url(data.url, tenant_slug=tenant_slug)

    if result["status"] != "ok":
        raise HTTPException(status_code=422, detail=result)

    # Auto-submit to quarantine if requested
    if data.auto_quarantine:
        conn.execute(
            text("""
                INSERT INTO knowledge_quarantine
                (source_url, source_type, raw_text, entities_json, relationships_json, graph_cypher)
                VALUES (:url, :type, :raw, :entities, :rels, :cypher)
            """),
            {
                "url": result["source_url"],
                "type": result["source_type"],
                "raw": result.get("raw_text", ""),
                "entities": json.dumps(result["entities_json"]),
                "rels": json.dumps(result["relationships_json"]),
                "cypher": result.get("graph_cypher"),
            }
        )
        conn.commit()
        result["quarantine_status"] = "queued"

    return result


@app.post("/api/v1/clinical/ingest/preview")
async def preview_url_content(data: IngestRequest):
    """Preview: apenas raspa a URL e mostra o conteudo limpo, sem extrair."""
    fetch_result = await fetch_url_content(data.url)
    return fetch_result


# ═══════════════════════════════════════════════════════════
# Automação Ademed — Geração de Documentos (Fase 5)
# ═══════════════════════════════════════════════════════════

from ademed_pipeline import (
    generate_document, generate_all_documents, DOCUMENT_TEMPLATES
)


class AdemedRequest(BaseModel):
    """Request para gerar documento medico a partir do SOAP."""
    soap: dict = Field(..., description="SOAP estruturado (output do copiloto ou agente SOAP)")
    patient_name: str = Field(default="", description="Nome do paciente")
    document_type: str = Field(..., description="Tipo: prescription, sick_note, exam_request, referral, report")
    extra_context: Optional[dict] = Field(default=None, description="Contexto adicional (ex: authorize_cid, dias afastamento)")


class AdemedBatchRequest(BaseModel):
    """Request para gerar multiplos documentos de uma vez."""
    soap: dict = Field(..., description="SOAP estruturado")
    patient_name: str = Field(default="", description="Nome do paciente")
    document_types: Optional[list] = Field(default=None, description="Lista de tipos (None = todos)")
    extra_context: Optional[dict] = Field(default=None, description="Contexto adicional por tipo")


@app.get("/api/v1/clinical/ademed/templates")
async def list_ademed_templates():
    """Lista todos os modelos de documentos disponiveis."""
    templates = {}
    for key, tmpl in DOCUMENT_TEMPLATES.items():
        templates[key] = {
            "name": tmpl["name"],
            "description": tmpl["description"],
            "required_soap_fields": tmpl["required_soap_fields"]
        }
    return {"templates": templates, "count": len(templates)}


@app.post("/api/v1/clinical/ademed/generate")
async def ademed_generate(data: AdemedRequest):
    """Gera um documento medico a partir do SOAP finalizado."""
    result = await generate_document(
        soap_data=data.soap,
        doc_type=data.document_type,
        patient_name=data.patient_name,
        extra_context=data.extra_context
    )
    return result


@app.post("/api/v1/clinical/ademed/generate/batch")
async def ademed_generate_batch(data: AdemedBatchRequest):
    """Gera multiplos documentos de uma vez (ex: receita + exames + atestado)."""
    result = await generate_all_documents(
        soap_data=data.soap,
        patient_name=data.patient_name,
        doc_types=data.document_types,
        extra_context=data.extra_context
    )
    return result


# ═══════════════════════════════════════════════════════════
# Pre-Flight Check — Verificação Pré-Consulta
# ═══════════════════════════════════════════════════════════

from preflight import run_preflight


@app.get("/api/v1/clinical/preflight")
async def preflight_check(tenant_slug: str = Depends(get_tenant_slug), conn = Depends(get_tenant_db)):
    """Executa verificacao completa de todos os subsistemas.
    Deve ser chamado ANTES de iniciar qualquer consulta."""
    result = await run_preflight(conn, neo4j_driver, CHROMA_HOST, CHROMA_PORT, tenant_slug=tenant_slug)

    # Adicionar status do Google Cloud STT
    if STT_AVAILABLE:
        try:
            stt_status = check_stt_health()
            result["stt"] = stt_status
        except Exception as e:
            result["stt"] = {"status": "error", "message": str(e)}
    else:
        result["stt"] = {"status": "unavailable", "message": "STT pipeline não carregado"}

    return result


# ═══════════════════════════════════════════════════════════
# SOAP Generation via HTTP (Fallback quando WS desconecta)
# ═══════════════════════════════════════════════════════════

class SoapGenerateRequest(BaseModel):
    transcript: str
    format: str = "structured"

@app.post("/api/v1/clinical/soap/generate")
async def generate_soap_http(req: SoapGenerateRequest, tenant_slug: str = Depends(get_tenant_slug)):
    """Gera SOAP via HTTP — usado como fallback quando o WebSocket desconecta."""
    from copilot_pipeline import CopilotSession, analyze_transcript_realtime
    import uuid

    if not req.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript vazio")

    session = CopilotSession(neo4j_driver, str(uuid.uuid4())[:8], tenant_slug=tenant_slug)
    session.add_text(req.transcript)

    result = await analyze_transcript_realtime(session, neo4j_driver)

    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message", "Erro na analise"))

    copilot = result.get("copilot", {})
    soap_partial = copilot.get("soap_partial", {})

    return {
        "soap": soap_partial,
        "alerts": copilot.get("alerts", []),
        "entities_detected": copilot.get("entities_detected", []),
        "knowledge_attribution": copilot.get("knowledge_attribution", {}),
    }


# ═══════════════════════════════════════════════════════════
# Pacientes & Histórico de Consultas
# ═══════════════════════════════════════════════════════════

class PatientCreate(BaseModel):
    cpf: str
    name: str
    sex: str = 'N'
    birth_date: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class ConsultationSave(BaseModel):
    patient_id: Optional[int] = None
    doctor_name: str = ''
    doctor_crm: str = ''
    transcript: str = ''
    soap_json: dict = {}
    documents_json: list = []
    duration_seconds: int = 0


@app.get("/api/v1/patients/search")
async def search_patients(request: Request, q: str = ""):
    """Busca pacientes por nome ou CPF."""
    tenant_slug = get_tenant_slug(request)
    if not q or len(q) < 2:
        return []
    try:
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO '{tenant_slug}', public"))
            rows = conn.execute(text("""
                SELECT id, cpf, name, sex, birth_date, phone
                FROM patients
                WHERE unaccent(name) ILIKE unaccent(:q_name) OR cpf LIKE :q_cpf
                ORDER BY name LIMIT 20
            """), {"q_name": f"%{q}%", "q_cpf": f"%{q}%"}).fetchall()
            return [
                {
                    "id": r[0], "cpf": r[1], "name": r[2],
                    "sex": r[3], "birth_date": str(r[4]) if r[4] else None,
                    "phone": r[5]
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"Erro ao buscar pacientes: {e}")
        return []


@app.post("/api/v1/patients")
async def create_or_update_patient(patient: PatientCreate, request: Request):
    """Cadastra ou atualiza paciente (upsert por CPF)."""
    tenant_slug = get_tenant_slug(request)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO '{tenant_slug}', public"))
            row = conn.execute(text("""
                INSERT INTO patients (cpf, name, sex, birth_date, phone, email)
                VALUES (:cpf, :name, :sex, :birth_date, :phone, :email)
                ON CONFLICT (cpf) DO UPDATE SET
                    name = EXCLUDED.name,
                    sex = EXCLUDED.sex,
                    birth_date = EXCLUDED.birth_date,
                    phone = EXCLUDED.phone,
                    email = EXCLUDED.email,
                    updated_at = NOW()
                RETURNING id, cpf, name, sex, birth_date, phone, email
            """), {
                "cpf": patient.cpf, "name": patient.name,
                "sex": patient.sex,
                "birth_date": patient.birth_date if patient.birth_date else None,
                "phone": patient.phone, "email": patient.email
            }).fetchone()
            conn.commit()
            return {
                "id": row[0], "cpf": row[1], "name": row[2],
                "sex": row[3], "birth_date": str(row[4]) if row[4] else None,
                "phone": row[5], "email": row[6]
            }
    except Exception as e:
        logger.error(f"Erro ao criar paciente: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ═══ Arquivos do Paciente ════════════════════════════════════

@app.post("/api/v1/patients/{patient_id}/files")
async def upload_patient_file(
    patient_id: int,
    request: Request,
    file: UploadFile = File(...),
    file_type: str = Form("outro"),
    description: str = Form(""),
):
    """Upload de arquivo para o paciente (exames, laudos, etc)."""
    tenant_slug = get_tenant_slug(request)
    if not minio_client:
        raise HTTPException(status_code=503, detail="Armazenamento de arquivos nao disponivel")

    try:
        file_bytes = await file.read()
        file_size = len(file_bytes)
        original_name = file.filename or "arquivo"
        mime = file.content_type or "application/octet-stream"

        # Gerar chave unica no MinIO
        ext = Path(original_name).suffix.lower()
        storage_key = f"{tenant_slug}/patients/{patient_id}/{uuid_lib.uuid4().hex}{ext}"

        # Upload para MinIO
        minio_client.put_object(
            MINIO_BUCKET,
            storage_key,
            io.BytesIO(file_bytes),
            length=file_size,
            content_type=mime,
        )

        # Salvar metadados no PostgreSQL
        # Extrair nome do medico do header se disponivel
        uploaded_by = ""
        try:
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                from jose import jwt
                token_data = jwt.decode(auth[7:], options={"verify_signature": False})
                uploaded_by = token_data.get("name", "")
        except Exception:
            pass

        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO '{tenant_slug}', public"))
            row = conn.execute(text("""
                INSERT INTO patient_files (patient_id, file_name, file_type, mime_type, file_size, storage_key, description, uploaded_by)
                VALUES (:patient_id, :file_name, :file_type, :mime_type, :file_size, :storage_key, :description, :uploaded_by)
                RETURNING id, created_at
            """), {
                "patient_id": patient_id,
                "file_name": original_name,
                "file_type": file_type,
                "mime_type": mime,
                "file_size": file_size,
                "storage_key": storage_key,
                "description": description,
                "uploaded_by": uploaded_by,
            }).fetchone()
            conn.commit()

        return {
            "id": row[0],
            "file_name": original_name,
            "file_type": file_type,
            "file_size": file_size,
            "created_at": str(row[1]),
            "status": "uploaded"
        }
    except S3Error as e:
        logger.error(f"MinIO upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no armazenamento: {e}")
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/patients/{patient_id}/files")
async def list_patient_files(patient_id: int, request: Request):
    """Lista todos os arquivos de um paciente."""
    tenant_slug = get_tenant_slug(request)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO '{tenant_slug}', public"))
            rows = conn.execute(text("""
                SELECT id, file_name, file_type, mime_type, file_size, description, uploaded_by, created_at
                FROM patient_files
                WHERE patient_id = :patient_id
                ORDER BY created_at DESC
            """), {"patient_id": patient_id}).fetchall()
            return [
                {
                    "id": r[0], "file_name": r[1], "file_type": r[2],
                    "mime_type": r[3], "file_size": r[4], "description": r[5],
                    "uploaded_by": r[6], "created_at": str(r[7])
                }
                for r in rows
            ]
    except Exception as e:
        logger.error(f"Erro ao listar arquivos: {e}")
        return []


@app.get("/api/v1/patients/files/{file_id}/download")
async def download_patient_file(file_id: int, request: Request):
    """Gera URL temporaria para download/visualizacao do arquivo."""
    tenant_slug = get_tenant_slug(request)
    if not minio_client:
        raise HTTPException(status_code=503, detail="Armazenamento nao disponivel")
    try:
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO '{tenant_slug}', public"))
            row = conn.execute(text("""
                SELECT storage_key, file_name, mime_type FROM patient_files WHERE id = :file_id
            """), {"file_id": file_id}).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Arquivo nao encontrado")

        from datetime import timedelta
        url = minio_client.presigned_get_object(
            MINIO_BUCKET,
            row[0],
            expires=timedelta(hours=1),
        )
        if url:
            url = url.replace("http://kairos-minio:9000", "/storage")

        return {
            "url": url,
            "file_name": row[1],
            "mime_type": row[2]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/patients/files/{file_id}")
async def delete_patient_file(file_id: int, request: Request):
    """Remove arquivo do paciente."""
    tenant_slug = get_tenant_slug(request)
    if not minio_client:
        raise HTTPException(status_code=503, detail="Armazenamento nao disponivel")
    try:
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO '{tenant_slug}', public"))
            row = conn.execute(text("""
                SELECT storage_key FROM patient_files WHERE id = :file_id
            """), {"file_id": file_id}).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Arquivo nao encontrado")

            # Remove do MinIO
            try:
                minio_client.remove_object(MINIO_BUCKET, row[0])
            except Exception:
                pass

            # Remove do banco
            conn.execute(text("DELETE FROM patient_files WHERE id = :file_id"), {"file_id": file_id})
            conn.commit()

        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/consultations")
async def save_consultation(data: ConsultationSave, request: Request):
    """Salva consulta finalizada no historico."""
    tenant_slug = get_tenant_slug(request)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO '{tenant_slug}', public"))
            row = conn.execute(text("""
                INSERT INTO consultations
                    (patient_id, doctor_name, doctor_crm, transcript,
                     soap_json, documents_json, duration_seconds, status)
                VALUES
                    (:patient_id, :doctor_name, :doctor_crm, :transcript,
                     :soap_json, :documents_json, :duration_seconds, 'completed')
                RETURNING id
            """), {
                "patient_id": data.patient_id,
                "doctor_name": data.doctor_name,
                "doctor_crm": data.doctor_crm,
                "transcript": data.transcript,
                "soap_json": json.dumps(data.soap_json),
                "documents_json": json.dumps(data.documents_json),
                "duration_seconds": data.duration_seconds,
            }).fetchone()
            conn.commit()
            return {"id": row[0], "status": "saved"}
    except Exception as e:
        logger.error(f"Erro ao salvar consulta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/consultations")
async def list_consultations(request: Request, q: str = "", page: int = 1, limit: int = 20):
    """Lista consultas com filtro por nome/CPF do paciente."""
    tenant_slug = get_tenant_slug(request)
    offset = (page - 1) * limit
    try:
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO '{tenant_slug}', public"))

            where_clause = ""
            params = {"lim": limit, "off": offset}
            if q:
                where_clause = "WHERE p.name ILIKE :q_name OR p.cpf LIKE :q_cpf"
                params["q_name"] = f"%{q}%"
                params["q_cpf"] = f"%{q}%"

            # Contagem total
            count_row = conn.execute(text(f"""
                SELECT COUNT(*) FROM consultations c
                LEFT JOIN patients p ON c.patient_id = p.id
                {where_clause}
            """), params).fetchone()
            total = count_row[0] if count_row else 0

            # Resultados paginados
            rows = conn.execute(text(f"""
                SELECT c.id, c.patient_id, p.name as patient_name, p.cpf as patient_cpf,
                       c.doctor_name, c.doctor_crm, c.duration_seconds, c.status,
                       c.soap_json, c.started_at, c.ended_at, c.created_at
                FROM consultations c
                LEFT JOIN patients p ON c.patient_id = p.id
                {where_clause}
                ORDER BY c.created_at DESC
                LIMIT :lim OFFSET :off
            """), params).fetchall()

            return {
                "total": total,
                "page": page,
                "limit": limit,
                "items": [
                    {
                        "id": r[0], "patient_id": r[1],
                        "patient_name": r[2] or "Não identificado",
                        "patient_cpf": r[3] or "",
                        "doctor_name": r[4], "doctor_crm": r[5],
                        "duration_seconds": r[6], "status": r[7],
                        "soap_json": r[8] if isinstance(r[8], dict) else json.loads(r[8]) if r[8] else {},
                        "started_at": str(r[9]) if r[9] else None,
                        "ended_at": str(r[10]) if r[10] else None,
                        "created_at": str(r[11]) if r[11] else None,
                    }
                    for r in rows
                ]
            }
    except Exception as e:
        logger.error(f"Erro ao listar consultas: {e}")
        return {"total": 0, "page": page, "limit": limit, "items": []}


@app.get("/api/v1/consultations/{consultation_id}")
async def get_consultation(consultation_id: int, request: Request):
    """Retorna detalhes completos de uma consulta."""
    tenant_slug = get_tenant_slug(request)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO '{tenant_slug}', public"))
            row = conn.execute(text("""
                SELECT c.id, c.patient_id, p.name as patient_name, p.cpf as patient_cpf,
                       p.sex, p.birth_date, p.phone,
                       c.doctor_name, c.doctor_crm, c.transcript,
                       c.soap_json, c.documents_json,
                       c.duration_seconds, c.status,
                       c.started_at, c.ended_at, c.created_at
                FROM consultations c
                LEFT JOIN patients p ON c.patient_id = p.id
                WHERE c.id = :cid
            """), {"cid": consultation_id}).fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Consulta não encontrada")

            return {
                "id": row[0], "patient_id": row[1],
                "patient_name": row[2] or "Não identificado",
                "patient_cpf": row[3] or "",
                "patient_sex": row[4], "patient_birth_date": str(row[5]) if row[5] else None,
                "patient_phone": row[6],
                "doctor_name": row[7], "doctor_crm": row[8],
                "transcript": row[9],
                "soap_json": row[10] if isinstance(row[10], dict) else json.loads(row[10]) if row[10] else {},
                "documents_json": row[11] if isinstance(row[11], list) else json.loads(row[11]) if row[11] else [],
                "duration_seconds": row[12], "status": row[13],
                "started_at": str(row[14]) if row[14] else None,
                "ended_at": str(row[15]) if row[15] else None,
                "created_at": str(row[16]) if row[16] else None,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar consulta: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# Copiloto Live — WebSocket em Tempo Real (Fase 4)
# ═══════════════════════════════════════════════════════════

from copilot_pipeline import CopilotSession, analyze_transcript_realtime
import uuid
import asyncio as _asyncio
import base64 as _base64

# STT Diarization (lazy import)
try:
    from stt_pipeline import diarize_accumulated_chunks, check_stt_health
    STT_AVAILABLE = True
except Exception as _stt_err:
    logger.warning(f"STT pipeline não disponível: {_stt_err}")
    STT_AVAILABLE = False

# Active copilot sessions in memory (persisted across reconnects)
active_sessions: dict[str, CopilotSession] = {}
# Audio chunks por sessão (para diarização)
session_audio_chunks: dict[str, list] = {}


@app.websocket("/ws/copilot")
async def copilot_websocket(ws: WebSocket, tenant_slug: str = ""):
    """WebSocket para copiloto clinico em tempo real.

    O tenant_slug vem como query parameter: /ws/copilot?tenant_slug=clinica_alfa
    """
    if not tenant_slug:
        # Tenta pegar do header (caso venha de proxy)
        tenant_slug = ws.headers.get("X-Tenant-Slug", "")
    if not tenant_slug:
        await ws.close(code=4000, reason="tenant_slug required")
        return
    await ws.accept()

    # Check for reconnection
    try:
        first_msg = await _asyncio.wait_for(ws.receive_json(), timeout=2.0)
        if first_msg.get("type") == "reconnect" and first_msg.get("session_id") in active_sessions:
            session_id = first_msg["session_id"]
            session = active_sessions[session_id]
            session.mark_reconnected()
            logger.info(f"Copilot session {session_id} RECONNECTED (attempt #{session.disconnect_count})")
            await ws.send_json({
                "type": "reconnected",
                "session_id": session_id,
                "state": session.get_session_state()
            })
        else:
            # New session — process first message after setup
            session_id = str(uuid.uuid4())[:8]
            session = CopilotSession(neo4j_driver, session_id, tenant_slug=tenant_slug)
            active_sessions[session_id] = session
            logger.info(f"Copilot session {session_id} started")
            await ws.send_json({"type": "connected", "session_id": session_id})

            # Process the first message if it wasn't a reconnect
            if first_msg.get("type") == "text" and first_msg.get("text", "").strip():
                session.add_text(first_msg["text"].strip())
                await ws.send_json({"type": "ack", "chars_total": len(session.full_transcript)})

    except _asyncio.TimeoutError:
        # No initial message, create new session
        session_id = str(uuid.uuid4())[:8]
        session = CopilotSession(neo4j_driver, session_id, tenant_slug=tenant_slug)
        active_sessions[session_id] = session
        logger.info(f"Copilot session {session_id} started")
        await ws.send_json({"type": "connected", "session_id": session_id})

    # Background task: monitor silence
    async def silence_monitor():
        while session.is_connected:
            await _asyncio.sleep(5)
            silence = session.check_silence()
            if silence:
                try:
                    await ws.send_json(silence)
                except:
                    break
            audio_alert = session.check_audio_level()
            if audio_alert:
                try:
                    await ws.send_json(audio_alert)
                except:
                    break

    monitor_task = _asyncio.create_task(silence_monitor())

    # Background analysis task management
    analysis_task = None

    async def _run_analysis_and_send(ws_conn, sess, neo4j_drv, msg_type="soap_update"):
        """Executa análise em background e envia resultado via WS."""
        try:
            result = await analyze_transcript_realtime(sess, neo4j_drv)
            sess.last_soap_result = result
            await ws_conn.send_json({
                "type": msg_type,
                "data": result
            })
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            try:
                await ws_conn.send_json({
                    "type": "error",
                    "message": f"Erro na análise: {str(e)}"
                })
            except Exception:
                pass  # WS may have closed

    try:
        while True:
            data = await ws.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "text":
                text = data.get("text", "").strip()
                if text:
                    session.add_text(text)
                    await ws.send_json({
                        "type": "ack",
                        "chars_total": len(session.full_transcript)
                    })

                    # Auto-analyze as background task (não bloqueia heartbeats)
                    if session.should_analyze():
                        await ws.send_json({"type": "analyzing"})
                        # Cancelar análise anterior se ainda rodando
                        if analysis_task and not analysis_task.done():
                            analysis_task.cancel()
                        analysis_task = _asyncio.create_task(
                            _run_analysis_and_send(ws, session, neo4j_driver)
                        )

            elif msg_type == "audio_level":
                level = float(data.get("level", 0))
                session.update_audio_level(level)

            elif msg_type == "heartbeat":
                session.update_heartbeat()
                await ws.send_json({
                    "type": "heartbeat_ack",
                    "server_time": time.time(),
                    "session_seconds": round(time.time() - session.created_at)
                })

            elif msg_type == "audio_chunk":
                # Receber chunk de áudio (base64) para diarização
                chunk_data = data.get("data", "")
                if chunk_data and STT_AVAILABLE:
                    try:
                        audio_bytes = _base64.b64decode(chunk_data)
                        if session_id not in session_audio_chunks:
                            session_audio_chunks[session_id] = []
                        session_audio_chunks[session_id].append(audio_bytes)
                    except Exception as e:
                        logger.warning(f"Erro ao decodificar audio_chunk: {e}")

            elif msg_type == "analyze":
                await ws.send_json({"type": "analyzing"})
                if analysis_task and not analysis_task.done():
                    analysis_task.cancel()
                analysis_task = _asyncio.create_task(
                    _run_analysis_and_send(ws, session, neo4j_driver)
                )

            elif msg_type == "end":
                # Para o end, esperamos a análise completar antes de encerrar
                if session.full_transcript.strip():
                    await ws.send_json({"type": "analyzing"})
                    # Cancelar background task anterior
                    if analysis_task and not analysis_task.done():
                        analysis_task.cancel()
                    # Executar análise final e aguardar
                    result = await analyze_transcript_realtime(
                        session, neo4j_driver
                    )
                    session.last_soap_result = result
                    await ws.send_json({
                        "type": "final_soap",
                        "data": result
                    })

                # Diarização final (se houver chunks de áudio)
                if STT_AVAILABLE and session_id in session_audio_chunks:
                    chunks = session_audio_chunks.pop(session_id, [])
                    if chunks:
                        try:
                            await ws.send_json({"type": "diarizing"})
                            diarization = await diarize_accumulated_chunks(chunks)
                            await ws.send_json({
                                "type": "diarization_result",
                                "data": diarization
                            })
                        except Exception as e:
                            logger.error(f"Erro na diarização: {e}")
                            await ws.send_json({
                                "type": "diarization_error",
                                "message": str(e)
                            })

                await ws.send_json({"type": "session_ended"})
                # Clean up finished session
                active_sessions.pop(session_id, None)
                session_audio_chunks.pop(session_id, None)
                break

    except WebSocketDisconnect:
        logger.info(f"Copilot session {session_id} disconnected")
        # Cancelar task de análise pendente
        if analysis_task and not analysis_task.done():
            analysis_task.cancel()
        # Keep session alive for 5 minutes for possible reconnect
        session.mark_disconnected()
        logger.info(f"Session {session_id} preserved for reconnect (transcript: {len(session.full_transcript)} chars)")

        # Auto-cleanup after 5 minutes if no reconnect
        async def cleanup_orphan():
            await _asyncio.sleep(300)  # 5 minutes
            if session_id in active_sessions and not active_sessions[session_id].is_connected:
                active_sessions.pop(session_id, None)
                logger.info(f"Orphan session {session_id} cleaned up after 5min timeout")
        _asyncio.create_task(cleanup_orphan())

    except Exception as e:
        logger.error(f"Copilot session {session_id} error: {e}")
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        monitor_task.cancel()


@app.get("/api/v1/copilot/sessions")
async def list_copilot_sessions(tenant_slug: str = Depends(get_tenant_slug)):
    """Lista sessoes ativas do copiloto."""
    return {
        "active_sessions": [
            {
                "session_id": s.session_id,
                "transcript_length": len(s.full_transcript),
                "analysis_count": s.analysis_count,
                "connected": s.is_connected,
                "disconnect_count": s.disconnect_count,
                "seconds_active": round(time.time() - s.created_at)
            }
            for s in active_sessions.values()
        ],
        "count": len(active_sessions)
    }


# ═══════════════════════════════════════════════════════════
# Backup Upload — Caixa-Preta da Consulta
# ═══════════════════════════════════════════════════════════

@app.post("/api/v1/clinical/soap/backup")
async def soap_from_backup(
    tenant_slug: str = Depends(get_tenant_slug),
    audio: UploadFile = File(...),
    session_id: Optional[str] = Form(default=None)
):
    """Recebe audio de backup gravado localmente no dispositivo do medico.
    Usado quando a transcricao em tempo real falhou durante a consulta.
    Processa o audio completo via Gemini e retorna SOAP final."""

    from soap_pipeline import process_audio_to_soap
    from pathlib import Path

    AUDIO_MIME_MAP = {
        ".wav": "audio/wav", ".mp3": "audio/mpeg", ".ogg": "audio/ogg",
        ".m4a": "audio/mp4", ".webm": "audio/webm", ".flac": "audio/flac",
    }

    ext = Path(audio.filename or "backup.webm").suffix.lower()
    mime_type = AUDIO_MIME_MAP.get(ext, "audio/webm")

    audio_bytes = await audio.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Arquivo de backup vazio")
    if len(audio_bytes) > 100 * 1024 * 1024:  # 100MB for full consultations
        raise HTTPException(status_code=413, detail="Backup excede 100MB")

    logger.info(f"Backup SOAP: {audio.filename} ({len(audio_bytes)} bytes, session={session_id})")

    result = await process_audio_to_soap(audio_bytes, audio.filename or "backup.webm", mime_type)

    if result.get("status") == "ok":
        result["source"] = "backup_upload"
        result["original_session_id"] = session_id

    return result


import time


# ═══════════════════════════════════════════════════════════
# Startup
# ═══════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup():
    logger.info("Kairos Clinical API v1.1.0 started")
    logger.info(f"Neo4j: {NEO4J_URI}")
    logger.info(f"Postgres: {PG_HOST}:5432/{PG_DB}")
    logger.info(f"ChromaDB: {CHROMA_HOST}:{CHROMA_PORT}")






class ChatRequest(BaseModel):
    message: str
    doctor_id: Optional[str] = None

from rag_pipeline import process_graph_chat

@app.post("/api/v1/clinical/graph/chat")
@app.post("/graph/chat")
async def graph_chat(req: ChatRequest, tenant_slug: str = Depends(get_tenant_slug)):
    if not neo4j_driver:
        raise HTTPException(status_code=503, detail="Neo4j nao disponivel")
    try:
        result = await process_graph_chat(req.message, req.doctor_id, tenant_slug, neo4j_driver)
        return result
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3100)


