"""
STT Pipeline — Google Cloud Speech-to-Text com Diarização
Transcreve áudio com identificação de falantes (Profissional vs Paciente).
"""

import os
import io
import logging
import base64
import tempfile
from typing import Optional

logger = logging.getLogger("kairos-stt")

# ─── Credenciais GCP ─────────────────────────────────────────

CREDENTIALS_PATH = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    os.path.join(os.path.dirname(__file__), "gcp-credentials.json")
)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH

# ─── Client (lazy init) ──────────────────────────────────────

_stt_client = None

def _get_client():
    """Inicializa o client Google Cloud STT (lazy)."""
    global _stt_client
    if _stt_client is None:
        try:
            from google.cloud import speech_v1p1beta1 as speech
            _stt_client = speech.SpeechClient()
            logger.info("Google Cloud STT client inicializado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao inicializar Google Cloud STT: {e}")
            raise
    return _stt_client


# ─── Diarização de Áudio ─────────────────────────────────────

async def diarize_audio(
    audio_bytes: bytes,
    encoding: str = "WEBM_OPUS",
    sample_rate: int = 48000,
    language: str = "pt-BR",
    min_speakers: int = 2,
    max_speakers: int = 2,
) -> dict:
    """
    Transcreve áudio com diarização de falantes usando Google Cloud STT.

    Args:
        audio_bytes: Bytes do áudio (webm/opus ou linear16)
        encoding: Formato do áudio (WEBM_OPUS, LINEAR16, FLAC)
        sample_rate: Taxa de amostragem em Hz
        language: Código do idioma
        min_speakers: Mínimo de falantes esperados
        max_speakers: Máximo de falantes esperados

    Returns:
        dict com:
            - diarized_segments: lista de {speaker: int, text: str, start: float, end: float}
            - full_transcript: transcrição completa
            - speaker_map: mapeamento speaker_tag → role (profissional/paciente)
    """
    import asyncio
    from google.cloud import speech_v1p1beta1 as speech

    client = _get_client()

    # Configurar encoding
    encoding_map = {
        "WEBM_OPUS": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        "LINEAR16": speech.RecognitionConfig.AudioEncoding.LINEAR16,
        "FLAC": speech.RecognitionConfig.AudioEncoding.FLAC,
        "OGG_OPUS": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
    }
    audio_encoding = encoding_map.get(encoding, speech.RecognitionConfig.AudioEncoding.WEBM_OPUS)

    # Configuração de diarização
    diarization_config = speech.SpeakerDiarizationConfig(
        enable_speaker_diarization=True,
        min_speaker_count=min_speakers,
        max_speaker_count=max_speakers,
    )

    config = speech.RecognitionConfig(
        encoding=audio_encoding,
        sample_rate_hertz=sample_rate,
        language_code=language,
        enable_automatic_punctuation=True,
        diarization_config=diarization_config,
        model="latest_long",  # Modelo para áudios longos
        use_enhanced=True,    # Modelo aprimorado
        enable_word_time_offsets=True,
    )

    audio = speech.RecognitionAudio(content=audio_bytes)

    # Usar long_running_recognize para áudios > 1 min
    # Para áudios curtos, usar recognize
    audio_duration_estimate = len(audio_bytes) / (sample_rate * 2)  # Rough estimate

    try:
        if audio_duration_estimate > 55:
            # Long running (> ~1 min)
            operation = client.long_running_recognize(config=config, audio=audio)
            logger.info(f"STT long_running_recognize iniciado, aguardando...")
            response = await asyncio.to_thread(
                lambda: operation.result(timeout=300)
            )
        else:
            # Synchronous (< 1 min)
            response = await asyncio.to_thread(
                client.recognize, config=config, audio=audio
            )
    except Exception as e:
        logger.error(f"Erro no Google Cloud STT: {e}")
        return {
            "diarized_segments": [],
            "full_transcript": "",
            "speaker_map": {},
            "error": str(e)
        }

    # ─── Processar resultado com diarização ───────────────────

    segments = []
    full_transcript = ""
    word_infos = []

    for result in response.results:
        alternative = result.alternatives[0]
        full_transcript += alternative.transcript + " "

        # Coletar informações de palavras com speaker tags
        for word_info in alternative.words:
            word_infos.append({
                "word": word_info.word,
                "speaker_tag": word_info.speaker_tag,
                "start_time": word_info.start_time.total_seconds() if word_info.start_time else 0,
                "end_time": word_info.end_time.total_seconds() if word_info.end_time else 0,
            })

    # ─── Agrupar palavras por falante (segmentos contíguos) ────

    if word_infos:
        current_speaker = word_infos[0]["speaker_tag"]
        current_words = []
        current_start = word_infos[0]["start_time"]

        for wi in word_infos:
            if wi["speaker_tag"] != current_speaker:
                # Finalizar segmento anterior
                if current_words:
                    segments.append({
                        "speaker": current_speaker,
                        "text": " ".join(current_words),
                        "start": current_start,
                        "end": wi["start_time"],
                    })
                # Iniciar novo segmento
                current_speaker = wi["speaker_tag"]
                current_words = [wi["word"]]
                current_start = wi["start_time"]
            else:
                current_words.append(wi["word"])

        # Último segmento
        if current_words:
            segments.append({
                "speaker": current_speaker,
                "text": " ".join(current_words),
                "start": current_start,
                "end": word_infos[-1]["end_time"],
            })

    # ─── Inferir roles (profissional vs paciente) ─────────────
    # Heurística: o falante que faz mais perguntas = profissional
    speaker_question_count = {}
    for seg in segments:
        tag = seg["speaker"]
        questions = seg["text"].count("?")
        speaker_question_count[tag] = speaker_question_count.get(tag, 0) + questions

    # O falante com mais perguntas é o profissional
    speaker_map = {}
    if speaker_question_count:
        sorted_speakers = sorted(speaker_question_count.items(), key=lambda x: -x[1])
        professional_tag = sorted_speakers[0][0]
        for tag in set(s["speaker"] for s in segments):
            if tag == professional_tag:
                speaker_map[tag] = "profissional"
            else:
                speaker_map[tag] = "paciente"

    # Adicionar role a cada segmento
    for seg in segments:
        seg["role"] = speaker_map.get(seg["speaker"], "desconhecido")

    return {
        "diarized_segments": segments,
        "full_transcript": full_transcript.strip(),
        "speaker_map": {str(k): v for k, v in speaker_map.items()},
        "word_count": len(word_infos),
        "segment_count": len(segments),
    }


# ─── Processar chunks acumulados ──────────────────────────────

async def diarize_accumulated_chunks(chunks: list[bytes], encoding: str = "WEBM_OPUS") -> dict:
    """
    Concatena chunks de áudio e processa diarização.

    Args:
        chunks: Lista de bytes de áudio (fragments WebM/Opus)

    Returns:
        Resultado da diarização (ver diarize_audio)
    """
    if not chunks:
        return {
            "diarized_segments": [],
            "full_transcript": "",
            "speaker_map": {},
        }

    # Concatenar todos os chunks
    combined = b"".join(chunks)
    logger.info(f"Processando diarização: {len(combined)} bytes, {len(chunks)} chunks")

    return await diarize_audio(combined, encoding=encoding)


# ─── Health Check ─────────────────────────────────────────────

def check_stt_health() -> dict:
    """Verifica se o Google Cloud STT está acessível."""
    try:
        client = _get_client()
        return {"status": "ok", "message": "Google Cloud STT disponível"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
