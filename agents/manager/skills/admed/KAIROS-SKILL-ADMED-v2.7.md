# SKILL: Operação do Sistema ADMED v2.02
## Para uso exclusivo do Agente 3 (Manager / Clínico)
## v2.7 — Arquitetura Híbrida: Crawl4AI (Leitura) + Playwright (Escrita)

---

## VISÃO GERAL

Esta skill define como o Agente 3 opera o sistema ADMED v2.02 usando uma
**arquitetura híbrida** que maximiza velocidade na leitura e confiabilidade
na escrita:

| Camada | Ferramenta | Quando usar | Ganho |
|---|---|---|---|
| **Leitura** | Crawl4AI | Consultas, buscas, extração de dados | **80% mais rápido** |
| **Escrita** | Playwright | Cadastros, agendamentos, guias, uploads | Garante execução do JavaScript |

**REGRA CRÍTICA DE SESSÃO:** O cookie `PHPSESSID` é compartilhado entre
Crawl4AI e Playwright. A sessão é **sempre iniciada pelo Playwright** (login)
e o Crawl4AI a reutiliza. Nunca criar sessão paralela — o ADMED não suporta
múltiplas sessões simultâneas do mesmo usuário.

**Processos de Leitura (Crawl4AI):**
- **Processo 2:** Busca de paciente por CPF
- **Processo 3:** Consultar histórico e agendamentos ativos
- **Processo 4:** Verificar disponibilidade de horários
- **Processo 9a:** Extrair agendamentos do dia (Agente 4)
- **Processo 9b:** Extrair lista de médicos (Agente 5)
- **Processo 10:** Validar convênios aceitos

**Processos de Escrita (Playwright):**
- **Processo 1:** Login e manutenção de sessão
- **Processo 5:** Cadastro de paciente novo + upload de documentos
- **Processo 6:** Criar agendamento
- **Processo 7:** Cancelamento e reagendamento
- **Processo 8:** Atendimento — guia, executante, ANS

---

## CONFIGURAÇÃO — PLAYWRIGHT (ESCRITA)

```python
import os
import asyncio
from playwright.async_api import async_playwright

ADMED_URL = os.getenv("SISTEMA_URL")
ADMED_USER = os.getenv("SISTEMA_USER")
ADMED_PASS = os.getenv("SISTEMA_PASS")
ADMED_UNIDADE = os.getenv("SISTEMA_UNIDADE", "DEMO")

TIMEOUT_PADRAO = 15000
TIMEOUT_DIALOG = 8000
TIMEOUT_UPLOAD = 30000
TIMEOUT_NAVEGACAO = 20000

# CRÍTICO: Manter contexto do browser entre operações para preservar PHPSESSID
# O contexto é iniciado UMA VEZ e reutilizado em todas as operações de escrita
_playwright_context = None
_playwright_page = None

async def obter_sessao_ativa() -> str:
    """Retorna o valor atual do cookie PHPSESSID para compartilhar com Crawl4AI."""
    global _playwright_page
    if _playwright_page is None:
        raise Exception("Sessão Playwright não iniciada. Executar login primeiro.")
    cookies = await _playwright_page.context.cookies()
    for cookie in cookies:
        if cookie["name"] == "PHPSESSID":
            return cookie["value"]
    raise Exception("Cookie PHPSESSID não encontrado na sessão ativa.")
```

---

## CONFIGURAÇÃO — CRAWL4AI (LEITURA)

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# Crawl4AI compartilha o PHPSESSID do Playwright — sem novo login
async def criar_config_crawl4ai(css_selector: str = None) -> CrawlerRunConfig:
    """
    Cria configuração do Crawl4AI com sessão compartilhada do Playwright.
    O cookie PHPSESSID é obtido da sessão Playwright ativa.
    """
    phpsessid = await obter_sessao_ativa()

    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,          # Sempre buscar dados frescos
        session_id="admed_shared_session",     # Sessão nomeada para reuso
        cookies=[{
            "name": "PHPSESSID",
            "value": phpsessid,
            "domain": ADMED_URL.replace("https://", "").split("/")[0],
            "path": "/",
        }],
        css_selector=css_selector,             # Extrai apenas o elemento relevante
        wait_for="networkidle",
        page_timeout=10000,                    # 10s — mais rápido que Playwright
    )
