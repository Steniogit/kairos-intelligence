"""
Kairós Intelligence v2.7.1 — Notificações: Filtro Circadiano
Mensagens NUNCA são enviadas entre 22h e 07h.
Se vencimento cai na madrugada, antecipa para antes das 22h.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger("notifications.circadian")


class CircadianFilter:
    """Filtro circadiano para respeitar horário de descanso."""

    QUIET_START = 22  # 22h — início do silêncio
    QUIET_END = 7     # 07h — fim do silêncio

    def is_quiet_hours(self, dt: datetime | None = None) -> bool:
        """Verifica se o horário está na faixa de silêncio (22h-07h)."""
        if dt is None:
            dt = datetime.now()
        return dt.hour >= self.QUIET_START or dt.hour < self.QUIET_END

    def adjust_time(self, proposed_time: datetime) -> datetime:
        """Ajusta horário para respeitar filtro circadiano.

        Se cai entre 22h-07h:
        - Antecipa para 21:50 do dia anterior (se for após 22h)
        - Adia para 07:05 do mesmo dia (se for antes de 7h)
        """
        if not self.is_quiet_hours(proposed_time):
            return proposed_time

        if proposed_time.hour >= self.QUIET_START:
            # Antecipa para antes das 22h do mesmo dia
            adjusted = proposed_time.replace(hour=21, minute=50, second=0)
            logger.info(
                f"Filtro circadiano: {proposed_time.strftime('%H:%M')} "
                f"→ {adjusted.strftime('%H:%M')}"
            )
            return adjusted

        if proposed_time.hour < self.QUIET_END:
            # Adia para 07:05
            adjusted = proposed_time.replace(hour=7, minute=5, second=0)
            logger.info(
                f"Filtro circadiano: {proposed_time.strftime('%H:%M')} "
                f"→ {adjusted.strftime('%H:%M')}"
            )
            return adjusted

        return proposed_time

    def can_send_now(self) -> bool:
        """Verifica se pode enviar mensagem agora."""
        return not self.is_quiet_hours()

    def next_available_time(self) -> datetime:
        """Retorna o próximo horário disponível para envio."""
        now = datetime.now()
        if not self.is_quiet_hours(now):
            return now

        if now.hour >= self.QUIET_START:
            # Amanhã 07:05
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=7, minute=5, second=0)
        else:
            # Hoje 07:05
            return now.replace(hour=7, minute=5, second=0)


circadian_filter = CircadianFilter()
