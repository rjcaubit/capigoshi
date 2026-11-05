# Tasks — Cérebro SNN: aprender o horário dos hábitos

**Issue:** #3
**Baseado em:** `02-spec.md`
**Total:** 19 tasks, ~1 h de execução e ~12 min de simulação

Convenções: comandos rodam na raiz do repositório. O código destas tasks foi rodado no planejamento, numa cópia
de `companion/` no scratchpad. Resultado: 29 testes OK, `micropython ok`, hábito 5 de 7, sementes [5, 5, 5, 6],
silêncio 12,0 → 0,1 sons/h e velocidade 68 s.

---

## FASE A — Via hora → saída

### A1. Criar a branch a partir da main
```bash
git status --short            # esperado: "?? firmware/" e "?? sdd/ISSUE_3/" (firmware/ é da issue #1: não mexer)
git switch main && git pull --ff-only && git switch -c feature/sdd-issue-3
```
**Esperado:** `Switched to a new branch 'feature/sdd-issue-3'`.

### A2. Constantes novas em `companion/config.py`
**Editar:** `companion/config.py:66-69`. Logo depois do `)` que fecha `DIRETO`, acrescentar:
```python
# Solidao (issue #3): afeto abaixo do limiar empurra pedir_carinho; e o que faz a Capi explorar ate achar a hora
SOLIDAO = (D_AFETO, 200, 'pedir_carinho', 1000)

# Via hora -> saida (issue #3, companion/relogio.py)
RELOGIO_BINS = 72          # celulas de 20 min
RELOGIO_K_POS = 24         # dw = eta * R * K, premio
RELOGIO_K = 8              # castigo
RELOGIO_MAX = 1500         # |peso| maximo (corrente por tick)
MARCA_K = 1                # castigo atrasado nos ocultos marcados: dw = eta * R * MARCA_K >> 2
```
**Verificar:** `python3 -c "from companion import config as C; print(C.RELOGIO_BINS, C.SOLIDAO)"` →
`72 (4, 200, 'pedir_carinho', 1000)`.

### A3. Criar `companion/relogio.py`
**Criar:** `companion/relogio.py`
```python
# Via direta hora -> saida (issue #3): RELOGIO_BINS celulas de tempo ligadas a todas as saidas, ao lado da rede.
# A corrente interpola as duas celulas vizinhas do minuto; o aprendizado credita o minuto em que a acao comecou,
# entao o castigo atrasado (ignorado em 60 s) tambem conta. Sem float.
from array import array
from companion import config as C

NB = C.RELOGIO_BINS
PASSO = 1440 // NB


def celulas(minuto):
    """(celula, vizinha, quanto da vizinha 0..PASSO-1) do minuto do dia."""
    b, f = divmod(minuto % 1440, PASSO)
    return b, (b + 1) % NB, f


class Relogio:
    def __init__(self, n_saidas):
        self.no = n_saidas
        self.w = array('h', [0] * (NB * n_saidas))     # [celula * no + o], -RELOGIO_MAX..RELOGIO_MAX

    def corrente(self, minuto, dire):
        """Soma em dire[o] a corrente de cada saida neste minuto."""
        b, b1, f = celulas(minuto)
        no, w = self.no, self.w
        p, q = b * no, b1 * no
        for o in range(no):
            x = w[p + o] * (PASSO - f) + w[q + o] * f
            if x:
                dire[o] += x // PASSO

    def recompensa(self, R, acao, minuto, eta):
        """Premio pesa RELOGIO_K_POS e castigo RELOGIO_K: um carinho na hora certa vale mais que um pedido ignorado."""
        b, b1, f = celulas(minuto)
        d = eta * R * (C.RELOGIO_K_POS if R > 0 else C.RELOGIO_K)
        m, no, w = C.RELOGIO_MAX, self.no, self.w
        for c, frac in ((b, PASSO - f), (b1, f)):
            k = c * no + acao
            x = w[k] + d * frac // PASSO
            w[k] = m if x > m else (-m if x < -m else x)

    def esquecer(self):
        """Uma vez por dia (6.5): ESQUECE_PCT de volta a zero, ao menos 1."""
        w = self.w
        for k in range(len(w)):
            x = w[k]
            if x:
                p = (abs(x) * C.ESQUECE_PCT + 99) // 100
                w[k] = x - p if x > 0 else x + p
```
**Verificar:**
`python3 -c "from companion.relogio import celulas; print(celulas(1140), celulas(1430))"` → `(57, 58, 0) (71, 0, 10)`.

