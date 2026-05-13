"""
Kairós Intelligence v2.7.1 — Pipeline de Ingestão GraphRAG
Alimenta Neo4j e ChromaDB com dados da clínica.
"""

import hashlib
from graphrag.chroma_store import chroma_store
from graphrag.neo4j_store import neo4j_store
from graphrag.config import (
    COLLECTION_FAQ, COLLECTION_PATIENTS,
    COLLECTION_HEALTH_TIPS, COLLECTION_PROTOCOLS,
)


def _generate_id(text: str) -> str:
    """Gera ID determinístico baseado no conteúdo."""
    return hashlib.md5(text.encode()).hexdigest()


def ingest_faq(clinic_id: str, faq_items: list[dict]):
    """Ingere FAQ da clínica no ChromaDB.

    Args:
        clinic_id: Identificador da clínica (tenant)
        faq_items: Lista de {"question": str, "answer": str, "category": str}
    """
    collection = COLLECTION_FAQ.format(clinic_id=clinic_id)
    documents = []
    metadatas = []
    ids = []

    for item in faq_items:
        # Combina pergunta + resposta para embedding mais rico
        doc = f"Pergunta: {item['question']}\nResposta: {item['answer']}"
        documents.append(doc)
        metadatas.append({
            "question": item["question"],
            "answer": item["answer"],
            "category": item.get("category", "geral"),
            "clinic_id": clinic_id,
        })
        ids.append(_generate_id(f"{clinic_id}:{item['question']}"))

    chroma_store.add_documents(collection, documents, metadatas, ids)
    print(f"✅ {len(faq_items)} itens de FAQ ingeridos para clínica {clinic_id}")


def ingest_doctors(clinic_id: str, doctors: list[dict]):
    """Ingere lista de médicos no Neo4j.

    Args:
        clinic_id: Identificador da clínica
        doctors: Lista de {"name": str, "crm": str, "specialties": [str],
                           "schedule": str, "active": bool}
    """
    for doctor in doctors:
        neo4j_store.add_doctor(clinic_id, doctor)
    print(f"✅ {len(doctors)} médicos ingeridos no Neo4j para clínica {clinic_id}")


def ingest_insurance(clinic_id: str, insurances: list[dict]):
    """Ingere lista de convênios no Neo4j.

    Args:
        clinic_id: Identificador da clínica
        insurances: Lista de {"name": str, "plans": [str], "active": bool}
    """
    for insurance in insurances:
        neo4j_store.add_insurance(clinic_id, insurance)
    print(f"✅ {len(insurances)} convênios ingeridos no Neo4j para clínica {clinic_id}")


def ingest_patient(clinic_id: str, patient: dict):
    """Ingere dados de paciente no Neo4j.

    Args:
        clinic_id: Identificador da clínica
        patient: {"cpf": str, "name": str, "phone": str, "birth_date": str,
                  "email": str, "opt_in_tips": bool}
    """
    neo4j_store.add_patient(clinic_id, patient)


def ingest_health_tips(clinic_id: str, tips: list[dict]):
    """Ingere dicas de saúde no ChromaDB.

    Args:
        clinic_id: Identificador da clínica
        tips: Lista de {"tip": str, "specialty": str, "validated_by": str}
    """
    collection = COLLECTION_HEALTH_TIPS.format(clinic_id=clinic_id)
    documents = []
    metadatas = []
    ids = []

    for tip in tips:
        documents.append(tip["tip"])
        metadatas.append({
            "specialty": tip.get("specialty", "geral"),
            "validated_by": tip.get("validated_by", ""),
            "clinic_id": clinic_id,
        })
        ids.append(_generate_id(f"{clinic_id}:tip:{tip['tip'][:50]}"))

    chroma_store.add_documents(collection, documents, metadatas, ids)
    print(f"✅ {len(tips)} dicas de saúde ingeridas para clínica {clinic_id}")


def ingest_protocols(clinic_id: str, protocols: list[dict]):
    """Ingere protocolos pré-consulta no ChromaDB.

    Args:
        clinic_id: Identificador da clínica
        protocols: Lista de {"procedure": str, "preparation": str, "specialty": str}
    """
    collection = COLLECTION_PROTOCOLS.format(clinic_id=clinic_id)
    documents = []
    metadatas = []
    ids = []

    for p in protocols:
        doc = f"Procedimento: {p['procedure']}\nPreparo: {p['preparation']}"
        documents.append(doc)
        metadatas.append({
            "procedure": p["procedure"],
            "specialty": p.get("specialty", ""),
            "clinic_id": clinic_id,
        })
        ids.append(_generate_id(f"{clinic_id}:protocol:{p['procedure']}"))

    chroma_store.add_documents(collection, documents, metadatas, ids)
    print(f"✅ {len(protocols)} protocolos ingeridos para clínica {clinic_id}")
