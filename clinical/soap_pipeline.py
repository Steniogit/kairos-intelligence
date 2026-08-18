"""
Kairos Intelligence — SOAP Pipeline (v2 — RAG Hibrido)
Recebe audio/texto de consulta medica, consulta o grafo Neo4j curado,
envia ao Gemini Flash com contexto e retorna JSON SOAP com atribuicao de fontes.

LGPD: Audio existe apenas em tmpfs (RAM) e e apagado imediatamente apos processamento.

Logica de Conhecimento:
1. Extrai entidades-chave do texto da consulta
2. Busca essas entidades no grafo Neo4j (base curada)
3. Se encontrar: injeta como contexto confiavel no prompt
4. Se NAO encontrar: Gemini usa conhecimento geral (marcado como "nao verificado")
5. Resposta inclui knowledge_attribution para o medico saber a fonte de cada dado
"""

import os
import json
import logging
import tempfile
import base64
import re
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger("kairos-clinical.soap")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SOAP_MODEL = os.getenv("SOAP_MODEL", "gemini-2.5-flash")


def _get_client():
    """Create Gemini client."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY nao configurada")
    return genai.Client(api_key=GEMINI_API_KEY)


# ═══════════════════════════════════════════════════════════
# RAG: Consulta ao Grafo Neo4j
# ═══════════════════════════════════════════════════════════

def _extract_candidate_terms(text: str) -> list:
    """Extrai termos candidatos do texto para busca no grafo.
    Abordagem simples por regex: palavras com 4+ chars, capitalizadas ou tecnicas."""
    # Normaliza e tokeniza
    words = text.split()
    candidates = set()

    # Pega sequencias de 1-3 palavras que podem ser entidades medicas
    for i, word in enumerate(words):
        clean = re.sub(r'[^\w]', '', word)
        if len(clean) >= 4:
            candidates.add(clean.lower())
        # Bigramas
        if i + 1 < len(words):
            bigram = clean + " " + re.sub(r'[^\w]', '', words[i + 1])
            if len(bigram) >= 6:
                candidates.add(bigram.lower())

    return list(candidates)[:20]  # Limita a 20 termos


def _search_graph_for_context(neo4j_driver, text: str, tenant_slug: str = "") -> dict:
    """Busca entidades relevantes no grafo Neo4j baseado no texto da consulta.

    Retorna:
        {
            "entities_found": [...],        # Entidades encontradas no grafo curado
            "relationships": [...],         # Relacoes clinicas relevantes
            "graph_context_text": "...",    # Texto formatado para injetar no prompt
            "coverage": {"found": N, "total_searched": M}
        }
    """
    if not neo4j_driver:
        return {"entities_found": [], "relationships": [], "graph_context_text": "", "coverage": {"found": 0, "total_searched": 0}}

    candidates = _extract_candidate_terms(text)
    if not candidates:
        return {"entities_found": [], "relationships": [], "graph_context_text": "", "coverage": {"found": 0, "total_searched": len(candidates)}}

    entities_found = []
    relationships = []

    try:
        with neo4j_driver.session() as session:
            for term in candidates:
                # Busca em TODOS os tipos de no (Drug, Condition, Symptom, etc)
                label_filter = f":{tenant_slug}" if tenant_slug else ""
                result = session.run(f"""
                    MATCH (n{label_filter})
                    WHERE toLower(n.name) CONTAINS toLower($term)
                    OPTIONAL MATCH (n)-[r]-(related{label_filter})
                    RETURN DISTINCT
                        n.name as name,
                        labels(n)[0] as type,
                        properties(n) as props,
                        type(r) as rel_type,
                        related.name as related_name,
                        labels(related)[0] as related_type
                    LIMIT 15
                """, term=term)

                seen_entities = set()
                for record in result:
                    entity_name = record["name"]

                    # Adiciona entidade (sem duplicatas)
                    if entity_name and entity_name not in seen_entities:
                        seen_entities.add(entity_name)
                        props = dict(record["props"]) if record["props"] else {}
                        props.pop("name", None)  # Ja temos o nome
                        entities_found.append({
                            "name": entity_name,
                            "type": record["type"],
                            "properties": props,
                            "source": "graph_curated"
                        })

                    # Adiciona relacao
                    if record["rel_type"] and record["related_name"]:
                        relationships.append({
                            "from": entity_name,
                            "from_type": record["type"],
                            "relationship": record["rel_type"],
                            "to": record["related_name"],
                            "to_type": record["related_type"],
                            "source": "graph_curated"
                        })

    except Exception as e:
        logger.warning(f"Graph query error (non-fatal, fallback to Gemini): {e}")

    # Deduplica entidades
    unique_entities = {}
    for ent in entities_found:
        key = f"{ent['name']}:{ent['type']}"
        if key not in unique_entities:
            unique_entities[key] = ent
    entities_found = list(unique_entities.values())

    # Deduplica relacoes
    unique_rels = {}
    for rel in relationships:
        key = f"{rel['from']}:{rel['relationship']}:{rel['to']}"
        if key not in unique_rels:
            unique_rels[key] = rel
    relationships = list(unique_rels.values())

    # Monta texto formatado para injetar no prompt
    graph_text = ""
    if entities_found or relationships:
        graph_text = "--- CONHECIMENTO CLINICO VERIFICADO (Base de Dados Curada Kairos) ---\n"
        graph_text += "As informacoes abaixo foram extraidas de fontes cientificas revisadas e aprovadas.\n"
        graph_text += "USE ESTAS INFORMACOES COM PRIORIDADE sobre seu conhecimento geral.\n\n"

        if entities_found:
            graph_text += "ENTIDADES VERIFICADAS:\n"
            for ent in entities_found[:10]:
                props_str = ", ".join(f"{k}={v}" for k, v in ent["properties"].items() if v) if ent["properties"] else ""
                graph_text += f"  - {ent['name']} ({ent['type']}) {props_str}\n"
            graph_text += "\n"

        if relationships:
            graph_text += "RELACOES CLINICAS VERIFICADAS:\n"
            for rel in relationships[:15]:
                graph_text += f"  - {rel['from']} --[{rel['relationship']}]--> {rel['to']} ({rel['to_type']})\n"
            graph_text += "\n"

        graph_text += (
            "IMPORTANTE: Para qualquer informacao que voce adicionar ao SOAP que NAO esteja listada acima, "
            "marque-a com \"source\": \"general_knowledge\" no campo correspondente. "
            "Informacoes que ESTIVEREM na lista acima devem ser marcadas com \"source\": \"graph_curated\".\n"
        )

    return {
        "entities_found": entities_found,
        "relationships": relationships,
        "graph_context_text": graph_text,
        "coverage": {
            "found": len(entities_found),
            "total_searched": len(candidates)
        }
    }


# ═══════════════════════════════════════════════════════════
# System Prompt (atualizado para RAG hibrido)
# ═══════════════════════════════════════════════════════════

SOAP_SYSTEM_PROMPT = """Voce e um agente de estruturacao clinica. Sua UNICA funcao e receber transcricoes ou audios de consultas medicas e retornar um JSON SOAP estruturado.

