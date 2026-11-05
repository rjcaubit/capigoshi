# Especificação — Cérebro SNN: humor e comportamento variam com o clima

**Issue:** #4
**Data:** 2026-11-05
**Status:** Aguardando implementação

## Objetivo

Fazer o clima lá fora mudar o humor e o comportamento da Capi pelo cérebro SNN (`companion/`). Em dia de chuva ela
fica mais triste e mais quieta, e com sol, mais animada. O clima entra de dois jeitos: como sentido (neurônios de
entrada que a rede pode associar ao que aprende) e como alvo do humor nos drives, e não como regra que escolhe ação.

## Pesquisa & Dependency Analysis

### Diagnóstico (medido no planejamento, protótipo no scratchpad)

Sem clima, num cenário `semana` de 6 dias, o humor médio das 8h às 22h já varia ±20 pontos de um dia para o outro.
O motivo são as recompensas: cada R soma `R*5` ao humor (x10), e os "ignorado" (−5) são o R mais comum no log.
O humor regride só 1 ponto por minuto, sempre em direção a 0. Consequências medidas:

- **Regredir para um alvo do clima, a 1/min, não aparece.** Chuva −57, sol −45, e ações tristes iguais nos dois
  (0,62/h × 0,64/h). Quase todo o tempo o humor está abaixo dos dois alvos, e aí os dois regridem igual (+1/min).
- **As ações tristes já existem e dependem só do humor:** `bico` (< 0), `resmungar` (< −20), `bravinha` e
  `emburrar` (< −30), `lagrimazinha` (< −50) e `suspirar` (tédio). Basta o humor ficar onde o clima manda.

### Experimentos do planejamento (`clima_teste.py`, semente 1, dias alternados chuva 18 °C / sol 25 °C)

| Configuração | Humor chuva | Humor sol | Tristes/h chuva | Tristes/h sol |
|---|---|---|---|---|
| Sem clima (referência; os rótulos só marcam os dias) | −38,6 | −30,5 | 1,07 | 1,26 |
| Alvo do clima, regride 1/min (`CLIMA_PUXA_PCT=0`) | −57,1 | −45,4 | 0,62 | 0,64 |
| **Alvo + 5 % da distância por minuto (`CLIMA_PUXA_PCT=5`)** | **−37,1** | **+17,9** | **1,19** | **0,00** |
| Alvo + 10 % da distância por minuto | −35,9 | +19,3 | 1,26 | 0,00 |

Com 5 %, sementes 2 a 4: humor chuva −36,5 / −36,8 / −37,3 e sol +18,3 / +18,6 / +17,9; tristes/h na chuva
1,00 / 0,52 / 1,45, e no sol 0,02 / 0,00 / 0,02. As ações alegres (`sorriso_largo`, `rir`, `cantarolar`, danças,
`pular`, `olhos_brilhando`) sobem no sol em 3 das 4 sementes; por isso ficam fora do aceite.

Aceites antigos no protótipo, sem clima: hábito 6 de 7 (antes 5), sementes [6, 6, 5, 5] (antes [5, 5, 5, 6]),
silêncio 10,8 → 0,1 sons/h (antes 12,0 → 0,1), velocidade 66 s. A rede da fonte nasce igual. Os números mudam
porque os sorteios do clima, feitos no fim do `__init__`, deslocam a sequência aleatória que vem depois, e porque a
normalização da entrada passa a somar também as linhas do clima, mesmo caladas.

### O que já existe e reuso (fonte: `CODEMAP.md`, seção "Cérebro SNN")

