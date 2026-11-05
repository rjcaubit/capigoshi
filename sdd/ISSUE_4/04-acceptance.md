# Aceite — Cérebro SNN: humor e comportamento variam com o clima (issue #4)

**Data:** 2026-11-05
**Branch:** `feature/sdd-issue-4`, mergeada na `main` em 2026-11-05
**Status:** aceita — 5 de 5 cenários passam

## Cenários

| CT | Comando | Resultado |
|---|---|---|
| CT01 chuva × sol | `python3 -m companion.sim.aceite clima` | ✅ nas 4 sementes (tabela abaixo) |
| CT02 sem regressão | `python3 -m companion.sim.aceite todos` | ✅ `ACEITE OK` em 10 min 51 s: velocidade 56 s, silêncio 10,8 → 0,1 sons/h, hábito 6 de 7, sementes [6, 6, 5, 5] |
| CT03 unitários | `python3 -m unittest discover -s companion/testes -t .` | ✅ 36 testes OK |
| CT04 clima desconhecido | `test_indice` (`'granizo'` e `None`), `test_efeito`, `test_neuronios` | ✅ |
| CT05 MicroPython | `micropython companion/sim/fumaca.py` | ✅ `micropython ok 4780 239` |

| Semente | Humor chuva | Humor sol | Tristes/h chuva | Tristes/h sol |
|---|---|---|---|---|
| 1 | −37,1 | +17,9 | 1,19 | 0,00 |
| 2 | −36,5 | +18,3 | 1,00 | 0,02 |
| 3 | −36,8 | +18,6 | 0,52 | 0,00 |
| 4 | −37,3 | +17,9 | 1,45 | 0,02 |

RNF02 (sem float no tick): `grep` só acha comentários.

## Revisão

Revisão combinada (spec + código) por subagente: **aprovado**, sem bloqueador. A rede da fonte foi conferida contra a
`main` (`w_ih` das 100 entradas, `w_ho`, oculta → oculta e `_rtab` iguais). Não-bloqueadores corrigidos em `0169eba`:
- `test_rede_da_fonte_nao_muda` comparava a rede consigo mesma; agora compara com uma rede montada sem as entradas do clima.
- Ocultos de tempo (`OCULTOS_TEMPO`, hoje 0) também não ouvem o clima.
- O codificador trunca `graus` para inteiro (`rede.clima['temp']` é float).
- O aceite conta os dias de cada tempo, em vez de fixar 3.
- Comentário em `Drives.avancar`: usa o clima da última leitura (fase 1).
- `CODEMAP.md`: ~1450 linhas em `companion/`.

## Doc-sync

`CALIBRACAO.md` (seção "Clima (issue #4)") e `CODEMAP.md` (módulo `clima`, nota dos sentidos, comando dos aceites).

## Commits

`ca638d7` fase A, `849f71b` fase B, `e70ea09` fase C, `0169eba` ajustes do code review.
