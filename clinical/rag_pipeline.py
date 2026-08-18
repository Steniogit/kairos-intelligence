import chromadb
from chromadb.config import Settings
import uuid
import json
import os
import time
import urllib.request
import urllib.parse
from science_client import search_openalex, search_rxnorm, search_openfda, search_who_guidelines

CHROMA_HOST = os.environ.get("CHROMA_HOST", "kairos-chromadb")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8000"))

try:
    chroma_client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
except Exception:
    chroma_client = None

def get_chroma_collection(tenant_slug: str):
    if not chroma_client: return None
    collection_name = f"chat_memory_{tenant_slug.replace('-', '_')}"
    try:
        return chroma_client.get_or_create_collection(name=collection_name)
    except Exception:
        return None

def store_chat_memory(tenant_slug: str, doctor_id: str, query: str, response: str):
    col = get_chroma_collection(tenant_slug)
    if not col: return
    doc_id = str(uuid.uuid4())
    text = f"Doctor: {query}\nAI: {response}"
    col.add(documents=[text], metadatas=[{"doctor_id": doctor_id, "type": "chat_history"}], ids=[doc_id])

def retrieve_chat_memory(tenant_slug: str, doctor_id: str, query: str, k: int = 3):
    col = get_chroma_collection(tenant_slug)
    if not col: return []
    try:
        results = col.query(query_texts=[query], n_results=k, where={"doctor_id": doctor_id})
        if results and results['documents'] and len(results['documents'][0]) > 0:
            return results['documents'][0]
    except Exception:
        pass
    return []

def get_knowledge_cache_collection(tenant_slug: str):
    if not chroma_client: return None
    collection_name = f"knowledge_cache_{tenant_slug.replace('-', '_')}"
    try:
        return chroma_client.get_or_create_collection(name=collection_name)
    except Exception:
        return None

def check_knowledge_cache(tenant_slug: str, query: str):
    col = get_knowledge_cache_collection(tenant_slug)
    if not col: return None
    try:
        results = col.query(query_texts=[query], n_results=1)
        if results and results['documents'] and len(results['documents'][0]) > 0:
            dist = results['distances'][0][0]
            # Usando threshold de 0.25 (distancia L2 pequena significa alta similaridade)
            if dist < 0.25:
                cached_str = results['documents'][0][0]
                return json.loads(cached_str)
    except Exception as e:
        print(f"Cache check error: {e}")
    return None

def store_knowledge_cache(tenant_slug: str, query: str, answer_data: dict):
    col = get_knowledge_cache_collection(tenant_slug)
    if not col: return
    try:
        doc_id = str(uuid.uuid4())
        text_to_store = json.dumps(answer_data, ensure_ascii=False)
        col.add(documents=[text_to_store], metadatas=[{"query": query}], ids=[doc_id])
    except Exception as e:
        print(f"Cache store error: {e}")

def _query_graph_patients(neo4j_driver, query_term: str, tenant_slug: str):
    if not neo4j_driver: return []
    try:
        with neo4j_driver.session() as session:
            cypher = """
            MATCH (p:Patient)-[:HAS_CONDITION|TAKES_MEDICATION]->(c)
            WHERE c.name =~ '(?i).*' + $term + '.*' 
               AND p.tenant_slug = $tenant
            RETURN p.name AS patient, c.name AS condition_or_med
            LIMIT 5
            """
            result = session.run(cypher, term=query_term, tenant=tenant_slug)
            return [f"Paciente: {rec['patient']} ({rec['condition_or_med']})" for rec in result]
    except Exception as e:
        print(f"Neo4j query error: {e}")
        return []

