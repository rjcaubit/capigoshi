# Especificação — Cérebro SNN da Capi, fase 0: simulador em CPython

**Issue:** #2
**Data:** 2026-11-04
**Status:** Aguardando implementação

## Objetivo

Construir o cérebro SNN (rede LIF em inteiros com STDP e R-STDP, 7 drives, catálogo de 100 ações e recompensas do
dono) como pacote `companion/` portável, e provar no PC, com sensores falsos e um dono simulado, que ele aprende a
ficar quieto quando ninguém responde a sons e a pedir carinho na hora em que o dono costuma dar. Nada vai para a placa
nesta issue; a fase 1 só começa com este aceite.

Fonte das regras: `sdd/ISSUE_2/00-fonte.md` (documento de 03/11/2026). Esta spec cita a seção da fonte entre
parênteses e lista abaixo tudo o que muda em relação a ela.

## Pesquisa & Dependency Analysis

### O que já existe e reuso (fonte: `CODEMAP.md`)

| Item | Localização | Como uso |
|---|---|---|
| Sensores reais: `Toque` (CST816D), `Movimento` (QMI8658), `Relogio` (PCF85063), `Som` (ES7210), `Bateria` (AXP2101) | `hw.py` | Confirmam a lista de sentidos da seção 3 da fonte; os nomes de campo do dicionário de sentidos seguem o que esses drivers dão. Leitura real fica para a fase 1 |
| Modo Companion ("Olhar") e `atualizar_companion` | `main.py:486-560` | É onde a fase 1 vai chamar o cérebro. Nesta fase não muda |
| Laço `main.passo(agora, dt)` | `main.py:1385` | Decide a API: `Cerebro.segundo(sentidos, agora_ms)` é chamado de dentro do laço, sem `Timer` |
| ESP-NOW de amigos | `rede.py` | Fonte futura de "Outra Capi" (fase 5); aqui é só valor falso |
| MicroPython unix | `/opt/homebrew/bin/micropython`, usado por `previa/` | Teste de fumaça de portabilidade do pacote |

### O que preciso criar (porque não existe)

| Item | Tipo | Onde | Por que não reuso |
|---|---|---|---|
| `config.py` | constantes | `companion/` | Exigência da fonte (seção 11): toda regra numérica nomeada, com seção no comentário |
| `actions.py` | catálogo + seleção | `companion/` | `vida.MOVES` tem 23 animações sem pré-condição, custo nem cooldown; o catálogo é a nova fonte de verdade, e o mapeamento ação → animação é da fase 1 |
| `encoder.py` | sentidos → spikes | `companion/` | Não há codificação neural |
| `snn.py` | rede LIF | `companion/` | Novo |
| `learn.py` | STDP, elegibilidade, R-STDP, homeostase | `companion/` | Novo |
| `drives.py` | 7 drives ×10 | `companion/` | O `pet` do `main.py` tem fome/alegria do modo Cuidar, com outras regras; o Companion ganha drives próprios |
| `reward.py` | eventos → R | `companion/` | Novo |
| `cerebro.py` | orquestrador | `companion/` | Junta os módulos e expõe a API que a fase 1 usa |
| `sim/` (mundo, dono, rodar, aceite) | simulador | `companion/sim/` | A `previa/` roda o jogo inteiro e desenha telas; o simulador do cérebro precisa ser rápido e sem tela |
| `testes/` | unittest | `companion/testes/` | Não há testes automatizados no repositório |
| `CALIBRACAO.md` | registro | raiz | Exigência da fonte (seção 11) |

### Padrões canônicos a seguir

- Estilo do repositório: nomes e comentários em português **sem acento** dentro do código Python (como `vida.py` e
  `rede.py`), funções curtas, sem type hints.
- Só o que existe no MicroPython 1.25: `array`, `random.getrandbits`/`randint`, `set`, `dict`. Sem `float` nos laços
  do tick, sem `int.bit_length`, sem f-strings complexas, sem `numpy`.
- Imports absolutos `from companion import config as C`; o pacote vai para a placa como pasta `companion/`
  (o `deploy.sh` lista arquivo por arquivo, então `sim/` e `testes/` não vão por engano).
- Testes com `unittest` da biblioteca padrão: `python3 -m unittest discover -s companion/testes -t .`.

### Decisões tomadas

