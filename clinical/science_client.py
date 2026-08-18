import urllib.request
import urllib.parse
import json

def reconstruct_abstract(inverted_index):
    if not inverted_index:
        return ""
    try:
        max_idx = max(idx for indices in inverted_index.values() for idx in indices)
        words = [""] * (max_idx + 1)
        for word, indices in inverted_index.items():
            for idx in indices:
                words[idx] = word
        return " ".join(words)
    except Exception:
        return ""

# ── PEDro keyword markers ──
# When these terms appear in the query, we know it's a physiotherapy/rehabilitation topic
# and should add PEDro-relevant filters to the OpenAlex search.
PEDRO_KEYWORDS = [
    "fisioterapia", "physiotherapy", "physical therapy", "reabilitacao", "rehabilitation",
    "exercicio", "exercise", "cinesioterapia", "kinesiology", "mobilizacao", "mobilization",
    "alongamento", "stretching", "fortalecimento", "strengthening", "terapia manual",
    "manual therapy", "eletroterapia", "electrotherapy", "ultrassom", "ultrasound therapy",
    "tens", "laser", "hidroterapia", "hydrotherapy", "pilates", "propriocepcao",
    "proprioception", "equilíbrio", "balance training", "marcha", "gait",
    "lombalgia", "low back pain", "cervicalgia", "neck pain", "ombro", "shoulder",
    "joelho", "knee", "tornozelo", "ankle", "quadril", "hip", "coluna", "spine",
    "tendinite", "tendinitis", "bursite", "bursitis", "artrose", "osteoarthritis",
    "entorse", "sprain", "pos-operatorio", "postoperative", "avc", "stroke",
    "paralisia cerebral", "cerebral palsy", "lesao medular", "spinal cord injury",
    "dor cronica", "chronic pain", "fibromialgia", "fibromyalgia"
]

def _is_physiotherapy_query(query: str) -> bool:
    """Detect if a query is related to physiotherapy/rehabilitation."""
    query_lower = query.lower()
    return any(kw in query_lower for kw in PEDRO_KEYWORDS)

def _expand_query(query: str) -> str:
    import os
    import json
    import urllib.request
    
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key: return query
    
    is_physio = _is_physiotherapy_query(query)
    
    if is_physio:
        sys_prompt = (
            "Atue como um especialista em buscas bibliograficas PubMed/DeCS/MeSH com foco em FISIOTERAPIA e REABILITACAO. "
            f"O usuario buscou por: '{query}'.\n"
            "INSTRUCOES ESPECIAIS PARA FISIOTERAPIA:\n"
            "1. Traduza para o MeSH term oficial em ingles.\n"
            "2. Expanda usando sinonimos com OR.\n"
            "3. OBRIGATORIAMENTE inclua termos que maximizem resultados indexados no PEDro (Physiotherapy Evidence Database), "
            "como: 'physical therapy modalities', 'exercise therapy', 'rehabilitation', 'musculoskeletal manipulations'.\n"
            "4. Adicione um AND com (randomized controlled trial OR systematic review OR clinical trial OR PEDro).\n"
            "5. Se a busca envolver uma regiao corporal, adicione o termo anatomico MeSH correspondente.\n"
            "Retorne APENAS a string de busca final, sem aspas externas e sem explicacoes extras."
        )
    else:
        sys_prompt = (
            "Atue como um especialista em buscas bibliograficas PubMed/DeCS/MeSH. "
            f"O usuario buscou por: '{query}'.\n"
            "Traduza para o MeSH term oficial em ingles e expanda a busca usando sinonimos com o operador OR. "
            "Se for pergunta sobre tratamento/eficacia, adicione um AND com (randomized controlled trial OR systematic review). "
            "Retorne APENAS a string de busca final, sem aspas externas e sem explicacoes extras."
        )
    
    # Determine which API to use
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    
    try:
        if gemini_key:
            body = {
                "model": "gemini-3.5-flash",
                "messages": [{"role": "user", "content": sys_prompt}],
                "temperature": 0.1,
                "max_tokens": 150,
            }
            req = urllib.request.Request(
                "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                data=json.dumps(body).encode('utf-8'),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {gemini_key}"
                }
            )
        else:
            openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
            body = {
                "model": "google/gemini-2.5-flash",
                "messages": [{"role": "user", "content": sys_prompt}],
                "temperature": 0.1,
                "max_tokens": 150,
            }
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=json.dumps(body).encode('utf-8'),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openrouter_key}"
                }
            )
        
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode('utf-8'))
        expanded = data["choices"][0]["message"]["content"].strip()
        # Remove any markdown code blocks if the LLM adds them
        if expanded.startswith("`"): expanded = expanded.strip("`")
        
        if is_physio:
            print(f"[PEDro-Enhanced] Original: {query} -> Expanded: {expanded}")
        
        return expanded
    except Exception as e:
        print(f"Expansion error: {e}")
        return query