```

---

## PADRÕES DE OPERAÇÃO — PLAYWRIGHT

### Padrão 1: Inicialização com contexto persistente

```python
async def iniciar_browser():
    global _playwright_context, _playwright_page
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    _playwright_context = await browser.new_context()
    _playwright_page = await _playwright_context.new_page()
    return playwright, browser, _playwright_context, _playwright_page
```

### Padrão 2: Aguardar diálogo jQuery UI

```python
await page.wait_for_selector(".ui-dialog:visible", timeout=TIMEOUT_DIALOG)
await page.wait_for_selector("#nome_pac:visible", timeout=TIMEOUT_DIALOG)
```

### Padrão 3: Campos com busca modal

```python
await page.click("#pesq-paciente")
await page.wait_for_selector(".ui-dialog:visible")
await page.fill("input.busca_paciente_modal", termo_busca)
await page.click("button.pesquisar_paciente_modal")
await page.wait_for_selector(".resultado_paciente tr:first-child")
await page.click(".resultado_paciente tr:first-child")
await page.wait_for_selector("#paciente[value!='']")
```

### Padrão 4: Detectar sessão expirada

```python
async def verificar_sessao(page) -> bool:
    url_atual = page.url
    if "formLogin.php" in url_atual or url_atual.rstrip("/").endswith("/demo"):
        await executar_login(page)
        return False
    return True
```

### Padrão 5: CKEditor

```python
# NÃO usar page.fill() — usar JavaScript diretamente
await page.evaluate(f"CKEDITOR.instances['textoaa'].setData('{conteudo}')")
```

### Padrão 6: Auto-complete CEP (ViaCEP)

```python
await page.fill("#cep", cep)
await page.press("#cep", "Tab")
await page.wait_for_timeout(2500)  # Aguarda chamada ViaCEP e preenchimento automático
```

---

## PROCESSO 1 — LOGIN (Playwright)

```python
async def executar_login(page) -> bool:
    """
    Realiza login no ADMED via Playwright.
    O PHPSESSID gerado será compartilhado com o Crawl4AI.
    """
    try:
        await page.goto(ADMED_URL, timeout=TIMEOUT_NAVEGACAO)
        await page.wait_for_load_state("networkidle")
        await page.select_option("#id_empresa", label=ADMED_UNIDADE)
        await page.fill("#login", ADMED_USER)
        await page.fill("#senha", ADMED_PASS)
        await page.click("#login_bnt")
        await page.wait_for_url("**/listaAgenda.php", timeout=TIMEOUT_PADRAO)
        log_acao("LOGIN", "sistema", "sucesso", f"usuário: {ADMED_USER}")
        return True
    except Exception as e:
        log_acao("LOGIN", "sistema", "erro", str(e))
        return False
