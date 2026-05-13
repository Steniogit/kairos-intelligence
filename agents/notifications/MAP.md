# MAP.md — Notificações (Segundo Cérebro)

> Mapa de decisões para envio de notificações.
> Versão: 2.7

---

## Decisão: Qual canal usar?

```
Precisa enviar notificação
├── Janela Meta aberta (24h desde última msg do paciente)?
│   └── SIM → WhatsApp gratuito ✅
│   └── NÃO ↓
├── Paciente tem email cadastrado?
│   └── SIM → Email
│   └── NÃO ↓
├── SMS configurado?
│   └── SIM → SMS
│   └── NÃO ↓
└── Template Meta pré-aprovado disponível?
    └── SIM → Template pago 💰
    └── NÃO → Log + notifica Prometheus
```

## Decisão: Pode enviar agora?

```
Hora atual
├── Entre 8h e 20h? → SIM, enviar
├── Entre 20h e 21h? → Só lembretes urgentes (4h antes)
└── Fora do horário? → Enfileirar para 8h do dia seguinte
```

---

*MAP.md — Notificações — Kairós Intelligence v2.7*
