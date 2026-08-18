import httpx
import json

BASE = 'http://kairos-clinical:3100'

# 1. Health check
print('=== TEST 1: Health Check ===')
r = httpx.get(f'{BASE}/health')
data = r.json()
print(json.dumps(data, indent=2))
assert data['postgres'] == 'online', 'Postgres offline!'
assert data['neo4j'] == 'online', 'Neo4j offline!'
print('PASS\n')

# 2. Create patient in graph
print('=== TEST 2: Create Patient Node ===')
r = httpx.post(f'{BASE}/api/v1/graph/patient', json={
    'cpf': '000.000.000-00',
    'name': 'Paciente Teste',
    'phone': '5561999990000',
    'birth_date': '1990-01-01'
})
print(r.json())
assert r.status_code == 200
print('PASS\n')

# 3. Query patient
print('=== TEST 3: Query Patient ===')
r = httpx.get(f'{BASE}/api/v1/graph/patient/000.000.000-00')
data = r.json()
print(json.dumps(data, indent=2))
assert data['found'] == True
print('PASS\n')

# 4. Search graph
print('=== TEST 4: Search Graph ===')
r = httpx.get(f'{BASE}/api/v1/graph/search', params={'query': 'Teste'})
data = r.json()
print(json.dumps(data, indent=2))
assert len(data['results']) > 0
print('PASS\n')

# 5. Add to quarantine
print('=== TEST 5: Add to Quarantine ===')
cypher_query = "MERGE (d:Drug {name: 'Losartana'}) SET d.drug_class = 'Anti-hipertensivo'"
r = httpx.post(f'{BASE}/api/v1/quarantine', json={
    'source_url': 'https://example.com/bula-teste',
    'source_type': 'url',
    'entities_json': {'drug': 'Losartana', 'class': 'Anti-hipertensivo'},
    'relationships_json': [{'from': 'Losartana', 'rel': 'TREATS', 'to': 'Hipertensao'}],
    'graph_cypher': cypher_query
})
print(r.json())
assert r.status_code == 200
print('PASS\n')

# 6. List quarantine
print('=== TEST 6: List Quarantine ===')
r = httpx.get(f'{BASE}/api/v1/quarantine', params={'status': 'pending'})
data = r.json()
print(f"Items in quarantine: {data['count']}")
assert data['count'] > 0
item_id = data['items'][0]['id']
print('PASS\n')

# 7. Approve quarantine (this should MERGE Losartana into Neo4j)
print('=== TEST 7: Approve Quarantine ===')
r = httpx.post(f'{BASE}/api/v1/quarantine/{item_id}/approve', params={'reviewer': 'test_admin'})
print(r.json())
assert r.status_code == 200
print('PASS\n')

# 8. Verify Drug was merged into Neo4j
print('=== TEST 8: Verify Drug in Graph ===')
r = httpx.get(f'{BASE}/api/v1/graph/search', params={'query': 'Losartana'})
data = r.json()
print(json.dumps(data, indent=2))
assert any(d['name'] == 'Losartana' for d in data['results'])
print('PASS\n')

print('ALL 8 TESTS PASSED!')
