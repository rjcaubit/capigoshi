# Aceite — Cérebro SNN: aprender o horário dos hábitos (issue #3)

**Data:** 2026-11-05
**Branch:** `feature/sdd-issue-3`, mergeada na `main` em 2026-11-05
**Status:** aceita — 6 de 6 cenários passam; o CT03 da fase 0 (hábito) está resolvido

## Cenários

| CT | Comando | Resultado |
|---|---|---|
| CT01 hábito | `python3 -m companion.sim.aceite habito` | ✅ 5 de 7 dias (meta 5) |
| CT02 sementes | `python3 -m companion.sim.aceite sementes` | ✅ [5, 5, 5, 6] dias, média 5,25 (meta média ≥ 5, mínimo ≥ 4) |
| CT03 sem regressão | `... aceite silencio` e `... aceite velocidade` | ✅ 12,0 → 0,1 sons/h; 7 dias em 65 s (limite 180 s) |
| CT04 unitários | `python3 -m unittest discover -s companion/testes -t .` | ✅ 29 testes OK |
| CT05 castigo atrasado sem marca | `test_castigo_atrasado_so_nos_marcados` | ✅ |
| CT06 MicroPython | `micropython companion/sim/fumaca.py` | ✅ `micropython ok 4520 226` |

`python3 -m companion.sim.aceite todos` → `ACEITE OK` em 7 min 25 s. RNF02 (sem float no tick): `grep` só acha comentários.

## Revisão

Revisão combinada por subagente: **pedidos de mudança**, sem bloqueador de lógica. Corrigido: o teste
`test_ignorado_usa_minuto_do_inicio` não discriminava o minuto de início do da chegada; agora usa 10h00 → 10h10 e
confere que a célula 31 fica intacta. Registrados em `CALIBRACAO.md`: o custo de som passa pelo relógio e o crédito
errado quando a ação recomeça antes do R atrasado. Não corrigidos (não bloqueiam): `sementes` repete a semente 1 dentro
de `todos` (~25 % de tempo); estimativa de linhas do `CODEMAP.md` desatualizada.

## Doc-sync

`CALIBRACAO.md` (seção "Hábito (issue #3)"), `CODEMAP.md` (módulo `relogio`, comando dos testes) e
`sdd/ISSUE_2/04-acceptance.md` (pendência resolvida).

## Commits

Fases A a D, mais o ajuste do code review.