```

---

## SEÇÃO DE LEITURA DE DADOS — CRAWL4AI

> Todos os processos desta seção usam Crawl4AI com sessão compartilhada.
> 80% mais rápidos que Playwright puro. Sem renderização JavaScript completa.

---

## PROCESSO 2 — BUSCA DE PACIENTE POR CPF (Crawl4AI)

```python
async def buscar_paciente_por_cpf(cpf: str) -> dict | None:
    """
    Busca paciente pelo CPF usando Crawl4AI.
    Compartilha sessão PHPSESSID do Playwright ativo.
    """
    config = await criar_config_crawl4ai(css_selector="table.resultado")

    schema = {
        "name": "Pacientes",
        "baseSelector": "table.resultado tr[data-id]",
        "fields": [
            {"name": "id", "selector": "", "type": "attribute", "attribute": "data-id"},
            {"name": "nome", "selector": "td.nome", "type": "text"},
            {"name": "cpf", "selector": "td.cpf", "type": "text"},
        ]
    }
    config.extraction_strategy = JsonCssExtractionStrategy(schema)

    async with AsyncWebCrawler() as crawler:
        # Submeter formulário de pesquisa via parâmetros GET
        result = await crawler.arun(
            url=f"{ADMED_URL}/admed/paciente/formPesquisaPaciente.php?cpf={cpf}&acao=pesquisar",
            config=config,
        )

    if not result.success or not result.extracted_content:
        log_acao("BUSCA_PACIENTE", mascarar_cpf(cpf), "não encontrado", "")
        return None

    import json
    dados_lista = json.loads(result.extracted_content)
    if not dados_lista:
        return None

    paciente = dados_lista[0]

    # Buscar dados completos via página de visualização
    config_detalhe = await criar_config_crawl4ai()
    schema_detalhe = {
        "name": "Detalhe",
        "baseSelector": "body",
        "fields": [
            {"name": "nome", "selector": "#nome_pac", "type": "attribute", "attribute": "value"},
            {"name": "cpf", "selector": "#cpf_pac", "type": "attribute", "attribute": "value"},
            {"name": "nascimento", "selector": "#nasci", "type": "attribute", "attribute": "value"},
            {"name": "rg", "selector": "#rg", "type": "attribute", "attribute": "value"},
            {"name": "email", "selector": "#email", "type": "attribute", "attribute": "value"},
            {"name": "celular", "selector": "#cel", "type": "attribute", "attribute": "value"},
            {"name": "cep", "selector": "#cep", "type": "attribute", "attribute": "value"},
            {"name": "convenio", "selector": "#conv_pac", "type": "attribute", "attribute": "value"},
            {"name": "plano", "selector": "#plano_pac", "type": "attribute", "attribute": "value"},
            {"name": "validade_carteirinha", "selector": "#val_pac", "type": "attribute", "attribute": "value"},
        ]
    }
    config_detalhe.extraction_strategy = JsonCssExtractionStrategy(schema_detalhe)

    async with AsyncWebCrawler() as crawler:
        result_detalhe = await crawler.arun(
            url=f"{ADMED_URL}/admed/paciente/formPesquisaPaciente.php?id={paciente['id']}&acao=visualizar",
            config=config_detalhe,
        )

    dados_detalhe = json.loads(result_detalhe.extracted_content)[0] if result_detalhe.success else {}
    dados_detalhe["id"] = paciente["id"]

    log_acao("BUSCA_PACIENTE", mascarar_cpf(cpf), "encontrado",
             f"id: {paciente['id']}, nome: {dados_detalhe.get('nome', '')}")
    return dados_detalhe
```

---

## PROCESSO 3 — CONSULTAR HISTÓRICO DO PACIENTE (Crawl4AI)

```python
async def consultar_historico_paciente(id_paciente: str) -> dict:
    """Consulta histórico via Crawl4AI. Rápido, sem renderização completa."""
    schema = {
        "name": "Agendamentos",
        "baseSelector": "tr.agendamento",
        "fields": [
            {"name": "id", "selector": "", "type": "attribute", "attribute": "data-id"},
            {"name": "situacao", "selector": "", "type": "attribute", "attribute": "data-situacao"},
            {"name": "data", "selector": "td.data", "type": "text"},
            {"name": "hora", "selector": "td.hora", "type": "text"},
            {"name": "medico", "selector": "td.medico", "type": "text"},
            {"name": "especialidade", "selector": "td.especialidade", "type": "text"},
        ]
    }

    config = await criar_config_crawl4ai()
    config.extraction_strategy = JsonCssExtractionStrategy(schema)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=f"{ADMED_URL}/admed/agenda/listaAgenda.php?id_paciente={id_paciente}",
            config=config,
        )

    import json
    todos = json.loads(result.extracted_content) if result.success else []

    historico = {
        "agendamentos_ativos": [a for a in todos if a.get("situacao") == "MARCADO"],
        "ultimas_consultas": [a for a in todos if a.get("situacao") == "ATENDIDO"][:5],
    }

    log_acao("HISTORICO", id_paciente, "sucesso",
             f"ativos: {len(historico['agendamentos_ativos'])}")
    return historico
```

---

## PROCESSO 4 — VERIFICAR DISPONIBILIDADE (Crawl4AI)

```python
async def verificar_disponibilidade(medico: str, data: str) -> list[str]:
    """Verifica horários disponíveis via Crawl4AI. Sem renderizar a grade completa."""
    schema = {
        "name": "HorariosLivres",
        "baseSelector": "td.horario-livre",
        "fields": [
            {"name": "hora", "selector": "", "type": "attribute", "attribute": "data-hora"},
        ]
    }

    config = await criar_config_crawl4ai(css_selector="td.horario-livre")
    config.extraction_strategy = JsonCssExtractionStrategy(schema)

    # URL com filtros de data e médico via query string
    url = f"{ADMED_URL}/admed/agenda/listaAgenda.php?data={data}&sala={medico}"

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)

    import json
    slots = json.loads(result.extracted_content) if result.success else []
    horarios = [s["hora"] for s in slots if s.get("hora")]

    log_acao("DISPONIBILIDADE", medico,
             f"{len(horarios)} livres", f"data: {data}")
    return horarios
