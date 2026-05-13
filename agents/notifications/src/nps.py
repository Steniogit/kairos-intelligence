"""
Kairós Intelligence v2.7.1 — Notificações: Pesquisa NPS
24h após a consulta: pesquisa NPS 1-5 estrelas.
Nota 4-5 → link Google Maps. Nota 1-3 → alerta Prometheus.
"""

import logging
from shared.evolution_client import evolution_client
from shared.config import settings

logger = logging.getLogger("notifications.nps")


class NPSSystem:
    """Pesquisa NPS pós-consulta."""

    async def send_nps_surveys(self, clinic_id: str):
        """Envia pesquisas NPS para pacientes que consultaram ontem."""
        # TODO: Manager.get_appointments_yesterday()
        # Para cada consulta realizada:
        #   1. Verificar filtro circadiano
        #   2. Enviar mensagem NPS
        logger.info(f"Pesquisas NPS processadas para clínica {clinic_id}")

    async def send_nps_message(self, phone: str, doctor_name: str):
        """Envia mensagem de NPS para paciente."""
        message = (
            f"Olá! 😊 Como foi sua consulta com Dr(a). {doctor_name}?\n\n"
            f"De 1 a 5 ⭐, como avalia a experiência?\n\n"
            f"1 ⭐ — Ruim\n"
            f"2 ⭐ — Regular\n"
            f"3 ⭐ — Bom\n"
            f"4 ⭐ — Muito Bom\n"
            f"5 ⭐ — Excelente\n\n"
            f"Responda com o número (1 a 5)! 💙"
        )
        await evolution_client.send_text(phone, message)

    async def process_nps_response(
        self, phone: str, score: int, clinic_id: str, doctor_name: str
    ):
        """Processa resposta NPS do paciente."""
        if score >= 4:
            # Nota 4-5: Link Google Maps
            await evolution_client.send_text(
                phone,
                f"Muito obrigado pela avaliação! 🎉\n\n"
                f"Se puder, deixe uma avaliação no Google para ajudar "
                f"outras pessoas a nos conhecerem:\n"
                f"🔗 [Link Google Maps da clínica]\n\n"
                f"Agradecemos! 💙",
            )
            logger.info(f"NPS {score}/5 - Link Google Maps enviado para ***{phone[-4:]}")
        else:
            # Nota 1-3: Alerta urgente ao Prometheus
            from agents.prometheus.src.monitoring import monitoring, AlertLevel
            await monitoring.check_nps_alert(clinic_id, score, phone)

            await evolution_client.send_text(
                phone,
                f"Lamentamos que a experiência não tenha sido boa. 😔\n"
                f"Vamos repassar seu feedback diretamente para o gestor "
                f"para que possamos melhorar. Obrigado pela sinceridade! 💙",
            )
            logger.info(f"NPS {score}/5 - Alerta enviado ao Prometheus para ***{phone[-4:]}")


nps_system = NPSSystem()
