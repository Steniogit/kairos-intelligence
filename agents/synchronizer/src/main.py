"""
Kairós Intelligence v2.7.1 — Agente 5: Sincronizador
Mantém o contexto do Front-Desk sincronizado com o Ademed.
Cron job a cada 30 minutos.
"""

import logging
from datetime import datetime

from shared.config import settings
from agents.synchronizer.src.sync_doctors import doctor_sync
from agents.synchronizer.src.sync_insurance import insurance_sync

logger = logging.getLogger("synchronizer")


class SynchronizerAgent:
    """Agente de sincronização Ademed ↔ GraphRAG/SOUL.md."""

    def __init__(self, clinic_id: str = "default"):
        self.clinic_id = clinic_id

    async def run_sync_cycle(self):
        """Ciclo de sincronização — executado a cada 30 minutos."""
        logger.info(f"Sincronização iniciada: {datetime.now().isoformat()}")

        # Sincronizar médicos
        doctors_changed = await doctor_sync.sync(self.clinic_id)

        # Sincronizar convênios (a cada 6h — a cada 12º ciclo)
        now = datetime.now()
        if now.minute < 30 and now.hour % 6 == 0:
            insurance_changed = await insurance_sync.sync(self.clinic_id)
        else:
            insurance_changed = False

        if doctors_changed or insurance_changed:
            logger.info("Mudanças detectadas — Front-Desk será reiniciado")
            # TODO: Reiniciar instância do Front-Desk no OpenClaw
            # TODO: Notificar Prometheus (informativo)
        else:
            logger.info("Nenhuma mudança detectada — aguardando próximo ciclo")


synchronizer = SynchronizerAgent()
