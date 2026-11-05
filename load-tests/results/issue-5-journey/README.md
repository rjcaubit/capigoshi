# Issue #5 — jornada E2E do raio-X

Página: `python3 -m companion.sim.raiox semana 3 2 chuva`, Chromium 390 × 844, modos claro e escuro.
Roteiro: `sdd/ISSUE_5/prototipo/e2e.py`.

| Captura | O que mostra |
|---|---|
| 01 / 07 | Página inteira (claro / escuro) |
| 02 / 08 | Hábito escolhido: arco destacado e dica |
| 03 / 09 | Aba "Ontem" |
| 04 / 10 | Todas as recompensas |
| 05 / 11 | Valor ao tocar no gráfico de vontade |
| 13 | Estado vazio (modelo sem dados) |

Checagens: 26, todas OK (sem rolagem lateral, 7 cartões, hábito com arco e dica, aba Ontem, ver todas / ver menos,
valor ao tocar no gráfico, dedo que começa no gráfico rola a página, botões ≥ 44 px, console limpo nos três estados).
O toque usa tela sensível (`has_touch`) e o arrasto é disparado pelo CDP.

Bugs encontrados no review e corrigidos em `dec1d0f`:
- `touch-action: none` nos gráficos de vontade travava a rolagem quando o dedo começava neles;
- num toque, o `pointerleave` apagava o valor logo depois de mostrar;
- aberta do disco sem dados, a página tentava `fetch('brain.json')` e deixava erro no console.

O teste de rolagem foi conferido contra a versão antiga: falha com `touch-action: none` e passa com `pan-y`.
