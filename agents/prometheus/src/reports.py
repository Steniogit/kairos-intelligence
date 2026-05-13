"""
Kairós Intelligence v2.7.1 — Prometheus: Geração de Relatórios
Relatórios automáticos: diário (8h), semanal (seg 8h), mensal (dia 1 8h).
"""

import logging
from datetime import datetime, timedelta

from shared.config import settings
from shared.evolution_client import evolution_client
from shared.paperclip_client import paperclip_client

logger = logging.getLogger("prometheus.reports")


class ReportGenerator:
    """Gera relatórios automáticos para o gestor."""

    def __init__(self):
        self.gestor_phone = settings.GESTOR_WHATSAPP

    async def generate_daily_report(self, clinic_id: str) -> str:
        """Relatório diário — enviado às 8h.

        Conteúdo: agendamentos, confirmados, sem resposta,
        cancelamentos, NPS médio.
        """
        # Coletar dados do Paperclip
        budget = await paperclip_client.check_budget(clinic_id)

        report = f"""📊 *Relatório Diário — {datetime.now().strftime('%d/%m/%Y')}*
━━━━━━━━━━━━━━━━━━━━━━

📅 *Agendamentos:*
• Total do dia: {{total_agendamentos}}
• Confirmados: {{confirmados}}
• Sem resposta: {{sem_resposta}}
• Cancelados: {{cancelados}}

⭐ *NPS Médio:* {{nps_medio}}/5

💰 *Tokens Consumidos:* {{tokens_dia}}
📉 *Custo Estimado:* R$ {{custo_dia}}

━━━━━━━━━━━━━━━━━━━━━━
_Kairós Intelligence — Relatório Automático_"""

        return report

    async def generate_weekly_report(self, clinic_id: str) -> str:
        """Relatório semanal — enviado às segundas-feiras 8h.

        Conteúdo: tendências, comparativos, gargalos.
        """
        report = f"""📊 *Relatório Semanal — Semana {datetime.now().isocalendar()[1]}*
━━━━━━━━━━━━━━━━━━━━━━

📈 *Tendências:*
• Atendimentos: {{total_semana}} ({{variacao_pct}}% vs semana anterior)
• Taxa de confirmação: {{taxa_confirmacao}}%
• Tempo médio de resposta: {{tempo_medio}}s

🏆 *Top Especialidades:*
{{top_especialidades}}

⚠️ *Gargalos Identificados:*
{{gargalos}}

💡 *Sugestões:*
{{sugestoes}}

━━━━━━━━━━━━━━━━━━━━━━
_Kairós Intelligence — Relatório Automático_"""

        return report

    async def generate_monthly_report(self, clinic_id: str) -> str:
        """Relatório mensal — enviado no dia 1 às 8h.

        Conteúdo: ROI consolidado, comparativo, sugestões estratégicas.
        """
        report = f"""📊 *Relatório Mensal — {datetime.now().strftime('%B/%Y')}*
━━━━━━━━━━━━━━━━━━━━━━

💰 *ROI Consolidado:*
• Atendimentos automatizados: {{total_mes}}
• Custo total plataforma: R$ {{custo_mes}}
• Economia estimada vs recepcionista: R$ {{economia}}
• ROI: {{roi_pct}}%

📊 *Comparativo Clínicas:*
{{comparativo_clinicas}}

🎯 *Sugestões Estratégicas:*
{{sugestoes_estrategicas}}

━━━━━━━━━━━━━━━━━━━━━━
_Kairós Intelligence — Relatório Automático_"""

        return report

    async def send_report(self, report: str):
        """Envia relatório para o gestor via WhatsApp."""
        await evolution_client.send_text(self.gestor_phone, report)
        logger.info("Relatório enviado ao gestor")

    def should_send_daily(self) -> bool:
        """Verifica se é hora de enviar relatório diário (8h)."""
        now = datetime.now()
        return now.hour == 8 and now.minute < 5

    def should_send_weekly(self) -> bool:
        """Verifica se é hora de enviar relatório semanal (segunda 8h)."""
        now = datetime.now()
        return now.weekday() == 0 and now.hour == 8 and now.minute < 5

    def should_send_monthly(self) -> bool:
        """Verifica se é hora de enviar relatório mensal (dia 1, 8h)."""
        now = datetime.now()
        return now.day == 1 and now.hour == 8 and now.minute < 5


report_generator = ReportGenerator()
