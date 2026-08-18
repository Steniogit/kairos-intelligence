"""
Kairos Intelligence — Curator Pipeline
Raspa URLs medicas, extrai entidades/relacionamentos via Gemini,
gera queries Cypher e submete para a quarentena de conhecimento.
"""

import os
import json
import logging
import re

import httpx
from google import genai
from google.genai import types

logger = logging.getLogger("kairos-clinical.curator")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
CURATOR_MODEL = os.getenv("CURATOR_MODEL", "gemini-2.5-flash")

CURATOR_SYSTEM_PROMPT = """Voce e um agente de curadoria cientifica medica. Sua UNICA funcao e receber textos de fontes medicas e extrair entidades e relacionamentos estruturados.

REGRAS:
1. Extraia APENAS informacoes explicitas no texto. NUNCA invente dados.
2. Use nomes genericos de medicamentos (nao marcas comerciais).
3. Inclua codigos CID-10 quando identificaveis.
4. Gere queries Cypher usando MERGE (idempotente).
5. Mantenha nomes em portugues brasileiro.
6. Retorne APENAS o JSON, sem markdown, sem explicacoes, sem ```json.

TIPOS DE ENTIDADES: Drug, Condition, Procedure, Symptom, Anatomy, Contraindication
TIPOS DE RELACOES: TREATS, CAUSES, CONTRAINDICATES, INTERACTS_WITH, SYMPTOM_OF, DIAGNOSED_BY

FORMATO DE SAIDA (JSON puro):
{
  "source": {
    "title": "Titulo do documento",
    "type": "bula | protocolo | artigo | diretriz"
  },
  "entities": [
    {
      "type": "Drug | Condition | Symptom",
      "name": "Nome normalizado",
      "properties": {}
    }
  ],
  "relationships": [
    {
      "from_entity": "Nome origem",
      "from_type": "Drug",
      "relationship": "TREATS",
      "to_entity": "Nome destino",
      "to_type": "Condition"
    }
  ],
  "cypher_queries": [
    "MERGE (d:Drug {name: 'X'}) SET d.drug_class = 'Y'"
  ],
  "metadata": {
    "entities_count": 0,
    "relationships_count": 0,
    "confidence": 0.0,
    "extraction_notes": ""
  }
}"""