| Decisão | Alternativa descartada | Motivo |
|---|---|---|
| `Cerebro.segundo()` chamado pelo laço de quem usa; os 20 ticks de uma decisão rodam juntos | `machine.Timer` de 50 ms (fonte, seção 9) | Callback de `Timer` não pode alocar e travaria toque e som; o `main.passo` já é o relógio |
| Pacote `companion/` com `sim/` e `testes/` dentro | `sim/` na raiz | Mantém o cérebro num lugar só; o deploy escolhe os arquivos |
| Rede só simula quando precisa decidir; durante a trava de uma ação o tempo da rede avança sem simular (`rede.t += 20`) | Simular 20 Hz o tempo todo | Medido: 0,07 a 0,26 ms por tick em CPython; 20 Hz direto dá cerca de 12 M ticks por semana |
| Traços pré/pós guardados como "último tick do spike" + tabela `TRACO[dt]`; STDP só sobre quem disparou nos últimos 16 ticks | Decair cada traço a cada tick | Corta o laço mais caro; dá o mesmo valor |
| Elegibilidade decai em lote a cada 16 ticks (×25/32 ≈ (63/64)¹⁶) e só nas colunas de saída que dispararam | Decair as 8.000 sinapses a cada tick | Mesmo resultado, uma fração do custo, e cabe na placa |
| R-STDP aplica a recompensa só na coluna da ação executada | Todas as sinapses elegíveis | A fonte quer que "só a ação que acabou de acontecer" receba; as saídas perdedoras também disparam e levariam crédito |
| Pesos entrada → oculta guardados ×16, com STDP de limite suave: `dw+ = A+·x·(Wmax−w) >> 14`, `dw− = A−·x·w >> 14` | STDP aditivo em 0..255 (fonte, 6.1) | No protótipo, com passos inteiros de 0, 1 ou 2, a depressão venceu e, com a normalização, o peso migrou para entradas mudas: em 10 min os ocultos calaram e o limiar foi a 49 |
| Normalização alvo = soma inicial de cada oculto | `SUM_TARGET` fixo | Com entrada esparsa (abaixo) a soma inicial varia por neurônio |
| 25 % das ligações entrada → oculta nascem fortes (20..80), o resto em 0..5 | Densa uniforme 20..80 | Com tudo uniforme nenhum oculto ficou seletivo a nada; o hábito generalizava para o dia todo |
| Corrente de saída = `soma(w) × I_OUT_MUL` (6) | `>> I_SCALE` (fonte) | Com `>> 2` nenhuma saída chegava ao limiar (contagem máxima 0 a 1) |
| Empate na contagem decide pelo potencial de membrana no fim da janela | Empate → `ficar_quieta` (fonte, 2) | As saídas sincronizam e empatavam quase sempre: 100 % `ficar_quieta` |
| Limiar adaptativo e normalização só na camada oculta | Também na saída | Desfariam o aprendizado: ação punida dispara menos, e o limiar dela desceria até voltar |
| Limiar oculto limitado a 500..4000 | Sem limite | Evita o colapso visto no protótipo |
| Bronca ("shh") fica como evento `shh` sem gesto definido nesta fase | Toque de dois dedos (fonte, 6.3) | O CST816D só lê um toque. O gesto é decidido na fase 2 (cutucar 3× seguidas ou virar de cabeça para baixo) |
| Habituação = contador ×10 que perde 1/6 a cada 10 min; a execução atual não conta para o próprio prêmio | Lista de horários da última hora | Inteiro, sem lista crescendo na placa |
| Teste do silêncio parte de uma Capi "falante" (pesos de som ×6) | Capi com pesos normais | Com pesos normais ela já nasce com menos de 1 som/h e o teste não prova nada; a falante tem 12,7 sons/h nas primeiras 6 h |
| Teste do hábito: no dia, taxa de `pedir_carinho` + `chamar_baixo` entre 18h50 e 19h10 ≥ 2× a taxa entre 8h e 22h fora da janela (e ≥ 1 ocorrência), em 5 de 7 dias | "Vencem entre 18h50 e 19h10" | Do jeito da fonte passa por acaso: em 20 min de decisões aleatórias uma das duas sempre vence |
| Meta de velocidade: 7 dias em ≤ 180 s | ≤ 60 s (fonte) | O protótipo mede cerca de 100 s por semana em CPython 3.14 no Mac; 60 s exigiria rodar menos ticks que a fonte manda |

### Divergências da fonte, para corrigir no documento original

1. Seção 2 diz ~80 neurônios de entrada; a tabela da seção 3 soma 100 (vale 100).
2. Seção 5 diz 21 ações com som; a tabela tem 20.
3. Seção 6.2 diz que R-STDP vale para saída → saída; a seção 2 diz que essa ligação é fixa (vale fixa).
4. Seção 6.1 (STDP aditivo 2/3) e seção 2 (`I_SCALE` igual na saída e empate → quieta) não funcionam como escritas;
   ver decisões acima.

### Riscos técnicos