def search_openalex(query: str, limit: int = 5, sort_by: str = "cited_by_count"):
    """
    Pesquisa literatura científica médica internacional.
    Use queries curtas e em inglês (ex: 'type 2 diabetes treatments').
    sort_by pode ser 'cited_by_count' (para impacto) ou 'publication_year' (para recentes).
    """
    try:
        expanded_query = _expand_query(query)
        print(f"Original query: {query} -> Expanded: {expanded_query}")
        
        sort_str = f"{sort_by}:desc" if ":" not in sort_by else sort_by
        url = f"https://api.openalex.org/works?search={urllib.parse.quote(expanded_query)}&per-page={limit}&sort={sort_str}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'mailto:kairos-med@example.com'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        results = []
        for work in data.get('results', []):
            title = work.get('title')
            if not title: continue
            
            abstract = reconstruct_abstract(work.get('abstract_inverted_index', {}))
            authors = [a['author']['display_name'] for a in work.get('authorships', []) if 'author' in a]
            
            results.append({
                'title': title,
                'abstract': abstract[:800] + '...' if len(abstract) > 800 else abstract,
                'authors': ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else ""),
                'year': work.get('publication_year', ''),
                'doi': work.get('doi', '')
            })
        return results
    except Exception as e:
        print(f"OpenAlex error: {e}")
        return []

def search_rxnorm(drug_name: str):
    """
    Busca o princípio ativo (Ingredient) de um medicamento no sistema RxNorm (EUA).
    Retorna o nome dos princípios ativos.
    """
    try:
        url = f"https://rxnav.nlm.nih.gov/REST/drugs.json?name={urllib.parse.quote(drug_name)}"
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read().decode('utf-8'))
        
        if 'drugGroup' not in data or 'conceptGroup' not in data['drugGroup']:
            return {"error": "Medicamento não encontrado no RxNorm."}
            
        rxcui = None
        for cg in data['drugGroup']['conceptGroup']:
            if 'conceptProperties' in cg:
                rxcui = cg['conceptProperties'][0]['rxcui']
                break
                
        if not rxcui:
             return {"error": "Sem RXCUI associado."}
             
        rel_url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/allrelated.json"
        rel_resp = urllib.request.urlopen(rel_url, timeout=10)
        rel_data = json.loads(rel_resp.read().decode('utf-8'))
        
        ingredients = []
        for group in rel_data.get('allRelatedGroup', {}).get('conceptGroup', []):
            if group.get('tty') in ['IN', 'MIN']:
                for prop in group.get('conceptProperties', []):
                    ingredients.append(prop['name'])
                    
        return {"drug_name": drug_name, "active_ingredients": ingredients}
    except Exception as e:
        print(f"RxNorm error: {e}")
        return {"error": str(e)}

def search_openfda(generic_name: str):
    """
    Busca a bula estruturada (Indicações, Advertências, Interações) de um princípio ativo no openFDA.
    Use o nome genérico em inglês.
    """
    try:
        url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:\"{urllib.parse.quote(generic_name)}\"&limit=1"
        resp = urllib.request.urlopen(url, timeout=15)
        data = json.loads(resp.read().decode('utf-8'))
        
        if 'results' not in data:
            return {"error": "Bula não encontrada."}
            
        label = data['results'][0]
        return {
            "indications": label.get('indications_and_usage', ['N/A'])[0][:500],
            "drug_interactions": label.get('drug_interactions', ['Não listadas'])[0][:500],
            "boxed_warning": label.get('boxed_warning', ['Nenhuma'])[0][:500],
            "brand_name": label.get('openfda', {}).get('brand_name', ['N/A'])[0]
        }
    except Exception as e:
        print(f"openFDA error: {e}")
        return {"error": str(e)}

def search_who_guidelines(condition: str):
    """
    Busca diretrizes do WHO Package of Interventions for Rehabilitation (PIR) para uma condicao de saude.
    Condicoes suportadas atualmente: 'low back pain', 'stroke'.
    """
    import os
    import json
    
    file_path = os.path.join(os.path.dirname(__file__), "who_guidelines.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            who_data = json.load(f)
            
        condition_lower = condition.lower()
        for key, data in who_data.items():
            if key in condition_lower or condition_lower in key:
                return data
                
        return {"error": "Diretrizes da OMS não encontradas para esta condição no banco local."}
    except Exception as e:
        print(f"WHO search error: {e}")
        return {"error": str(e)}