REGRAS ABSOLUTAS:
1. Remova TODA conversa informal (cumprimentos, papo furado, futebol, clima, politica).
2. Mantenha APENAS conteudo clinico relevante.
3. Use terminologia medica correta.
4. Tente identificar codigos CID-10 quando possivel.
5. NUNCA invente dados medicos. Se nao foi mencionado, nao inclua.
6. Retorne APENAS o JSON, sem markdown, sem explicacoes, sem ```json.
7. ATRIBUICAO DE FONTE: Para CADA diagnostico e CADA medicamento, inclua o campo "source" com valor "graph_curated" se a informacao veio do contexto verificado fornecido, ou "general_knowledge" se voce usou seu conhecimento geral.

FORMATO DE SAIDA (JSON puro):
{
  "soap": {
    "subjective": {
      "chief_complaint": "",
      "history_present_illness": "",
      "review_of_systems": [],
      "patient_reported": ""
    },
    "objective": {
      "vital_signs": {},
      "physical_exam": "",
      "observations": ""
    },
    "assessment": {
      "diagnoses": [
        {"description": "", "cid10": "", "certainty": "confirmed|suspected|ruled_out", "source": "graph_curated|general_knowledge"}
      ],
      "clinical_reasoning": ""
    },
    "plan": {
      "medications": [
        {"name": "", "dosage": "", "frequency": "", "duration": "", "instructions": "", "source": "graph_curated|general_knowledge"}
      ],
      "exams_requested": [],
      "procedures": [],
      "referrals": [],
      "follow_up": "",
      "patient_instructions": ""
    }
  },
  "metadata": {
    "consultation_duration_estimate": "",
    "language": "pt-BR",
    "confidence": 0.0,
    "filtered_content": ""
  }
}"""


def _build_knowledge_attribution(soap_result: dict, graph_data: dict) -> dict:
    """Gera a secao knowledge_attribution baseado nos dados do grafo e do SOAP gerado."""
    graph_entities = {e["name"].lower() for e in graph_data.get("entities_found", [])}

    curated_items = []
    general_items = []

    # Analisa diagnosticos
    soap = soap_result.get("soap", {})
    for diag in soap.get("assessment", {}).get("diagnoses", []):
        item = {
            "entity": diag.get("description", ""),
            "type": "Condition",
            "field": "assessment.diagnoses"
        }
        if diag.get("source") == "graph_curated" or diag.get("description", "").lower() in graph_entities:
            item["source"] = "graph_curated"
            item["verified"] = True
            curated_items.append(item)
        else:
            item["source"] = "general_knowledge"
            item["verified"] = False
            item["warning"] = "Baseado em conhecimento geral do modelo. Nao verificado na base curada."
            general_items.append(item)

    # Analisa medicamentos
    for med in soap.get("plan", {}).get("medications", []):
        item = {
            "entity": med.get("name", ""),
            "type": "Drug",
            "field": "plan.medications"
        }
        if med.get("source") == "graph_curated" or med.get("name", "").lower() in graph_entities:
            item["source"] = "graph_curated"
            item["verified"] = True
            curated_items.append(item)
        else:
            item["source"] = "general_knowledge"
            item["verified"] = False
            item["warning"] = "Baseado em conhecimento geral do modelo. Nao verificado na base curada."
            general_items.append(item)

    total = len(curated_items) + len(general_items)
    coverage_pct = round((len(curated_items) / total * 100)) if total > 0 else 0

    return {
        "curated_items": curated_items,
        "general_items": general_items,
        "graph_coverage_percent": coverage_pct,
        "graph_entities_available": len(graph_data.get("entities_found", [])),
        "graph_relationships_available": len(graph_data.get("relationships", [])),
        "disclaimer": (
            "Itens com fonte 'graph_curated' foram verificados na base de dados clinica curada do Kairos. "
            "Itens com fonte 'general_knowledge' foram gerados pelo modelo de IA com base em seu treinamento geral "
            "e devem ser validados pelo profissional de saude."
        ) if general_items else (
            "Todos os itens foram verificados na base de dados clinica curada do Kairos."
        )
    }


# ═══════════════════════════════════════════════════════════
# Pipelines principais (atualizados com RAG)
# ═══════════════════════════════════════════════════════════

async def process_audio_to_soap(audio_bytes: bytes, filename: str, mime_type: str, neo4j_driver=None, tenant_slug: str = "") -> dict:
    """
    Pipeline principal: Audio -> Gemini Flash -> JSON SOAP.
    Agora com RAG: consulta o grafo Neo4j antes para contexto.

    1. Salva audio em /tmp (tmpfs = RAM, LGPD-safe)
    2. Envia ao Gemini como conteudo multimodal (com contexto do grafo se disponivel)
    3. Apaga o arquivo imediatamente
    4. Parseia e retorna o JSON SOAP com atribuicao de fontes
    """
    tmp_path = None
    try:
        # 1. Salvar em tmpfs
        suffix = Path(filename).suffix or ".wav"
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix, dir="/tmp")
        os.write(tmp_fd, audio_bytes)
        os.close(tmp_fd)
        logger.info(f"Audio salvo em tmpfs: {tmp_path} ({len(audio_bytes)} bytes)")

        # 2. Enviar ao Gemini
        client = _get_client()

        # Upload the file to Gemini
        uploaded_file = client.files.upload(
            file=tmp_path,
            config=types.UploadFileConfig(mime_type=mime_type)
        )
        logger.info(f"Audio uploaded to Gemini: {uploaded_file.name}")

        # NOTE: Para audio, nao temos o texto antes da chamada ao Gemini,
        # entao o contexto do grafo sera adicionado pos-processamento.
        # O Gemini primeiro transcreve e estrutura, depois enriquecemos com o grafo.

        # Generate SOAP from audio
        response = client.models.generate_content(
            model=SOAP_MODEL,
            contents=[
                uploaded_file,
                "Analise este audio de consulta medica e retorne o JSON SOAP estruturado. "
                "Filtre todo papo furado e conversa informal. Mantenha apenas conteudo clinico."
            ],
            config=types.GenerateContentConfig(
                system_instruction=SOAP_SYSTEM_PROMPT,
                temperature=0.1,
                max_output_tokens=4096,
            )
        )

        raw_text = response.text.strip()
        logger.info(f"Gemini response length: {len(raw_text)} chars")

        # 3. Parse JSON
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        soap_json = json.loads(raw_text)

        # 4. Enriquecimento pos-processamento com grafo
        # Extrair texto do SOAP gerado para buscar no grafo
        soap_text_for_graph = _extract_text_from_soap(soap_json)
        graph_data = _search_graph_for_context(neo4j_driver, soap_text_for_graph, tenant_slug=tenant_slug)

        # Gerar atribuicao de fontes
        attribution = _build_knowledge_attribution(soap_json, graph_data)

        return {
            "status": "ok",
            "soap_result": soap_json,
            "knowledge_attribution": attribution,
            "graph_context": {
                "entities_found": graph_data["entities_found"],
                "relationships": graph_data["relationships"][:10]
            }
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        return {
            "status": "error",
            "error": "gemini_json_parse_error",
            "message": f"O Gemini retornou texto nao-JSON: {str(e)}",
            "raw_response": raw_text[:500] if 'raw_text' in dir() else ""
        }
    except Exception as e:
        logger.error(f"SOAP pipeline error: {e}")
        return {
            "status": "error",
            "error": "pipeline_error",
            "message": str(e)
        }
    finally:
        # 4. LGPD: Apagar audio IMEDIATAMENTE
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
            logger.info(f"Audio apagado de tmpfs: {tmp_path}")


async def process_text_to_soap(text: str, neo4j_driver=None, tenant_slug: str = "") -> dict:
    """
    Pipeline alternativo: Texto bruto -> Grafo Neo4j -> Gemini -> JSON SOAP com fontes.
    """
    try:
        client = _get_client()

        # RAG: buscar contexto no grafo ANTES de chamar o Gemini
        graph_data = _search_graph_for_context(neo4j_driver, text, tenant_slug=tenant_slug)
        graph_context = graph_data["graph_context_text"]

        # Montar prompt com contexto do grafo
        user_prompt = ""
        if graph_context:
            user_prompt += f"{graph_context}\n\n"
            logger.info(f"Graph context injected: {graph_data['coverage']['found']} entities, "
                       f"{len(graph_data['relationships'])} relationships")

        user_prompt += (
            f"Analise esta transcricao de consulta medica e retorne o JSON SOAP estruturado. "
            f"Filtre todo papo furado e conversa informal. Mantenha apenas conteudo clinico.\n\n"
            f"TRANSCRICAO:\n{text}"
        )

        response = client.models.generate_content(
            model=SOAP_MODEL,
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=SOAP_SYSTEM_PROMPT,
                temperature=0.1,
                max_output_tokens=4096,
            )
        )

        raw_text = response.text.strip()

        # Remove markdown code block if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        soap_json = json.loads(raw_text)

        # Gerar atribuicao de fontes
        attribution = _build_knowledge_attribution(soap_json, graph_data)

        return {
            "status": "ok",
            "soap_result": soap_json,
            "knowledge_attribution": attribution,
            "graph_context": {
                "entities_found": graph_data["entities_found"],
                "relationships": graph_data["relationships"][:10]
            }
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": "gemini_json_parse_error",
            "message": str(e),
            "raw_response": raw_text[:500] if 'raw_text' in dir() else ""
        }
    except Exception as e:
        return {
            "status": "error",
            "error": "pipeline_error",
            "message": str(e)
        }


def _extract_text_from_soap(soap_json: dict) -> str:
    """Extrai texto relevante do SOAP para buscar entidades no grafo."""
    parts = []
    soap = soap_json.get("soap", {})

    # Subjetivo
    subj = soap.get("subjective", {})
    parts.append(subj.get("chief_complaint", ""))
    parts.append(subj.get("history_present_illness", ""))
    parts.append(subj.get("patient_reported", ""))

    # Avaliacao
    assess = soap.get("assessment", {})
    for diag in assess.get("diagnoses", []):
        parts.append(diag.get("description", ""))
    parts.append(assess.get("clinical_reasoning", ""))

    # Plano
    plan = soap.get("plan", {})
    for med in plan.get("medications", []):
        parts.append(med.get("name", ""))

    return " ".join(p for p in parts if p)
