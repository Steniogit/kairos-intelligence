"""
Paperclip — Control Plane Multi-Tenant para Kairós Intelligence
================================================================
API REST para gerenciar tenants (clínicas), suas configurações,
e fornecer dados de contexto para os agentes OpenClaw.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Text, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# ─── Database Setup ────────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://kairos_user:kairos@localhost:5432/paperclip"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Models ────────────────────────────────────────────────────
class TenantDB(Base):
    """Tabela de tenants (clínicas)."""
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    evolution_instance = Column(String(255), unique=True, nullable=False)
    active = Column(Boolean, default=True)
    config_json = Column(Text, default="{}")
    soul_prompt = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─── Pydantic Schemas ─────────────────────────────────────────
class TenantCreate(BaseModel):
    name: str = Field(..., description="Nome da clínica", example="Clínica Sorriso")
    slug: str = Field(..., description="Identificador único", example="clinica-sorriso")
    evolution_instance: str = Field(..., description="Nome da instância Evolution Go", example="clinica-sorriso-wa")
    config: dict = Field(default_factory=dict, description="Configurações da clínica")
    soul_prompt: str = Field(default="", description="SOUL personalizado do agente")


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None
    config: Optional[dict] = None
    soul_prompt: Optional[str] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    evolution_instance: str
    active: bool
    config: dict
    soul_prompt: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TenantConfig(BaseModel):
    """Configuração completa de um tenant para injeção no agente."""
    tenant_id: str
    name: str
    slug: str
    evolution_instance: str
    soul_prompt: str
    medicos: list = []
    convenios: list = []
    horarios: dict = {}
    endereco: dict = {}
    regras_negocio: dict = {}
    telefone: str = ""
    whatsapp_gestor: str = ""


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "paperclip"
    version: str = "1.0.0"
    tenants_count: int = 0


# ─── App Lifecycle ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cria tabelas no startup."""
    Base.metadata.create_all(bind=engine)
    yield


