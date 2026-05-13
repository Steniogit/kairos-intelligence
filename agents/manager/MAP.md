# MAP.md — Manager (Segundo Cérebro)

> Mapa de decisões para operações no ERP Ademed.
> Versão: 2.7

---

## Decisão: Crawl4AI ou Playwright?

```
Operação solicitada
├── É LEITURA? (busca, consulta, lista)
│   └── Crawl4AI (~1s) — CSS selectors diretos
├── É ESCRITA? (criar, alterar, deletar, upload)
│   └── Playwright (~5s) — JS do Ademed necessário
└── É LOGIN?
    └── Playwright sempre (formulário com JS)
```

## Seletores Conhecidos (Ademed v2.02)
<!-- ATENÇÃO: Validar contra HTML real antes de usar em produção -->

| Elemento | Seletor (especulativo) |
|----------|----------------------|
| Campo busca paciente | `#busca_paciente` |
| Tabela de resultados | `table.resultado tr[data-id]` |
| Grade de horários | `td.horario-livre` |
| Agendamento existente | `tr.agendamento[data-situacao]` |
| Diálogo novo agendamento | `#dialog-agendamento` |
| Campo paciente (agenda) | `#id_paciente_agenda` |
| Campo médico (agenda) | `#id_profissional_agenda` |
| Botão salvar | `#btn-salvar-agendamento` |

> ⚠️ Estes seletores são ESPECULATIVOS. Devem ser validados contra o HTML real.

---

*MAP.md — Manager — Kairós Intelligence v2.7*
