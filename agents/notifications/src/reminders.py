"""
Kairós Intelligence v2.7.1 — Notificações: Sistema de Lembretes
D-1 (véspera), D-0 (varredura matinal), H-4 (último lembrete).
"""

import logging
from datetime import datetime, timedelta

from shared.evolution_client import evolution_client
from shared.redis_client import redis_client
from agents.notifications.src.circadian import circadian_filter

logger = logging.getLogger("notifications.reminders")


class ReminderSystem:
    """Sistema de lembretes de consulta em múltiplas etapas."""

    async def send_eve_reminders(self, clinic_id: str):
        """D-1 (Véspera) — Lembrete com janela dinâmica.

        Calcula o melhor momento dentro da janela de 24h para enviar.
        Se janela aberta → envio gratuito.
        Se janela fechada → cascata paga.
        """
        # TODO: Buscar agendamentos de amanhã via Manager
        # Para cada agendamento:
        #   1. Calcular horário ótimo do lembrete
        #   2. Verificar filtro circadiano
        #   3. Verificar se janela Meta está aberta
        #   4. Enviar lembrete

        logger.info(f"Lembretes D-1 processados para clínica {clinic_id}")

    async def morning_sweep(self, clinic_id: str):
        """D-0 (08:00) — Varredura matinal.

        Manager navega no Ademed e varre agendamentos do dia sem confirmação.
        Para cada um: nova tentativa de contato.
        """
        logger.info(f"Varredura matinal iniciada para clínica {clinic_id}")

        # TODO: Manager.get_appointments_today()
        # Filtrar sem confirmação
        # Enviar nova tentativa

    async def send_final_reminders(self, clinic_id: str):
        """H-4 (4 horas antes) — Tentativa final.

        Se silêncio → Manager atualiza status "Sem resposta" no Ademed.
        Aciona transbordo humano para a recepcionista.
        """
        logger.info(f"Lembretes H-4 processados para clínica {clinic_id}")

        # TODO: Para agendamentos em 4h sem confirmação:
        #   1. Enviar último lembrete
        #   2. Se sem resposta → Manager.update_status("sem_resposta")
        #   3. Notificar recepcionista

    def calculate_reminder_time(
        self, window_closes: datetime, appointment_time: datetime
    ) -> tuple[datetime, str]:
        """Calcula horário ótimo para lembrete (minimiza custo Meta).

        Lógica do PRD:
        1. Aplicar filtro circadiano (nunca entre 22h-07h)
        2. Lembrete 1h antes da janela fechar (dentro da janela = grátis)
        3. Se lembrete ficaria < 4h antes da consulta → cascata paga
        """
        # Filtro circadiano
        if window_closes.hour < 7:
            window_closes = window_closes.replace(hour=22) - timedelta(days=1)

        # Lembrete 1h antes da janela fechar
        reminder = window_closes - timedelta(hours=1)

        # Garantir pelo menos 4h antes da consulta
        if reminder > appointment_time - timedelta(hours=4):
            return appointment_time - timedelta(hours=18), "template_pago"

        return reminder, "gratuito"


reminder_system = ReminderSystem()
