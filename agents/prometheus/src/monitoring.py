"""
Kairós Intelligence v2.7.1 — Prometheus: Monitoramento em 3 Níveis
🔴 Urgente → notifica imediatamente
🟡 Aviso → relatório diário
🟢 Insight → relatório semanal
"""

import logging
from datetime import datetime
from enum import Enum

from shared.config import settings
from shared.evolution_client import evolution_client
from shared.paperclip_client import paperclip_client

logger = logging.getLogger("prometheus.monitoring")


class AlertLevel(Enum):
    URGENT = "🔴"      # Notifica imediatamente
    WARNING = "🟡"     # Relatório diário
    INSIGHT = "🟢"     # Relatório semanal


class MonitoringSystem:
    """Sistema de monitoramento em 3 níveis."""

    def __init__(self):
        self.gestor_phone = settings.GESTOR_WHATSAPP
        self.daily_alerts: list[dict] = []
        self.weekly_insights: list[dict] = []

    async def alert(self, level: AlertLevel, clinic_id: str, message: str):
        """Registra alerta conforme nível de urgência."""
        alert_data = {
            "level": level.value,
            "clinic_id": clinic_id,
            "message": message,
            "timestamp": datetime.now().isoformat(),
        }

        if level == AlertLevel.URGENT:
            await self._send_urgent(alert_data)
        elif level == AlertLevel.WARNING:
            self.daily_alerts.append(alert_data)
        elif level == AlertLevel.INSIGHT:
            self.weekly_insights.append(alert_data)

        # Registrar no Paperclip audit log
        await paperclip_client.audit_log(clinic_id, "monitoring_alert", alert_data)

    async def _send_urgent(self, alert: dict):
        """Envia alerta urgente imediatamente ao gestor."""
        message = f"""{alert['level']} *ALERTA URGENTE*
━━━━━━━━━━━━━━━━━━━━━━
📍 Clínica: {alert['clinic_id']}
⚡ {alert['message']}
🕐 {alert['timestamp'][:19]}
━━━━━━━━━━━━━━━━━━━━━━"""

        await evolution_client.send_text(self.gestor_phone, message)
        logger.warning(f"Alerta urgente enviado: {alert['message']}")

    async def check_budget_alert(self, clinic_id: str):
        """Verifica se budget de tokens excedeu 20% do estimado."""
        budget = await paperclip_client.check_budget(clinic_id)
        if budget.get("usage_pct", 0) > 120:
            await self.alert(
                AlertLevel.URGENT,
                clinic_id,
                f"Budget de tokens excedeu 20% do estimado! "
                f"Uso: {budget.get('usage_pct', 0)}%",
            )

    async def check_nps_alert(self, clinic_id: str, nps_score: int, patient_phone: str):
        """Alerta se NPS for baixo (1-3)."""
        if nps_score <= 3:
            await self.alert(
                AlertLevel.URGENT,
                clinic_id,
                f"NPS baixo ({nps_score}/5) recebido de paciente ***{patient_phone[-4:]}",
            )

    async def check_llm_failure(self, clinic_id: str, error: str):
        """Alerta se LLM falhar (erro 429, timeout, etc)."""
        await self.alert(
            AlertLevel.URGENT,
            clinic_id,
            f"Falha no LLM: {error}. Ativando fallback automático.",
        )

    async def check_ademed_down(self, clinic_id: str):
        """Alerta se Ademed estiver fora do ar."""
        await self.alert(
            AlertLevel.URGENT,
            clinic_id,
            "ERP Ademed não responde. Agendamentos salvos em fila pendente.",
        )

    async def record_empty_schedule(self, clinic_id: str, date: str):
        """Registra agenda vazia como insight."""
        await self.alert(
            AlertLevel.INSIGHT,
            clinic_id,
            f"Agenda vazia detectada para {date}. Sugestão: broadcast segmentado.",
        )

    def flush_daily(self) -> list[dict]:
        """Retorna e limpa alertas diários."""
        alerts = self.daily_alerts.copy()
        self.daily_alerts.clear()
        return alerts

    def flush_weekly(self) -> list[dict]:
        """Retorna e limpa insights semanais."""
        insights = self.weekly_insights.copy()
        self.weekly_insights.clear()
        return insights


monitoring = MonitoringSystem()
