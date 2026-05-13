"""
Kairós Intelligence v2.7.1 — Agente 4: Notificações (Proativo)
Toda comunicação proativa com pacientes ao longo do ciclo completo.
"""

import logging
from datetime import datetime

from shared.config import settings
from agents.notifications.src.reminders import reminder_system
from agents.notifications.src.cascade import cascade_sender
from agents.notifications.src.nps import nps_system
from agents.notifications.src.circadian import circadian_filter

logger = logging.getLogger("notifications")


class NotificationsAgent:
    """Agente de notificações proativas."""

    def __init__(self, clinic_id: str = "default"):
        self.clinic_id = clinic_id

    async def run_daily_cycle(self):
        """Ciclo diário de notificações — executado via cron."""
        now = datetime.now()
        logger.info(f"Ciclo de notificações iniciado: {now.isoformat()}")

        # D-0 08:00 — Varredura matinal
        if now.hour == 8:
            await reminder_system.morning_sweep(self.clinic_id)

        # D-1 — Lembretes da véspera (janela dinâmica)
        await reminder_system.send_eve_reminders(self.clinic_id)

        # H-4 — Último lembrete
        await reminder_system.send_final_reminders(self.clinic_id)

        # Pós-consulta — NPS (24h depois)
        await nps_system.send_nps_surveys(self.clinic_id)

        # Dicas de saúde (opt-in, a cada 3-4 dias)
        await self._send_health_tips()

        # Aniversários
        await self._send_birthday_messages()

        logger.info("Ciclo de notificações concluído")

    async def _send_health_tips(self):
        """Envia dicas de saúde para pacientes opt-in."""
        # TODO: Consultar GraphRAG para pacientes opt-in
        # Para cada paciente:
        #   1. Verificar filtro circadiano
        #   2. Verificar se janela Meta está aberta
        #   3. Enviar dica personalizada por especialidade
        #   4. Incluir pergunta aberta no final (renova janela)
        pass

    async def _send_birthday_messages(self):
        """Envia mensagens de aniversário."""
        # TODO: Manager extrai datas de nascimento do Ademed
        # Verificar se hoje é aniversário
        # Enviar mensagem humanizada
        pass


notifications = NotificationsAgent()
