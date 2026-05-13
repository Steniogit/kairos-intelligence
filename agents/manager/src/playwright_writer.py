"""
Kairós Intelligence v2.7.1 — Manager: Escrita no Ademed via Playwright
Operações de escrita que exigem interação com formulários jQuery UI.
"""

import logging

logger = logging.getLogger("manager.writer")

# =============================================================
# NOTA: Seletores CSS são ESPECULATIVOS baseados no MAP.md
# Precisam ser validados contra o HTML real do Ademed v2.02
# REGRA: UMA operação de browser por vez (fila sequencial)
# =============================================================


class AdemedWriter:
    """Operações de escrita no Ademed usando Playwright."""

    async def register_patient(self, params: dict) -> str:
        """Cadastra paciente novo no Ademed.

        Params: {"name": str, "cpf": str, "birth_date": str,
                 "rg": str, "cep": str, "email": str,
                 "phone": str, "insurance": str, "plan": str}

        Seletores esperados (VALIDAR):
        - Botão novo paciente: #btnNovoPaciente
        - Nome: #txtNome
        - CPF: #txtCPF
        - Nascimento: #txtNascimento
        - RG: #txtRG
        - CEP: #txtCEP (auto-complete ViaCEP)
        - Email: #txtEmail
        - Celular: #txtCelular
        - Convênio: #cmbConvenio
        - Plano: #cmbPlano
        - Salvar: #btnSalvarPaciente
        """
        name = params.get("name", "")
        logger.info(f"Cadastrando paciente: {name}")

        # TODO: Implementar com Playwright
        # async with async_playwright() as p:
        #     browser = await p.chromium.connect_over_cdp("ws://chromium:3000")
        #     page = browser.contexts[0].pages[0]
        #     await page.click("#btnNovoPaciente")
        #     await page.wait_for_selector("#txtNome", state="visible")
        #     await page.fill("#txtNome", params["name"])
        #     await page.fill("#txtCPF", params["cpf"])
        #     ...
        #     await page.click("#btnSalvarPaciente")
        #     await page.wait_for_load_state("networkidle")

        return f"patient_registered:{name}"

    async def create_appointment(self, params: dict) -> str:
        """Cria agendamento na grade de agenda.

        Params: {"patient_id": str, "doctor": str, "date": str,
                 "time": str, "specialty": str, "insurance": str}

        Seletores esperados (VALIDAR):
        - Slot horário: .agenda-grid td[data-hora="{time}"]
        - Dialog agendamento: #dialogAgendamento
        - Paciente: #cmbPacienteAgendamento
        - Confirmar: #btnConfirmarAgendamento
        """
        doctor = params.get("doctor", "")
        date = params.get("date", "")
        time = params.get("time", "")
        logger.info(f"Criando agendamento: Dr. {doctor} em {date} {time}")

        # TODO: Implementar com Playwright
        return f"appointment_created:{doctor}:{date}:{time}"

    async def cancel_appointment(self, params: dict) -> str:
        """Cancela agendamento existente.

        Params: {"appointment_id": str, "reason": str}

        Seletores esperados (VALIDAR):
        - Linha agendamento: tr[data-id="{appointment_id}"]
        - Menu contexto: .context-menu .cancelar
        - Confirmação: #btnConfirmarCancelamento
        """
        appt_id = params.get("appointment_id", "")
        logger.info(f"Cancelando agendamento: {appt_id}")

        # TODO: Implementar com Playwright
        return f"appointment_cancelled:{appt_id}"

    async def upload_document(self, params: dict) -> str:
        """Upload de documento (RG/Carteirinha) na seção Arquivos.

        Params: {"patient_id": str, "file_path": str, "doc_type": str}
        LGPD: Arquivo deletado do VPS imediatamente após upload.

        Seletores esperados (VALIDAR):
        - Aba Arquivos: #tabArquivos
        - Input file: #fileUpload
        - Tipo: #cmbTipoDocumento
        - Upload: #btnUpload
        """
        doc_type = params.get("doc_type", "")
        logger.info(f"Upload de documento: {doc_type}")

        # TODO: Implementar com Playwright
        # LGPD: Deletar arquivo local após upload confirmado
        # import os
        # os.remove(params["file_path"])

        return f"document_uploaded:{doc_type}"

    async def update_status(self, params: dict) -> str:
        """Atualiza status do agendamento (atendido, sem resposta, desmarcado).

        Params: {"appointment_id": str, "status": str}

        Seletores esperados (VALIDAR):
        - Linha: tr[data-id="{appointment_id}"]
        - Status dropdown: .status-select
        """
        status = params.get("status", "")
        logger.info(f"Atualizando status: {status}")

        # TODO: Implementar com Playwright
        return f"status_updated:{status}"

    async def create_consultation_guide(self, params: dict) -> str:
        """Cria Guia de Consulta TISS.

        Params: {"patient_id": str, "doctor": str, "insurance": str,
                 "procedure": str, "ans_code": str}

        Seletores esperados (VALIDAR):
        - Menu Guias: #menuGuias
        - Nova Guia Consulta: #btnNovaGuiaConsulta
        - Campos TISS: #campo1..#campo99
        - Salvar: #btnSalvarGuia
        """
        logger.info("Criando Guia de Consulta TISS")

        # TODO: Implementar com Playwright
        return "consultation_guide_created"


ademed_writer = AdemedWriter()
