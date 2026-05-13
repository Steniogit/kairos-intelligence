# Kairós Intelligence v2.7.1

**Data:** 13/05/2026
**Status:** Fase 2 — Paperclip + GraphRAG + Código Executável

## Changelog v2.7.1

### Adicionado
- **Paperclip** (Control Plane) — governança multi-tenant, budget de tokens, audit log
- **Neo4j** (GraphRAG) — grafo de conhecimento com relações paciente-médico-convênio
- **ChromaDB** (GraphRAG) — vetores de embedding para busca semântica (FAQ, protocolos)
- **Código executável Python** para todos os 5 agentes:
  - Prometheus: human-in-the-loop, relatórios, monitoramento 3 níveis
  - Front-Desk: buffer 8s, identificação híbrida, multimodal, handoff
  - Manager: fila sequencial, Crawl4AI reader, Playwright writer, session manager
  - Notificações: lembretes 3 etapas, cascata fallback, NPS, filtro circadiano
  - Sincronizador: sync médicos 30min, sync convênios 6h
- **Shared modules** — config, Redis client, Evolution client, Paperclip client
- **GraphRAG pipeline** — embeddings, ingestão, retrieval híbrido
- Docker Compose: 10 serviços (+ Paperclip, Neo4j, ChromaDB)
- Health check e smoke test: 9 verificações (+ 3 novos serviços)

### Alterado
- PostgreSQL agora serve Kairós + Paperclip (database separada)
- .env.example expandido com 6 novas variáveis