### A4. Criar `companion/testes/test_habito.py`
**Criar:** `companion/testes/test_habito.py`
```python
# Testes da issue #3: via hora -> saida, marca do castigo atrasado e solidao.
import unittest
from array import array
from companion import config as C
from companion import actions as A
from companion.relogio import Relogio, celulas
from companion.cerebro import Cerebro

PC = A.INDICE['pedir_carinho']


class TestRelogio(unittest.TestCase):
    def test_celulas(self):
        self.assertEqual(celulas(19 * 60), (57, 58, 0))
        self.assertEqual(celulas(19 * 60 + 5), (57, 58, 5))
        self.assertEqual(celulas(23 * 60 + 50), (71, 0, 10))       # meia-noite fecha o circulo

    def test_premio_na_hora_certa(self):
        r = Relogio(A.N_ACOES)
        r.recompensa(10, PC, 19 * 60, 4)                            # 4 * 10 * 24 = 960, todo na celula 57
        self.assertEqual(r.w[57 * A.N_ACOES + PC], 960)
        self.assertEqual(r.w[58 * A.N_ACOES + PC], 0)
        d = array('h', [0] * A.N_ACOES)
        r.corrente(19 * 60, d)
        self.assertEqual(d[PC], 960)
        d[PC] = 0
        r.corrente(19 * 60 + 10, d)                                 # meio caminho para a celula 58
        self.assertEqual(d[PC], 480)
        d[PC] = 0
        r.corrente(10 * 60, d)
        self.assertEqual(d[PC], 0)

    def test_castigo_e_limite(self):
        r = Relogio(A.N_ACOES)
        r.recompensa(-5, PC, 10 * 60 + 5, 4)                        # 4 * -5 * 8 = -160: 3/4 na 30, 1/4 na 31
        self.assertEqual(r.w[30 * A.N_ACOES + PC], -120)
        self.assertEqual(r.w[31 * A.N_ACOES + PC], -40)
        for _ in range(50):
            r.recompensa(-5, PC, 10 * 60, 4)
        self.assertEqual(r.w[30 * A.N_ACOES + PC], -C.RELOGIO_MAX)

    def test_esquecer(self):
        r = Relogio(A.N_ACOES)
        r.w[0], r.w[1], r.w[2] = 1000, -50, 0
        r.esquecer()
        self.assertEqual((r.w[0], r.w[1], r.w[2]), (990, -49, 0))


class TestMarca(unittest.TestCase):
    def test_castigo_atrasado_so_nos_marcados(self):
        c = Cerebro(1)
        apr, r, no = c.apr, c.rede, A.N_ACOES
        apr.marcas[PC] = (0, 1)
        antes = [r.w_ho[h * no + PC] for h in range(3)]
        apr.recompensa_atrasada(-5, PC, 4)                          # (4 * -5 * 1) >> 2 = -5
        self.assertEqual(r.w_ho[0 * no + PC], max(apr.pisos[PC], antes[0] - 5))
        self.assertEqual(r.w_ho[1 * no + PC], max(apr.pisos[PC], antes[1] - 5))
        self.assertEqual(r.w_ho[2 * no + PC], antes[2])
        piscar = A.INDICE['piscar']                                 # CT05: sem marca, nada muda
        coluna = [r.w_ho[h * no + piscar] for h in range(C.N_EXC)]
        apr.recompensa_atrasada(-6, piscar, 4)
        self.assertEqual([r.w_ho[h * no + piscar] for h in range(C.N_EXC)], coluna)

    def test_ignorado_usa_minuto_do_inicio(self):
        c = Cerebro(1)
        c.minuto = 10 * 60
        c._executar(PC, {'minuto': 10 * 60}, 36000 * 1000)
        self.assertIn(PC, c.apr.marcas)
        c.minuto = 10 * 60 + 1                                      # o ignorado chega 60 s depois
        c._aplicar(-5, PC, 'ignorado', 36060 * 1000)
        self.assertLess(c.relogio.w[30 * A.N_ACOES + PC], 0)


class TestSolidao(unittest.TestCase):
    def _corrente(self, afeto):
        c = Cerebro(1)
        c.drives.d[C.D_AFETO] = afeto
        s = {'minuto': 600, 'fim_semana': 0, 'toques_60s': 0, 'sem_toque': 0, 'orient': 0, 'som_nivel': 0,
             'noite': 0, 'bateria': 80, 'carregando': 0, 'outra': 0, 'outra_estado': 0, 'novidade': 0}
        c._decidir(s, 600 * 60 * 1000)
        return c.rede.direto[PC]

    def test_solidao(self):
        self.assertEqual(self._corrente(100), C.SOLIDAO[3])
        self.assertEqual(self._corrente(500), 0)


if __name__ == '__main__':
    unittest.main()
```
**Verificar:** `python3 -m unittest companion.testes.test_habito.TestRelogio` → `Ran 4 tests ... OK`. As classes
`TestMarca` e `TestSolidao` falham até a fase B, e isso é esperado.

