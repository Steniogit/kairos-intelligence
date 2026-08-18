"""
Kairos Intelligence — Copilot Pipeline (Fase 4)
WebSocket copilot que recebe transcricao em tempo real,
gera SOAP parcial e busca sugestoes clinicas no grafo.
"""

import os
import json
import logging
import asyncio
import time

from google import genai
from google.genai import types

logger = logging.getLogger("kairos-clinical.copilot")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
COPILOT_MODEL = os.getenv("COPILOT_MODEL", "gemini-2.5-flash")


def _get_client():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY nao configurada")
    return genai.Client(api_key=GEMINI_API_KEY)


COPILOT_SYSTEM_PROMPT = """Voce e um copiloto clinico em tempo real.
Seu objetivo e atualizar um SOAP existente com base nos fragmentos recentes da consulta.

{tenant_context}

REGRAS:
- Retorne APENAS JSON valido.
- Voce recebera o estado atual do SOAP e as novas falas do paciente/medico.
- Atualize os campos do SOAP agregando as novas informacoes ao que ja existe.
- NUNCA apague informacoes do SOAP anterior a menos que tenham sido corrigidas na nova fala.
- Marque campos incompletos com null.
- Nao invente dados nao mencionados.
- Foque em alertas de seguranca do paciente baseados na conversa inteira.

FORMATO:
{
  "soap_partial": {
    "subjective": {"chief_complaint": "", "details": ""},
    "objective": {"vital_signs": {}, "exam_findings": ""},
    "assessment": {"working_diagnoses": [], "differential": []},
    "plan": {"medications_mentioned": [], "exams_mentioned": []}
  },
  "alerts": [
    {"type": "interaction|contraindication|allergy|dosage", "severity": "high|medium|low", "message": ""}
  ],
  "suggested_questions": [],
  "entities_detected": [],
  "confidence": 0.0
}"""


class CopilotSession:
    """Gerencia uma sessao de copiloto durante a consulta.
    Inclui heartbeat, deteccao de silencio e suporte a reconexao."""

    def __init__(self, neo4j_driver, session_id: str, tenant_slug: str = ""):
        self.session_id = session_id
        self.tenant_slug = tenant_slug
        self.neo4j_driver = neo4j_driver
        self.transcript_buffer = []
        self.full_transcript = ""
        self.last_analysis_time = 0
        self.analysis_count = 0
        self.min_interval = 15  # Seconds between Gemini calls (Optimized from 8s)
        self.min_chars_for_analysis = 80  # Min new chars before analyzing
        self.analyzed_transcript_length = 0  # To track what has been sent

        # Heartbeat & health monitoring
        self.created_at = time.time()
        self.last_heartbeat = time.time()
        self.last_text_received = time.time()
        self.heartbeat_interval = 5  # Expected ping every 5s
        self.silence_threshold = 15  # Alert after 15s without text
        self.silence_alerted = False

        # Audio level monitoring
        self.last_audio_level = 0.0  # 0.0 - 1.0
        self.low_audio_count = 0  # Consecutive low-audio reports

        # Reconnection support
        self.is_connected = True
        self.disconnect_count = 0
        self.last_soap_result = None  # Cache last SOAP for reconnect

    def add_text(self, text: str):
        """Adiciona texto ao buffer."""
        self.transcript_buffer.append(text)
        self.full_transcript += " " + text
        self.last_text_received = time.time()
        self.silence_alerted = False  # Reset silence alert

    def update_heartbeat(self):
        """Atualiza timestamp do heartbeat."""
        self.last_heartbeat = time.time()

    def update_audio_level(self, level: float):
        """Atualiza nivel de audio reportado pelo cliente."""
        self.last_audio_level = level
        if level < 0.05:  # Quase silencio
            self.low_audio_count += 1
        else:
            self.low_audio_count = 0

    def check_silence(self) -> dict | None:
        """Verifica se ha silencio prolongado. Retorna alerta se necessario."""
        elapsed = time.time() - self.last_text_received
        if elapsed >= self.silence_threshold and not self.silence_alerted:
            self.silence_alerted = True
            return {
                "type": "silence_alert",
                "seconds_silent": round(elapsed),
                "message": f"Nenhum audio detectado ha {round(elapsed)}s. Verifique o microfone."
            }
        return None

    def check_audio_level(self) -> dict | None:
        """Verifica se o nivel de audio esta muito baixo."""
        if self.low_audio_count >= 3:
            return {
                "type": "low_audio_alert",
                "level": self.last_audio_level,
                "message": "Nivel de audio muito baixo. O microfone pode estar longe ou mutado."
            }
        return None

    def should_analyze(self) -> bool:
        """Decide se deve enviar ao Gemini agora."""
        now = time.time()
        time_ok = (now - self.last_analysis_time) >= self.min_interval
        buffer_text = " ".join(self.transcript_buffer)
        has_enough = len(buffer_text.strip()) >= self.min_chars_for_analysis
        return time_ok and has_enough

    def get_unprocessed_transcript(self) -> str:
        """Retorna apenas o texto que ainda nao foi analisado."""
        return self.full_transcript[self.analyzed_transcript_length:].strip()

    def mark_analyzed(self):
        self.last_analysis_time = time.time()
        self.analysis_count += 1
        self.analyzed_transcript_length = len(self.full_transcript)

    def mark_disconnected(self):
        self.is_connected = False
        self.disconnect_count += 1

    def mark_reconnected(self):
        self.is_connected = True
        self.last_heartbeat = time.time()

    def get_session_state(self) -> dict:
        """Retorna estado completo da sessao para reconexao."""
        return {
            "session_id": self.session_id,
            "transcript_length": len(self.full_transcript),
            "analysis_count": self.analysis_count,
            "disconnect_count": self.disconnect_count,
            "seconds_active": round(time.time() - self.created_at),
            "last_soap": self.last_soap_result
        }


