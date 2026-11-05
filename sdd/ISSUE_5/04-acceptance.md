# Aceite — Raio-X do cérebro (etapa 1, simulador)

**Issue:** #5 · **Branch:** `feature/sdd-issue-5` · **Data:** 2026-11-05

## Cenários
| CT | Como | Resultado |
|---|---|---|
| CT01 resumo completo e JSON | `test_chaves_e_json`, `test_so_inteiros`, `test_hoje_bate_com_as_decisoes`, `test_horas_e_recompensas` | OK |
| CT02 resumo não muda a decisão | `test_resumo_nao_muda_o_cerebro` + aceite antigo idêntico | OK |
| CT03 limites e virada do dia | `test_limite_das_recompensas`, `test_virada_do_dia` | OK |
| CT04 hábito aparece no relógio | `test_habito_aparece_no_relogio`; `raiox habito 7 1` → `habito 19h00: pedir_carinho (1453)` | OK |
| CT05 página embute o resumo / estado vazio | `test_pagina_embute_o_resumo`; E2E na página sem dados, console limpo | OK |
| CT06 MicroPython | `micropython companion/sim/fumaca.py` → `micropython ok 4780 239 1300` | OK |
| CT07 E2E click-by-click | `sdd/ISSUE_5/prototipo/e2e.py`, 26 checagens, claro e escuro, capturas em `load-tests/results/issue-5-journey/` | OK |

## Suíte e aceites
- `python3 -m unittest discover -s companion/testes -t .` → 45 testes OK.
- `python3 -m companion.sim.aceite todos` (11 min 34 s) → `ACEITE OK`, com os mesmos números da issue #4:
  velocidade 58 s; silêncio 10,8 → 0,1 sons/h; hábito 6 de 7; sementes [6, 6, 5, 5]; clima OK nas 4 sementes.

## Review
Review combinado: PEDIDOS DE MUDANÇA com 2 bloqueadores (rolagem travada nos gráficos e erro de console no estado
vazio). Corrigidos em `dec1d0f`, junto com o valor que sumia num toque e o cartão de vontades sem histórico. O E2E
ganhou toque real, teste de rolagem (validado contra a versão antiga) e console na página vazia.

Pedidos não-bloqueadores deixados para depois:
- contraste do texto branco sobre o laranja dos chips e do topo;
- gráficos de vontade sem caminho por teclado;
- hábito que cruza a meia-noite aparece em duas faixas;
- `raiox.main` muda `C.RAIOX_HORAS` global (só no simulador);
- etapa 2: horário em cada linha de `horas`, virada do dia pelo `minuto` local, JSON em streaming no portal.

## Commits
- `667ab77` fase A — `Cerebro.resumo` e estado do raio-X
- `cfc8c52` fase B — página e gerador
- `dec1d0f` ajustes do code review
- fase C — E2E, aceite e CODEMAP (este commit)
