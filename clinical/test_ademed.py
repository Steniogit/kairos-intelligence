"""
Teste da Fase 5 — Automacao Ademed
Simula o fluxo completo: SOAP finalizado -> geracao de documentos medicos.
"""
import json
import sys
import httpx

BASE = "http://172.16.2.12:3100"

# SOAP de exemplo (simulando output do Copiloto/Agente SOAP)
SOAP_EXAMPLE = {
    "subjective": {
        "chief_complaint": "Falta de ar e dor no peito ha 15 dias",
        "details": "Paciente relata dispneia aos esforcos (subir escadas) e dor precordial "
                   "em aperto. Nega febre, tosse ou expectoracao. Uso cronico de Atenolol 50mg "
                   "e AAS infantil ha 3 anos."
    },
    "objective": {
        "vital_signs": {
            "blood_pressure": "140/90 mmHg",
            "heart_rate": "88 bpm",
            "respiratory_rate": "20 irpm",
            "oxygen_saturation": "95%"
        },
        "exam_findings": "Ausculta pulmonar com crepitacoes bibasais. "
                         "Edema 2+ em membros inferiores. "
                         "Ritmo cardiaco regular, sem sopros."
    },
    "assessment": {
        "working_diagnoses": [
            {"condition": "Insuficiencia cardiaca congestiva", "cid10": "I50.0"},
            {"condition": "Hipertensao arterial sistemica", "cid10": "I10"}
        ],
        "differential": ["Pneumonia", "TEP"]
    },
    "plan": {
        "medications": [
            {"name": "Atenolol", "dosage": "100mg", "frequency": "1x/dia", "route": "via oral",
             "notes": "Aumentado de 50mg para 100mg"},
            {"name": "Furosemida", "dosage": "40mg", "frequency": "1x/dia pela manha",
             "route": "via oral", "notes": "Novo - diuretico"},
            {"name": "AAS", "dosage": "100mg", "frequency": "1x/dia", "route": "via oral",
             "notes": "Manter"}
        ],
        "exams": [
            {"name": "Ecocardiograma trantoracico", "justification": "Avaliar funcao ventricular"},
            {"name": "BNP", "justification": "Marcador de insuficiencia cardiaca"},
            {"name": "Troponina", "justification": "Descartar sindrome coronariana aguda"},
            {"name": "Raio-X de torax PA e perfil", "justification": "Avaliar congestao pulmonar"}
        ],
        "follow_up": "Retorno em 7 dias com exames. Se piora da dispneia, procurar PS."
    }
}


print("=" * 60)
print("TESTE FASE 5 - Automacao Ademed")
print("=" * 60)


# ═══ TEST 1: Listar Templates ═══
print("\n=== TEST 1: Templates Disponiveis ===")
r = httpx.get(f"{BASE}/api/v1/clinical/ademed/templates", timeout=10.0)
data = r.json()
print(f"Templates: {data['count']}")
for key, tmpl in data["templates"].items():
    print(f"  [{key}] {tmpl['name']} — {tmpl['description']}")
assert data["count"] >= 5, f"Esperava 5+ templates, got {data['count']}"
print("PASS")


# ═══ TEST 2: Gerar Receituario ═══
print("\n=== TEST 2: Receituario ===")
r = httpx.post(f"{BASE}/api/v1/clinical/ademed/generate", json={
    "soap": SOAP_EXAMPLE,
    "patient_name": "Joao Carlos da Silva",
    "document_type": "prescription"
}, timeout=30.0)
data = r.json()
print(f"Status: {data['status']}")
assert data["status"] == "ok", f"Falhou: {data}"
doc = data["document"]
print(f"Titulo: {doc.get('title')}")
print(f"Paciente: {doc.get('patient_name')}")
items = doc.get("items", [])
print(f"Medicamentos: {len(items)}")
for item in items:
    print(f"  {item.get('number')}. {item.get('medication')} {item.get('dosage')} — "
          f"{item.get('frequency')} ({item.get('route')})")
print("PASS")


# ═══ TEST 3: Gerar Solicitacao de Exames ═══
print("\n=== TEST 3: Solicitacao de Exames ===")
r = httpx.post(f"{BASE}/api/v1/clinical/ademed/generate", json={
    "soap": SOAP_EXAMPLE,
    "patient_name": "Joao Carlos da Silva",
    "document_type": "exam_request"
}, timeout=30.0)
data = r.json()
print(f"Status: {data['status']}")
assert data["status"] == "ok", f"Falhou: {data}"
doc = data["document"]
exams = doc.get("exams", [])
print(f"Exames solicitados: {len(exams)}")
for ex in exams:
    print(f"  - {ex.get('name')} [{ex.get('urgency')}] ({ex.get('type')})")
print("PASS")


# ═══ TEST 4: Gerar Atestado ═══
print("\n=== TEST 4: Atestado Medico ===")
r = httpx.post(f"{BASE}/api/v1/clinical/ademed/generate", json={
    "soap": SOAP_EXAMPLE,
    "patient_name": "Joao Carlos da Silva",
    "document_type": "sick_note",
    "extra_context": {"authorize_cid": True, "days_requested": 3}
}, timeout=30.0)
data = r.json()
print(f"Status: {data['status']}")
assert data["status"] == "ok", f"Falhou: {data}"
doc = data["document"]
print(f"Texto: {doc.get('text', '')[:120]}...")
print(f"Dias afastamento: {doc.get('days_off')}")
print(f"CID-10: {doc.get('cid10')}")
print("PASS")


# ═══ TEST 5: Batch — Gerar Tudo de Uma Vez ═══
print("\n=== TEST 5: Batch (Todos os Documentos) ===")
r = httpx.post(f"{BASE}/api/v1/clinical/ademed/generate/batch", json={
    "soap": SOAP_EXAMPLE,
    "patient_name": "Joao Carlos da Silva",
    "document_types": ["prescription", "exam_request", "referral"],
    "extra_context": {
        "referral": {"preferred_specialty": "Cardiologia"}
    }
}, timeout=60.0)
data = r.json()
print(f"Status: {data['status']}")
print(f"Documentos gerados: {data['documents_generated']}")
for doc_type, doc in data.get("documents", {}).items():
    print(f"  [{doc_type}] {doc.get('title', doc_type)}")
if data.get("errors"):
    print(f"Erros: {data['errors']}")
assert data["documents_generated"] >= 2, f"Esperava 2+ docs, got {data['documents_generated']}"
print("PASS")


print("\n" + "=" * 60)
print("ADEMED TESTS COMPLETED!")
print("=" * 60)
