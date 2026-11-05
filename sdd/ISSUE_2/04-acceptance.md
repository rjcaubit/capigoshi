# Aceite — Cérebro SNN da Capi, fase 0 (issue #2)

**Data:** 2026-11-05
**Branch:** `feature/sdd-issue-2`, mergeada na `main` em 2026-11-05
**Status:** aceita sem o CT03 — 5 de 6 cenários passam; o teste do hábito foi para a issue #3 por decisão do dono do projeto

## Commits

| Commit | Fase |
|---|---|
| `66da9b8` | A — catálogo de ações, drives e recompensa |
| `0c4341c` | B — rede LIF, STDP e R-STDP com testes |
| `9fc261d` | C — cérebro, simulador e aceites de velocidade e silêncio |
| `b1c1964` | E — `CALIBRACAO.md` e `CODEMAP.md` |
| `ca29fef` | ajustes do code review |

A fase D (calibração do hábito) não gerou commit: nenhum experimento passou, e a regra de parada D6 foi aplicada.

## Cenários

| CT | Comando | Resultado |
|---|---|---|
| CT01 velocidade | `python3 -m companion.sim.aceite velocidade` | ✅ 7 dias em 68 s (limite 180 s) |
| CT02 silêncio | `python3 -m companion.sim.aceite silencio` | ✅ 13,2 sons/h nas 6 primeiras horas → 0,8 sons/h no dia 3 |
| CT03 hábito | `python3 -m companion.sim.aceite habito` | ❌ 0 de 7 dias (meta 5) — movido para a #3; ver `CALIBRACAO.md`, seção "Hábito — não resolvido" |
| CT04 unitários | `python3 -m unittest discover -s companion/testes -t .` | ✅ 22 testes OK |
| CT05 pré-condição e trava | incluído no CT04 (`test_cooldown_e_trava`) | ✅ |
| CT06 portabilidade | `micropython companion/sim/fumaca.py` | ✅ `micropython ok` |

RNF03 (sem float nos módulos do tick): `grep` sem nenhuma linha fora de comentários. RNF04 (determinismo): mesma
semente, mesmas decisões (conferido na revisão).

## Revisão

Revisão combinada (spec + código) por subagente: **pedidos de mudança**, com 3 bloqueadores, todos corrigidos em
`ca29fef` e cobertos por testes novos:
1. Chamado atendido creditava a ação corrente, e não o chamado (janela real de 2 s em vez de 10 s).
2. Modulação por drive usava a fome de depois de comer (28 viraria 22).
3. Esquecimento não andava em desvios < 100 (oculta→saída nunca esquecia).

Re-revisão de `ca29fef`: **aprovado**, sem bloqueador novo. Não-bloqueador que sobrou: um toque logo depois de um
pedido que não é chamado (`pedir_carinho` → `ficar_quieta` → toque em 1 s) ainda dá −2 à quieta.

Também corrigidos: elegibilidade zerada depois de trava longa, normalização sem limite, estímulo guardado durante o
sono, refeição dentro da janela do hábito e um teste que passava por acaso.

## Doc-sync

- `CODEMAP.md`: pacote `companion/` e `CALIBRACAO.md` no índice, seção "Cérebro SNN". O arquivo veio da branch da
  issue #1, que ainda não está na `main`; quando ela for mergeada, o conflito fica restrito às linhas novas.
- `CALIBRACAO.md`: novo.

## Pendente

- CT03 (hábito): resolvido na issue #3 (`sdd/ISSUE_3/04-acceptance.md`).
