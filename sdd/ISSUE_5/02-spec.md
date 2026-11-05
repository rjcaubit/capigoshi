# Especificação — Raio-X do cérebro: ver o que a Capi aprendeu (etapa 1, simulador)

**Issue:** #5
**Data:** 2026-11-05
**Status:** Aguardando implementação

## Objetivo

Dar a quem cuida da Capi, e a quem desenvolve o cérebro, uma página que mostra o que ela aprendeu:
- as vontades e o humor agora e nas últimas horas;
- os hábitos de horário;
- as ações que mais vencem;
- o que a rede fortaleceu ou enfraqueceu;
- as últimas recompensas.

A fonte diz que "sem enxergar o cérebro não dá para saber se ele aprende" (`sdd/ISSUE_2/00-fonte.md`, seção 10).
Esta issue entrega a etapa 1, no simulador. A mesma página e o mesmo resumo servem depois ao portal da placa (etapa 2).

## Escopo desta spec

| Etapa | O que é | Nesta spec |
|---|---|---|
| 1 | `Cerebro.resumo()`, a página `companion/raiox.html` e o gerador `python3 -m companion.sim.raiox` | **Sim** |
| 2 | Rota `/brain.json` e a página no `portal.py` da placa | Não: depende do cérebro rodando na placa (fases 1 e 2 do roteiro da fonte, ainda sem issue). A página já pede `brain.json` quando não tem dados embutidos, então a etapa 2 só precisa servir os dois arquivos |

## Pesquisa & Dependency Analysis

### Protótipo do planejamento (scratchpad, cópia de `companion/`)

Todo o código desta spec rodou no planejamento. Os arquivos que não cabem inline nas tasks estão em
`sdd/ISSUE_5/prototipo/`: `raiox.html`, `raiox.py`, `test_raiox.py`, `e2e.py` e as prévias `previa-claro.png` e
`previa-escuro.png`.

**Resultados do protótipo**
- **Testes:** 45 testes OK, sendo 9 novos.
- **MicroPython:** `micropython ok 4780 239 1300` (o último número são os bytes do JSON do resumo).
- **Tempo do `resumo()`:** 2 ms no CPython depois de 7 dias simulados e 1 ms no MicroPython unix.
- **Tamanho:** o modelo tem 16,3 KB; a página gerada com 7 dias, 34 KB.
- **E2E:** 23 checagens OK nos modos claro e escuro, mais o estado vazio.

**O que o raio-X já mostrou no simulador**
- **Cenário `habito`, 7 dias:** o relógio aprendeu `pedir_carinho` às 19h00 (peso 1453 de 1500). Fora dessa hora, ele
  aprendeu a evitar o mesmo pedido (−150 a −990).
- **Rede oculta → saída:** só perdeu peso. A lista "gosta" fica vazia e a "evita" traz os pedidos e os sons
  (`pedir_carinho` −3095, `chamar_alto` −2800...). Ou seja, o que a Capi aprende a *fazer* fica no relógio, e o que
  aprende a *não fazer* fica na rede.

### O que já existe e reuso (fonte: `CODEMAP.md`, seção "Cérebro SNN")