```

---

## PROCESSO 9a — EXTRAIR AGENDAMENTOS DO DIA (Crawl4AI)

```python
async def extrair_agendamentos_do_dia(data: str) -> list[dict]:
    """
    Usado pelo Agente 4 para disparar notificações.
    Extração via Crawl4AI — muito mais rápido que Playwright.
    """
    schema = {
        "name": "AgendamentosDia",
        "baseSelector": "tr.agendamento[data-situacao='MARCADO']",
        "fields": [
            {"name": "id", "selector": "", "type": "attribute", "attribute": "data-id"},
            {"name": "hora", "selector": "td.hora", "type": "text"},
            {"name": "paciente_nome", "selector": "td.paciente", "type": "text"},
            {"name": "paciente_celular", "selector": "", "type": "attribute", "attribute": "data-celular"},
            {"name": "paciente_email", "selector": "", "type": "attribute", "attribute": "data-email"},
            {"name": "medico", "selector": "td.medico", "type": "text"},
            {"name": "especialidade", "selector": "td.especialidade", "type": "text"},
        ]
    }

    config = await criar_config_crawl4ai()
    config.extraction_strategy = JsonCssExtractionStrategy(schema)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=f"{ADMED_URL}/admed/agenda/listaAgenda.php?data={data}",
            config=config,
        )

    import json
    agendamentos = json.loads(result.extracted_content) if result.success else []

    log_acao("AGENDAMENTOS_DIA", data, "sucesso",
             f"{len(agendamentos)} agendamentos")
    return agendamentos
```

---

## PROCESSO 9b — EXTRAIR LISTA DE MÉDICOS (Crawl4AI)

```python
async def extrair_lista_medicos() -> list[dict]:
    """
    Usado pelo Agente 5 para sincronização do SOUL.md.
    Crawl4AI extrai a lista sem renderizar JavaScript desnecessário.
    """
    schema = {
        "name": "Medicos",
        "baseSelector": "table.lista tr[data-id][data-ativo='1']",
        "fields": [
            {"name": "id", "selector": "", "type": "attribute", "attribute": "data-id"},
            {"name": "nome", "selector": "td.nome", "type": "text"},
            {"name": "especialidade", "selector": "td.especialidade", "type": "text"},
            {"name": "dias", "selector": "td.dias", "type": "text"},
            {"name": "horario", "selector": "td.horario", "type": "text"},
        ]
    }

    config = await criar_config_crawl4ai()
    config.extraction_strategy = JsonCssExtractionStrategy(schema)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=f"{ADMED_URL}/admed/profissional/listaProfissional.php",
            config=config,
        )

    import json
    medicos = json.loads(result.extracted_content) if result.success else []

    log_acao("SYNC_MEDICOS", "agente5", "sucesso",
             f"{len(medicos)} médicos extraídos")
    return medicos
```

---

## PROCESSO 10 — VALIDAR CONVÊNIO (Crawl4AI)

```python
async def validar_convenio(nome_convenio: str) -> bool:
    """
    Verifica se um convênio é aceito pela clínica.
    Leitura rápida via Crawl4AI.
    """
    schema = {
        "name": "Convenios",
        "baseSelector": "table.convenios tr[data-ativo='1']",
        "fields": [
            {"name": "nome", "selector": "td.nome", "type": "text"},
        ]
    }

    config = await criar_config_crawl4ai()
    config.extraction_strategy = JsonCssExtractionStrategy(schema)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=f"{ADMED_URL}/admed/convenio/listaConvenio.php",
            config=config,
        )

    import json
    convenios = json.loads(result.extracted_content) if result.success else []
    nomes = [c["nome"].lower() for c in convenios]
    aceito = any(nome_convenio.lower() in n for n in nomes)

    log_acao("VALIDAR_CONVENIO", nome_convenio,
             "aceito" if aceito else "não aceito", "")
    return aceito
