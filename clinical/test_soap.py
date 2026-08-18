"""
Teste da Fase 2 — SOAP Pipeline
Envia uma transcricao de consulta medica simulada e valida o JSON retornado.
"""
import httpx
import json
import sys

BASE = 'http://172.16.2.12:3100'

# Transcricao simulada com papo furado misturado a conteudo clinico
FAKE_CONSULTATION = """
Bom dia dona Maria, como a senhora esta? 
Ah doutor, tudo bem gracas a Deus! E o senhor, viu o jogo do Flamengo ontem? Foi lindo ne?
Haha, vi sim, foi um jogaco! Mas vamos la, o que traz a senhora aqui hoje?
Entao doutor, eu to sentindo uma dor de cabeca muito forte ja faz uma semana. Comeca aqui atras da nuca e vai pra frente. E quando eu me abaixo piora muito.
Entendo. A senhora tem medido a pressao?
Medi sim, tava 16 por 10 anteontem.
Hmm, 160 por 100 e alta. A senhora toma algum remedio pra pressao?
Tomo Losartana 50 mas as vezes esqueco.
Vou examinar a senhora. Pressao agora 155 por 95. Ausculta cardiaca normal, sem sopros. 
Dona Maria, pelo quadro a senhora esta com a pressao descontrolada. Vou aumentar a Losartana para 100mg, uma vez ao dia, e adicionar Hidroclorotiazida 25mg pela manha.
Preciso tambem que a senhora faca uns exames: hemograma completo, creatinina, potassio, e um eletrocardiograma.
A senhora volta daqui a 30 dias com os resultados. E nada de sal em excesso, hein!
Ah doutor, meu neto ta fazendo aniversario semana que vem, o senhor nao quer ir?
Obrigado pelo convite dona Maria! Mas vamos focar na saude. Evite comida muito salgada na festa!
"""

print("=" * 60)
print("TESTE FASE 2 — SOAP Pipeline via Gemini Flash")
print("=" * 60)

# Teste 1: Endpoint de texto
print("\n=== TEST 1: SOAP from Text ===")
print(f"Enviando transcricao simulada ({len(FAKE_CONSULTATION)} chars)...")

try:
    r = httpx.post(
        f'{BASE}/api/v1/clinical/soap/text',
        json={"text": FAKE_CONSULTATION},
        timeout=60.0  # Gemini pode levar alguns segundos
    )

    if r.status_code != 200:
        print(f"FAIL: HTTP {r.status_code}")
        print(r.text)
        sys.exit(1)

    data = r.json()
    print(f"Status: {data.get('status')}")

    if data.get('status') != 'ok':
        print(f"FAIL: {data}")
        sys.exit(1)

    soap = data['soap_result']['soap']

    # Validar estrutura SOAP
    print("\n--- SUBJECTIVE ---")
    print(f"  Queixa principal: {soap['subjective']['chief_complaint']}")
    print(f"  Historia: {soap['subjective']['history_present_illness'][:100]}...")
    assert soap['subjective']['chief_complaint'], "chief_complaint vazio!"

    print("\n--- OBJECTIVE ---")
    print(f"  Sinais vitais: {soap['objective'].get('vital_signs', {})}")
    print(f"  Exame fisico: {soap['objective'].get('physical_exam', '')[:100]}")

    print("\n--- ASSESSMENT ---")
    diagnoses = soap['assessment']['diagnoses']
    print(f"  Diagnosticos encontrados: {len(diagnoses)}")
    for d in diagnoses:
        print(f"    - {d['description']} (CID: {d.get('cid10', '?')}, {d.get('certainty', '?')})")
    assert len(diagnoses) > 0, "Nenhum diagnostico encontrado!"

    print("\n--- PLAN ---")
    meds = soap['plan']['medications']
    print(f"  Medicamentos: {len(meds)}")
    for m in meds:
        print(f"    - {m['name']} {m.get('dosage', '')} {m.get('frequency', '')}")
    assert len(meds) > 0, "Nenhum medicamento encontrado!"

    exams = soap['plan'].get('exams_requested', [])
    print(f"  Exames solicitados: {exams}")
    assert len(exams) > 0, "Nenhum exame solicitado!"

    follow = soap['plan'].get('follow_up', '')
    print(f"  Retorno: {follow}")

    print("\n--- METADATA ---")
    meta = data['soap_result'].get('metadata', {})
    print(f"  Confianca: {meta.get('confidence', 'N/A')}")
    print(f"  Conteudo filtrado: {meta.get('filtered_content', 'N/A')[:100]}")

    print("\n" + "=" * 60)
    print("SOAP TEST PASSED!")
    print("=" * 60)

    # Salvar resultado completo
    print("\n\nJSON COMPLETO:")
    print(json.dumps(data['soap_result'], indent=2, ensure_ascii=False))

except httpx.TimeoutException:
    print("FAIL: Timeout (>60s). Gemini pode estar lento.")
    sys.exit(1)
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
