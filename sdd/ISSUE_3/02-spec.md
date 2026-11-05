# Especificação — Cérebro SNN: aprender o horário dos hábitos

**Issue:** #3
**Data:** 2026-11-05
**Status:** Aguardando implementação
**Origem:** CT03 da issue #2 (fase 0), que não passou

## Objetivo

A Capi precisa aprender **quando** um pedido funciona. Com um dono que só dá carinho às 19h, `pedir_carinho` e
`chamar_baixo` devem ficar mais frequentes perto das 19h do que no resto do dia. Hoje ela aprende a pedir sempre ou
a nunca pedir. O motivo foi medido no planejamento e está descrito abaixo.

## Pesquisa & Dependency Analysis

### Diagnóstico (medido no planejamento, protótipo no scratchpad)

No cenário do hábito, a main de hoje faz isto:

1. **O castigo do "ignorado" nunca chega à rede.** O "ignorado" (−5) chega 60 s depois do pedido. A elegibilidade
   decai ×25/32 a cada 16 ticks e zera em uns 16 s. `Aprendizado.recompensa` não acha nada para mudar, e a rede
   não aprende a parar de pedir: são 183 pedidos ignorados em 3 dias, até 9 pedidos/h às 3h da manhã.
2. **O carinho das 19h vale +3.** O R de 10 cai pela habituação: com centenas de pedidos por dia, `n_acao` é alto
   e `R*3//(3+n)` fica pequeno. O castigo de fora pesa mais que o prêmio de dentro.
3. **A camada oculta não separa 19h de 17h ou 21h.** São 8 neurônios de hora em tenda, um a cada 3 h. Mesmo com o
   prêmio chegando, a rede generaliza para o dia todo. Essa foi a falha das 13 configurações da #2.
4. **Exploração.** Quando a rede aprende a não pedir, ela não pede às 19h e não descobre o hábito. Com a taxa de
   hoje (~5 pedidos/dia), a chance de um pedido cair entre 19h00 e 19h15 é de ~5 % por dia.

### Experimentos do planejamento (`aceite habito`, semente 1)

| Ajuste | Dias ok |
|---|---|
| via hora → saída (célula de 20 min), crédito no minuto da recompensa | 0 a 1 |
| + crédito no minuto em que a ação **começou** | 1 |
| + prêmio pesando 6x o castigo (`K_POS=24`, `K=4`) | 2 |
| + marca dos ocultos para o castigo atrasado | 3 (pedidos fora caem a 0/h) |
| + solidão (afeto < 20 → corrente em `pedir_carinho`) 450..700 | 0 a 3 |
| **+ solidão 1000, `K=8`, `RELOGIO_MAX=1500`** | **6** (sementes 2, 3, 4: 5, 5, 7) |
| idem, ligação direta somando em vez de sobrescrever | 4 (sementes 2, 3, 4: 6, 7, 7) |
| idem, marca também nas ações com som | 4 (sementes: 3, 5, 5) |
| **versão final das tasks (com esquecimento diário do relógio)** | **5** (sementes 1 a 4: 5, 5, 5, 6) |

Na versão final: silêncio 12,0 → 0,1 sons/h, velocidade 68 s, 29 testes OK, `micropython ok`. Na semana normal
(3 dias), a Capi pede menos que a main: `pedir_carinho` cai de 498 para 246 e `pedir_comida` de 544 para 70.

### O que já existe e reuso (fonte: `CODEMAP.md`, seção "Cérebro SNN")

| Item | Localização | Como uso |
|---|---|---|
| `Rede.direto` | `companion/snn.py` | corrente fixa por saída, somada todo tick; o relógio e a solidão entram por ela |
| `Cerebro._decidir` | `companion/cerebro.py:142` | zera `direto` e aplica `DIRETO`; ganha o relógio antes e a solidão depois |
| `Cerebro._aplicar` | `companion/cerebro.py:69` | todo R passa por aqui; ganha o relógio e a marca |
| `Cerebro._executar` | `companion/cerebro.py:173` | guarda o minuto de início e a marca |
| `Aprendizado` | `companion/learn.py` | ganha `marcar` e `recompensa_atrasada`, com o mesmo piso de `recompensa` |
| `Rede.recentes(rec_h)` | `companion/snn.py` | ocultos que dispararam nos últimos 16 ticks = a marca |
| `ESQUECE_PCT` e o arredondamento de `esquecer` | `companion/learn.py` | mesmo esquecimento diário para o relógio |
| `aceite.habito` | `companion/sim/aceite.py` | vira `dias_habito(semente)`; o critério de 5 de 7 dias continua |
| `A.PEDIDOS` | `companion/actions.py` | ações que recebem marca |

### O que preciso criar (porque não existe)