### A5. Commit Fase A
```bash
git add companion/config.py companion/relogio.py companion/testes/test_habito.py sdd/ISSUE_3/
git commit -m "feat(issue-3): fase A - via hora -> saida (relogio) com testes (#3)"
```

---

## FASE B — Marca, solidão e ligação no cérebro

### B1. Marca em `companion/learn.py`
**Editar:** `companion/learn.py:18`. Depois de `self.t_decai = 0 ...`, acrescentar:
```python
        self.marcas = {}                           # acao -> ocultos excitatorios ativos quando ela comecou
```
**Editar:** `companion/learn.py:104`. Antes de `def homeostase(self):`, inserir:
```python
    def marcar(self, acao):
        """Guarda os ocultos excitatorios dos ultimos RECENTE ticks. O castigo atrasado (ignorado, 60 s) chega
        quando a elegibilidade ja zerou; sem a marca, a rede nunca aprende a parar de pedir."""
        r = self.rede
        self.marcas[acao] = tuple(h for h in r.recentes(r.rec_h) if h < NE)

    def recompensa_atrasada(self, R, acao, eta):
        """R vai para a coluna da acao, so nos ocultos marcados quando ela comecou."""
        hs = self.marcas.get(acao)
        if not hs:
            return
        no, w, piso = self.rede.no, self.rede.w_ho, self.pisos[acao]
        d = (eta * R * C.MARCA_K) >> 2
        for h in hs:
            k = h * no + acao
            x = w[k] + d
            w[k] = C.W_MAX if x > C.W_MAX else (piso if x < piso else x)

```
**Verificar:** `python3 -c "import companion.learn"` sem erro.

### B2. Import e constante em `companion/cerebro.py`
**Editar:** `companion/cerebro.py:10`. Depois de `from companion.reward import Recompensa`:
```python
from companion.relogio import Relogio
```
**Editar:** `companion/cerebro.py:14`. Depois de `ACORDAR = A.INDICE['acordar']`:
```python
ATRASADOS = ('ignorado', 'som_sem_resposta')      # chegam depois que a elegibilidade zerou
```

### B3. Estado novo em `Cerebro.__init__`
**Editar:** `companion/cerebro.py:28`. Depois da linha `self.direto_idx = ...`:
```python
        self.solidao = (C.SOLIDAO[0], C.SOLIDAO[1], A.INDICE[C.SOLIDAO[2]], C.SOLIDAO[3])
        self.relogio = Relogio(A.N_ACOES)
        self.minuto = 0                            # minuto do dia do ultimo segundo()
        self.min_acao = array('H', [0] * A.N_ACOES)   # minuto em que cada acao comecou (credito do relogio)
```

### B4. Recompensa em `_aplicar`
**Editar:** `companion/cerebro.py:72`. Trocar
```python
        self.apr.recompensa(R, acao, self.eta())
```
por
```python
        eta = self.eta()
        self.apr.recompensa(R, acao, eta)
        if motivo in ATRASADOS:
            self.apr.recompensa_atrasada(R, acao, eta)
        self.relogio.recompensa(R, acao, self.min_acao[acao], eta)
```

### B5. Minuto e esquecimento em `segundo`
**Editar:** `companion/cerebro.py:110`. Depois de `self.idade_s += 1`:
```python
        self.minuto = s['minuto']
```
**Editar:** `companion/cerebro.py:118`. Depois de `self.apr.esquecer()`, no mesmo nível:
```python
            self.relogio.esquecer()
```

### B6. Corrente do relógio e da solidão em `_decidir`
**Editar:** `companion/cerebro.py:154-156`. Trocar
```python
        for di, lim, o, corr in self.direto_idx:
            if d.d[di] > lim:
                dire[o] = corr
```
por
```python
        self.relogio.corrente(self.minuto, dire)
        for di, lim, o, corr in self.direto_idx:  # sobrescreve o relogio (somar piorou o habito na calibracao)
            if d.d[di] > lim:
                dire[o] = corr
        di, lim, o, corr = self.solidao
        if d.d[di] < lim:
            dire[o] += corr
```

