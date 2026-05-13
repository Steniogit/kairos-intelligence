# MAP.md — Sincronizador (Segundo Cérebro)

> Mapa de decisões para sincronização com ERP Ademed.
> Versão: 2.7

---

## Ciclo de Sincronização

```
A cada 30 minutos:
1. Crawl4AI → extrai lista de médicos ativos do Ademed
2. Compara com SOUL.md do Front-Desk
3. Diferença encontrada?
   ├── SIM → Atualiza SOUL.md + reinicia Front-Desk + notifica Prometheus
   └── NÃO → Log silencioso, próximo ciclo em 30min

A cada 6 horas:
1. Crawl4AI → extrai lista de convênios do Ademed
2. Compara com SOUL.md do Front-Desk
3. Diferença encontrada?
   ├── SIM → Atualiza + notifica
   └── NÃO → Próximo ciclo em 6h
```

## Última Sincronização
- Data: —
- Resultado: —
- Mudanças detectadas: —

---

*MAP.md — Sincronizador — Kairós Intelligence v2.7*
