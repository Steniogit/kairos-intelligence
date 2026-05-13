# MAP.md — Front-Desk (Segundo Cérebro)

> Mapa de decisões para atendimento de pacientes.
> Versão: 2.7

---

## Árvore de Decisão Principal

```
Mensagem do paciente
├── É paciente identificado?
│   ├── SIM → Saudação personalizada + "Como posso ajudar?"
│   └── NÃO → "Parece que é sua primeira vez! Vou precisar de alguns dados."
│
├── O que o paciente quer?
│   ├── Agendar consulta → Fluxo de Agendamento
│   ├── Cancelar/remarcar → Fluxo de Cancelamento (máx 2x)
│   ├── Dúvida do FAQ → Responde direto
│   ├── Urgência médica → "Procure o SAMU (192) ou UPA mais próxima"
│   ├── Falar com humano → Handoff para recepcionista
│   └── Fora do escopo → Redireciona (máx 3 tentativas, depois handoff)
```

## Fluxo de Agendamento
```
1. Paciente diz médico e/ou especialidade desejada
2. Manager verifica disponibilidade (Crawl4AI)
3. Oferece até 3 opções de horário
4. Paciente escolha → confirma dados
5. Manager agenda no Ademed (Playwright)
6. Confirma ao paciente com detalhes
7. Notifica recepcionista
```

## Frases-Chave para Detecção de Intenção
| Intenção | Palavras-chave |
|----------|---------------|
| Agendar | marcar, agendar, consulta, horário, vaga |
| Cancelar | cancelar, desmarcar, não vou poder |
| Remarcar | remarcar, trocar, mudar, alterar |
| FAQ | horário, endereço, convênio, estacionamento |
| Urgência | urgente, emergência, dor forte, passando mal |
| Humano | humano, pessoa, recepcionista, atendente |

---

*MAP.md — Front-Desk — Kairós Intelligence v2.7*
