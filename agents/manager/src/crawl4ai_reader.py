"""
Kairós Intelligence v2.7.1 — Manager: Leitura do Ademed via Crawl4AI
Operações de leitura rápida sem necessidade de interação com formulários.
"""

import logging

logger = logging.getLogger("manager.reader")

# =============================================================
# NOTA: Seletores CSS são ESPECULATIVOS baseados no MAP.md
# Precisam ser validados contra o HTML real do Ademed v2.02
# =============================================================


class AdemedReader:
    """Operações de leitura no Ademed usando Crawl4AI."""

    def __init__(self):
        self.base_url = ""  # Configurado via settings

    async def search_patient(self, params: dict) -> str:
        """Busca paciente por CPF no Ademed.

        Params: {"cpf": str}
        Retorna: dados do paciente ou "not_found"

        Seletores esperados (VALIDAR):
        - Input pesquisa: #txtPesquisa
        - Botão buscar: #btnPesquisar
        - Resultado: .grid-paciente tr
        """
        cpf = params.get("cpf", "")
        logger.info(f"Buscando paciente por CPF: ***{cpf[-4:]}")

        # TODO: Implementar com Crawl4AI
        # async with crawl4ai.AsyncWebCrawler() as crawler:
        #     result = await crawler.arun(
        #         url=f"{self.base_url}/listaAgenda.php",
        #         session_id="ademed_session",
        #         js_code=f"""
        #             document.querySelector('#txtPesquisa').value = '{cpf}';
        #             document.querySelector('#btnPesquisar').click();
        #         """,
        #         wait_for=".grid-paciente tr",
        #     )
        #     return result.extracted_content

        return f"patient_search:{cpf}"

    async def check_availability(self, params: dict) -> str:
        """Verifica horários disponíveis na agenda.

        Params: {"doctor": str, "date": str, "specialty": str}

        Seletores esperados (VALIDAR):
        - Seletor médico: #cmbMedico
        - Data: #txtData
        - Grade: .agenda-grid td.disponivel
        """
        doctor = params.get("doctor", "")
        date = params.get("date", "")
        logger.info(f"Verificando disponibilidade: Dr. {doctor} em {date}")

        # TODO: Implementar com Crawl4AI
        return f"availability:{doctor}:{date}"

    async def get_appointments_today(self, params: dict) -> str:
        """Extrai agendamentos do dia (para Agente 4 — Notificações).

        Seletores esperados (VALIDAR):
        - Grade agenda: .agenda-grid tr
        - Status: .status-agendamento
        - Nome paciente: .nome-paciente
        - Telefone: .telefone-paciente
        """
        logger.info("Extraindo agendamentos do dia")

        # TODO: Implementar com Crawl4AI
        return "appointments_today:[]"

    async def get_doctors(self, params: dict) -> str:
        """Extrai lista de médicos ativos (para Agente 5 — Sincronizador).

        Seletores esperados (VALIDAR):
        - Menu profissionais: #menuCadastro > li:nth-child(2)
        - Grid médicos: .grid-profissional tr
        - Nome: .nome-profissional
        - Especialidade: .especialidade-profissional
        """
        logger.info("Extraindo lista de médicos ativos")

        # TODO: Implementar com Crawl4AI
        return "doctors:[]"

    async def get_insurance_list(self, params: dict) -> str:
        """Extrai lista de convênios aceitos.

        Seletores esperados (VALIDAR):
        - Menu convênios: #menuCadastro > li:nth-child(3)
        - Grid convênios: .grid-convenio tr
        """
        logger.info("Extraindo lista de convênios")

        # TODO: Implementar com Crawl4AI
        return "insurance:[]"


ademed_reader = AdemedReader()