def _get_client():
    """Create Gemini client."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY nao configurada")
    return genai.Client(api_key=GEMINI_API_KEY)


def _clean_html(html: str) -> str:
    """Remove HTML tags and excessive whitespace, keep text content."""
    # Remove script and style blocks
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode common entities
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


async def fetch_url_content(url: str) -> dict:
    """Fetch and clean content from a URL."""
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Kairos-Curator/1.0)"}
        ) as client:
            response = await client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            raw_html = response.text

            # Clean HTML to plain text
            clean_text = _clean_html(raw_html)

            # Truncate to ~8000 chars to keep Gemini output manageable
            if len(clean_text) > 8000:
                clean_text = clean_text[:8000] + "\n\n[TEXTO TRUNCADO - fonte muito longa]"

            return {
                "status": "ok",
                "url": url,
                "content_type": content_type,
                "text_length": len(clean_text),
                "text": clean_text
            }
    except httpx.HTTPStatusError as e:
        return {"status": "error", "error": f"HTTP {e.response.status_code}", "url": url}
    except Exception as e:
        return {"status": "error", "error": str(e), "url": url}


async def extract_knowledge(url: str, text: str) -> dict:
    """Send text to Gemini and extract medical entities/relationships."""
    try:
        client = _get_client()

        response = client.models.generate_content(
            model=CURATOR_MODEL,
            contents=[
                f"Analise o seguinte texto de fonte medica e extraia as PRINCIPAIS entidades "
                f"(medicamentos, condicoes, sintomas, procedimentos) e seus relacionamentos. "
                f"Gere no maximo 15 queries Cypher MERGE. Use aspas simples dentro das queries Cypher. "
                f"IMPORTANTE: retorne JSON valido, sem caracteres especiais fora de strings.\n\n"
                f"URL FONTE: {url}\n\n"
                f"TEXTO:\n{text}"
            ],
            config=types.GenerateContentConfig(
                system_instruction=CURATOR_SYSTEM_PROMPT,
                temperature=0.1,
                max_output_tokens=16384,
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            )
        )

        raw_text = response.text.strip()

        logger.info(f"Gemini raw response length: {len(raw_text)} chars")
        logger.info(f"Gemini raw first 100: {repr(raw_text[:100])}")

        # With response_mime_type="application/json", Gemini returns clean JSON
        # But sometimes it adds markdown fences anyway, so strip them
        clean = raw_text.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:])  # Remove first line (```json)
            if clean.rstrip().endswith("```"):
                clean = clean.rstrip()[:-3].rstrip()

        # Try direct parse first
        try:
            result = json.loads(clean)
        except json.JSONDecodeError:
            # Attempt repair: fix common issues
            repaired = clean
            # Remove trailing commas before } or ]
            repaired = re.sub(r',\s*([}\]])', r'\1', repaired)
            # Try again
            try:
                result = json.loads(repaired)
            except json.JSONDecodeError:
                # Last fallback: extract between first { and last }
                first_brace = repaired.find("{")
                last_brace = repaired.rfind("}")
                if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                    json_str = repaired[first_brace:last_brace + 1]
                    result = json.loads(json_str)
                else:
                    raise

        # Add source URL
        if "source" not in result:
            result["source"] = {}
        result["source"]["url"] = url

        return {"status": "ok", "extraction": result}

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed. Raw response first 500 chars: {repr(raw_text[:500])}")
        return {
            "status": "error",
            "error": "gemini_json_parse_error",
            "message": str(e),
            "raw_preview": raw_text[:300] if raw_text else ""
        }
    except Exception as e:
        return {
            "status": "error",
            "error": "extraction_error",
            "message": str(e)
        }


async def ingest_url(url: str) -> dict:
    """
    Pipeline completo: URL -> Fetch -> Extract -> Quarantine-ready.
    1. Raspa o conteudo da URL
    2. Envia ao Gemini para extracaoo de entidades
    3. Retorna dados prontos para a quarentena
    """
    # Step 1: Fetch
    logger.info(f"Fetching URL: {url}")
    fetch_result = await fetch_url_content(url)
    if fetch_result["status"] != "ok":
        return fetch_result

    text = fetch_result["text"]
    logger.info(f"Fetched {fetch_result['text_length']} chars from {url}")

    # Step 2: Extract knowledge
    logger.info(f"Extracting knowledge via Gemini...")
    extract_result = await extract_knowledge(url, text)
    if extract_result["status"] != "ok":
        return extract_result

    extraction = extract_result["extraction"]

    # Step 3: Build quarantine entry
    entities_count = len(extraction.get("entities", []))
    relationships_count = len(extraction.get("relationships", []))
    cypher_queries = extraction.get("cypher_queries", [])

    # Join all cypher queries into one batch
    combined_cypher = ";\n".join(cypher_queries) if cypher_queries else None

    logger.info(
        f"Extracted {entities_count} entities, "
        f"{relationships_count} relationships, "
        f"{len(cypher_queries)} cypher queries"
    )

    return {
        "status": "ok",
        "source_url": url,
        "source_type": extraction.get("source", {}).get("type", "url"),
        "raw_text": text[:2000],  # Keep first 2000 chars as reference
        "entities_json": {
            "entities": extraction.get("entities", []),
            "source": extraction.get("source", {})
        },
        "relationships_json": extraction.get("relationships", []),
        "graph_cypher": combined_cypher,
        "metadata": extraction.get("metadata", {}),
        "entities_count": entities_count,
        "relationships_count": relationships_count
    }
