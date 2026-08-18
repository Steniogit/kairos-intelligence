"""
Kairos Intelligence — Pre-Flight Check
Valida todos os subsistemas antes de iniciar uma consulta.
Garante que nenhuma consulta seja perdida por falha tecnica.
"""

import os
import time
import logging
import tempfile

from google import genai
from google.genai import types

logger = logging.getLogger("kairos-clinical.preflight")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


async def check_postgres(engine_or_conn) -> dict:
    """Verifica conectividade com Postgres."""
    try:
        from sqlalchemy import text
        start = time.time()
        if hasattr(engine_or_conn, "connect"):
            with engine_or_conn.connect() as conn:
                conn.execute(text("SELECT 1"))
        else:
            engine_or_conn.execute(text("SELECT 1"))
        latency = round((time.time() - start) * 1000)
        return {"status": "ok", "latency_ms": latency}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def check_neo4j(driver) -> dict:
    """Verifica conectividade com Neo4j."""
    if not driver:
        return {"status": "error", "message": "Driver nao configurado"}
    try:
        start = time.time()
        with driver.session() as session:
            session.run("RETURN 1")
        latency = round((time.time() - start) * 1000)
        return {"status": "ok", "latency_ms": latency}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def check_chromadb(host: str, port: int) -> dict:
    """Verifica conectividade com ChromaDB."""
    import httpx
    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"http://{host}:{port}/api/v1/heartbeat")
        latency = round((time.time() - start) * 1000)
        if r.status_code in [200, 410, 404, 401]:
            return {"status": "ok", "latency_ms": latency}
        return {"status": "error", "message": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


_gemini_cache = {"status": None, "timestamp": 0}

async def check_gemini() -> dict:
    """Verifica se a API Gemini esta acessivel otimizando chamadas (Cache de 30s)."""
    global _gemini_cache
    if not GEMINI_API_KEY:
        return {"status": "error", "message": "GEMINI_API_KEY nao configurada"}
    
    # Retornar cache se for recente (< 30 segundos)
    now = time.time()
    if _gemini_cache["status"] and (now - _gemini_cache["timestamp"] < 30):
        return _gemini_cache["status"]

    try:
        start = time.time()
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Otimizacao: Apenas pegar os metadados do modelo em vez de gerar texto
        # Isso nao consome a cota pesada de generate_content
        model_name = os.getenv("COPILOT_MODEL", "gemini-2.5-flash")
        
        # Para evitar bloqueio do event loop, delegamos para thread
        import asyncio
        def _fetch_model():
            return client.models.get(model=model_name)
            
        model_info = await asyncio.to_thread(_fetch_model)
        
        latency = round((time.time() - start) * 1000)
        if model_info:
            result = {"status": "ok", "latency_ms": latency, "model": model_name}
            _gemini_cache = {"status": result, "timestamp": now}
            return result
            
        return {"status": "error", "message": "Modelo nao encontrado no Gemini"}
    except Exception as e:
        # Em caso de 429, se ja tivermos um cache anterior, podemos tentar mante-lo
        if "429" in str(e) and _gemini_cache["status"] and _gemini_cache["status"]["status"] == "ok":
            return _gemini_cache["status"]
            
        return {"status": "error", "message": str(e)}


async def check_tmpfs() -> dict:
    """Verifica espaco disponivel no tmpfs (disco RAM para audio LGPD)."""
    try:
        tmpfs_path = "/tmp"
        stat = os.statvfs(tmpfs_path)
        free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
        total_mb = (stat.f_blocks * stat.f_frsize) / (1024 * 1024)
        used_pct = round((1 - stat.f_bavail / stat.f_blocks) * 100, 1)

        if free_mb < 50:
            return {
                "status": "warning",
                "message": f"Espaco baixo: {free_mb:.0f}MB livres",
                "free_mb": round(free_mb),
                "total_mb": round(total_mb),
                "used_percent": used_pct
            }
        return {
            "status": "ok",
            "free_mb": round(free_mb),
            "total_mb": round(total_mb),
            "used_percent": used_pct
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def check_write_permission() -> dict:
    """Verifica se consegue escrever no tmpfs (necessario para processar audio)."""
    try:
        fd, path = tempfile.mkstemp(dir="/tmp", prefix="preflight_")
        os.write(fd, b"preflight_test")
        os.close(fd)
        os.unlink(path)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def run_preflight(engine_or_conn, neo4j_driver, chroma_host, chroma_port, tenant_slug: str = "") -> dict:
    """Executa todas as verificacoes pre-voo.
    
    Retorna um dicionario com o resultado de cada check e um status geral.
    Se QUALQUER check critico falhar, o status geral sera 'fail'.
    """
    import asyncio

    # Executar checks em paralelo
    results = await asyncio.gather(
        check_postgres(engine_or_conn),
        check_neo4j(neo4j_driver),
        check_chromadb(chroma_host, chroma_port),
        check_gemini(),
        check_tmpfs(),
        check_write_permission(),
        return_exceptions=True
    )

    checks = {
        "postgres": results[0] if not isinstance(results[0], Exception) else {"status": "error", "message": str(results[0])},
        "neo4j": results[1] if not isinstance(results[1], Exception) else {"status": "error", "message": str(results[1])},
        "chromadb": results[2] if not isinstance(results[2], Exception) else {"status": "error", "message": str(results[2])},
        "gemini": results[3] if not isinstance(results[3], Exception) else {"status": "error", "message": str(results[3])},
        "tmpfs": results[4] if not isinstance(results[4], Exception) else {"status": "error", "message": str(results[4])},
        "write_permission": results[5] if not isinstance(results[5], Exception) else {"status": "error", "message": str(results[5])},
    }

    # Definir quais checks sao criticos (bloqueiam a consulta)
    critical = ["postgres", "neo4j", "gemini", "tmpfs", "write_permission"]
    non_critical = ["chromadb"]

    has_critical_fail = any(
        checks[c].get("status") == "error" for c in critical
    )
    has_warning = any(
        checks[c].get("status") in ("error", "warning") for c in non_critical
    ) or any(
        checks[c].get("status") == "warning" for c in critical
    )

    if has_critical_fail:
        overall = "fail"
        message = "Um ou mais sistemas criticos estao indisponiveis. NAO inicie a consulta."
    elif has_warning:
        overall = "warning"
        message = "Sistemas funcionando com ressalvas. Consulta pode prosseguir com cautela."
    else:
        overall = "ready"
        message = "Todos os sistemas operacionais. Consulta liberada."

    return {
        "overall_status": overall,
        "message": message,
        "ready_to_consult": overall in ("ready", "warning"),
        "checks": checks,
        "timestamp": time.time()
    }