# ── Tool definitions for the LLM ──
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_openalex",
            "description": "Pesquisa literatura cientifica medica internacional. Insira os termos principais da doenca/tratamento (pode ser em portugues, o sistema traduzira e expandira automaticamente).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Termo de busca principal (pode ser em portugues)"},
                    "limit": {"type": "integer", "description": "Numero de resultados (padrao 5)"},
                    "sort_by": {"type": "string", "description": "Ordenacao: cited_by_count ou publication_year"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_rxnorm",
            "description": "Busca o principio ativo (Ingredient) de um medicamento no sistema RxNorm (EUA). Retorna ingredientes ativos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "drug_name": {"type": "string", "description": "Nome do medicamento em ingles"}
                },
                "required": ["drug_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_openfda",
            "description": "Busca informacoes da bula oficial (indicacoes, interacoes, advertencias) de um principio ativo no openFDA. Use o nome generico em ingles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "generic_name": {"type": "string", "description": "Nome generico do principio ativo em ingles"}
                },
                "required": ["generic_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_who_guidelines",
            "description": "Busca diretrizes globais de reabilitacao da OMS (WHO Package of Interventions for Rehabilitation) para uma doenca.",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition": {"type": "string", "description": "Condicao de saude em ingles (ex: 'low back pain', 'stroke')"}
                },
                "required": ["condition"]
            }
        }
    }
]

TOOL_FUNCTIONS = {
    "search_openalex": search_openalex,
    "search_rxnorm": search_rxnorm,
    "search_openfda": search_openfda,
    "search_who_guidelines": search_who_guidelines,
}

def _call_gemini(messages, tools=None, max_retries=3):
    """Call Google Gemini API (OpenAI-compatible) with retry."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    
    for attempt in range(max_retries):
        try:
            body = {
                "model": "gemini-3.5-flash",
                "messages": messages,
                "temperature": 0.3,
                "max_tokens": 4000,
            }
            if tools:
                body["tools"] = tools
                body["tool_choice"] = "auto"
            
            data = json.dumps(body).encode('utf-8')
            req = urllib.request.Request(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )
            resp = urllib.request.urlopen(req, timeout=60)
            return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            error_str = str(e)
            if "429" in error_str:
                wait_time = (2 ** attempt) * 3
                print(f"Gemini API rate limited (attempt {attempt+1}/{max_retries}). Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)
    raise Exception("Limite de requisicoes excedido apos retries.")


async def process_graph_chat(query: str, doctor_id: str, tenant_slug: str, neo4j_driver):
    
    # 0. Check Knowledge Cache
    cached_response = check_knowledge_cache(tenant_slug, query)
    if cached_response:
        print(f"Cache HIT for query: {query}")
        store_chat_memory(tenant_slug, doctor_id, query, cached_response["answer"])
        return {
            "answer": cached_response["answer"],
            "references": cached_response.get("references", []),
            "local_context": [],
            "cached": True
        }
    
    # 1. Fetch from Neo4j (Local Clinical Graph)
    patients = _query_graph_patients(neo4j_driver, query, tenant_slug)
    patients_text = "\n".join(patients) if patients else "Nenhum paciente encontrado."
    
    # 2. Fetch from ChromaDB (Past memory)
    memories = retrieve_chat_memory(tenant_slug, doctor_id, query)
    memory_text = "\n".join(memories) if memories else "Sem conversas anteriores."
    
    # 3. Build system prompt
    sys_prompt = f"""Voce e o Kairos AI, um Assistente Medico Especialista empatico e autonomo, com expertise especial em Fisioterapia e Reabilitacao.
Voce tem acesso a 4 ferramentas farmacologicas/cientificas:
1. search_openalex: Para buscar literatura medica (busque em portugues e o sistema fara a expansao DeCS/MeSH). O sistema automaticamente prioriza estudos indexados no PEDro quando a busca envolve fisioterapia.
2. search_rxnorm: Para descobrir o principio ativo oficial de um medicamento.
3. search_openfda: Para buscar informacoes da bula (interacoes, advertencias).
4. search_who_guidelines: Para buscar as diretrizes oficiais de reabilitacao da OMS.

REGRAS:
- Se a pergunta for uma saudacao (ex: "Bom dia", "Ola"), NAO use ferramentas.
- Se for pergunta clinica, use as ferramentas necessarias.
- Sempre responda em portugues brasileiro.

