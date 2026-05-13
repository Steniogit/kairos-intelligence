"""
Kairós Intelligence v2.7.1 — Notificações: Cascata de Fallback
WhatsApp (gratuito) → Email (SendGrid) → SMS (Zenvia) → Template Meta (pago).
"""

import logging
import httpx
from shared.evolution_client import evolution_client
from shared.redis_client import redis_client

logger = logging.getLogger("notifications.cascade")


class CascadeSender:
    """Cascata de fallback para envio de mensagens quando janela Meta está fechada."""

    async def send_with_fallback(
        self, phone: str, message: str, email: str = "", patient_name: str = ""
    ) -> dict:
        """Envia mensagem usando cascata de fallback.

        Ordem:
        1. WhatsApp (se janela Meta aberta) — GRATUITO
        2. Email via SendGrid — GRATUITO (até 100/dia)
        3. SMS via Zenvia — ~R$0.20
        4. Template Meta (pré-aprovado) — ~R$0.50
        """
        # 1. Tentar WhatsApp gratuito
        if await redis_client.is_window_open(phone):
            try:
                await evolution_client.send_text(phone, message)
                logger.info(f"Mensagem enviada via WhatsApp (gratuito) para ***{phone[-4:]}")
                return {"channel": "whatsapp", "cost": 0.0, "success": True}
            except Exception as e:
                logger.warning(f"Falha WhatsApp: {e}")

        # 2. Tentar Email (SendGrid)
        if email:
            success = await self._send_email(email, patient_name, message)
            if success:
                logger.info(f"Mensagem enviada via Email para ***{email[-10:]}")
                return {"channel": "email", "cost": 0.0, "success": True}

        # 3. Tentar SMS (Zenvia)
        success = await self._send_sms(phone, message)
        if success:
            logger.info(f"SMS enviado para ***{phone[-4:]}")
            return {"channel": "sms", "cost": 0.20, "success": True}

        # 4. Último recurso: Template Meta (pago)
        try:
            await evolution_client.send_text(phone, message)
            logger.info(f"Template Meta enviado para ***{phone[-4:]}")
            return {"channel": "meta_template", "cost": 0.50, "success": True}
        except Exception as e:
            logger.error(f"Todas as tentativas falharam para ***{phone[-4:]}: {e}")
            return {"channel": "none", "cost": 0.0, "success": False}

    async def _send_email(self, email: str, name: str, message: str) -> bool:
        """Envia email via SendGrid API."""
        # TODO: Integrar com SendGrid
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://api.sendgrid.com/v3/mail/send",
        #         headers={"Authorization": f"Bearer {SENDGRID_KEY}"},
        #         json={...},
        #     )
        #     return response.status_code == 202
        return False

    async def _send_sms(self, phone: str, message: str) -> bool:
        """Envia SMS via Zenvia API."""
        # TODO: Integrar com Zenvia
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://api.zenvia.com/v2/channels/sms/messages",
        #         headers={"X-API-TOKEN": ZENVIA_KEY},
        #         json={...},
        #     )
        #     return response.status_code == 200
        return False


cascade_sender = CascadeSender()
