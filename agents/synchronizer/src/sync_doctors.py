"""
Kairós Intelligence v2.7.1 — Sincronizador: Sync de Médicos
Extrai lista de médicos do Ademed e atualiza SOUL.md do Front-Desk.
"""

import logging
from graphrag.ingest import ingest_doctors
from graphrag.neo4j_store import neo4j_store

logger = logging.getLogger("synchronizer.doctors")


class DoctorSync:
    """Sincronização de médicos Ademed → GraphRAG → SOUL.md."""

    def __init__(self):
        self._last_doctors_hash: str = ""

    async def sync(self, clinic_id: str) -> bool:
        """Sincroniza lista de médicos.

        Retorna True se houve mudança.

        Processo:
        1. Extrai lista atual do Ademed via Crawl4AI
        2. Compara com dados no Neo4j
        3. Se diferente: atualiza Neo4j + SOUL.md do Front-Desk
        """
        # 1. Extrair do Ademed
        current_doctors = await self._extract_from_ademed(clinic_id)

        if not current_doctors:
            logger.warning("Nenhum médico extraído do Ademed")
            return False

        # 2. Comparar com Neo4j
        has_changes = self._detect_changes(current_doctors)

        if not has_changes:
            return False

        # 3. Atualizar Neo4j
        ingest_doctors(clinic_id, current_doctors)

        # 4. Atualizar SOUL.md do Front-Desk
        await self._update_frontdesk_soul(current_doctors)

        logger.info(f"Sincronização concluída: {len(current_doctors)} médicos")
        return True

    async def _extract_from_ademed(self, clinic_id: str) -> list[dict]:
        """Extrai lista de médicos via Manager/Crawl4AI."""
        # TODO: Chamar Manager.get_doctors()
        # Placeholder retornando lista vazia
        return []

    def _detect_changes(self, current: list[dict]) -> bool:
        """Detecta se houve mudança na lista de médicos."""
        import hashlib
        import json
        current_hash = hashlib.md5(
            json.dumps(current, sort_keys=True).encode()
        ).hexdigest()

        if current_hash == self._last_doctors_hash:
            return False

        self._last_doctors_hash = current_hash
        return True

    async def _update_frontdesk_soul(self, doctors: list[dict]):
        """Atualiza SOUL.md do Front-Desk com lista de médicos atualizada."""
        doctors_section = "\n## Médicos Disponíveis\n\n"
        for doc in doctors:
            specialties = ", ".join(doc.get("specialties", []))
            schedule = doc.get("schedule", "")
            doctors_section += (
                f"- **Dr(a). {doc['name']}** — {specialties}\n"
                f"  Horários: {schedule}\n\n"
            )

        # TODO: Ler SOUL.md atual, substituir seção de médicos, salvar
        logger.info("SOUL.md do Front-Desk atualizado com nova lista de médicos")


doctor_sync = DoctorSync()
