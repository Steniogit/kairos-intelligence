"""
Kairós Intelligence v2.7.1 — Front-Desk: Handoff para Humano
Escalonamento para recepcionista em casos que o bot não consegue resolver.
"""

import logging
from shared.config import settings
from shared.evolution_client import evolution_client
from shared.redis_client import redis_client

logger = logging.getLogger("front-desk.handoff")


class HandoffManager:
    """Gerencia escalonamento para recepcionista humana."""

    TRIGGERS = [
        "falar com atendente",
        "falar com humano",
        "falar com pessoa",
        "recepcionista",
        "atendente",
        "humano",
        "não estou satisfeito",
        "quero reclamar",
    ]

    def __init__(self):
        self.recepcionista_phone = settings.RECEPCIONISTA_WHATSAPP

    def should_handoff(self, message: str, off_topic_count: int, reschedule_count: int) -> bool:
        """Verifica se deve escalar para humano.

        Condições:
        1. Paciente pediu explicitamente
        2. 3 mensagens fora do escopo consecutivas
        3. 3ª tentativa de reagendamento
        4. Paciente demonstra irritação
        """
        msg_lower = message.lower()

        # Pedido explícito
        if any(trigger in msg_lower for trigger in self.TRIGGERS):
            return True

        # 3 mensagens fora do escopo
        if off_topic_count >= 3:
            return True

        # 3ª tentativa de reagendamento
        if reschedule_count >= 3:
            return True

        return False

    async def execute_handoff(self, patient_phone: str, context: dict):
        """Executa handoff: notifica recepcionista e informa paciente."""
        # Montar resumo do contexto
        history = context.get("history", [])
        summary = self._build_summary(history)

        # Notificar recepcionista
        await evolution_client.send_text(
            self.recepcionista_phone,
            f"🔔 *Transbordo de Atendimento*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📱 Paciente: {patient_phone}\n"
            f"📋 Resumo: {summary}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"_Por favor, assuma o atendimento deste paciente._",
        )

        # Informar paciente
        await evolution_client.send_text(
            patient_phone,
            "Entendi! Vou transferir você para nossa recepcionista agora mesmo. "
            "Ela já tem o resumo da nossa conversa. "
            "Em instantes ela vai falar com você! 😊💙",
        )

        # Limpar estado
        await redis_client.clear_conversation(patient_phone)
        logger.info(f"Handoff executado para ***{patient_phone[-4:]}")

    def _build_summary(self, history: list[dict]) -> str:
        """Gera resumo do atendimento para a recepcionista."""
        if not history:
            return "Sem contexto disponível"

        last_messages = history[-6:]
        summary_parts = []
        for msg in last_messages:
            role = "Paciente" if msg["role"] == "user" else "Bot"
            content = msg["content"][:100]
            summary_parts.append(f"{role}: {content}")

        return "\n".join(summary_parts)


handoff_manager = HandoffManager()