async def analyze_transcript_realtime(session: CopilotSession, neo4j_driver=None) -> dict:
    """Analisa a transcricao acumulada e retorna SOAP parcial + alertas.

    Fluxo RAG hibrido:
    1. Busca entidades da transcricao no grafo Neo4j
    2. Injeta contexto curado no prompt do Gemini
    3. Gemini analisa COM o contexto curado
    4. Resposta inclui knowledge_attribution para o medico
    """
    try:
        client = _get_client()
        new_text = session.get_unprocessed_transcript()

        if not new_text and session.last_soap_result:
            return session.last_soap_result

        # Prepara o contexto hibrido (Estado Atual + Novo Texto)
        current_soap_json = "{}"
        if session.last_soap_result and "copilot" in session.last_soap_result:
            current_soap_json = json.dumps(session.last_soap_result["copilot"].get("soap_partial", {}))

        # RAG: buscar contexto no grafo ANTES de chamar o Gemini
        graph_context_text = ""
        graph_entities_found = []
        graph_relationships = []

        if session.neo4j_driver or neo4j_driver:
            driver = session.neo4j_driver or neo4j_driver
            graph_data = _query_graph_context(driver, session.full_transcript, session.tenant_slug)
            graph_context_text = graph_data.get("context_text", "")
            graph_entities_found = graph_data.get("entities", [])
            graph_relationships = graph_data.get("relationships", [])

        # Montar prompt com contexto do grafo
        prompt = "Atualize o SOAP abaixo com as novas informacoes da consulta.\n\n"

        if graph_context_text:
            prompt += f"{graph_context_text}\n\n"

        prompt += (
            f"--- ESTADO ATUAL DO SOAP ---\n{current_soap_json}\n\n"
            f"--- NOVAS FALAS (Fragmento recente) ---\n{new_text}"
        )

        # Fetch tenant config dynamically from Paperclip (non-blocking)
        import urllib.request
        import json
        tenant_context = ""
        if session.tenant_slug:
            def _fetch_tenant():
                try:
                    paperclip_url = os.getenv("PAPERCLIP_URL", "http://kairos-paperclip:3000")
                    req = urllib.request.Request(
                        f"{paperclip_url}/api/tenants/by-slug/{session.tenant_slug}",
                    )
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        return json.loads(resp.read().decode())
                except Exception as e:
                    logger.warning(f"Não foi possível carregar contexto do tenant {session.tenant_slug}: {e}")
                    return None

            tenant_data = await asyncio.to_thread(_fetch_tenant)
            if tenant_data:
                t_name = tenant_data.get("name", "")
                t_rules = tenant_data.get("regras_negocio", {})
                t_insurance = ", ".join(tenant_data.get("convenios", []))
                tenant_context = f"--- CONTEXTO DA CLÍNICA ---\nVocê atua na clínica '{t_name}'.\n"
                if t_insurance:
                    tenant_context += f"Convênios aceitos: {t_insurance}.\n"
                if t_rules:
                    tenant_context += f"Regras sugeridas: {json.dumps(t_rules, ensure_ascii=False)}.\n"
                tenant_context += "Nota: Pode sugerir exames ou medicamentos padrão, não precisa se ater estritamente a estas regras a menos que explicitamente exigido.\n"

        final_system_prompt = COPILOT_SYSTEM_PROMPT.replace("{tenant_context}", tenant_context)

        # Gemini call em thread separada para não bloquear o event loop
        def _call_gemini():
            return client.models.generate_content(
                model=COPILOT_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction=final_system_prompt,
                    temperature=0.1,
                    max_output_tokens=4096,
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                )
            )

        response = await asyncio.to_thread(_call_gemini)

        raw = response.text.strip()
        result = json.loads(raw)

        # Adicionar atribuicao de fontes
        graph_entity_names = {e["name"].lower() for e in graph_entities_found}
        entities_detected = result.get("entities_detected", [])

        curated = []
        general = []
        for ent in entities_detected:
            # Gemini pode retornar strings ou dicts
            ent_name = ent if isinstance(ent, str) else (ent.get("name", str(ent)) if isinstance(ent, dict) else str(ent))
            if ent_name.lower() in graph_entity_names:
                curated.append({"entity": ent_name, "source": "graph_curated", "verified": True})
            else:
                general.append({
                    "entity": ent_name,
                    "source": "general_knowledge",
                    "verified": False,
                    "warning": "Nao verificado na base curada."
                })

        result["knowledge_attribution"] = {
            "curated_items": curated,
            "general_items": general,
            "graph_coverage_percent": round(len(curated) / max(len(curated) + len(general), 1) * 100),
            "disclaimer": (
                "Itens 'graph_curated' foram verificados na base clinica curada. "
                "Itens 'general_knowledge' usam conhecimento geral do modelo e devem ser validados."
            )
        }

        # Manter compatibilidade: graph_context como lista
        if graph_entities_found:
            result["graph_context"] = [{
                "entity": e["name"],
                "source": "graph_curated",
                "graph_data": e.get("relationships", [])
            } for e in graph_entities_found]

        session.mark_analyzed()
        result["analysis_number"] = session.analysis_count
        result["transcript_length"] = len(session.full_transcript)

        return {"status": "ok", "copilot": result}

    except json.JSONDecodeError as e:
        return {"status": "error", "error": "json_parse", "message": str(e)}
    except Exception as e:
        return {"status": "error", "error": "analysis_error", "message": str(e)}