| Item | Tipo | Onde | Por que não reuso |
|---|---|---|---|
| `Relogio` | classe | `companion/relogio.py` | não há caminho plástico hora → saída. O grupo `hora` do codificador tem 8 neurônios de 3 h e passa pela camada oculta, que não separa as horas |
| `Aprendizado.marcar` / `recompensa_atrasada` | métodos | `companion/learn.py` | a elegibilidade não sobrevive aos 60 s do "ignorado" |
| `SOLIDAO` e `RELOGIO_*`, `MARCA_K` | constantes | `companion/config.py` | — |
| `aceite sementes` | comando | `companion/sim/aceite.py` | uma semente só é frágil: entre sementes o resultado varia de 4 a 7 dias |
| `test_habito.py` | testes | `companion/testes/` | — |

### Padrões canônicos a seguir

- Código em português sem acento, inteiros, `array`, sem float no tick (RNF03 da #2).
- Toda constante nova em `config.py`, com origem em comentário; o desvio da fonte vai para `CALIBRACAO.md`.
- MicroPython 1.25: só `array`; `//` com negativo arredonda para baixo igual ao CPython.

### Decisões tomadas

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| Relógio como via direta ao lado da rede (opção c da #2) | mais neurônios de hora na entrada, ocultos só de tempo | testado na #2 (`OCULTOS_TEMPO`, `P_MAX_HORA`): 0 a 2 dias |
| 72 células de 20 min, corrente interpolada entre vizinhas | 24 células de 1 h | a janela do teste tem 20 min; com 1 h, 18h e 20h herdam o prêmio |
| Crédito no minuto em que a ação começou | minuto em que o R chegou | o "ignorado" chega 60 s depois e cairia na célula seguinte |
| Prêmio pesa 3x o castigo (`RELOGIO_K_POS=24`, `RELOGIO_K=8`) | simétrico | simétrico dá 1 dia: um carinho por dia contra vários pedidos ignorados |
| Relógio para as 100 ações | só os pedidos | 14,4 KB (`72*100*2`); deixa a Capi aprender a hora de qualquer ação; silêncio continua passando |
| Marca só nos `PEDIDOS` | pedidos + ações com som | com som também: 4 dias (sementes 3, 5, 5) |
| Solidão: afeto < 20 → +1000 em `pedir_carinho` | otimismo inicial do relógio (`INI=200`) | o otimismo acaba nas primeiras horas e não volta; a solidão é um motivo do bicho (seção 4 da fonte: afeto é drive) |
| `DIRETO` continua sobrescrevendo, relógio aplicado antes | somar | somar piorou a semente 1 (4 dias) |
| Critério de robustez: sementes 1 a 4, média >= 5 e mínimo >= 4 | 5 de 7 em todas | a variação entre sementes é real (4 a 7); o CT03 original continua sendo a semente 1 |

### Riscos técnicos

- **Margem curta.** A versão final dá 5, 5, 5, 6, e uma mudança pequena em qualquer constante pode derrubar um dia.
  Mitigação: o aceite `sementes` entra no `todos`; os botões estão na tabela da fase C do `03-tasks.md`.
- **Capi solitária pede carinho com insistência** quando o afeto fica < 20. Na semana normal ela pede menos que
  hoje (marca), mas um dono ausente o dia todo vê pedidos nas primeiras horas. É o comportamento desejado da
  exploração, mas fica no registro para a fase 3 (resposta do dono real).
- **Memória.** O relógio ocupa 14,4 KB na placa e a marca até 8 tuplas de ≤ 80 inteiros. O relógio precisa
  entrar no arquivo de pesos quando houver persistência (fase 1); está fora do escopo aqui.

## Requisitos Funcionais

- [ ] RF01: `companion/relogio.py` com `Relogio(n_saidas)`: `corrente(minuto, dire)` soma em `dire[o]` o peso interpolado das duas células vizinhas; `recompensa(R, acao, minuto, eta)` credita as duas células na proporção do minuto, com `RELOGIO_K_POS` para R > 0 e `RELOGIO_K` para R < 0, limitado a ±`RELOGIO_MAX`; `esquecer()` volta `ESQUECE_PCT` para zero (ao menos 1).
- [ ] RF02: `Cerebro` guarda o minuto em que cada ação começou (`min_acao`), e todo R aplicado em `_aplicar` atualiza o relógio nesse minuto.
- [ ] RF03: `_decidir` aplica o relógio em `direto` antes da ligação direta, e a ligação direta continua sobrescrevendo.
- [ ] RF04: Ao começar um pedido (`A.PEDIDOS`), `Aprendizado.marcar(acao)` guarda os ocultos excitatórios dos últimos 16 ticks. Um R com motivo `ignorado` ou `som_sem_resposta` aplica `recompensa_atrasada`: `dw = eta*R*MARCA_K >> 2` só nos ocultos marcados, com o piso da coluna.
- [ ] RF05: Com afeto < `SOLIDAO[1]`, `_decidir` soma `SOLIDAO[3]` à corrente de `pedir_carinho`.
- [ ] RF06: O relógio esquece uma vez por dia, junto com `apr.esquecer()`.
- [ ] RF07: `aceite sementes` roda o hábito com as sementes 1 a 4 e passa com média >= 5 dias e nenhuma < 4; `aceite todos` inclui `habito` e `sementes`.

## Requisitos Não-Funcionais

- [ ] RNF01: Velocidade — 7 dias da semana em <= 180 s (CT01 da #2 continua).
- [ ] RNF02: Sem float nos módulos do tick (`relogio.py`, `learn.py`, `cerebro.py`).
- [ ] RNF03: Determinismo — mesma semente, mesmas decisões.
- [ ] RNF04: `micropython companion/sim/fumaca.py` continua passando.

## Modelo de Dados

Sem banco. Estado novo em memória:

| Onde | Estrutura | Tamanho |
|---|---|---|
| `Relogio.w` | `array('h')`, `[celula * 100 + acao]`, ±1500 | 72 × 100 × 2 B = 14,4 KB |
| `Cerebro.min_acao` | `array('H')`, minuto do dia | 200 B |
| `Aprendizado.marcas` | `dict acao -> tuple(h)` | até 8 entradas |

## API (Python, não HTTP)

| Chamada | Descrição |
|---|---|
| `Relogio(n_saidas)` | pesos zerados |
| `Relogio.corrente(minuto, dire)` | soma a corrente do minuto em `dire` |
| `Relogio.recompensa(R, acao, minuto, eta)` | aprende |
| `Relogio.esquecer()` | 1 %/dia de volta a zero |
| `relogio.celulas(minuto)` | `(celula, vizinha, f)` com `0 <= f < 20` |
| `Aprendizado.marcar(acao)` | guarda os ocultos ativos |
| `Aprendizado.recompensa_atrasada(R, acao, eta)` | R nos ocultos marcados |
| `aceite.dias_habito(semente)` | dias ok (0 a 7), imprime dia a dia |

## Frontend

Não há.

## Cenários de Teste

### CT01: Hábito (o CT03 da #2)
```
DADO um dono ausente o dia todo, que chega às 19h00 e atende pedidos de carinho até 19h15
QUANDO python3 -m companion.sim.aceite habito
ENTÃO em pelo menos 5 dos 7 dias a taxa de pedir_carinho + chamar_baixo entre 18h50 e 19h10 é >= 2x a taxa
     das 8h às 22h fora da janela, com pelo menos 1 ocorrência; sai com código 0
```

### CT02: Robustez entre sementes
```
QUANDO python3 -m companion.sim.aceite sementes
ENTÃO "sementes: [a, b, c, d] dias" com a+b+c+d >= 20 e nenhum < 4; sai com código 0
     (planejamento: [5, 5, 5, 6])
```

### CT03: Sem regressão da fase 0
```
QUANDO python3 -m companion.sim.aceite velocidade  e  python3 -m companion.sim.aceite silencio
ENTÃO velocidade <= 180 s; silêncio > 2 sons/h no início e < 2 sons/h no dia 3
```

### CT04: Unitários
```
QUANDO python3 -m unittest discover -s companion/testes -t .
ENTÃO 29 testes OK (22 da fase 0 + 7 novos):
  - células: 19h00 → (57, 58, 0); 23h50 → (71, 0, 10)
  - prêmio às 19h00 vira 960 na célula 57 e corrente 480 às 19h10
  - castigo às 10h05 se divide 3/4 e 1/4, e satura em -RELOGIO_MAX
  - esquecer: 1000 → 990, -50 → -49
  - castigo atrasado só muda os ocultos marcados
  - "ignorado" 60 s depois credita a célula do início do pedido
  - solidão: afeto 10 → corrente 1000; afeto 50 → 0
```

### CT05: Erro — castigo atrasado sem marca
```
DADO uma ação que não é pedido (sem marca), com R 'som_sem_resposta'
QUANDO _aplicar
ENTÃO recompensa_atrasada não muda nada (marcas.get devolve None) e não levanta exceção
```

### CT06: Portabilidade
```
QUANDO micropython companion/sim/fumaca.py
ENTÃO "micropython ok" sem exceção
```

## Decisões Arquiteturais

Ver "Decisões tomadas" acima.

## Fora do Escopo

- Clima como entrada (issue #4).
- Persistência do relógio e dos pesos na placa (fase 1).
- Mexer na habituação (6.4) ou no R do carinho: o relógio resolve sem isso.
- Corrigir a fonte (`00-fonte.md`); os acréscimos vão para `CALIBRACAO.md`.

## Docs canônicas a atualizar

- [x] `CODEMAP.md` (raiz) — `relogio` na linha do `companion/` e o comando `sementes`
- [x] `CALIBRACAO.md` (raiz) — seção da #3 e "Hábito — não resolvido" vira resolvido
- [x] `sdd/ISSUE_2/04-acceptance.md` — pendência do CT03 aponta para o aceite da #3
- [ ] `docs/` — não (é o site)
