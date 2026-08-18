"""
Kairos Intelligence — Ademed Pipeline (Fase 5)
Gera documentos medicos automaticamente a partir do SOAP estruturado.
Documentos: Receituario, Atestado, Solicitacao de Exames, Encaminhamento, Relatorio.
"""

import os
import json
import logging
import time

from google import genai
from google.genai import types

logger = logging.getLogger("kairos-clinical.ademed")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ADEMED_MODEL = os.getenv("ADEMED_MODEL", "gemini-2.5-flash")


def _get_client():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY nao configurada")
    return genai.Client(api_key=GEMINI_API_KEY)


# ═══════════════════════════════════════════════════════════
# Templates de Documentos
# ═══════════════════════════════════════════════════════════

DOCUMENT_TEMPLATES = {
    "prescription": {
        "name": "Receituario",
        "description": "Prescricao de medicamentos com posologia completa",
        "required_soap_fields": ["plan"],
        "system_prompt": """Voce gera receituarios medicos validos no Brasil.
A partir do SOAP fornecido, extraia TODOS os medicamentos mencionados no plano e gere um receituario padrao.

REGRAS:
- Inclua nome generico e comercial quando possivel
- Inclua dosagem, via de administracao, frequencia e duracao
- Numere cada item
- Use formato padrao brasileiro de receituario
- Se o medicamento for controlado (tarja preta/vermelha), sinalize com [CONTROLADO]
- NAO invente medicamentos que nao estejam no SOAP

Retorne JSON:
{
  "document_type": "prescription",
  "title": "Receituario Medico",
  "patient_name": "",
  "date": "",
  "items": [
    {
      "number": 1,
      "medication": "",
      "dosage": "",
      "route": "",
      "frequency": "",
      "duration": "",
      "instructions": "",
      "controlled": false
    }
  ],
  "notes": "",
  "has_controlled": false
}"""
    },

    "sick_note": {
        "name": "Atestado Medico",
        "description": "Atestado de comparecimento ou afastamento",
        "required_soap_fields": ["assessment"],
        "system_prompt": """Voce gera atestados medicos validos no Brasil.
A partir do SOAP fornecido, gere um atestado medico adequado.

REGRAS:
- Inclua CID-10 apenas se autorizado pelo paciente (campo authorize_cid)
- Sugira dias de afastamento baseado no diagnostico
- Use linguagem formal e medica
- NAO inclua detalhes do diagnostico no atestado (sigilo medico)

Retorne JSON:
{
  "document_type": "sick_note",
  "title": "Atestado Medico",
  "patient_name": "",
  "date": "",
  "text": "Atesto para os devidos fins que o(a) paciente...",
  "days_off": 0,
  "cid10": null,
  "include_cid": false,
  "period": {"start": "", "end": ""}
}"""
    },

    "exam_request": {
        "name": "Solicitacao de Exames",
        "description": "Guias de solicitacao de exames complementares",
        "required_soap_fields": ["plan"],
        "system_prompt": """Voce gera solicitacoes de exames medicos validos no Brasil.
A partir do SOAP fornecido, extraia TODOS os exames mencionados no plano.

REGRAS:
- Inclua o nome completo do exame
- Inclua a indicacao clinica (CID-10 quando disponivel)
- Classifique a urgencia (rotina, urgente, emergencia)
- Agrupe por tipo (laboratorial, imagem, funcional)
- NAO invente exames que nao estejam no SOAP

Retorne JSON:
{
  "document_type": "exam_request",
  "title": "Solicitacao de Exames Complementares",
  "patient_name": "",
  "date": "",
  "clinical_indication": "",
  "cid10": "",
  "exams": [
    {
      "name": "",
      "type": "laboratorial|imagem|funcional|outro",
      "urgency": "rotina|urgente|emergencia",
      "clinical_justification": "",
      "special_instructions": ""
    }
  ]
}"""
    },

    "referral": {
        "name": "Encaminhamento",
        "description": "Encaminhamento para especialista ou servico",
        "required_soap_fields": ["assessment", "plan"],
        "system_prompt": """Voce gera encaminhamentos medicos validos no Brasil.
A partir do SOAP fornecido, gere um encaminhamento para o especialista adequado.

REGRAS:
- Identifique a especialidade baseada no diagnostico
- Inclua resumo clinico relevante para o especialista
- Inclua medicamentos em uso
- Inclua resultados de exames relevantes
- Use linguagem tecnica adequada

Retorne JSON:
{
  "document_type": "referral",
  "title": "Encaminhamento Medico",
  "patient_name": "",
  "date": "",
  "to_specialty": "",
  "clinical_summary": "",
  "current_medications": [],
  "relevant_exams": [],
  "reason": "",
  "urgency": "eletivo|prioritario|urgente"
}"""
    },

    "report": {
        "name": "Relatorio Medico",
        "description": "Relatorio clinico detalhado",
        "required_soap_fields": ["subjective", "objective", "assessment", "plan"],
        "system_prompt": """Voce gera relatorios medicos completos validos no Brasil.
A partir do SOAP fornecido, gere um relatorio medico detalhado.

REGRAS:
- Inclua anamnese, exame fisico, hipotese diagnostica e conduta
- Use linguagem tecnica formal
- Inclua todos os CID-10 relevantes
- Seja completo mas objetivo

Retorne JSON:
{
  "document_type": "report",
  "title": "Relatorio Medico",
  "patient_name": "",
  "date": "",
  "anamnesis": "",
  "physical_exam": "",
  "complementary_exams": "",
  "diagnosis": "",
  "cid10_codes": [],
  "treatment_plan": "",
  "prognosis": "",
  "observations": ""
}"""
    }
}