### B7. Minuto de início e marca em `_executar`
**Editar:** `companion/cerebro.py:179`. Depois de `self.ultima = acao`:
```python
        self.min_acao[acao] = self.minuto
        if acao in A.PEDIDOS:
            self.apr.marcar(acao)
```

### B8. Rodar unitários e fumaça
```bash
python3 -m unittest discover -s companion/testes -t . 2>&1 | tail -3
micropython companion/sim/fumaca.py
grep -nE "float|[0-9]\.[0-9]" companion/relogio.py companion/learn.py companion/cerebro.py
```
**Esperado:** `Ran 29 tests` / `OK`; `micropython ok ...`; o `grep` só acha comentários e docstrings, nenhuma
conta com float (RNF02).

### B9. Commit Fase B
```bash
git add companion/learn.py companion/cerebro.py
git commit -m "feat(issue-3): fase B - marca do castigo atrasado, solidao e relogio no cerebro (#3)"
```

---

## FASE C — Aceites

### C1. `dias_habito` e `sementes` em `companion/sim/aceite.py`
**Editar:** `companion/sim/aceite.py:1`. Trocar o comentário por:
```python
# Testes de aceite da fase 0 (secao 11). Uso: python3 -m companion.sim.aceite [velocidade|silencio|habito|sementes|todos]
```
**Editar:** a função `habito(semente=1)` inteira (de `def habito(semente=1):` até `return bons >= 5`) vira:
```python
def dias_habito(semente):
    cer, acoes = simular(CENARIOS['habito'](), 7, semente)
    bons = 0
    for dia in range(7):
        base = dia * 86400
        j0, j1 = base + 18 * 3600 + 50 * 60, base + 19 * 3600 + 10 * 60
        na_janela = sum(1 for s, a in acoes if j0 <= s < j1 and a in ALVO_HABITO)
        fora = sum(1 for s, a in acoes if base + 8 * 3600 <= s < base + 22 * 3600 and not j0 <= s < j1
                   and a in ALVO_HABITO)
        taxa_j, taxa_f = na_janela * 3.0, fora / (14 - 1 / 3)
        ok = na_janela >= 1 and taxa_j >= 2 * taxa_f
        bons += ok
        print('habito dia %d: %.1f/h na janela 18h50-19h10, %.1f/h fora %s' % (dia + 1, taxa_j, taxa_f,
                                                                               'ok' if ok else '-'))
    return bons


def habito():
    bons = dias_habito(1)
    print('habito: %d de 7 dias (meta 5)' % bons)
    return bons >= 5


def sementes():
    """Robustez do habito (issue #3): sementes 1 a 4, media >= 5 dias e nenhuma abaixo de 4."""
    dias = [dias_habito(s) for s in (1, 2, 3, 4)]
    print('sementes: %s dias, media %.2f (meta media >= 5, minimo >= 4)' % (dias, sum(dias) / 4))
    return sum(dias) >= 20 and min(dias) >= 4
```
**Editar:** a linha `testes = {...}` em `__main__` vira:
```python
    testes = {'velocidade': velocidade, 'silencio': silencio, 'habito': habito, 'sementes': sementes}
```

### C2. CT01 — hábito
```bash
python3 -m companion.sim.aceite habito
```
**Esperado:** `habito: 5 de 7 dias (meta 5)` (planejamento: 5) e `ACEITE OK`. Leva ~1 min.

### C3. CT02 — sementes
```bash
python3 -m companion.sim.aceite sementes | tail -2
```
**Esperado:** `sementes: [5, 5, 5, 6] dias, media 5.25 ...` e `ACEITE OK`. Leva ~4 min.

### C4. CT03 — sem regressão
```bash
python3 -m companion.sim.aceite silencio & python3 -m companion.sim.aceite velocidade & wait
```
**Esperado:** silêncio `12.0 sons/h ... 0.1 sons/h no dia 3` e velocidade `<= 180 s` (planejamento: 68 s), as
duas com `ACEITE OK`.

**Se C2 ou C3 falhar** (por exemplo, um número diferente do planejamento por ordem de operações), a calibração usa
estes botões, um de cada vez, com `python3 -m companion.sim.aceite sementes NOME=valor`. Regra de parada: 6
tentativas sem passar → gate arquitetural (`/sdd-execute` Etapa 3).