```

---

## SEÇÃO DE AUTOMAÇÃO DE ESCRITA — PLAYWRIGHT

> Todos os processos desta seção usam Playwright com sessão persistente.
> Playwright garante execução correta do JavaScript do ADMED (jQuery UI,
> validações, cálculos automáticos de totais).

---

## PROCESSO 5 — CADASTRO DE PACIENTE NOVO (Playwright)

```python
async def cadastrar_paciente_novo(page, dados: dict) -> str:
    """
    Cadastra novo paciente no ADMED via Playwright.
    Playwright necessário para interação com diálogos jQuery UI.

    dados esperados:
        nome, nascimento, cpf, rg, cep, email, celular,
        convenio_nome, plano, carteirinha_validade,
        arquivo_rg (path), arquivo_carteirinha (path)
    """
    await verificar_sessao(page)

    await page.goto(
        f"{ADMED_URL}/admed/paciente/formPesquisaPaciente.php",
        timeout=TIMEOUT_NAVEGACAO
    )
    await page.wait_for_load_state("networkidle")

    await page.click("button:has-text('Novo')")
    await page.wait_for_selector("#nome_pac:visible", timeout=TIMEOUT_DIALOG)

    # Dados pessoais
    await page.fill("#nome_pac", dados["nome"])
    await page.fill("#nasci", dados["nascimento"])
    await page.fill("#cpf_pac", dados["cpf"])
    await page.fill("#rg", dados.get("rg", ""))

    # Endereço via CEP (auto-complete ViaCEP)
    await page.fill("#cep", dados["cep"])
    await page.press("#cep", "Tab")
    await page.wait_for_timeout(2500)

    # Contato
    await page.fill("#email", dados["email"])
    await page.fill("#cel", dados["celular"])

    # Convênio via modal
    await page.click("#pesq_convenio_pac")
    await page.wait_for_selector(".ui-dialog:visible")
    await page.fill("input.busca_convenio", dados["convenio_nome"])
    await page.click("button.pesquisar_convenio")
    await page.wait_for_selector(".resultado_convenio tr:first-child")
    await page.click(".resultado_convenio tr:first-child")
    await page.fill("#plano_pac", dados["plano"])
    await page.fill("#val_pac", dados["carteirinha_validade"])

    # Gravar
    await page.click("button:has-text('Gravar')")
    await page.wait_for_timeout(2000)

    id_paciente = await page.input_value("#id_novo_paciente")
    if not id_paciente:
        raise Exception(f"Falha ao cadastrar: {dados['nome']}")

    log_acao("CADASTRO", mascarar_cpf(dados["cpf"]),
             "sucesso", f"id: {id_paciente}")

    # Upload de documentos
    await fazer_upload_documentos(page, id_paciente, dados)
    return id_paciente


async def fazer_upload_documentos(page, id_paciente: str, dados: dict):
    """
    Upload de RG e Carteirinha via Playwright.
    REGRA LGPD: Deletar arquivos locais imediatamente após upload confirmado.
    """
    try:
        await page.click("button:has-text('Arquivos')")
        await page.wait_for_selector(".ui-dialog:visible", timeout=TIMEOUT_DIALOG)

        for campo, chave_log in [
            ("arquivo_rg", "UPLOAD_RG"),
            ("arquivo_carteirinha", "UPLOAD_CARTEIRINHA")
        ]:
            arquivo = dados.get(campo)
            if arquivo and os.path.exists(arquivo):
                input_file = await page.query_selector("input[type='file']")
                await input_file.set_input_files(arquivo)
                await page.click("button:has-text('Enviar')")
                await page.wait_for_timeout(3000)
                os.remove(arquivo)  # DELETAR IMEDIATAMENTE — LGPD
                log_acao(chave_log, id_paciente, "sucesso", "arquivo deletado do VPS")

        await page.click(".ui-dialog-titlebar-close")

    except Exception as e:
        log_acao("UPLOAD_DOCS", id_paciente, "erro", str(e))
        notificar_recepcionista(
            f"Upload de documentos falhou — paciente ID {id_paciente}. "
            f"Fazer upload manual no ADMED."
        )