REGRAS ESPECIAIS PARA FISIOTERAPIA E REABILITACAO (PEDro Priority):
- Quando a pergunta envolver fisioterapia, exercicios terapeuticos, reabilitacao, dor musculoesqueletica, ou qualquer intervencao fisica:
  a) De ALTISSIMA PRIORIDADE a estudos que voce identifique como provavelmente indexados no PEDro (Physiotherapy Evidence Database). Estes sao tipicamente ensaios clinicos randomizados (RCTs) e revisoes sistematicas focados em intervencoes fisioterapeuticas.
  b) Ao apresentar resultados, DESTAQUE estudos que tenham caracteristicas de artigos PEDro: alto rigor metodologico, grupo controle, cegamento, outcomes funcionais.
  c) Inclua na resposta a escala de qualidade metodologica quando possivel (ex: "Nivel de evidencia: Alto - ensaio clinico randomizado").
  d) Sempre que mencionar um exercicio ou intervencao, inclua: tipo de exercicio, dosagem (series/repeticoes), frequencia e duracao quando disponiveis no estudo.
  e) Priorize estudos publicados em journals reconhecidos de fisioterapia: Journal of Physiotherapy, Physical Therapy, Physiotherapy, JOSPT, Archives of Physical Medicine and Rehabilitation, Clinical Rehabilitation.
  f) Use a ferramenta search_who_guidelines quando a pergunta envolver reabilitacao para complementar com diretrizes oficiais da OMS.

=== CONTEXTO CLINICO LOCAL ===
{patients_text}

=== MEMORIA ===
{memory_text}

Sua resposta FINAL deve ser EXCLUSIVAMENTE um JSON valido:
{{
  "resposta": "Sua resposta medica aqui...",
  "consulta_clinica": true,
  "pedro_relevante": true,
  "nivel_evidencia": "Alto/Moderado/Baixo",
  "referencias_usadas": [
    {{"title": "Titulo", "year": "Ano", "authors": "Autores", "doi": "Link", "pedro_indexado": true}}
  ]
}}
Se for saudacao, use consulta_clinica: false, pedro_relevante: false e referencias_usadas: []
Se a pergunta NAO for de fisioterapia, use pedro_relevante: false e omita nivel_evidencia"""

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": query}
    ]
    
    try:
        # First call: may request tool use
        result = _call_gemini(messages, tools=TOOLS)
        choice = result["choices"][0]
        msg = choice["message"]
        
        # Handle tool calls (agent loop - max 3 iterations)
        iterations = 0
        while msg.get("tool_calls") and iterations < 3:
            iterations += 1
            messages.append(msg)
            
            for tool_call in msg["tool_calls"]:
                fn_name = tool_call["function"]["name"]
                fn_args = json.loads(tool_call["function"]["arguments"])
                
                print(f"Tool call: {fn_name}({fn_args})")
                
                fn = TOOL_FUNCTIONS.get(fn_name)
                if fn:
                    tool_result = fn(**fn_args)
                else:
                    tool_result = {"error": f"Ferramenta {fn_name} nao encontrada."}
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result, ensure_ascii=False)[:3000]
                })
            
            # Call again with tool results
            result = _call_gemini(messages)
            choice = result["choices"][0]
            msg = choice["message"]
        
        # Parse final response
        raw = msg.get("content", "").strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            if raw.endswith("```"):
                raw = raw[:-3]
        data = json.loads(raw.strip())
        answer = data.get("resposta", "...")
        papers = data.get("referencias_usadas", [])
        if not data.get("consulta_clinica", True):
            papers = []
            patients = []
            
    except json.JSONDecodeError:
        answer = raw if 'raw' in locals() else "Erro ao processar resposta."
        papers = []
    except Exception as e:
        print(f"Agent error: {e}")
        error_msg = str(e)
        if "429" in error_msg:
            answer = "Desculpe, o sistema esta temporariamente sobrecarregado. Tente novamente em alguns segundos."
        else:
            answer = "Desculpe, ocorreu um erro ao processar sua pergunta. Por favor, tente novamente."
        papers = []
    
    # 4. Store memory
    store_chat_memory(tenant_slug, doctor_id, query, answer)
    
    # 5. Save to knowledge cache (if valid clinical response)
    if data.get("consulta_clinica", True) and not answer.startswith("Desculpe"):
        store_knowledge_cache(tenant_slug, query, {"answer": answer, "references": papers})
    
    return {
        "answer": answer,
        "references": papers,
        "local_context": patients,
        "cached": False
    }
