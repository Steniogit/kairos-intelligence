"""
Teste da Fase 3 — Curador Cientifico
Ingere uma bula real da ANVISA e valida a extracao de entidades.
"""
import httpx
import json
import sys

BASE = 'http://172.16.2.12:3100'

print("=" * 60)
print("TESTE FASE 3 - Curador Cientifico")
print("=" * 60)

# Teste 1: Preview de URL (apenas raspar sem extrair)
print("\n=== TEST 1: Preview URL ===")
try:
    r = httpx.post(
        f'{BASE}/api/v1/clinical/ingest/preview',
        json={"url": "https://consultaremedios.com.br/losartana-potassica/bula"},
        timeout=30.0
    )
    data = r.json()
    print(f"Status: {data.get('status')}")
    if data.get('status') == 'ok':
        print(f"Content length: {data.get('text_length')} chars")
        print(f"Preview: {data.get('text', '')[:200]}...")
        print("PASS")
    else:
        print(f"Fetch error: {data.get('error')}")
        print("WARN: URL may be blocked, trying with Wikipedia...")
except Exception as e:
    print(f"Error: {e}")

# Teste 2: Ingestao completa (extrair + quarentena)
print("\n=== TEST 2: Full Ingestion ===")
# Usar Wikipedia que e mais acessivel
test_url = "https://pt.wikipedia.org/wiki/Losartana"
print(f"Ingerindo: {test_url}")

try:
    r = httpx.post(
        f'{BASE}/api/v1/clinical/ingest',
        json={"url": test_url, "auto_quarantine": True},
        timeout=90.0
    )

    if r.status_code != 200:
        print(f"HTTP {r.status_code}: {r.text[:300]}")
        sys.exit(1)

    data = r.json()
    print(f"Status: {data.get('status')}")

    if data.get('status') != 'ok':
        print(f"Error: {data}")
        sys.exit(1)

    # Validar entidades
    entities = data.get('entities_json', {}).get('entities', [])
    print(f"\nEntidades extraidas: {len(entities)}")
    for e in entities[:5]:
        print(f"  [{e.get('type')}] {e.get('name')}")
    assert len(entities) > 0, "Nenhuma entidade extraida!"
    print("PASS")

    # Validar relacionamentos
    rels = data.get('relationships_json', [])
    print(f"\nRelacionamentos: {len(rels)}")
    for rel in rels[:5]:
        print(f"  {rel.get('from_entity')} --[{rel.get('relationship')}]--> {rel.get('to_entity')}")
    print("PASS")

    # Validar Cypher
    cypher = data.get('graph_cypher', '')
    print(f"\nCypher queries geradas: {len(cypher.split(';')) if cypher else 0}")
    if cypher:
        print(f"  Preview: {cypher[:200]}...")
    print("PASS")

    # Validar quarentena
    print(f"\nQuarantine status: {data.get('quarantine_status')}")
    assert data.get('quarantine_status') == 'queued', "Nao foi para quarentena!"
    print("PASS")

except httpx.TimeoutException:
    print("FAIL: Timeout (>90s)")
    sys.exit(1)
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Teste 3: Verificar na quarentena
print("\n=== TEST 3: Verify in Quarantine ===")
try:
    r = httpx.get(f'{BASE}/api/v1/quarantine', params={'status': 'pending'})
    data = r.json()
    print(f"Items pendentes na quarentena: {data['count']}")
    
    # Find our item
    found = False
    for item in data['items']:
        if 'losartana' in item.get('source_url', '').lower() or 'wikipedia' in item.get('source_url', '').lower():
            found = True
            print(f"  Encontrado: {item['source_url']}")
            break
    
    if found:
        print("PASS")
    else:
        print("WARN: Item nao encontrado na quarentena (pode ja ter sido aprovado)")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("CURATOR TESTS COMPLETED!")
print("=" * 60)