```

---

## PROCESSO 6 — CRIAR AGENDAMENTO (Playwright)

```python
async def criar_agendamento(page, dados: dict) -> dict:
    """
    Cria agendamento via Playwright.
    Playwright necessário para interação com a grade de agenda jQuery.
    """
    await verificar_sessao(page)

    await page.goto(f"{ADMED_URL}/admed/agenda/listaAgenda.php",
                    timeout=TIMEOUT_NAVEGACAO)
    await page.wait_for_load_state("networkidle")

    await page.click("button:has-text('Novo')")
    await page.wait_for_selector("#paciente:visible", timeout=TIMEOUT_DIALOG)

    await page.select_option("#empresa", label=ADMED_UNIDADE)
    await page.select_option("#sala", label=dados["medico"])
    await page.fill("#data", dados["data"])
    await page.fill("#hora", dados["hora"])

    # Paciente via modal
    await page.click("#pesq-paciente")
    await page.wait_for_selector(".ui-dialog:visible")
    await page.fill("input.busca_paciente_modal", dados["nome_paciente"])
    await page.click("button.pesquisar_paciente_modal")
    await page.wait_for_selector(".resultado_paciente tr:first-child")
    await page.click(".resultado_paciente tr:first-child")
    await page.wait_for_selector("#paciente[value!='']")

    # Convênio via modal
    await page.click("#pesq-convenio")
    await page.wait_for_selector(".ui-dialog:visible")
    await page.fill("input.busca_convenio_modal", dados["convenio"])
    await page.click("button.pesquisar_convenio_modal")
    await page.wait_for_selector(".resultado_convenio tr:first-child")
    await page.click(".resultado_convenio tr:first-child")

    await page.select_option("#situacao", "MARCADO")
    await page.click("button:has-text('Gravar')")
    await page.wait_for_timeout(2000)

    numero_agendamento = await page.input_value("#lanc1")

    resultado = {
        "numero_agendamento": numero_agendamento,
        "paciente": dados["nome_paciente"],
        "medico": dados["medico"],
        "data": dados["data"],
        "hora": dados["hora"],
        "convenio": dados["convenio"],
    }

    log_acao("AGENDAMENTO", dados.get("id_paciente", ""),
             "sucesso", f"agendamento: {numero_agendamento}")
    return resultado
```

---

## PROCESSO 7 — CANCELAMENTO (Playwright)

```python
async def cancelar_agendamento(page, numero_agendamento: str):
    """Cancela agendamento via Playwright. Altera status no jQuery UI."""
    await verificar_sessao(page)

    await page.goto(f"{ADMED_URL}/admed/agenda/listaAgenda.php",
                    timeout=TIMEOUT_NAVEGACAO)
    await page.wait_for_load_state("networkidle")

    await page.fill("#busca_agendamento", numero_agendamento)
    await page.press("#busca_agendamento", "Enter")
    await page.wait_for_selector(f"tr[data-agendamento='{numero_agendamento}']")
    await page.click(f"tr[data-agendamento='{numero_agendamento}']")
    await page.wait_for_selector("#situacao:visible")

    await page.select_option("#situacao", "DESMARCADO")
    await page.click("button:has-text('Gravar')")
    await page.wait_for_timeout(1000)

    log_acao("CANCELAMENTO", numero_agendamento, "sucesso", "")
```

---

## PROCESSO 8 — ATENDIMENTO / GUIA / FATURA (Playwright)

### 8a: Marcar como ATENDIDO

```python
async def marcar_como_atendido(page, numero_agendamento: str):
    """Altera status para ATENDIDO via Playwright."""
    await verificar_sessao(page)

    await page.goto(f"{ADMED_URL}/admed/agenda/listaAgenda.php",
                    timeout=TIMEOUT_NAVEGACAO)
    await page.wait_for_load_state("networkidle")

    await page.fill("#busca_agendamento", numero_agendamento)
    await page.press("#busca_agendamento", "Enter")
    await page.wait_for_selector(f"tr[data-agendamento='{numero_agendamento}']")
    await page.click(f"tr[data-agendamento='{numero_agendamento}']")
    await page.wait_for_selector("#situacao:visible")

    await page.select_option("#situacao", "ATENDIDO")
    await page.click("button:has-text('Gravar')")
    await page.wait_for_timeout(1000)

    log_acao("STATUS_ATENDIDO", numero_agendamento, "sucesso", "")
