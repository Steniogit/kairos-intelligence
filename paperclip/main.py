import os,json,uuid
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException,Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine,Column,String,Text,DateTime,Boolean
from sqlalchemy.orm import sessionmaker,Session,declarative_base

DATABASE_URL=os.getenv("DATABASE_URL","postgresql://kairos_user:kairos@localhost:5432/paperclip")
engine=create_engine(DATABASE_URL,pool_pre_ping=True)
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)
Base=declarative_base()

class TenantDB(Base):
    __tablename__="tenants"
    id=Column(String(36),primary_key=True,default=lambda:str(uuid.uuid4()))
    name=Column(String(255),nullable=False)
    slug=Column(String(100),unique=True,nullable=False)
    evolution_instance=Column(String(255),unique=True,nullable=False)
    active=Column(Boolean,default=True)
    config_json=Column(Text,default="{}")
    soul_prompt=Column(Text,default="")
    created_at=Column(DateTime,default=datetime.utcnow)
    updated_at=Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)

class TenantCreate(BaseModel):
    name:str;slug:str;evolution_instance:str;config:dict={};soul_prompt:str=""
class TenantUpdate(BaseModel):
    name:Optional[str]=None;active:Optional[bool]=None;config:Optional[dict]=None;soul_prompt:Optional[str]=None
class TenantResponse(BaseModel):
    id:str;name:str;slug:str;evolution_instance:str;active:bool;config:dict;soul_prompt:str;created_at:datetime;updated_at:datetime
    class Config:
        from_attributes=True
class TenantConfig(BaseModel):
    tenant_id:str;name:str;slug:str;evolution_instance:str;soul_prompt:str;medicos:list=[];convenios:list=[];horarios:dict={};endereco:dict={};regras_negocio:dict={};telefone:str="";whatsapp_gestor:str=""

@asynccontextmanager
async def lifespan(app:FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app=FastAPI(title="Paperclip - Kairos Control Plane",version="1.0.0",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

def get_db():
    db=SessionLocal()
    try:yield db
    finally:db.close()

def _resp(t):
    c=json.loads(t.config_json)if t.config_json else{}
    return TenantResponse(id=t.id,name=t.name,slug=t.slug,evolution_instance=t.evolution_instance,active=t.active,config=c,soul_prompt=t.soul_prompt or"",created_at=t.created_at,updated_at=t.updated_at)

@app.get("/health")
def health(db:Session=Depends(get_db)):
    return{"status":"healthy","service":"paperclip","tenants":db.query(TenantDB).count()}

@app.post("/api/tenants",response_model=TenantResponse,status_code=201)
def create_tenant(t:TenantCreate,db:Session=Depends(get_db)):
    if db.query(TenantDB).filter(TenantDB.slug==t.slug).first():raise HTTPException(409,"Tenant ja existe")
    o=TenantDB(name=t.name,slug=t.slug,evolution_instance=t.evolution_instance,config_json=json.dumps(t.config,ensure_ascii=False),soul_prompt=t.soul_prompt)
    db.add(o);db.commit();db.refresh(o)
    return _resp(o)

@app.get("/api/tenants",response_model=list[TenantResponse])
def list_tenants(active_only:bool=True,db:Session=Depends(get_db)):
    q=db.query(TenantDB)
    if active_only:q=q.filter(TenantDB.active==True)
    return[_resp(t)for t in q.all()]

@app.get("/api/tenants/{tid}",response_model=TenantResponse)
def get_tenant(tid:str,db:Session=Depends(get_db)):
    t=db.query(TenantDB).filter(TenantDB.id==tid).first()
    if not t:raise HTTPException(404,"Nao encontrado")
    return _resp(t)

@app.get("/api/tenants/by-instance/{inst}",response_model=TenantConfig)
def get_by_instance(inst:str,db:Session=Depends(get_db)):
    t=db.query(TenantDB).filter(TenantDB.evolution_instance==inst,TenantDB.active==True).first()
    if not t:raise HTTPException(404,f"Sem tenant para '{inst}'")
    c=json.loads(t.config_json)if t.config_json else{}
    return TenantConfig(tenant_id=t.id,name=t.name,slug=t.slug,evolution_instance=t.evolution_instance,soul_prompt=t.soul_prompt,medicos=c.get("medicos",[]),convenios=c.get("convenios",[]),horarios=c.get("horarios",{}),endereco=c.get("endereco",{}),regras_negocio=c.get("regras_negocio",{}),telefone=c.get("telefone",""),whatsapp_gestor=c.get("whatsapp_gestor",""))

@app.put("/api/tenants/{tid}",response_model=TenantResponse)
def update_tenant(tid:str,u:TenantUpdate,db:Session=Depends(get_db)):
    t=db.query(TenantDB).filter(TenantDB.id==tid).first()
    if not t:raise HTTPException(404,"Nao encontrado")
    if u.name is not None:t.name=u.name
    if u.active is not None:t.active=u.active
    if u.config is not None:t.config_json=json.dumps(u.config,ensure_ascii=False)
    if u.soul_prompt is not None:t.soul_prompt=u.soul_prompt
    db.commit();db.refresh(t)
    return _resp(t)

@app.delete("/api/tenants/{tid}",status_code=204)
def delete_tenant(tid:str,db:Session=Depends(get_db)):
    t=db.query(TenantDB).filter(TenantDB.id==tid).first()
    if not t:raise HTTPException(404,"Nao encontrado")
    t.active=False;db.commit()
