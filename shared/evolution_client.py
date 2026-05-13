"""
Kairós Intelligence v2.7.1 — Cliente Evolution Go
Envio e recebimento de mensagens WhatsApp via Evolution Go API.
"""

import httpx
from shared.config import settings


class EvolutionClient:
    """Cliente HTTP para a API do Evolution Go."""

    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance = settings.EVOLUTION_INSTANCE
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json",
        }

    async def send_text(self, phone: str, message: str) -> dict:
        """Envia mensagem de texto via WhatsApp."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/message/sendText/{self.instance}",
                headers=self.headers,
                json={
                    "number": phone,
                    "text": message,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

    async def send_audio(self, phone: str, audio_url: str) -> dict:
        """Envia mensagem de áudio via WhatsApp."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/message/sendWhatsAppAudio/{self.instance}",
                headers=self.headers,
                json={
                    "number": phone,
                    "audio": audio_url,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

    async def send_image(self, phone: str, image_url: str, caption: str = "") -> dict:
        """Envia imagem via WhatsApp."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/message/sendMedia/{self.instance}",
                headers=self.headers,
                json={
                    "number": phone,
                    "mediatype": "image",
                    "media": image_url,
                    "caption": caption,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        """Verifica se o Evolution Go está respondendo."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/instance/connectionState/{self.instance}",
                    headers=self.headers,
                    timeout=10,
                )
                return response.status_code == 200
        except Exception:
            return False


evolution_client = EvolutionClient()