| Botão | Valor | Efeito medido no planejamento |
|---|---|---|
| `RELOGIO_K` | 4 / 8 | 8 suprime mais os pedidos fora da janela |
| `RELOGIO_K_POS` | 12 / 24 | 24: dois dias a mais que 12 |
| `RELOGIO_MAX` | 600 / 1500 | 1500 deixa o castigo vencer a solidão |
| `SOLIDAO` (corrente) | 450 / 700 / 1000 | abaixo de 1000 a Capi quase não explora |
| `MARCA_K` | 0 / 1 / 2 | 2 cala os pedidos também às 19h |

(`SOLIDAO` é tupla: para variar a corrente, editar o 4º valor em `config.py` em vez de usar `NOME=valor`.)

### C5. Commit Fase C
```bash
git add companion/sim/aceite.py
git commit -m "feat(issue-3): fase C - aceite do habito por semente e robustez (#3)"
```

---

## FASE D — Documentação

### D1. `CALIBRACAO.md`
**Editar:** `CALIBRACAO.md`. Trocar a seção `## Hábito — não resolvido` inteira (até o fim do arquivo) por:
```markdown
## Hábito (issue #3, 2026-11)

Resolvido com três acréscimos à fonte. Planejamento e execução: `sdd/ISSUE_3/`.

| Acréscimo | Constante | Por quê (medido) |
|---|---|---|
| Via hora → saída: 72 células de 20 min ligadas às 100 saídas, crédito no minuto em que a ação começou | `RELOGIO_BINS=72`, `RELOGIO_K_POS=24`, `RELOGIO_K=8`, `RELOGIO_MAX=1500` | A camada oculta não separa 19h de 17h ou 21h (8 neurônios de 3 h); 13 configurações na #2 deram 0 a 2 dias |
| Marca: ocultos ativos quando um pedido começa recebem o castigo atrasado | `MARCA_K=1` | O "ignorado" chega em 60 s e a elegibilidade zera em ~16 s: a rede nunca aprendia a parar de pedir (9 pedidos/h às 3h) |
| Solidão: afeto < 20 soma corrente em `pedir_carinho` | `SOLIDAO=(D_AFETO, 200, 'pedir_carinho', 1000)` | Sem exploração a Capi não pede às 19h e não descobre o hábito |

Resultado: hábito 5 de 7 dias (semente 1); sementes 1 a 4: [5, 5, 5, 6]. Silêncio e velocidade continuam passando.
Na semana normal (3 dias) a Capi pede menos: `pedir_carinho` 498 → 246, `pedir_comida` 544 → 70.

A ligação direta (`DIRETO`) continua sobrescrevendo a corrente do relógio: somar deu 4 dias na semente 1.
O CT03 da #2 tinha a tabela das 13 tentativas sem o relógio; ela continua no histórico do git (commit `01932af`).
```
(Os números ficam os medidos em C2 e C3; se forem outros, usar os da execução.)

### D2. `CODEMAP.md`
**Editar:** `CODEMAP.md:16`. Na linha do `companion/`, trocar
`` `encoder`, `snn`, `learn`, `drives`, `reward`, `cerebro`; `` por
`` `encoder`, `snn`, `learn`, `drives`, `reward`, `relogio` (hora → saída, issue #3), `cerebro`; ``.

**Editar:** `CODEMAP.md:43`. A linha dos testes vira:
```markdown
- **Testes:** `python3 -m unittest discover -s companion/testes -t .` e `python3 -m companion.sim.aceite todos`
  (velocidade, silêncio, hábito e `sementes`, ~7 min).
```

### D3. `sdd/ISSUE_2/04-acceptance.md`
**Editar:** a seção `## Pendente` vira:
```markdown
## Pendente

- CT03 (hábito): resolvido na issue #3 (`sdd/ISSUE_3/04-acceptance.md`).
```

### D4. Commit Fase D
```bash
git add CALIBRACAO.md CODEMAP.md sdd/ISSUE_2/04-acceptance.md
git commit -m "docs(issue-3): fase D - CALIBRACAO, CODEMAP e pendencia da #2 (#3)"
```

---

## Depois das fases

Review, doc-sync, `04-acceptance.md`, merge e fechamento seguem o `/sdd-execute` (Etapas 4 a 7). Comando final
antes do merge: `python3 -m companion.sim.aceite todos` → `ACEITE OK` (~7 min).
