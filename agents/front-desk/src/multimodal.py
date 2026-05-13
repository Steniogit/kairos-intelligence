"""
Kairós Intelligence v2.7.1 — Front-Desk: Processamento Multimodal
Texto→Texto, Áudio→Áudio (TTS), Imagem→Texto (Gemini Vision).
"""

import base64
import logging
import httpx
from shared.config import settings

logger = logging.getLogger("front-desk.multimodal")


class MultimodalProcessor:
    """Processamento multimodal: texto, áudio e imagem."""

    async def process_audio(self, audio_url: str) -> str:
        """Transcreve áudio usando Gemini Flash."""
        try:
            async with httpx.AsyncClient() as client:
                # Baixar áudio
                audio_resp = await client.get(audio_url, timeout=30)
                audio_b64 = base64.b64encode(audio_resp.content).decode()

                # Enviar para Gemini Flash (transcrição)
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{settings.GEMINI_MODEL_FLASH}:generateContent"
                    f"?key={settings.GEMINI_API_KEY}",
                    json={
                        "contents": [{
                            "parts": [
                                {"text": "Transcreva este áudio em português do Brasil. "
                                         "Retorne apenas o texto transcrito."},
                                {"inline_data": {
                                    "mime_type": "audio/ogg",
                                    "data": audio_b64,
                                }},
                            ],
                        }],
                    },
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                logger.info(f"Áudio transcrito: {len(text)} chars")
                return text
        except Exception as e:
            logger.error(f"Erro ao transcrever áudio: {e}")
            return "[Não foi possível transcrever o áudio]"

    async def process_image(self, image_url: str, prompt: str = "") -> str:
        """Processa imagem usando Gemini Vision (OCR de documentos)."""
        if not prompt:
            prompt = ("Extraia as seguintes informações deste documento: "
                      "nome completo, CPF, data de nascimento, número do documento. "
                      "Retorne em JSON.")

        try:
            async with httpx.AsyncClient() as client:
                # Baixar imagem
                img_resp = await client.get(image_url, timeout=30)
                img_b64 = base64.b64encode(img_resp.content).decode()

                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{settings.GEMINI_MODEL_FLASH}:generateContent"
                    f"?key={settings.GEMINI_API_KEY}",
                    json={
                        "contents": [{
                            "parts": [
                                {"text": prompt},
                                {"inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": img_b64,
                                }},
                            ],
                        }],
                    },
                    timeout=60,
                )
                response.raise_for_status()
                data = response.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                logger.info("Imagem processada com Gemini Vision")
                return text
        except Exception as e:
            logger.error(f"Erro ao processar imagem: {e}")
            return "[Não foi possível processar a imagem]"

    async def text_to_speech(self, text: str) -> str | None:
        """Converte texto em áudio usando Google TTS Journey."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://texttospeech.googleapis.com/v1/text:synthesize",
                    headers={
                        "X-Goog-Api-Key": settings.GOOGLE_TTS_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={
                        "input": {"text": text},
                        "voice": {
                            "languageCode": "pt-BR",
                            "name": settings.GOOGLE_TTS_VOICE,
                        },
                        "audioConfig": {
                            "audioEncoding": "OGG_OPUS",
                            "speakingRate": settings.GOOGLE_TTS_SPEED,
                        },
                    },
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()
                audio_b64 = data.get("audioContent", "")
                if audio_b64:
                    logger.info("TTS gerado com sucesso")
                    return audio_b64
                return None
        except Exception as e:
            logger.error(f"Erro TTS: {e}")
            return None


multimodal = MultimodalProcessor()