| Item | Localização | Como uso |
|---|---|---|
| Clima na placa | `rede.py`: `baixar_clima`, `wx_de`, `tipo_de`, `wx()` | `tipo_de` dá o nome (`sol`, `nublado`, `chuva`, `tempestade`, `neve`, `neblina`, `vento`); `wx()` devolve `None` sem previsão de até 3 h. Na fase 1, o `main.py` passa esse nome e os graus ao cérebro |
| Codificador | `companion/encoder.py`: `GRUPOS`, `_bin`, `_pop` | Grupo `clima` (binário, 4) e `temperatura` (população, 3) no fim da tabela |
| Rede | `companion/snn.py`: `Rede.__init__` | As 7 linhas novas de `w_ih` são sorteadas depois de tudo, e a rede da fonte nasce igual para a mesma semente |
| Drives | `companion/drives.py`: `minuto()` | O humor regride para o alvo do clima, e não para 0; a energia e a curiosidade ganham um termo por minuto |
| Ações tristes | `companion/actions.py`: `bico`, `bravinha`, `lagrimazinha`, `resmungar`, `emburrar`, `suspirar` | Já têm pré-condição por humor; nada muda no catálogo |
| `mostrar_clima` | `companion/actions.py` (pré-condição `wifi`) | O simulador passa `wifi=1` quando há clima |
| Simulador | `companion/sim/mundo.py`, `rodar.py`, `aceite.py` | `Mundo(tempos=...)`, `simular(..., tempos, humor)`, aceite `clima` |
| Padrão de aceite por semente | `aceite.sementes` (issue #3) | O aceite `clima` roda as sementes 1 a 4 |

### O que preciso criar (porque não existe)

| Item | Tipo | Onde | Por que não reuso |
|---|---|---|---|
| `clima.py` | módulo | `companion/clima.py` | `rede.wx_de`/`tipo_de` usam float e moram no firmware, que o cérebro não importa; aqui só o nome vira índice 0..3 e efeito inteiro nos drives |
| Constantes do clima | config | `companion/config.py` | Novas |
| `N_IN_FONTE` | config | `companion/config.py` | Separa as 100 entradas da fonte das 7 do clima, para sortear essas por último |
| Aceite `clima` | função | `companion/sim/aceite.py` | Não existe cenário com clima |
| `test_clima.py` | testes | `companion/testes/` | 7 testes novos |

### Padrões canônicos a seguir

- Inteiros x10 nos drives; sem float no que roda por tick (RNF02).
- Código e comentários em português sem acento; o número da seção da fonte ou da issue no comentário.
- Constantes em `config.py`, e cada mudança de comportamento anotada em `CALIBRACAO.md`.
- `todos` em `aceite.py` continua sendo o comando de aceite.

### Decisões tomadas

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| Humor regride para um **alvo** do clima, com puxada proporcional (`10 + 5 % da distância` por minuto) | Deriva fixa (−0,5/min até um piso, como na issue) | A regressão de 1/min para 0 anula uma deriva de 0,5/min; e o alvo a 1/min não aparece (tabela acima) |
| A puxada proporcional só vale com previsão | Sempre | Sem previsão (`tempo=None`), o humor regride como hoje: 1/min para 0 |
| Clima no fim da tabela de entradas (`N_IN` 100 → 107), sorteado por último | Trocar um grupo existente | A rede da fonte nasce igual; nenhum sentido some |
| `clima` binário 4 (sol, nublado, chuva, tempestade); neve conta como chuva, neblina e vento como nublado | Os 7 tipos do `tipo_de` | 4 bastam para o humor; menos linhas em `w_ih` |
| `temperatura` em população de 3 (5 a 35 °C) | Binário frio/calor | Mesmo padrão dos outros contínuos |
| Frio (< 15 °C) só acelera o cansaço (−0,3/min) | Frio força `dormir` | Sem regra fixa: com menos energia, `dormir`, `cochilar` e `bocejar` ficam disponíveis mais cedo |
| Chuva e tempestade cansam (−0,3/min); sol dá +1/min de curiosidade | Sem efeito em outros drives | Pedido na issue ("energia cai mais rápido", "sol puxa curiosidade") |
| Aceite com humor e ações tristes, sementes 1 a 4 | Também ações alegres | As alegres não sobem no sol em todas as sementes (semente 3: 0,71 × 0,74) |
| `graus` chega inteiro | Aceitar float | O codificador grava em `array('H')`; quem chama arredonda (na fase 1, `main.py`) |

### Riscos técnicos

- **Sol deixa a Capi sem nenhuma ação triste** (0 a 0,02/h). É o pedido da issue, mas pode soar artificial. O botão é
  `CLIMA_HUMOR[0]`: um alvo menor (por exemplo 100) devolve um pouco de `bico`.
- **O hábito muda de número** (5 → 6 na semente 1), sem que o clima esteja ligado. O motivo é a sequência aleatória
  e a normalização (diagnóstico). Os aceites antigos continuam passando com folga maior; a `CALIBRACAO.md` registra.
- **A Capi aprender "brincar quando chove"** é possível com os neurônios novos (R-STDP), mas não foi medido nem
  entra no aceite: depende de um dono simulado que brinque mais na chuva.
- **Memória:** +7 × 96 × 2 B × 2 (`w_ih` e `w_ih0`) = 2,7 KB na placa.
- **Tempo:** o aceite `clima` leva ~3 min 20 s (4 sementes × 6 dias); `todos` passa de ~7 para ~11 min.

## Requisitos Funcionais

- [ ] RF01: `companion/clima.py` traduz o nome do tempo (`rede.tipo_de`) em índice 0..3 (`sol`, `nublado`/`neblina`/
  `vento`, `chuva`/`neve`, `tempestade`) e `None` sem previsão; `efeito(tipo, graus)` devolve
  `(alvo do humor, % de puxada, energia/min, curiosidade/min)`, todos inteiros x10, e `(0, 0, 0, 0)` sem previsão.
- [ ] RF02: Os sentidos ganham `tempo` (nome ou `None`) e `graus` (inteiro ou `None`). O codificador liga 1 dos 4
  neurônios do grupo `clima` e codifica `graus` em população de 3 (5 a 35 °C); sem previsão, os 7 ficam calados.
- [ ] RF03: `N_IN` passa a 107. As linhas de `w_ih` das entradas 100 a 106 são sorteadas depois de todo o resto, e as
  100 primeiras linhas, `w_ho` e oculta → oculta nascem iguais às de antes para a mesma semente.
- [ ] RF04: A cada minuto, o cérebro passa `clima.efeito(s['tempo'], s['graus'])` aos drives antes de `minuto()`.
- [ ] RF05: Em `Drives.minuto()`, o humor regride para o alvo do clima, `HUMOR_REGRIDE + |humor − alvo| ×
  CLIMA_PUXA_PCT / 100` por minuto (sem passar do alvo). Sem previsão, fica idêntico a hoje.
- [ ] RF06: Acordada, a energia ganha o termo do clima (chuva e tempestade −3; frio < 15 °C, mais −3), e a curiosidade
  ganha +10/min no sol.
- [ ] RF07: O simulador aceita `tempos` (um `(tipo, graus)` por dia, em ciclo) e registra o humor por minuto. O aceite
  `clima` roda 6 dias alternando chuva (18 °C) e sol (25 °C) nas sementes 1 a 4.

## Requisitos Não-Funcionais

- [ ] RNF01: Os aceites `velocidade`, `silencio`, `habito` e `sementes` continuam passando sem clima.
- [ ] RNF02: Sem float em `clima.py`, `drives.py`, `encoder.py` e `snn.py`.
- [ ] RNF03: Determinismo: mesma semente e mesmos `tempos`, mesmas decisões.
- [ ] RNF04: Roda em MicroPython 1.25 (`fumaca.py`).

## Modelo de Dados

Sem banco. Estado novo em memória:

| Estado | Tipo | Tamanho |
|---|---|---|
| `Drives.clima` | tupla `(alvo, puxa, energia, curiosidade)` | 4 inteiros |
| `Rede.w_ih` / `w_ih0` | +7 linhas de 96 | +2,7 KB no total |

Persistência dos pesos continua fora (fase 1).

## API (Python, não HTTP)

| Chamada | Mudança |
|---|---|
| `Cerebro.segundo(s, agora_ms)` | `s` aceita `tempo` (str ou `None`) e `graus` (int ou `None`); sem as chaves, vale `None` |
| `clima.indice(tipo)` | novo: `0..3` ou `None` |
| `clima.efeito(tipo, graus)` | novo: `(alvo, puxa, energia, curiosidade)` |
| `Mundo(dia_semana=0, tempos=None)` | `tempos`: tupla de `(tipo, graus)` por dia |
| `simular(..., tempos=None, humor=None)` | `humor`: lista que recebe `(segundo, humor x10)` por minuto |
| `python3 -m companion.sim.aceite clima` | novo aceite |

## Frontend

Nenhum. A Capi abatida no desenho fica para a ligação do cérebro à placa (fase 1). Sem CT E2E.

## Cenários de Teste

### CT01: Chuva deixa a Capi mais triste que o sol
```
DADO o dono padrão (cenário semana) e 6 dias alternando chuva 18 °C e sol 25 °C
QUANDO python3 -m companion.sim.aceite clima
ENTÃO em cada semente de 1 a 4, das 8h às 22h: humor médio na chuva pelo menos 30 pontos abaixo do sol,
      e ações tristes por hora na chuva ≥ 0,3 e ≥ 2 × as do sol
```

### CT02: Sem regressão
```
DADO nenhum clima nos sentidos
QUANDO python3 -m companion.sim.aceite todos
ENTÃO velocidade, silencio, habito, sementes e clima com ACEITE OK
```

### CT03: Unitários
```
QUANDO python3 -m unittest discover -s companion/testes -t .
ENTÃO 36 testes OK (29 de antes + 7 de test_clima.py)
```
Os 7: `test_indice`, `test_efeito` (inclui o frio), `test_humor_vai_para_o_alvo` (e volta a regredir 1/min sem
previsão), `test_puxada_proporcional`, `test_neuronios` (calados sem previsão; chuva e 5 °C ligam o certo),
`test_rede_da_fonte_nao_muda`, `test_cerebro_le_o_clima`.

### CT04: Erro — clima desconhecido
```
DADO s['tempo'] = 'granizo' (nome que o tipo_de não devolve) ou None
QUANDO o cérebro roda um minuto
ENTÃO clima.indice devolve None, o grupo clima fica calado e o humor regride para 0 como hoje
```
(coberto por `test_indice`, `test_efeito` e `test_neuronios`; `'granizo'` cai no `GRUPO.get`.)

### CT05: Portabilidade
```
QUANDO micropython companion/sim/fumaca.py
ENTÃO micropython ok ...
```

## Decisões Arquiteturais

| Decisão | Justificativa |
|---|---|
| Clima como alvo do humor, e não como regra de ação | A issue pede que entre "pelo cérebro": o humor muda as pré-condições e a entrada `drives` da rede, e a rede escolhe |
| Grupo de entrada novo | Permite aprender associações com o clima (por exemplo, brincar quando chove) sem código novo |

## Fora do Escopo

- Ligar o cérebro à placa e desenhar a Capi abatida (fase 1).
- Previsão do tempo (só o clima atual).
- Aceite de "aprender a brincar na chuva" (risco anotado).
- Mudar o catálogo de ações.

## Docs canônicas a atualizar

- [x] `CODEMAP.md` (módulo `clima`, comando dos aceites)
- [x] `CALIBRACAO.md` (seção "Clima (issue #4)")
- [ ] `MODULES.md`, banco, `ARCHITECTURE.md`, `CHANGELOG.md`: não existem neste repositório