async def generate_document(soap_data: dict, doc_type: str, patient_name: str = "",
                           extra_context: dict = None) -> dict:
    """Gera um documento medico a partir do SOAP.
    
    Args:
        soap_data: JSON do SOAP estruturado (output do copiloto/agente SOAP)
        doc_type: Tipo do documento (prescription, sick_note, exam_request, referral, report)
        patient_name: Nome do paciente
        extra_context: Dados adicionais (ex: authorize_cid, dias de afastamento)
    """
    if doc_type not in DOCUMENT_TEMPLATES:
        return {
            "status": "error",
            "message": f"Tipo de documento invalido: {doc_type}. "
                       f"Tipos disponiveis: {list(DOCUMENT_TEMPLATES.keys())}"
        }

    template = DOCUMENT_TEMPLATES[doc_type]
    
    try:
        client = _get_client()

        # Monta o prompt com o SOAP e contexto extra
        soap_json = json.dumps(soap_data, ensure_ascii=False)
        
        prompt_parts = [
            f"Gere o documento '{template['name']}' para o paciente '{patient_name}' "
            f"com base no SOAP abaixo.\n\n"
            f"--- SOAP ESTRUTURADO ---\n{soap_json}"
        ]

        if extra_context:
            prompt_parts.append(
                f"\n\n--- CONTEXTO ADICIONAL ---\n{json.dumps(extra_context, ensure_ascii=False)}"
            )

        response = client.models.generate_content(
            model=ADEMED_MODEL,
            contents=["\n".join(prompt_parts)],
            config=types.GenerateContentConfig(
                system_instruction=template["system_prompt"],
                temperature=0.1,
                max_output_tokens=4096,
                response_mime_type="application/json",
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            )
        )

        raw = response.text.strip()
        document = json.loads(raw)

        # Preenche o nome do paciente se nao veio do Gemini
        if patient_name and not document.get("patient_name"):
            document["patient_name"] = patient_name

        logger.info(f"Ademed: Generated {doc_type} for {patient_name}")

        return {
            "status": "ok",
            "document_type": doc_type,
            "document": document
        }

    except json.JSONDecodeError as e:
        return {"status": "error", "error": "json_parse", "message": str(e)}
    except Exception as e:
        logger.error(f"Ademed generation error: {e}")
        return {"status": "error", "error": "generation_error", "message": str(e)}


async def generate_all_documents(soap_data: dict, patient_name: str = "",
                                 doc_types: list = None,
                                 extra_context: dict = None) -> dict:
    """Gera multiplos documentos de uma vez a partir do mesmo SOAP.
    
    Args:
        soap_data: JSON do SOAP
        patient_name: Nome do paciente
        doc_types: Lista de tipos a gerar (None = gera todos disponiveis)
        extra_context: Contexto adicional por tipo {doc_type: {context}}
    """
    import asyncio

    if doc_types is None:
        doc_types = list(DOCUMENT_TEMPLATES.keys())

    # Gera todos em paralelo
    tasks = []
    for dt in doc_types:
        ctx = (extra_context or {}).get(dt, None)
        tasks.append(generate_document(soap_data, dt, patient_name, ctx))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    documents = {}
    errors = []
    for dt, result in zip(doc_types, results):
        if isinstance(result, Exception):
            errors.append({"type": dt, "error": str(result)})
        elif result.get("status") == "ok":
            documents[dt] = result["document"]
        else:
            errors.append({"type": dt, "error": result.get("message", "Unknown error")})

    return {
        "status": "ok" if documents else "error",
        "patient_name": patient_name,
        "documents_generated": len(documents),
        "documents": documents,
        "errors": errors if errors else None
    }
