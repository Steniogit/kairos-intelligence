"""
Teste da Fase 4 — Copiloto Live (WebSocket)
Simula uma consulta medica em tempo real, enviando chunks de texto.
"""
import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
    import websockets


WS_URL = "ws://172.16.2.12:3100/ws/copilot"

# Consulta simulada em chunks (como se fosse transcricao ao vivo)
CHUNKS = [
    "Bom dia seu Joao, como vai? Eu tava preocupado com esses resultados do exame.",
    "Entao doutor, eu venho sentindo muita falta de ar quando subo escada.",
    "E uma dor no peito tambem, tipo um aperto. Ja faz uns 15 dias.",
    "Tomo Atenolol 50 faz uns 3 anos ja. E AAS infantil.",
    "Pressao hoje ta 140 por 90. Frequencia cardiaca 88.",
    "Ausculta pulmonar com crepitacoes bibasais. Edema 2+ em membros inferiores.",
    "Vou pedir um ecocardiograma, BNP, troponina e raio-X de torax.",
    "Vou aumentar o Atenolol pra 100mg e adicionar Furosemida 40mg pela manha.",
    "Retorno em 7 dias com os exames. Se piorar a falta de ar, vai pro pronto-socorro."
]


async def test_copilot():
    print("=" * 60)
    print("TESTE FASE 4 - Copiloto Live (WebSocket)")
    print("=" * 60)

    async with websockets.connect(WS_URL) as ws:
        # 1. Receber conexao
        msg = json.loads(await ws.recv())
        print(f"\nConexao: {msg}")
        assert msg["type"] == "connected", f"Expected 'connected', got {msg['type']}"
        session_id = msg["session_id"]
        print(f"Session ID: {session_id}")
        print("PASS")

        # 2. Enviar chunks de texto
        print(f"\n=== Enviando {len(CHUNKS)} chunks ===")
        for i, chunk in enumerate(CHUNKS):
            await ws.send(json.dumps({"type": "text", "text": chunk}))
            msg = json.loads(await ws.recv())
            print(f"  Chunk {i+1}: {chunk[:50]}... -> {msg['type']} ({msg.get('chars_total', '?')} chars)")

            # Check for auto-analysis
            if msg.get("type") == "ack":
                # May get a soap_update right after if auto-analyze triggered
                try:
                    extra = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    extra_msg = json.loads(extra)
                    if extra_msg["type"] == "analyzing":
                        print(f"    -> Analyzing...")
                        soap_msg = json.loads(await ws.recv())
                        print(f"    -> Auto SOAP update received!")
                except asyncio.TimeoutError:
                    pass

            await asyncio.sleep(0.5)  # Simular pausa natural

        print("PASS")

        # 3. Forcar analise
        print("\n=== Forcando analise ===")
        await ws.send(json.dumps({"type": "analyze"}))

        msg = json.loads(await ws.recv())
        assert msg["type"] == "analyzing", f"Expected 'analyzing', got {msg['type']}"
        print("Analisando...")

        msg = json.loads(await ws.recv())
        assert msg["type"] == "soap_update", f"Expected 'soap_update', got {msg['type']}"
        result = msg["data"]

        print(f"Status: {result.get('status')}")
        assert result["status"] == "ok", f"Analysis failed: {result}"

        copilot = result["copilot"]
        soap = copilot.get("soap_partial", {})

        print(f"\n--- SOAP Parcial ---")
        print(f"  Queixa: {soap.get('subjective', {}).get('chief_complaint', 'N/A')}")
        print(f"  Sinais vitais: {soap.get('objective', {}).get('vital_signs', {})}")

        diagnoses = soap.get("assessment", {}).get("working_diagnoses", [])
        print(f"  Diagnosticos: {diagnoses}")

        meds = soap.get("plan", {}).get("medications_mentioned", [])
        print(f"  Medicamentos: {meds}")

        alerts = copilot.get("alerts", [])
        print(f"\n--- Alertas ({len(alerts)}) ---")
        for a in alerts:
            print(f"  [{a.get('severity', '?')}] {a.get('message', '?')}")

        questions = copilot.get("suggested_questions", [])
        print(f"\n--- Sugestoes de perguntas ({len(questions)}) ---")
        for q in questions:
            print(f"  ? {q}")

        entities = copilot.get("entities_detected", [])
        print(f"\n--- Entidades detectadas ({len(entities)}) ---")
        print(f"  {entities}")

        graph_ctx = copilot.get("graph_context", [])
        if graph_ctx:
            print(f"\n--- Contexto do Grafo ({len(graph_ctx)}) ---")
            for g in graph_ctx:
                print(f"  {g['entity']}: {g['graph_data'][:2]}")

        print(f"\n  Analise #{copilot.get('analysis_number')}, Confianca: {copilot.get('confidence')}")
        print("PASS")

        # 4. Encerrar sessao
        print("\n=== Encerrando sessao ===")
        await ws.send(json.dumps({"type": "end"}))

        msg = json.loads(await ws.recv())
        print(f"  {msg['type']}")

        if msg["type"] == "analyzing":
            final = json.loads(await ws.recv())
            print(f"  SOAP final recebido: {final['type']}")
            ended = json.loads(await ws.recv())
            print(f"  {ended['type']}")
        elif msg["type"] == "session_ended":
            print("  Sessao encerrada")

        print("PASS")

    print("\n" + "=" * 60)
    print("COPILOT TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_copilot())
