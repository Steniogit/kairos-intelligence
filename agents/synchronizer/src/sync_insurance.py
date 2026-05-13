"""
Kairós Intelligence v2.7.1 — Sincronizador: Sync de Convênios
Extrai lista de convênios do Ademed e atualiza Neo4j/Front-Desk.
"""

import logging
from graphrag.ingest import ingest_insurance

logger = logging.getLogger("synchronizer.insurance")


class InsuranceSync:
    """Sincronização de convênios Ademed → GraphRAG → Front-Desk."""

    def __init__(self):
        self._last_insurance_hash: str = ""

    async def sync(self, clinic_id: str) -> bool:
        """Sincroniza lista de convênios. Retorna True se houve mudança."""
        # 1. Extrair do Ademed
        current_insurance = await self._extract_from_ademed(clinic_id)

        if not current_insurance:
            logger.warning("Nenhum convênio extraído do Ademed")
            return False

        # 2. Detectar mudanças
        has_changes = self._detect_changes(current_insurance)
        if not has_changes:
            return False

        # 3. Atualizar Neo4j
        ingest_insurance(clinic_id, current_insurance)

        logger.info(f"Convênios sincronizados: {len(current_insurance)} itens")
        return True

    async def _extract_from_ademed(self, clinic_id: str) -> list[dict]:
        """Extrai lista de convênios via Manager/Crawl4AI."""
        # TODO: Chamar Manager.get_insurance_list()
        return []

    def _detect_changes(self, current: list[dict]) -> bool:
        """Detecta se houve mudança na lista de convênios."""
        import hashlib
        import json
        current_hash = hashlib.md5(
            json.dumps(current, sort_keys=True).encode()
        ).hexdigest()

        if current_hash == self._last_insurance_hash:
            return False

        self._last_insurance_hash = current_hash
        return True


insurance_sync = InsuranceSync()