```

### 8b: Criar Guia/Fatura

```python
async def criar_guia(page, numero_agendamento: str, dados_guia: dict) -> str:
    """
    Cria guia/fatura via Playwright.
    Playwright necessário: cálculos de totais feitos por JavaScript do ADMED.

    dados_guia:
        tipo_guia: "SP/SADT" ou "CONSULTA"
        convenio, matricula, plano
        tipo_atendimento: "04-Consulta" (padrão)
        tipo_consulta: "Primeira" ou "Segmento"
        medico_executante: nome do médico
        empresa_executante: razão social (CONTRATADO EXECUTANTE)
        procedimento_codigo: código TUSS
        senha_autorizacao: (opcional — ANS)
        data_autorizacao: (opcional — ANS)
    """
    from datetime import date
    hoje = date.today().strftime("%d/%m/%Y")

    await page.click("button:has-text('Fatura')")
    await page.wait_for_selector("#tipo_guia:visible", timeout=TIMEOUT_DIALOG)

    # Cabeçalho
    await page.select_option("#tipo_guia", dados_guia["tipo_guia"])
    await page.fill("#conv_fatura", dados_guia["convenio"])
    await page.fill("#matr_fatura", dados_guia["matricula"])
    await page.fill("#plano_fatura", dados_guia["plano"])
    await page.fill("#data_lanc_fatura", hoje)

    # Informações clínicas
    await page.select_option("#tipo_atend_fatura",
                              dados_guia.get("tipo_atendimento", "04-Consulta"))
    await page.select_option("#tipo_consulta_fatura",
                              dados_guia.get("tipo_consulta", "Primeira"))
    await page.select_option("#regime_atend", "Ambulatorial")
    await page.select_option("#carater_sol_fatura", "Eletiva")

    # Autorização ANS (se necessário)
    if dados_guia.get("senha_autorizacao"):
        await page.fill("#senha_aut_fatura", dados_guia["senha_autorizacao"])
        await page.fill("#data_aut_fatura",
                        dados_guia.get("data_autorizacao", hoje))

    # Profissional executante — Campo 29 SP/SADT / Campo 9 Guia Consulta
    await page.click("#pesq_prof_exec_fatura")
    await page.wait_for_selector(".ui-dialog:visible")
    await page.fill("input.busca_prof_exec", dados_guia["medico_executante"])
    await page.click("button.pesquisar_prof_exec")
    await page.wait_for_selector(".resultado_prof_exec tr:first-child")
    await page.click(".resultado_prof_exec tr:first-child")

    # Empresa executante (CONTRATADO EXECUTANTE)
    await page.click("#pesq_emp_exec_fatura")
    await page.wait_for_selector(".ui-dialog:visible")
    await page.fill("input.busca_emp_exec", dados_guia["empresa_executante"])
    await page.click("button.pesquisar_emp_exec")
    await page.wait_for_selector(".resultado_emp_exec tr:first-child")
    await page.click(".resultado_emp_exec tr:first-child")

    # Procedimento
    await page.fill("#cod_proc_fatura_1", dados_guia["procedimento_codigo"])
    await page.wait_for_timeout(1000)
    await page.fill("#qt_sol_fatura_1", "1")
    await page.fill("#qt_aut_fatura_1", "1")
    # NUNCA preencher #total_proc_fatura e #total_geral_fatura
    # — calculados automaticamente pelo JavaScript do ADMED

    # Gravar
    await page.click("button:has-text('Gravar Fatura')")
    await page.wait_for_timeout(2000)

    numero_guia = await page.input_value("#cod_fatura")
    if not numero_guia:
        raise Exception("Falha ao criar guia — número não gerado")

    log_acao("CRIAR_GUIA", numero_agendamento, "sucesso",
             f"guia: {numero_guia}, tipo: {dados_guia['tipo_guia']}")
    return numero_guia
```

---

## LOG DE AÇÕES (OBRIGATÓRIO EM TODAS AS OPERAÇÕES)

```python
import json
from datetime import datetime

LOG_FILE = os.path.expanduser("~/logs/agente3-actions.log")