def _query_graph_context(neo4j_driver, text: str, tenant_slug: str = "") -> dict:
    """Busca entidades relevantes no grafo Neo4j e formata para injecao no prompt.

    Retorna dict com 'context_text' (str para o prompt), 'entities' e 'relationships'.
    """
    import re

    # Garantir que text é string
    if not isinstance(text, str):
        text = str(text)

    # Extrair termos candidatos
    words = text.split()
    candidates = set()
    for i, word in enumerate(words):
        clean = re.sub(r'[^\w]', '', str(word))
        if len(clean) >= 4:
            candidates.add(clean.lower())
    candidates = list(candidates)[:15]

    entities = []
    relationships = []

    if not candidates:
        return {"context_text": "", "entities": [], "relationships": []}

    try:
        with neo4j_driver.session() as db_session:
            # Tentar com label do tenant; se nao existir, buscar sem filtro
            label_filter = f":{tenant_slug}" if tenant_slug else ""
            
            # Verificar se o label existe
            if tenant_slug:
                check = db_session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
                existing_labels = check.single()["labels"]
                if tenant_slug not in existing_labels:
                    label_filter = ""  # Fallback: buscar sem filtro de tenant
            for term in candidates:
                # Busca medicamentos
                result = db_session.run(f"""
                    MATCH (d:Drug{label_filter})
                    WHERE toLower(d.name) CONTAINS toLower($name)
                    OPTIONAL MATCH (d)-[r]->(related{label_filter})
                    RETURN DISTINCT d.name as name, labels(d)[0] as type,
                           type(r) as rel, related.name as related_name,
                           labels(related)[0] as related_type
                    LIMIT 10
                """, name=term)

                seen = set()
                rels = []
                for record in result:
                    if record["name"] not in seen:
                        seen.add(record["name"])
                        entities.append({
                            "name": record["name"],
                            "type": record["type"],
                            "source": "graph_curated"
                        })
                    if record["rel"] and record["related_name"]:
                        rel_entry = {
                            "from": record["name"],
                            "relationship": record["rel"],
                            "to": record["related_name"],
                            "to_type": record["related_type"]
                        }
                        rels.append(rel_entry)
                        relationships.append(rel_entry)

                # Busca condicoes
                result = db_session.run(f"""
                    MATCH (c:Condition{label_filter})
                    WHERE toLower(c.name) CONTAINS toLower($name)
                    OPTIONAL MATCH (c)<-[r]-(related{label_filter})
                    RETURN DISTINCT c.name as name, c.cid10 as cid10,
                           labels(c)[0] as type,
                           type(r) as rel, related.name as related_name,
                           labels(related)[0] as related_type
                    LIMIT 10
                """, name=term)

                for record in result:
                    if record["name"] not in seen:
                        seen.add(record["name"])
                        entities.append({
                            "name": record["name"],
                            "type": record["type"],
                            "cid10": record.get("cid10"),
                            "source": "graph_curated"
                        })
                    if record["rel"] and record["related_name"]:
                        relationships.append({
                            "from": record["related_name"],
                            "relationship": record["rel"],
                            "to": record["name"],
                            "to_type": record["type"]
                        })

    except Exception as e:
        logger.warning(f"Graph context query error (non-fatal): {e}")

    # Deduplica
    unique_ents = {}
    for e in entities:
        unique_ents[e["name"]] = e
    entities = list(unique_ents.values())

    # Montar texto de contexto
    context_text = ""
    if entities or relationships:
        context_text = "--- CONHECIMENTO VERIFICADO (Base Curada Kairos) ---\n"
        context_text += "USE estas informacoes com PRIORIDADE. Marque dados que NAO vierem desta lista com source='general_knowledge'.\n\n"

        for ent in entities[:8]:
            cid = f" (CID-10: {ent['cid10']})" if ent.get("cid10") else ""
            context_text += f"  - {ent['name']} [{ent['type']}]{cid}\n"

        if relationships:
            context_text += "\nRelacoes verificadas:\n"
            for rel in relationships[:10]:
                context_text += f"  - {rel['from']} --[{rel['relationship']}]--> {rel['to']}\n"

    return {
        "context_text": context_text,
        "entities": entities,
        "relationships": relationships
    }

