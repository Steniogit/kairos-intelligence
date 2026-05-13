"""
Kairós Intelligence v2.7.1 — Front-Desk: Identificação Híbrida do Paciente
1. Busca no GraphRAG por número WhatsApp
2. Se não encontrar → pede CPF
3. Se CPF não encontrar → fluxo paciente novo (OCR)
"""

import logging
from enum import Enum

from graphrag.retriever import retriever
from graphrag.ingest import ingest_patient

logger = logging.getLogger("front-desk.identification")


class PatientStatus(Enum):
    IDENTIFIED = "identified"             # Paciente encontrado
    NEEDS_CPF = "needs_cpf"               # Pedir CPF
    NEEDS_REGISTRATION = "needs_registration"  # Paciente novo
    CPF_FOUND = "cpf_found"               # CPF encontrado no Ademed


class PatientIdentifier:
    """Identifica pacientes usando GraphRAG + Ademed."""

    async def identify_by_phone(self, clinic_id: str, phone: str) -> dict:
        """Tenta identificar paciente pelo número de WhatsApp.

        Fluxo:
        1. Busca no GraphRAG (Neo4j)
        2. Se encontrar → retorna dados + pede confirmação do nome
        3. Se não encontrar → retorna status NEEDS_CPF
        """
        patient = retriever.identify_patient(clinic_id, phone)

        if patient:
            logger.info(f"Paciente identificado por telefone: {patient.get('name', 'N/A')}")
            return {
                "status": PatientStatus.IDENTIFIED,
                "patient": patient,
                "confirmation_message": f"Olá! Você é o(a) {patient['name']}? 😊",
            }

        return {
            "status": PatientStatus.NEEDS_CPF,
            "patient": None,
            "confirmation_message": (
                "Olá! Bem-vindo(a)! 😊\n"
                "Para dar continuidade, pode me informar seu CPF, por favor?"
            ),
        }

    async def identify_by_cpf(self, clinic_id: str, cpf: str, phone: str) -> dict:
        """Busca paciente por CPF no Ademed (via Manager).

        Se encontrar → registra no GraphRAG e retorna dados.
        Se não encontrar → inicia fluxo de novo paciente.
        """
        # TODO: Chamar Manager para buscar CPF no Ademed via Playwright
        # Placeholder: retorna NEEDS_REGISTRATION
        return {
            "status": PatientStatus.NEEDS_REGISTRATION,
            "patient": None,
            "confirmation_message": (
                "Parece que você é novo(a) por aqui! 🎉\n"
                "Vamos fazer seu cadastro rapidinho.\n\n"
                "Para começar, pode enviar uma foto do seu *documento de identidade* "
                "(RG ou CNH)? 📸"
            ),
        }

    async def register_new_patient(
        self, clinic_id: str, patient_data: dict
    ) -> dict:
        """Registra novo paciente no GraphRAG após cadastro no Ademed."""
        ingest_patient(clinic_id, patient_data)
        logger.info(f"Novo paciente registrado no GraphRAG: {patient_data.get('name', 'N/A')}")
        return {
            "status": PatientStatus.IDENTIFIED,
            "patient": patient_data,
        }

    def mask_cpf(self, cpf: str) -> str:
        """Mascara CPF para logs (LGPD). Ex: 123.456.789-00 → ***.456.***-**"""
        clean = cpf.replace(".", "").replace("-", "")
        if len(clean) == 11:
            return f"***.{clean[3:6]}.***-**"
        return "***.***.***-**"


patient_identifier = PatientIdentifier()