def log_acao(operacao: str, identificador: str, resultado: str, detalhe: str):
    """
    NUNCA incluir dados de saúde — apenas ações e identificadores.
    Retenção: 90 dias.
    """
    entrada = {
        "timestamp": datetime.now().isoformat(),
        "operacao": operacao,
        "identificador": identificador,
        "resultado": resultado,
        "detalhe": detalhe,
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")


def mascarar_cpf(cpf: str) -> str:
    partes = cpf.replace(".", "").replace("-", "")
    if len(partes) == 11:
        return f"{partes[:3]}.***.***.{partes[-2:]}"
    return "***.***.***-**"
```

---

## TRATAMENTO DE ERROS E FALLBACK

```python
async def executar_com_retry(page, func, max_tentativas=2, **kwargs):
    """
    Retry automático para operações Playwright.
    Se todas falharem: salva pendente + notifica recepcionista.
    """
    ultimo_erro = None
    for tentativa in range(max_tentativas):
        try:
            return await func(page, **kwargs)
        except Exception as e:
            ultimo_erro = e
            log_acao("RETRY", func.__name__,
                     f"tentativa {tentativa+1}/{max_tentativas}", str(e))
            # Verificar se é problema de sessão expirada
            if "login" in str(e).lower() or "PHPSESSID" in str(e):
                await executar_login(page)
            await asyncio.sleep(3)

    salvar_pendente(func.__name__, str(ultimo_erro), kwargs)
    notificar_recepcionista(
        f"⚠️ Operação falhou no ADMED após {max_tentativas} tentativas.\n"
        f"Operação: {func.__name__}\nErro: {ultimo_erro}\n"
        f"Processar manualmente."
    )
    raise ultimo_erro


async def executar_crawl4ai_com_retry(func, max_tentativas=2, **kwargs):
    """
    Retry automático para operações Crawl4AI.
    Se sessão expirou: reexecuta login via Playwright e tenta novamente.
    """
    ultimo_erro = None
    for tentativa in range(max_tentativas):
        try:
            return await func(**kwargs)
        except Exception as e:
            ultimo_erro = e
            log_acao("RETRY_CRAWL4AI", func.__name__,
                     f"tentativa {tentativa+1}/{max_tentativas}", str(e))
            # Se sessão expirou, refazer login via Playwright
            if "PHPSESSID" in str(e) or "login" in str(e).lower():
                await executar_login(_playwright_page)
            await asyncio.sleep(2)

    log_acao("FALHA_CRAWL4AI", func.__name__, "erro_permanente", str(ultimo_erro))
    raise ultimo_erro


def salvar_pendente(operacao: str, erro: str, dados: dict):
    pendente = {
        "timestamp": datetime.now().isoformat(),
        "operacao": operacao,
        "erro": erro,
        "dados": str(dados),
    }
    PENDENTES = os.path.expanduser("~/logs/agendamentos-pendentes.json")
    with open(PENDENTES, "a", encoding="utf-8") as f:
        f.write(json.dumps(pendente, ensure_ascii=False) + "\n")
```

---

## NOTAS TÉCNICAS IMPORTANTES

1. **Arquitetura Híbrida** — Leitura via Crawl4AI (80% mais rápido), escrita via Playwright (garante JS do ADMED).

2. **Sessão PHP compartilhada** — O cookie `PHPSESSID` é iniciado pelo Playwright no login e reutilizado pelo Crawl4AI em todas as leituras. Uma única sessão PHP para tudo.

3. **Sistema ADMED v2.02** — PHP com sessão por cookie. Mega-page com 2.415 elementos em `listaAgenda.php`. Formulários são diálogos jQuery UI sem URLs próprias.

4. **Sessão PHP** — Manter contexto do browser Playwright entre operações. Renovar automaticamente quando expirar.

5. **Performance** — `listaAgenda.php` é pesada. Playwright usa `waitForLoadState("networkidle")` com timeouts de 15-20s. Crawl4AI opera com seletores CSS diretos, timeout de 10s.

6. **Fila sequencial** — Processar UMA operação de escrita (Playwright) por vez. Leituras Crawl4AI podem ser paralelas quando necessário.

7. **Segurança** — Credenciais apenas em variáveis de ambiente. Arquivos de documentos deletados do VPS imediatamente após upload (LGPD).

8. **Totais da guia** — Calculados pelo JavaScript do ADMED. Nunca preencher `#total_proc_fatura` e `#total_geral_fatura` manualmente.

9. **Dependências** — `pip install crawl4ai playwright` + `playwright install chromium`

---

*SKILL: Operação do Sistema ADMED v2.02*
*Versão 2.7 — Arquitetura Híbrida Crawl4AI + Playwright — Maio 2026*
*Para uso exclusivo do Agente 3 (Manager / Clínico)*
