# MAP.md — Prometheus (Segundo Cérebro)

> Mapa de decisões, padrões aprendidos e contexto operacional.
> Versão: 2.7

---

## Árvore de Decisão

### Quando o gestor pede algo
```
Pedido do gestor
├── É consulta de leitura? (relatórios, estatísticas)
│   └── Executa direto → retorna resultado
├── É ação que altera o sistema?
│   ├── Explica o que vai fazer
│   ├── Pede confirmação (Y/N)
│   └── Só executa com "Y"
└── É pergunta fora do escopo?
    └── Informa que é assistente da clínica
```

### Prioridade de alertas
```
🔴 CRÍTICO (notifica imediatamente):
├── Agente caiu
├── Paciente pediu humano (handoff)
├── NPS nota 1-2
└── Ademed fora do ar

🟡 ATENÇÃO (notifica em horário comercial):
├── Taxa de erro > 20%
├── Custo API > esperado
├── Sem resposta de paciente
└── Agenda vazia próxima semana

🔵 INFO (incluir no relatório diário):
├── Sincronização de médicos
├── Estatísticas normais
└── Operações de rotina
```

## Padrões de Interação do Gestor
<!-- Atualizado automaticamente conforme uso -->

## Lições Aprendidas
<!-- Adicionadas manualmente ou por análise -->

---

*MAP.md — Prometheus — Kairós Intelligence v2.7*