- **Teste do hábito (o maior):** no protótipo a Capi aprendeu a pedir carinho, mas em todas as horas (dia 7: 12/h na
  janela e 9,7/h fora). A fase D desta issue é uma calibração com experimentos fixos; se nenhum passar, a fase para e
  volta para `/sdd-refine` com os números.
- **Desempenho na placa:** o tick do protótipo custa ~0,1 ms em CPython no Mac; o ESP32-S3 a 240 MHz é umas 30 a 50×
  mais lento sem viper. O orçamento de 10 ms por tick fica para medir na fase 1 (as escolhas acima já cortam o custo).
- **Memória:** pesos 9.600 (entrada→oculta ×16 em int16) + 8.000 (oculta→saída) + cópias de nascença + 8.000 de
  elegibilidade int32 ≈ 100 KB. Cabe; medir com `gc.mem_free()` na fase 1.

## Requisitos Funcionais

- [ ] RF01: `companion/config.py` tem toda constante numérica da fonte usada nesta fase, com a seção em comentário, e as
  constantes de calibração marcadas "calibrado".
- [ ] RF02: `companion/actions.py` tem as 100 ações da seção 5 da fonte com nome, categoria, som, pré-condição, custo,
  duração e cooldown; pré-condição em texto (`'energia<40|noite'`) compilada uma vez; seleção por contagem, mínimo de
  4 spikes, cooldown, trava pela duração e bloqueio de ações de custo ≥ 3 com energia < 40.
- [ ] RF03: `companion/encoder.py` converte o dicionário de sentidos nos 100 neurônios da tabela da seção 3
  (população em tenda, binário e rajada de 3 spikes para eventos).
- [ ] RF04: `companion/snn.py` simula 100 entradas, 96 ocultos (80 excitatórios, 16 inibitórios, recorrência esparsa
  10 %), uma saída por ação, inibição lateral fixa de 80, ruído ±30, refratário de 2 ticks, tudo inteiro.
- [ ] RF05: `companion/learn.py` aplica STDP (entrada → oculta), elegibilidade + R-STDP (oculta → saída) com janela
  de ~3 s, normalização e limiar adaptativo a cada 100 ticks, esquecimento de 1 %/dia, piso 5 em Social e Fisiológica.
- [ ] RF06: `companion/drives.py` atualiza os 7 drives por minuto (×10), com piso do afeto em 50 depois de passar de 60
  e avanço por tempo desligado.
- [ ] RF07: `companion/reward.py` gera R da tabela 6.3, custo de som −3 com habituação, −10 em horário de silêncio,
  "som sem resposta" em 30 s, "pedido ignorado" em 60 s, modulação por drive.
- [ ] RF08: `companion/cerebro.py` expõe `Cerebro(semente)`, `segundo(sentidos, agora_ms) -> acao`,
  `evento(nome, agora_ms)` e a regra fixa de sono com energia < 20.
- [ ] RF09: `python3 -m companion.sim.rodar {semana|silencio|barulho|habito} [dias] [semente]` roda o cérebro com o
  dono simulado e imprime sons/h por dia.
- [ ] RF10: `python3 -m companion.sim.aceite [velocidade|silencio|habito|todos]` roda os testes de aceite e sai com
  código 1 se algum falhar.
- [ ] RF11: `CALIBRACAO.md` registra cada constante que mudou em relação à fonte, com o motivo e o número medido.

## Requisitos Não-Funcionais

- [ ] RNF01: Desempenho — 7 dias simulados em ≤ 180 s (`aceite velocidade`) com CPython 3.14 no Mac.
- [ ] RNF02: Portabilidade — `micropython` (unix) roda 1 h simulada do pacote sem erro.
- [ ] RNF03: Sem `float` em `snn.py`, `learn.py`, `encoder.py`, `drives.py`, `reward.py`, `actions.py`
  (verificado por `grep`).
- [ ] RNF04: Determinismo — mesma semente, mesmo resultado.
- Não se aplicam: autenticação, dark mode, responsividade (não há UI nem API nesta fase).

## Modelo de Dados

Sem banco. Estado em memória:

| Estrutura | Tipo | Tamanho |
|---|---|---|
| `Rede.w_ih` (×16) e `w_ih0` | `array('h')` | 100 × 96 cada |
| `Rede.w_ho` e `w_ho0` | `array('h')` | 80 × 100 cada |
| `Rede.hh_ini/hh_pos/hh_w` (CSR) | `array` | ~920 ligações |
| `Aprendizado.e` | `array('i')` | 80 × 100 |
| `Drives.d` (×10) | `array('h')` | 7 |
| `Recompensa.n` (×10) | `array('H')` | 100 |

Persistência (`brain.bin`) é da fase 2.