| Item | Localização | Como uso |
|---|---|---|
| Estado do cérebro | `companion/cerebro.py`: `Cerebro` (drives, `rede`, `relogio`, `acoes`, `eta()`, `ticks_rodados`) | `resumo()` lê tudo daqui, sem mudar nada |
| Pesos e pesos de nascença | `companion/snn.py`: `w_ho`/`w_ho0`, `w_ih`/`w_ih0`, `th_h`, `ruido` | "gosta/evita" = soma de `w_ho − w_ho0` por ação; "entrada mexida" = soma de `|w_ih − w_ih0|` |
| Relógio dos hábitos | `companion/relogio.py`: `Relogio.w` (72 células × 100 saídas) | O hábito mais forte e o mais evitado de cada célula, acima de `RAIOX_HABITO` |
| Recompensas | `Cerebro._aplicar` (ponto único por onde passa todo R com motivo) | Anel com as últimas `RAIOX_RECS` (200, como diz a fonte) |
| Clima | `clima.efeito`, `Drives.clima` (issue #4) | Guarda o `tempo` e os `graus` da última leitura; o alvo do humor vem de `Drives.clima[0]` |
| Catálogo | `companion/actions.py`: `CATALOGO` | Nome de cada ação |
| Simulador | `companion/sim/rodar.py`: `simular`, `CENARIOS`; `sim/aceite.py`: `TEMPOS_CHUVA` | O gerador roda um cenário e chama `resumo()` no fim |
| Fumaça MicroPython | `companion/sim/fumaca.py` | Passa a chamar `resumo()` e `json.dumps` também |
| Paleta | skill `dataviz`, paleta de referência (8 cores categóricas validadas, claro e escuro) | Uma cor por vontade, a mesma na barra e na linha; azul/laranja para positivo/negativo |

### O que preciso criar (porque não existe)

| Item | Tipo | Onde | Por que não reuso |
|---|---|---|---|
| `Cerebro.resumo()` e o estado que ele lê (`recs`, `horas`, `vezes`, `vezes_ontem`, `agora_s`, `tempo`, `graus`) | método e atributos | `companion/cerebro.py` | `log` é consumido e cortado pelo simulador e não conta decisões por dia; nada guarda o histórico dos drives |
| `RAIOX_*` | constantes | `companion/config.py` | — |
| `raiox.html` | página estática, sem dependência externa | `companion/raiox.html` | O portal (`portal.py`) só tem o formulário do Wi-Fi; no modo portal a placa não tem internet, então nada de CDN |
| `raiox.py` | gerador CLI | `companion/sim/raiox.py` | `rodar.py` só imprime sons/h |
| `test_raiox.py` | unittest | `companion/testes/` | — |
| `companion/sim/saida/` | pasta de saída, fora do git | `.gitignore` | — |

### Decisões tomadas

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| Uma página-modelo com `var D = /*DADOS*/null;`. O simulador troca a marca pelo JSON; sem dados, a página faz `fetch('brain.json')` | Duas páginas, uma do simulador e outra da placa | Um só lugar para manter. A etapa 2 só serve o arquivo e a rota |
| O resumo guarda o próprio histórico (`horas`, um anel de 48) | O simulador tirar fotos do resumo a cada hora | A placa precisa do mesmo histórico, e o JSON fica igual nas duas. O gerador aumenta `RAIOX_HORAS` para cobrir todos os dias simulados |
| "Gosta/evita" pela soma de `w_ho − w_ho0` | Subtrair a mediana (testado: a mediana é 0, porque a maioria das ações nunca dispara) | Mostra o que de fato aconteceu: a rede só aprendeu a evitar, e a lista "gosta" vazia já é informação de debug |
| `RAIOX_HABITO = 200` (13 % de `RELOGIO_MAX`) | 300 | Com 200, aparecem o hábito das 19h e as faixas evitadas. Células seguidas com a mesma ação viram uma faixa na página |
| Contagem "hoje/ontem" de decisões, com virada à meia-noite (`seg % 86400`) | Janela deslizante de 24 h | Custa 2 arrays de 100 e casa com a ficha de personalidade da fonte ("10 ações mais frequentes") |
| Os novos atributos ficam fora da decisão | — | `test_resumo_nao_muda_o_cerebro` prova que as decisões não mudam. Os aceites antigos continuam com os mesmos números |
| A saída do gerador fica em `companion/sim/saida/`, fora do git | scratchpad ou `/tmp` | O desenvolvedor abre a página direto no navegador |
| Texto da página com acento | Sem acento (regra do código) | É texto para gente ler; a regra de não usar acento vale para identificadores e comentários. A placa serve os bytes UTF-8 |

### Riscos técnicos

- **Custo do `resumo()` na placa.** São cerca de 25 mil acessos a arrays: 1 ms no MicroPython unix e talvez
  100 a 300 ms no ESP32. Mitigação: só é chamado sob pedido do portal, com o jogo pausado. Medir na etapa 2.
- **Memória na placa.** `recs` são 200 tuplas, cerca de 10 KB no MicroPython, e `horas` são 48 listas de 7. Medir
  com `gc.mem_free()` na etapa 2. Se apertar, baixar `RAIOX_RECS` ou guardar em `array`.
- **`</script>` dentro do JSON.** O gerador escapa `</`, e o teste `test_pagina_embute_o_resumo` cobre esse caso.

## Requisitos Funcionais

- [ ] **RF01:** `Cerebro.resumo()` devolve um `dict` só com `int`, `str`, `bool`, `None`, `list` e `dict`, com as chaves:
  - `versao`, `semente`, `idade_s`, `agora_s`, `minuto`, `acao`, `dormindo`;
  - `drives`: 7 pares `[nome, valor x10]`;
  - `clima`: `{tempo, graus, alvo}`;
  - `hoje` e `ontem`: até 10 pares `[ação, vezes]`;
  - `gosta` e `evita`: até 10 pares `[ação, Δpeso]`;
  - `relogio`: `{passo_min, max, habitos, evita}`, em que cada item de `habitos` e de `evita` é
    `[célula, ação, peso]`;
  - `recompensas`: até 200 itens `[s, ação, R, motivo]`;
  - `horas`: listas de 7 drives x10;
  - `rede`: `{eta, ruido, ticks, ih_mudou_pct, limiar: [mín, mediana, máx]}`.
- [ ] **RF02:** `resumo()` não muda o estado: com a mesma semente, chamar a cada minuto não altera nenhuma decisão.
- [ ] **RF03:** o cérebro guarda as últimas `RAIOX_RECS` recompensas, os drives de hora em hora (as últimas
  `RAIOX_HORAS`) e a contagem de decisões de hoje. À meia-noite, a contagem de hoje vira a de ontem.
- [ ] **RF04:** `python3 -m companion.sim.raiox [cenario] [dias] [semente] [chuva]` roda o cenário. Depois:
  - imprime um resumo em texto (idade, drives, hábitos por horário, gosta/evita, mais feitas);
  - grava `companion/sim/saida/raiox-<cenario>-<semente>[-chuva].html`;
  - imprime o caminho do arquivo.
- [ ] **RF05:** a página mostra 8 seções:
  1. **Topo:** idade, ação atual, hora e clima.
  2. **Como ela está:** 7 barras; a do humor é centrada no zero.
  3. **Relógio dos hábitos:** anel de 24 h com os hábitos por fora e o que ela evita por dentro, mais a lista de
     faixas. Tocar numa faixa destaca o arco correspondente e escreve a dica.
  4. **O que ela mais fez:** abas Hoje e Ontem.
  5. **O que ela aprendeu:** gosta e evita.
  6. **Últimas recompensas:** as 12 mais recentes, com o botão "Ver todas"/"Ver menos".
  7. **Vontades nas últimas horas:** uma linha por vontade; tocar mostra o valor da hora.
  8. **Por dentro:** semente, η, ruído, ticks, entrada mexida e limiar.
- [ ] **RF06:** sem dados embutidos, a página pede `brain.json`. Se o pedido falhar, mostra o estado vazio
  "Sem dados do cérebro", com as instruções.
- [ ] **RF07:** `micropython companion/sim/fumaca.py` imprime `micropython ok <ticks> <decisoes> <bytes do resumo>`.

## Requisitos Não-Funcionais

- [ ] **RNF01:** `resumo()` leva menos de 50 ms no CPython depois de 7 dias simulados.
- [ ] **RNF02:** a página-modelo fica abaixo de 20 KB, sem nenhum recurso externo (no modo portal não há internet):
  ```bash
  grep -c "http" companion/raiox.html
  ```
  O comando só deve encontrar o namespace do SVG.
- [ ] **RNF03:** mobile-first. Em 390 px de largura a página não rola para os lados, e todo botão tem 44 px ou mais.
- [ ] **RNF04:** modo escuro pelo `prefers-color-scheme` e por `data-theme`. As cores vêm da paleta de referência da
  skill `dataviz`, com os passos próprios do escuro.
- [ ] **RNF05:**
  - lúdica: topo em degradê, emoji por vontade e cantos arredondados;
  - acessível: o relógio tem `aria-label`, a dica tem `aria-live`, e a cor nunca é a única pista (cada barra tem
    rótulo e número).
- [ ] **RNF06:** os aceites antigos não mudam: `python3 -m companion.sim.aceite todos` dá `ACEITE OK` com os mesmos
  números da issue #4.

## Modelo de Dados / API / Banco

Não há banco nem API HTTP nesta etapa. O "contrato" é o JSON do `resumo()` (RF01), que a etapa 2 vai servir em
`GET /brain.json`. Exemplo, cortado:

```json
{"versao": 1, "semente": 2, "idade_s": 259200, "agora_s": 280799, "minuto": 359, "acao": "ficar_quieta_longa",
 "dormindo": false, "drives": [["fome", 1000], ["energia", 530], ["humor", 160], ...],
 "clima": {"tempo": "sol", "graus": 25, "alvo": 200},
 "hoje": [["ficar_quieta", 192], ["ficar_quieta_longa", 58], ...], "ontem": [...],
 "gosta": [], "evita": [["chamar_alto", -3342], ["pedir_carinho", -3210], ...],
 "relogio": {"passo_min": 20, "max": 1500, "habitos": [[21, "adivinha_a_mao", 1485], ...], "evita": [...]},
 "recompensas": [[280500, "pedir_comida", -5, "ignorado"], ...],
 "horas": [[300, 800, 0, 200, 300, 500, 0], ...],
 "rede": {"eta": 4, "ruido": 30, "ticks": 81180, "ih_mudou_pct": 150, "limiar": [687, 803, 980]}}
```

## Cenários de Teste

### CT01 — Resumo completo e serializável
```
DADO 2 h simuladas (Dono padrão, semente 1)
QUANDO resumo()
ENTÃO tem todas as chaves do RF01, só tipos simples, json.dumps funciona, idade_s = 7200,
      hoje bate com a contagem de decisões do simulador e horas tem 2 linhas de 7 valores
```
Testes: `test_chaves_e_json`, `test_so_inteiros`, `test_hoje_bate_com_as_decisoes` e `test_horas_e_recompensas`.

### CT02 — O raio-X não mexe no cérebro
```
DADO duas simulações de 1 h com a semente 3
QUANDO uma delas chama resumo() a cada minuto
ENTÃO as listas de decisões são idênticas
```
Teste: `test_resumo_nao_muda_o_cerebro`. Na ponta, RNF06 roda os aceites inteiros.

### CT03 — Limites e virada do dia
```
DADO RAIOX_RECS + 5 recompensas
ENTÃO só as últimas RAIOX_RECS ficam guardadas, as mais antigas saem primeiro

DADO 20 h simuladas a partir das 6h
ENTÃO ontem não está vazio e hoje (2 h) tem menos decisões que ontem
```
Testes: `test_limite_das_recompensas` e `test_virada_do_dia`.

### CT04 — Hábito no relógio vira faixa
```
DADO o peso do relógio de pedir_carinho em RAIOX_HABITO na célula 57 e em −RAIOX_HABITO na célula 10
ENTÃO relogio.habitos = [[57, 'pedir_carinho', 200]] e relogio.evita = [[10, 'pedir_carinho', -200]]
```
Teste: `test_habito_aparece_no_relogio`.

### CT05 — Erro: dados ausentes ou perigosos
```
DADO a página-modelo aberta do disco, sem dados (o fetch de brain.json falha)
ENTÃO mostra "Sem dados do cérebro" sem erro no console

DADO um resumo
QUANDO pagina(resumo)
ENTÃO a marca some, o JSON embutido é igual ao resumo e não contém "</"
```
O primeiro caso é coberto pelo E2E (CT07); o segundo, pelo teste `test_pagina_embute_o_resumo`.

### CT06 — Portabilidade
```
QUANDO micropython companion/sim/fumaca.py
ENTÃO "micropython ok 4780 239 <bytes>", com bytes > 0
```

### CT07 — [E2E click-by-click] A página no celular
**Pré-condição:**
```bash
python3 -m companion.sim.raiox semana 3 2 chuva
```
Depois, `python3 sdd/ISSUE_5/prototipo/e2e.py` (Playwright em Python, Chromium a 390 × 844) roda a sequência abaixo,
em claro e em escuro:
1. Abrir a página e fazer a captura inteira. Conferir que não há rolagem lateral e que há 7 cartões ou mais.
2. Tocar no 1º hábito. Esperado: o botão fica `aria-pressed=true`, o arco é destacado no relógio e a dica começa com
   "Faz" ou "Evita".
3. Tocar em "Ontem". Esperado: a aba fica ativa.
4. Tocar em "Ver todas". Esperado: aparecem mais linhas. Depois, "Ver menos" volta ao número inicial.
5. Passar o dedo no 1º gráfico de vontade. Esperado: a dica mostra o valor.
6. Conferir que todo botão tem 44 px ou mais e que o console não tem erro.
7. Abrir a página-modelo sem dados. Esperado: o estado vazio.

**Saída:** capturas numeradas em `load-tests/results/issue-5-journey/` e `E2E OK`.
**Critério:** nenhum botão sem efeito e nenhum erro no console.

## Fora do Escopo

- **Etapa 2:** a rota `/brain.json`, servir a página no `portal.py`, o botão no menu da placa e a medida de memória e de
  tempo no ESP32.
- **Botões da fonte:** "resetar cérebro", "exportar DNA" e "baixar brain.bin". Eles dependem da persistência (fase 2 da
  fonte).
- **Controles de η, ruído, horário de silêncio e modo muda.**
- **Na tela da placa:** o raio-X por toque longo e a ficha de personalidade (fase 4 da fonte); nesta etapa a página
  fica só no navegador.
- **Traços e DNA:** ainda não existem (fase 6).

## Docs canônicas a atualizar

- [x] `CODEMAP.md`, que fica na raiz: `raiox.html` e `sim/raiox.py` no item `companion/`, a nota "Raio-X" na seção
  Cérebro SNN e a contagem de linhas.
- [ ] `CALIBRACAO.md`: nenhuma constante do cérebro muda de valor.
- [ ] `ARCHITECTURE`, `MODULES`, banco: não existem neste projeto ou não se aplicam.
