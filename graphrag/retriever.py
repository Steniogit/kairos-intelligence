"""
Kairós Intelligence v2.7.1 — Hybrid Retriever
Pipeline de retrieval: ChromaDB (similaridade) + Neo4j (contexto relacional).
"""

from graphrag.chroma_store import chroma_store
from graphrag.neo4j_store import neo4j_store
from graphrag.config import COLLECTION_FAQ, COLLECTION_HEALTH_TIPS


class HybridRetriever:
    """Retrieval híbrido: busca semântica (Chroma) + contexto relacional (Neo4j)."""

    def query_faq(self, clinic_id: str, question: str) -> list[dict]:
        """Busca resposta no FAQ por similaridade semântica."""
        collection = COLLECTION_FAQ.format(clinic_id=clinic_id)
        return chroma_store.search(collection, question)

    def query_health_tips(self, clinic_id: str, specialty: str) -> list[dict]:
        """Busca dicas de saúde por especialidade."""
        collection = COLLECTION_HEALTH_TIPS.format(clinic_id=clinic_id)
        return chroma_store.search(collection, f"dica saúde {specialty}")

    def identify_patient(self, clinic_id: str, phone: str) -> dict | None:
        """Identifica paciente pelo número de telefone via Neo4j."""
        return neo4j_store.get_patient_context(clinic_id, phone)

    def find_doctors(self, clinic_id: str, specialty: str) -> list[dict]:
        """Busca médicos por especialidade via Neo4j."""
        return neo4j_store.get_doctors_by_specialty(clinic_id, specialty)

    def get_full_context(self, clinic_id: str, phone: str, question: str) -> dict:
        """Monta contexto completo para o agente responder.

        Combina:
        1. Dados do paciente (Neo4j)
        2. FAQ relevante (ChromaDB)
        3. Médicos disponíveis (Neo4j)
        """
        patient = self.identify_patient(clinic_id, phone)
        faq_results = self.query_faq(clinic_id, question)

        return {
            "patient": patient,
            "faq_matches": faq_results,
            "has_patient": patient is not None,
        }


retriever = HybridRetriever()
