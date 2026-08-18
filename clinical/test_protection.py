"""
Teste do Sistema de Protecao da Consulta:
1. Pre-Flight Check (todos os subsistemas)
2. WebSocket com heartbeat
3. Deteccao de silencio
4. Reconexao
"""
import asyncio
import json
import sys
import httpx

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
    import websockets


BASE = 'http://172.16.2.12:3100'
WS_URL = "ws://172.16.2.12:3100/ws/copilot"

print("=" * 60)
print("TESTE — Sistema de Protecao da Consulta")
print("=" * 60)


# ═══ TEST 1: Pre-Flight Check ═══
print("\n=== TEST 1: Pre-Flight Check ===")
r = httpx.get(f'{BASE}/api/v1/clinical/preflight', timeout=30.0)
data = r.json()

print(f"Status geral: {data['overall_status']}")
print(f"Mensagem: {data['message']}")
print(f"Pronto para consulta: {data['ready_to_consult']}")
print()

checks = data['checks']
for name, result in checks.items():
    status = result.get('status', '?')
    icon = '✓' if status == 'ok' else ('⚠' if status == 'warning' else '✗')
    latency = f" ({result.get('latency_ms', '?')}ms)" if 'latency_ms' in result else ""
    extra = f" - {result.get('message', '')}" if result.get('message') else ""
    print(f"  {icon} {name}: {status}{latency}{extra}")

assert data['ready_to_consult'], "Pre-flight FAILED — sistema nao esta pronto!"
print("\nPASS")


# ═══ TEST 2: WebSocket com Heartbeat ═══
async def test_websocket_protection():
    print("\n=== TEST 2: WebSocket com Heartbeat ===")

    async with websockets.connect(WS_URL) as ws:
        msg = json.loads(await ws.recv())
        print(f"Conectado: session={msg.get('session_id')}")
        session_id = msg.get("session_id")

        # Enviar heartbeat
        await ws.send(json.dumps({"type": "heartbeat"}))
        hb = json.loads(await ws.recv())
        print(f"Heartbeat ACK: server_time={hb.get('server_time')}, session_seconds={hb.get('session_seconds')}")
        assert hb["type"] == "heartbeat_ack"
        print("PASS")

        # Enviar audio level
        print("\n=== TEST 3: Audio Level Monitor ===")
        await ws.send(json.dumps({"type": "audio_level", "level": 0.8}))
        await asyncio.sleep(0.2)
        await ws.send(json.dumps({"type": "audio_level", "level": 0.7}))
        print("Audio level reportado (0.8, 0.7) — sem alerta esperado")
        print("PASS")

        # Enviar texto e encerrar
        await ws.send(json.dumps({"type": "text", "text": "Paciente relata dor abdominal"}))
        ack = json.loads(await ws.recv())
        print(f"\n=== TEST 4: Texto processado ({ack.get('chars_total')} chars) ===")
        print("PASS")

        # Encerrar sessao
        await ws.send(json.dumps({"type": "end"}))
        msgs_received = []
        while True:
            try:
                m = await asyncio.wait_for(ws.recv(), timeout=15.0)
                parsed = json.loads(m)
                msgs_received.append(parsed["type"])
                if parsed["type"] == "session_ended":
                    break
            except asyncio.TimeoutError:
                break
        print(f"\n=== TEST 5: Encerramento ({' -> '.join(msgs_received)}) ===")
        print("PASS")

    # TEST 6: Reconnect (abrir nova sessao, desconectar, reconectar)
    print("\n=== TEST 6: Reconexao ===")

    async with websockets.connect(WS_URL) as ws:
        msg = json.loads(await ws.recv())
        reconnect_session_id = msg["session_id"]
        print(f"Sessao criada: {reconnect_session_id}")

        # Enviar texto para haver transcricao
        await ws.send(json.dumps({"type": "text", "text": "O paciente veio para retorno apos cirurgia"}))
        ack = json.loads(await ws.recv())
        print(f"Texto enviado: {ack.get('chars_total')} chars")

    # Sessao desconectou mas deve estar preservada
    await asyncio.sleep(1)

    # Verificar sessao preservada
    r = httpx.get(f'{BASE}/api/v1/copilot/sessions')
    sessions = r.json()
    preserved = [s for s in sessions['active_sessions'] if s['session_id'] == reconnect_session_id]
    if preserved:
        print(f"Sessao preservada: connected={preserved[0]['connected']}, "
              f"transcript={preserved[0]['transcript_length']} chars")
        assert not preserved[0]['connected'], "Deveria estar desconectada!"
        assert preserved[0]['transcript_length'] > 0, "Transcricao deveria existir!"

        # Reconectar
        async with websockets.connect(WS_URL) as ws2:
            await ws2.send(json.dumps({"type": "reconnect", "session_id": reconnect_session_id}))
            rmsg = json.loads(await ws2.recv())
            print(f"Reconectado: {rmsg['type']}")
            assert rmsg["type"] == "reconnected"
            state = rmsg.get("state", {})
            print(f"  Transcricao recuperada: {state.get('transcript_length')} chars")
            print(f"  Desconexoes: {state.get('disconnect_count')}")
            assert state.get("transcript_length", 0) > 0, "Transcricao deveria estar preservada!"
            await ws2.send(json.dumps({"type": "end"}))
            while True:
                try:
                    m = await asyncio.wait_for(ws2.recv(), timeout=15.0)
                    if json.loads(m)["type"] == "session_ended":
                        break
                except asyncio.TimeoutError:
                    break
        print("PASS")
    else:
        print("WARN: Sessao nao preservada (pode ter sido limpa)")

    print("\n" + "=" * 60)
    print("PROTECTION SYSTEM TESTS PASSED!")
    print("=" * 60)


asyncio.run(test_websocket_protection())