## API (Python, não HTTP)

| Chamada | Quem chama | O que faz |
|---|---|---|
| `Cerebro(semente)` | sim / fase 1 | Cria rede, drives e catálogo; `semente` gera os pesos de nascença |
| `cer.segundo(s, agora_ms)` | a cada segundo | Avança drives, prazos de recompensa, trava; se livre, roda 20 ticks e escolhe; devolve o índice da ação em curso |
| `cer.evento(nome, agora_ms)` | reação do dono/mundo | `carinho`, `toque`, `estrela`, `shh`, `comida`, `sacudida_leve`, `sacudida_forte`, `jogo_fim`, `jogo_repetiu`, `social_ok`, `desligou`, `barulho`, `novidade` |
| `cer.log` | sim / raio-X | Lista de `('A', s, acao)` e `('R', s, acao, R, motivo)` |

Dicionário de sentidos `s` (montado por `sim/mundo.py`; na fase 1 por `sensors.py`): `minuto` (0..1439),
`fim_semana`, `toque_reg` e `toque_tipo` (0..3 ou `None`), `toques_60s`, `sem_toque` (s), `mov` (0..3 ou `None`),
`orient` (0..2), `som_nivel` (0..100), `som_evento` (0..2 ou `None`), `noite`, `bateria` (0..100), `carregando`,
`outra` (0 ausente, 1 longe, 2 perto), `outra_estado` (6 bits), `novidade` (0..100), `comida`. O cérebro acrescenta
`drives`, `ultima` e `resposta`.

## Frontend

Não há (o raio-X é da fase 4).

## Cenários de Teste

### CT01: Fluxo principal — semana completa
```
DADO o cenário 'semana' (dono presente 7h-8h e 18h-22h, responde a sons com p=0,5)
QUANDO python3 -m companion.sim.aceite velocidade
ENTÃO imprime "7 dias em N s" com N <= 180 e sai com código 0
```

### CT02: Teste do silêncio
```
DADO uma Capi falante (pesos das 20 ações com som x6) e um dono que nunca responde a sons
QUANDO python3 -m companion.sim.aceite silencio
ENTÃO mais de 2 sons/h nas 6 primeiras horas e menos de 2 sons/h no dia 3 (48-72 h)
```

### CT03: Teste do hábito (movido para a issue #3 em 2026-11-05)

> Não passou na fase 0 (melhor resultado 2 de 7 dias; 0 de 7 após a revisão). Por decisão do dono do projeto, a
> fase 0 foi mergeada sem este critério, que segue na issue #3. O comando e o critério abaixo continuam valendo lá.

```
DADO um dono ausente o dia todo, que chega às 19h00 e atende pedidos de carinho até 19h15
QUANDO python3 -m companion.sim.aceite habito
ENTÃO em pelo menos 5 dos 7 dias a taxa de pedir_carinho + chamar_baixo entre 18h50 e 19h10 é >= 2x a taxa
     das 8h às 22h fora da janela, com pelo menos 1 ocorrência na janela
```

### CT04: Unitários (LIF, STDP, R-STDP, catálogo, drives, recompensa)
```
QUANDO python3 -m unittest discover -s companion/testes -t .
ENTÃO 19 testes OK, entre eles:
  - LIF dispara exatamente no tick previsto pela equação e respeita o refratário
  - STDP potencia pré-antes-de-pós e deprime pós-antes-de-pré
  - R-STDP sobe o peso com R 1 s depois do spike, não muda com R 20 s depois, só mexe na coluna da ação
```

### CT05: Erro — pré-condição e trava
```
DADO 'piscar' executado no segundo 100 (cooldown 5 s)
QUANDO disponiveis() no segundo 103
ENTÃO piscar está bloqueada; no segundo 105 volta
```

### CT06: Portabilidade
```
QUANDO micropython companion/sim/fumaca.py
ENTÃO imprime "micropython ok" sem exceção
```

## Decisões Arquiteturais

Ver "Decisões tomadas" acima.

## Fora do Escopo

- Qualquer código na placa, `main.py`, `hw.py`, animações, sons (fases 1 a 3).
- `sensors.py`, `social.py`, `brain_io.py`, `traits.py`, raio-X, portal, `/brain.json` (fases 1 a 6).
- DNA com viés por traço, 9 traços e limites 5-80 (fase 6). A `semente` desta fase só gera pesos aleatórios.
- Gesto do "shh" (fase 2).

## Docs canônicas a atualizar

- [x] `CODEMAP.md` (raiz) — linha do pacote `companion/` no índice
- [x] `CALIBRACAO.md` (raiz, novo)
- [ ] `docs/` — não (é o site)