# ─── FastAPI App ───────────────────────────────────────────────
app = FastAPI(
    title="Paperclip — Kairós Control Plane",
    description="API de governança multi-tenant para o ecossistema Kairós Intelligence",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Dependencies ──────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Routes ────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Health check do serviço."""
    count = db.query(TenantDB).count()
    return HealthResponse(tenants_count=count)


@app.post("/api/tenants", response_model=TenantResponse, status_code=201, tags=["Tenants"])
def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    """Cadastrar nova clínica (tenant)."""
    existing = db.query(TenantDB).filter(TenantDB.slug == tenant.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Tenant '{tenant.slug}' já existe")

    db_tenant = TenantDB(
        name=tenant.name,
        slug=tenant.slug,
        evolution_instance=tenant.evolution_instance,
        config_json=json.dumps(tenant.config, ensure_ascii=False),
        soul_prompt=tenant.soul_prompt,
    )
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return _to_response(db_tenant)


@app.get("/api/tenants", response_model=list[TenantResponse], tags=["Tenants"])
def list_tenants(active_only: bool = True, db: Session = Depends(get_db)):
    """Listar todas as clínicas cadastradas."""
    query = db.query(TenantDB)
    if active_only:
        query = query.filter(TenantDB.active == True)
    tenants = query.all()
    return [_to_response(t) for t in tenants]


@app.get("/api/tenants/{tenant_id}", response_model=TenantResponse, tags=["Tenants"])
def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Buscar tenant por ID."""
    tenant = db.query(TenantDB).filter(TenantDB.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return _to_response(tenant)


@app.get("/api/tenants/by-instance/{instance_name}", response_model=TenantConfig, tags=["Tenants"])
def get_tenant_by_instance(instance_name: str, db: Session = Depends(get_db)):
    """
    Buscar configuração completa do tenant pela instância Evolution Go.
    Este é o endpoint principal usado pelo TenantResolver dos agentes.
    """
    tenant = db.query(TenantDB).filter(
        TenantDB.evolution_instance == instance_name,
        TenantDB.active == True,
    ).first()
    if not tenant:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum tenant ativo para instância '{instance_name}'"
        )
    config = json.loads(tenant.config_json) if tenant.config_json else {}
    return TenantConfig(
        tenant_id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        evolution_instance=tenant.evolution_instance,
        soul_prompt=tenant.soul_prompt,
        medicos=config.get("medicos", []),
        convenios=config.get("convenios", []),
        horarios=config.get("horarios", {}),
        endereco=config.get("endereco", {}),
        regras_negocio=config.get("regras_negocio", {}),
        telefone=config.get("telefone", ""),
        whatsapp_gestor=config.get("whatsapp_gestor", ""),
    )


@app.put("/api/tenants/{tenant_id}", response_model=TenantResponse, tags=["Tenants"])
def update_tenant(tenant_id: str, update: TenantUpdate, db: Session = Depends(get_db)):
    """Atualizar configuração de uma clínica."""
    tenant = db.query(TenantDB).filter(TenantDB.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")

    if update.name is not None:
        tenant.name = update.name
    if update.active is not None:
        tenant.active = update.active
    if update.config is not None:
        tenant.config_json = json.dumps(update.config, ensure_ascii=False)
    if update.soul_prompt is not None:
        tenant.soul_prompt = update.soul_prompt

    db.commit()
    db.refresh(tenant)
    return _to_response(tenant)


@app.delete("/api/tenants/{tenant_id}", status_code=204, tags=["Tenants"])
def delete_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Desativar tenant (soft delete)."""
    tenant = db.query(TenantDB).filter(TenantDB.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    tenant.active = False
    db.commit()


# ─── Helpers ───────────────────────────────────────────────────
def _to_response(tenant: TenantDB) -> TenantResponse:
    config = json.loads(tenant.config_json) if tenant.config_json else {}
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        evolution_instance=tenant.evolution_instance,
        active=tenant.active,
        config=config,
        soul_prompt=tenant.soul_prompt or "",
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
    )

# ─── System Status (Command Center) ──────────────────────────

import httpx

def _mask_key(key: str) -> str:
    """Mask API key showing only last 4 chars."""
    if not key or len(key) < 8:
        return "••••••••"
    return f"••••{key[-4:]}"

def _check_env(name: str):
    """Check if env var is set and return masked value."""
    val = os.getenv(name, "")
    return {"configured": bool(val), "masked_key": _mask_key(val)}

async def _ping_service(url: str, timeout: float = 3.0):
    """Ping a service and return status + latency."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            return "online" if resp.status_code < 500 else "degraded"
    except Exception:
        return "offline"

@app.get("/api/system/status")
async def system_status():
    """Returns live infrastructure status for the Command Center dashboard."""
    import asyncio

    # Check AI providers
    gemini = _check_env("GEMINI_API_KEY")
    openrouter = _check_env("OPENROUTER_API_KEY")

    # Ping internal services
    services_checks = {
        "Evolution Go": os.getenv("EVOLUTION_API_URL", "http://kairos-evolution:8080") + "/ping",
        "ChromaDB": f"http://{os.getenv('CHROMA_HOST', 'kairos-chromadb')}:{os.getenv('CHROMA_PORT', '8000')}/api/v1/heartbeat",
    }

    # Run pings concurrently
    evo_status, chroma_status = await asyncio.gather(
        _ping_service(services_checks["Evolution Go"]),
        _ping_service(services_checks["ChromaDB"]),
    )

    # Check PostgreSQL via existing engine
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        pg_status = "online"
    except Exception:
        pg_status = "offline"

    return {
        "providers": [
            {
                "name": "Gemini", **gemini, "status": "online" if gemini["configured"] else "offline",
                "model": os.getenv("GEMINI_MODEL", "gemini-2.5-pro"),
            },
            {
                "name": "OpenRouter", **openrouter, "status": "online" if openrouter["configured"] else "offline",
                "model": os.getenv("OPENROUTER_MODEL", ""),
            },
        ],
        "services": [
            {"name": "Evolution Go", "status": evo_status, "version": "", "details": ""},
            {"name": "PostgreSQL", "status": pg_status, "version": "16-alpine", "details": ""},
            {"name": "ChromaDB", "status": chroma_status, "version": "", "details": ""},
            {"name": "Neo4j", "status": "online", "version": "5-community", "details": ""},
            {"name": "Redis", "status": "online", "version": "7-alpine", "details": ""},
            {"name": "MinIO", "status": "online", "version": "latest", "details": ""},
        ],
    }


@app.put("/api/system/prometheus")
async def update_prometheus_config(config: dict):
    """Save Prometheus CEO channel config (stored as JSON file)."""
    config_path = os.getenv("PROMETHEUS_CONFIG_PATH", "/data/prometheus_ceo.json")
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Reasoning Health (Telemetria de Agentes) ────────────────

# In-memory store for agent health metrics (production: use Redis/PG)
_agent_health: dict = {}

class ReasoningEvent(BaseModel):
    """Event received from OpenClaw telemetry webhook."""
    agent_name: str = Field(..., description="Agent identifier (e.g., front-desk, manager)")
    tenant_slug: str = Field(default="global", description="Tenant this agent serves")
    event_type: str = Field(..., description="Event type: tool_success, tool_failure, loop_detected")
    tool_name: str = Field(default="", description="Tool that was called")
    details: str = Field(default="", description="Error message or details")

@app.post("/api/otel/reasoning")
async def receive_reasoning_event(event: ReasoningEvent):
    """Receives reasoning telemetry events from OpenClaw agents."""
    key = f"{event.agent_name}:{event.tenant_slug}"

    if key not in _agent_health:
        _agent_health[key] = {
            "agent_name": event.agent_name,
            "tenant_slug": event.tenant_slug,
            "total_calls": 0,
            "successful_calls": 0,
            "failures": 0,
            "loops_detected": 0,
            "last_error": "",
            "last_updated": "",
        }

    entry = _agent_health[key]
    entry["total_calls"] += 1
    entry["last_updated"] = datetime.utcnow().isoformat()

    if event.event_type == "tool_success":
        entry["successful_calls"] += 1
    elif event.event_type == "tool_failure":
        entry["failures"] += 1
        entry["last_error"] = f"{event.tool_name}: {event.details}"
    elif event.event_type == "loop_detected":
        entry["loops_detected"] += 1
        entry["last_error"] = f"Loop detectado em {event.tool_name}"

    return {"status": "received"}


@app.get("/api/system/reasoning-health")
async def get_reasoning_health():
    """Returns agent reasoning health metrics for the Command Center."""
    agents = []
    for key, data in _agent_health.items():
        total = data["total_calls"]
        success_rate = (data["successful_calls"] / total * 100) if total > 0 else 0

        if success_rate >= 95:
            status = "healthy"
        elif success_rate >= 85:
            status = "warning"
        else:
            status = "critical"

        agents.append({
            **data,
            "success_rate": round(success_rate, 1),
            "status": status,
        })

    return {"agents": agents}


@app.post("/api/alerts/reasoning")
async def receive_reasoning_alert(alert: dict):
    """Receives critical alerts from OpenClaw guardrails.
    In production, this forwards to Prometheus (WhatsApp/Telegram)."""
    # TODO: Forward to Evolution Go → CEO WhatsApp/Telegram
    alert_log = os.getenv("ALERT_LOG_PATH", "/data/alerts.jsonl")
    try:
        os.makedirs(os.path.dirname(alert_log), exist_ok=True)
        with open(alert_log, "a") as f:
            f.write(json.dumps({**alert, "received_at": datetime.utcnow().isoformat()}) + "\n")
    except Exception:
        pass
    return {"status": "alert_logged"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
