# Tasks — Cérebro SNN: humor e comportamento variam com o clima

**Issue:** #4
**Baseado em:** `02-spec.md`
**Total:** 19 tasks, ~1 h de execução e ~15 min de simulação

Convenções: comandos rodam na raiz do repositório. O código destas tasks rodou no planejamento numa cópia de
`companion/` no scratchpad. Resultado: 36 testes OK, `micropython ok 4780 239`, aceite `clima` OK nas 4 sementes,
hábito 6 de 7, sementes [6, 6, 5, 5], silêncio 10,8 → 0,1 sons/h e velocidade 66 s.

---

## FASE A — Clima como sentido e como alvo do humor

### A1. Criar a branch a partir da main
```bash
git status --short            # esperado: "?? firmware/" e "?? sdd/ISSUE_4/" (firmware/ é da issue #1: não mexer)
git switch main && git pull --ff-only && git switch -c feature/sdd-issue-4
```
**Esperado:** `Switched to a new branch 'feature/sdd-issue-4'`.

### A2. Constantes em `companion/config.py`
**Editar:** `companion/config.py:5`. Trocar
```python
N_IN = 100                 # 3. tabela de sentidos (a secao 2 dizia ~80; vale a soma da tabela)
```
por
```python
N_IN = 107                 # 3. tabela de sentidos (100) + clima e temperatura (issue #4)
N_IN_FONTE = 100           # entradas da fonte; as do clima nascem depois (mesma rede para a mesma semente)
```
**Editar:** `companion/config.py:81`. Antes de `# 6. Aprendizado`, inserir:
```python
# Clima (issue #4, companion/clima.py). Por tempo: sol, nublado, chuva, tempestade; None = sem previsao (como antes)
CLIMA_HUMOR = (200, -100, -350, -500)      # alvo do humor x10: ele regride para ca, e nao para 0
CLIMA_PUXA_PCT = 5                         # com previsao, o humor anda tambem esta % da distancia ao alvo por minuto
CLIMA_ENERGIA = (0, 0, -3, -3)             # x10 por minuto acordada, alem de ENERGIA_ACORDADA
CLIMA_CURIOSIDADE = (10, 0, 0, 0)          # x10 por minuto, alem de CURIOSIDADE_MIN
FRIO = 15                                  # graus C: abaixo disso a energia cai mais rapido
FRIO_ENERGIA = -3                          # x10 por minuto acordada

```
**Verificar:** `python3 -c "from companion import config as C; print(C.N_IN, C.N_IN_FONTE, C.CLIMA_HUMOR)"` →
`107 100 (200, -100, -350, -500)` (o import de `encoder` ainda quebra até a A4; aqui só o `config`).

### A3. Criar `companion/clima.py`
**Criar:** `companion/clima.py`
```python
# Clima (issue #4): tipo do tempo (rede.tipo_de) e graus viram indice de tempo e efeito nos drives. Sem float.
from companion import config as C

TEMPOS = ('sol', 'nublado', 'chuva', 'tempestade')
GRUPO = {'sol': 0, 'nublado': 1, 'neblina': 1, 'vento': 1, 'chuva': 2, 'neve': 2, 'tempestade': 3}


def indice(tipo):
    """Nome de rede.tipo_de -> 0..3, ou None sem previsao."""
    return GRUPO.get(tipo) if tipo else None


def efeito(tipo, graus):
    """(alvo do humor, % de puxada, energia/min, curiosidade/min) x10 para este clima."""
    k = indice(tipo)
    if k is None:
        return 0, 0, 0, 0
    e = C.CLIMA_ENERGIA[k]
    if graus is not None and graus < C.FRIO:
        e += C.FRIO_ENERGIA
    return C.CLIMA_HUMOR[k], C.CLIMA_PUXA_PCT, e, C.CLIMA_CURIOSIDADE[k]
```
**Verificar:** `python3 -c "from companion import clima as K; print(K.indice('neve'), K.efeito('sol', 10))"` →
`2 (200, 5, -3, 10)`.

### A4. Grupo `clima` e `temperatura` em `companion/encoder.py`
**Editar:** `companion/encoder.py:5`. Depois de `from companion import config as C`:
```python
from companion import clima as K
```
**Editar:** `companion/encoder.py:7-10`. Trocar o comentário e o fim de `GRUPOS`:
```python
# (nome, primeiro neuronio, quantidade) na ordem da tabela da secao 3; soma = 100
```
por
```python
# (nome, quantidade) na ordem da tabela da secao 3 (soma 100), mais clima e temperatura (issue #4); soma = N_IN
```
e
```python
          ('outra', 3), ('outra_estado', 6), ('novidade', 3), ('drives', 28), ('ultima', 8), ('resposta', 3))
```
por
```python
          ('outra', 3), ('outra_estado', 6), ('novidade', 3), ('drives', 28), ('ultima', 8), ('resposta', 3),
          ('clima', 4), ('temperatura', 3))
```
**Editar:** `companion/encoder.py:84`. Depois de `self.evento('resposta', s.get('resposta'))`, no fim de
`codificar`:
```python
        k = K.indice(s.get('tempo'))               # sem previsao: grupo calado (nenhum sorteio a mais)
        for j in range(4):
            self._bin('clima', j, j == k)
        g = s.get('graus')
        b = BASE['temperatura']
        for j in range(3):
            self.ativ[b + j] = 0
        if g is not None:
            self._pop('temperatura', 3, max(5, min(35, g)), 5, 36)
```
**Verificar:** `python3 -c "from companion.encoder import BASE; print(BASE['clima'], BASE['temperatura'])"` →
`100 104`.

### A5. Linhas do clima sorteadas por último em `companion/snn.py`
**Editar:** `companion/snn.py:8`. Depois de `NI, NH, NE = C.N_IN, C.N_HID, C.N_EXC`:
```python
NF = C.N_IN_FONTE                 # entradas da fonte; as do clima (issue #4) sao sorteadas no fim do __init__
```
**Editar:** `companion/snn.py:26`. No fim da compreensão de `self.w_ih`, trocar `for _ in range(NI * NH)])` por
`for _ in range(NF * NH)])`.

**Editar:** `companion/snn.py:30`. No laço de `OCULTOS_TEMPO`, trocar `for i in range(NI):` por `for i in range(NF):`.

**Editar:** `companion/snn.py:32-33`. Apagar estas duas linhas (elas descem para o fim do `__init__`):
```python
        self.w_ih0 = array('h', self.w_ih)
        self.soma_h = array('i', [sum(self.w_ih[i * NH + h] for i in range(NI)) for h in range(NH)])  # alvo da normalizacao
```
**Editar:** `companion/snn.py:62`. Depois de `self._rk = 0`:
```python
        for _ in range((NI - NF) * NH):            # clima: sorteado por ultimo, a rede da fonte nao muda
            self.w_ih.append((ri(*C.W_IH_INI) if random.getrandbits(7) < 128 * C.IH_FORTES // 100
                              else ri(0, C.W_IH_FRACO)) << C.W_FRAC)
        self.w_ih0 = array('h', self.w_ih)
        self.soma_h = array('i', [sum(self.w_ih[i * NH + h] for i in range(NI)) for h in range(NH)])  # alvo da normalizacao
```
**Verificar:** `python3 -c "from companion.snn import Rede; r = Rede(100, 1); print(len(r.w_ih), len(r.soma_h))"`
→ `10272 96`.

### A6. Humor, energia e curiosidade em `companion/drives.py`
**Editar:** `companion/drives.py:12`. Depois de `self._min = 0`:
```python
        self.clima = (0, 0, 0, 0)          # (alvo do humor, % de puxada, energia, curiosidade), de clima.efeito
```
**Editar:** `companion/drives.py:26-28`. Trocar
```python
        self._soma(C.D_ENERGIA, C.ENERGIA_DORMINDO if self.dormindo else C.ENERGIA_ACORDADA)
        h = d[C.D_HUMOR]
        self._soma(C.D_HUMOR, -min(C.HUMOR_REGRIDE, h) if h > 0 else min(C.HUMOR_REGRIDE, -h))
```
por
```python
        alvo, puxa, energia, curiosidade = self.clima
        self._soma(C.D_ENERGIA, C.ENERGIA_DORMINDO if self.dormindo else C.ENERGIA_ACORDADA + energia)
        h = d[C.D_HUMOR] - alvo                    # regride para o alvo do clima (0 sem previsao)
        p = C.HUMOR_REGRIDE + abs(h) * puxa // 100
        self._soma(C.D_HUMOR, -min(p, h) if h > 0 else min(p, -h))
```
**Editar:** `companion/drives.py:36`. Trocar `self._soma(C.D_CURIOSIDADE, C.CURIOSIDADE_MIN)` por
`self._soma(C.D_CURIOSIDADE, C.CURIOSIDADE_MIN + curiosidade)`.

### A7. O cérebro passa o clima aos drives (`companion/cerebro.py`)
**Editar:** `companion/cerebro.py:11`. Depois de `from companion.relogio import Relogio`:
```python
from companion import clima as K
```
**Editar:** `companion/cerebro.py:124-125`. Trocar
```python
        if seg % 60 == 0:
            d.minuto()
```
por
```python
        if seg % 60 == 0:
            d.clima = K.efeito(s.get('tempo'), s.get('graus'))
            d.minuto()
```

### A8. Criar `companion/testes/test_clima.py`
**Criar:** `companion/testes/test_clima.py`
```python
# Testes da issue #4: clima como sentido e como alvo do humor.
import unittest
from companion import config as C
from companion import clima as K
from companion.drives import Drives
from companion.encoder import Codificador, BASE
from companion.snn import Rede
from companion.cerebro import Cerebro


def sentidos(tempo=None, graus=None):
    return {'minuto': 600, 'fim_semana': 0, 'toques_60s': 0, 'sem_toque': 0, 'orient': 0, 'som_nivel': 0,
            'noite': 0, 'bateria': 80, 'carregando': 0, 'outra': 0, 'outra_estado': 0, 'novidade': 0,
            'drives': [0] * 7, 'ultima': 0, 'tempo': tempo, 'graus': graus}


class TestClima(unittest.TestCase):
    def test_indice(self):
        self.assertEqual([K.indice(t) for t in ('sol', 'nublado', 'neblina', 'vento', 'chuva', 'neve', 'tempestade')],
                         [0, 1, 1, 1, 2, 2, 3])
        self.assertIsNone(K.indice(None))
        self.assertIsNone(K.indice('granizo'))                    # nome desconhecido: sem previsao

    def test_efeito(self):
        self.assertEqual(K.efeito(None, None), (0, 0, 0, 0))
        self.assertEqual(K.efeito('chuva', 20), (C.CLIMA_HUMOR[2], C.CLIMA_PUXA_PCT, C.CLIMA_ENERGIA[2], 0))
        self.assertEqual(K.efeito('sol', 10)[2], C.CLIMA_ENERGIA[0] + C.FRIO_ENERGIA)     # frio cansa

    def test_humor_vai_para_o_alvo(self):
        d = Drives()
        d.clima = K.efeito('chuva', 20)
        for _ in range(40):                             # 40 min: a fome ainda nao passou de 80
            d.minuto()
        self.assertEqual(d.d[C.D_HUMOR], C.CLIMA_HUMOR[2])
        d.clima = K.efeito(None, None)                  # sem previsao: volta a regredir para 0, 1/min
        d.minuto()
        self.assertEqual(d.d[C.D_HUMOR], C.CLIMA_HUMOR[2] + C.HUMOR_REGRIDE)

    def test_puxada_proporcional(self):
        d = Drives()
        d.d[C.D_HUMOR] = 200
        d.clima = K.efeito('chuva', 20)                 # distancia 550: 10 + 550 * 5 // 100 = 37
        d.minuto()
        self.assertEqual(d.d[C.D_HUMOR], 200 - C.HUMOR_REGRIDE - 550 * C.CLIMA_PUXA_PCT // 100)


class TestEntrada(unittest.TestCase):
    def test_neuronios(self):
        c = Codificador()
        c.codificar(sentidos())
        b, t = BASE['clima'], BASE['temperatura']
        self.assertEqual(list(c.ativ[b:b + 7]), [0] * 7)          # sem previsao: grupo calado
        c.codificar(sentidos('chuva', 5))
        self.assertEqual(list(c.ativ[b:b + 4]), [0, 0, 255, 0])
        self.assertEqual(list(c.ativ[t:t + 3]), [255, 0, 0])
        self.assertEqual(t + 3, C.N_IN)

    def test_rede_da_fonte_nao_muda(self):
        r = Rede(100, 1)
        self.assertEqual(len(r.w_ih), C.N_IN * C.N_HID)
        n = C.N_IN_FONTE * C.N_HID
        self.assertEqual(r.w_ih[:n], Rede(100, 1).w_ih[:n])       # sorteio deterministico por semente

    def test_cerebro_le_o_clima(self):
        c = Cerebro(1)
        s = sentidos('tempestade', 20)
        c.segundo(s, 60 * 1000)
        self.assertEqual(c.drives.clima, K.efeito('tempestade', 20))


if __name__ == '__main__':
    unittest.main()
```

### A9. Rodar unitários, fumaça e grep de float
```bash
python3 -m unittest discover -s companion/testes -t . 2>&1 | tail -3
micropython companion/sim/fumaca.py
grep -nE "float|[0-9]\.[0-9]" companion/clima.py companion/drives.py companion/encoder.py companion/snn.py
```
**Esperado:** `Ran 36 tests` / `OK`; `micropython ok 4780 239`; o `grep` só acha comentários (RNF02).

### A10. Commit Fase A
```bash
git add companion/config.py companion/clima.py companion/encoder.py companion/snn.py companion/drives.py \
        companion/cerebro.py companion/testes/test_clima.py sdd/ISSUE_4/
git commit -m "feat(issue-4): fase A - clima como sentido e alvo do humor (#4)"
```

---

## FASE B — Simulador e aceite

### B1. Tempo nos sentidos do `companion/sim/mundo.py`
**Editar:** `companion/sim/mundo.py:3-4`. Trocar
```python
    def __init__(self, dia_semana=0):
        self.dia0 = dia_semana
```
por
```python
    def __init__(self, dia_semana=0, tempos=None):
        self.dia0 = dia_semana
        self.tempos = tempos            # issue #4: (tipo, graus) por dia, repetido em ciclo; None = sem previsao
```
**Editar:** `companion/sim/mundo.py:16`. Depois de `recente = self.toques and self.toques[-1] == seg`:
```python
        tipo, graus = self.tempos[(seg // 86400) % len(self.tempos)] if self.tempos else (None, None)
```
**Editar:** `companion/sim/mundo.py:22`. Depois da linha `'outra': 0, 'outra_estado': 0, 'novidade': 0, 'comida': comida,`:
```python
            'tempo': tipo, 'graus': graus, 'wifi': 1 if tipo else 0,
```

### B2. `tempos` e `humor` em `companion/sim/rodar.py`
**Editar:** `companion/sim/rodar.py:29`. Trocar a linha do `def` por:
```python
def simular(dono, dias, semente=1, inicio_h=6, falante=0, tempos=None, humor=None):
    """tempos: (tipo, graus) por dia, em ciclo (issue #4). humor: lista que recebe (segundo, humor x10) por minuto."""
```
**Editar:** `companion/sim/rodar.py:34`. Trocar `mundo = Mundo()` por `mundo = Mundo(tempos=tempos)`.

**Editar:** `companion/sim/rodar.py:54`. Antes de `antes = len(cer.log)`:
```python
        if humor is not None and seg % 60 == 0:
            humor.append((seg, cer.drives.d[C.D_HUMOR]))
```

### B3. Aceite `clima` em `companion/sim/aceite.py`
**Editar:** `companion/sim/aceite.py:1`. Trocar `[velocidade|silencio|habito|sementes|todos]` por
`[velocidade|silencio|habito|sementes|clima|todos]`.

**Editar:** `companion/sim/aceite.py:9`. Depois de `LIMITE_SEMANA_S = 180 ...`:
```python
TEMPOS_CHUVA = (('chuva', 18), ('sol', 25))        # issue #4: dias alternados, 3 de cada em 6 dias
TRISTES = tuple(A.INDICE[n] for n in ('bico', 'bravinha', 'lagrimazinha', 'resmungar', 'emburrar', 'suspirar'))
```
**Editar:** `companion/sim/aceite.py:58`. Antes de `if __name__ == '__main__':`:
```python
def dias_clima(semente):
    """Humor medio (pontos) e acoes tristes por hora, das 8h as 22h, nos dias de chuva e de sol."""
    humor = []
    cer, acoes = simular(CENARIOS['semana'](), 6, semente, tempos=TEMPOS_CHUVA, humor=humor)
    soma = {'chuva': [0, 0, 0], 'sol': [0, 0, 0]}      # humor x10 somado, minutos, acoes tristes
    for dia in range(6):
        a, b = dia * 86400 + 8 * 3600, dia * 86400 + 22 * 3600
        t = soma[TEMPOS_CHUVA[dia % 2][0]]
        hs = [h for s, h in humor if a <= s < b]
        t[0] += sum(hs)
        t[1] += len(hs)
        t[2] += sum(1 for s, x in acoes if a <= s < b and x in TRISTES)
    return {k: (v[0] / v[1] / 10, v[2] / (3 * 14)) for k, v in soma.items()}


def clima():
    """Issue #4: sementes 1 a 4; chuva com humor >= 30 pontos abaixo do sol e o dobro de acoes tristes (>= 0,3/h)."""
    ok = True
    for semente in (1, 2, 3, 4):
        r = dias_clima(semente)
        (hc, tc), (hs, ts) = r['chuva'], r['sol']
        bom = hc <= hs - 30 and tc >= 0.3 and tc >= 2 * ts
        ok = ok and bom
        print('clima semente %d: humor chuva %+.1f sol %+.1f; tristes/h chuva %.2f sol %.2f %s' % (
            semente, hc, hs, tc, ts, 'ok' if bom else '-'))
    return ok


```
**Editar:** a linha `testes = {...}` em `__main__` vira:
```python
    testes = {'velocidade': velocidade, 'silencio': silencio, 'habito': habito, 'sementes': sementes,
              'clima': clima}
```

### B4. CT01 — clima
```bash
python3 -m companion.sim.aceite clima
```
**Esperado** (~3 min 20 s):
```
clima semente 1: humor chuva -37.1 sol +17.9; tristes/h chuva 1.19 sol 0.00 ok
clima semente 2: humor chuva -36.5 sol +18.3; tristes/h chuva 1.00 sol 0.02 ok
clima semente 3: humor chuva -36.8 sol +18.6; tristes/h chuva 0.52 sol 0.00 ok
clima semente 4: humor chuva -37.3 sol +17.9; tristes/h chuva 1.45 sol 0.02 ok
ACEITE OK
```

### B5. CT02 — sem regressão
```bash
python3 -m companion.sim.aceite habito | tail -2 & python3 -m companion.sim.aceite sementes | tail -2 & \
python3 -m companion.sim.aceite silencio & python3 -m companion.sim.aceite velocidade & wait
```
**Esperado:** `habito: 6 de 7 dias`, `sementes: [6, 6, 5, 5]`, silêncio `10.8 ... 0.1 sons/h no dia 3`, velocidade
`<= 180 s` (planejamento: 66 s), todos com `ACEITE OK`.

**Se B4 ou B5 falhar**, calibrar um botão por vez (`python3 -m companion.sim.aceite clima NOME=valor`; as tuplas
se editam em `config.py`). Regra de parada: 6 tentativas sem passar → gate arquitetural (`/sdd-execute` Etapa 3).

| Botão | Valores | Efeito medido no planejamento |
|---|---|---|
| `CLIMA_PUXA_PCT` | 0 / 5 / 10 | 0 não separa chuva de sol (tristes 0,62 × 0,64); 10 dá o mesmo que 5 |
| `CLIMA_HUMOR[2]` (chuva) | −350 / −500 | −350 libera `bico`, `resmungar`, `bravinha` e `emburrar`; mais baixo libera `lagrimazinha` |
| `CLIMA_HUMOR[0]` (sol) | 100 / 200 | 200 zera as tristes no sol |

### B6. Commit Fase B
```bash
git add companion/sim/mundo.py companion/sim/rodar.py companion/sim/aceite.py
git commit -m "feat(issue-4): fase B - clima no simulador e aceite (#4)"
```

---

## FASE C — Documentação

### C1. `CALIBRACAO.md`
**Editar:** `CALIBRACAO.md`. No fim do arquivo, acrescentar:
```markdown

## Clima (issue #4, 2026-11)

O clima entra como sentido (grupo `clima`, 4 binários, e `temperatura`, 3 em população; `N_IN` 100 → 107) e como
alvo do humor. Planejamento e execução: `sdd/ISSUE_4/`.

| Mudança | Constante | Por quê (medido) |
|---|---|---|
| Com previsão, o humor regride para o alvo do clima, `1 + 5 % da distância` por minuto | `CLIMA_HUMOR=(200, -100, -350, -500)`, `CLIMA_PUXA_PCT=5` | Só o alvo, a 1/min, não aparece: as recompensas mantêm o humor abaixo dos dois alvos (tristes/h 0,62 na chuva × 0,64 no sol) |
| Chuva e tempestade cansam; frio também | `CLIMA_ENERGIA=(0, 0, -3, -3)`, `FRIO=15`, `FRIO_ENERGIA=-3` | Pedido na issue; sem regra fixa de sono |
| Sol dá curiosidade | `CLIMA_CURIOSIDADE=(10, 0, 0, 0)` | Pedido na issue |

Resultado (sementes 1 a 4, chuva 18 °C × sol 25 °C, das 8h às 22h): humor −37 na chuva e +18 no sol; ações tristes
0,5 a 1,45/h na chuva e 0 a 0,02/h no sol.

As 7 linhas novas de `w_ih` são sorteadas no fim do `Rede.__init__`, e a rede da fonte nasce igual. Mesmo sem clima,
os aceites antigos mudam de número: hábito 5 → 6 dias e sementes [5, 5, 5, 6] → [6, 6, 5, 5]; silêncio 12,0 → 10,8
sons/h no começo. O motivo é a sequência aleatória deslocada e a normalização da entrada, que soma as linhas do clima.
```
(Os números ficam os medidos em B4 e B5; se forem outros, usar os da execução.)

### C2. `CODEMAP.md`
**Editar:** `CODEMAP.md:16`. Na linha do `companion/`, trocar `` `relogio` (hora → saída, issue #3), `cerebro`; `` por
`` `relogio` (hora → saída, issue #3), `clima` (tempo lá fora → alvo do humor, issue #4), `cerebro`; ``.

**Editar:** `CODEMAP.md:43-44`. Trocar
```markdown
  (velocidade, silêncio, hábito e `sementes`, ~7 min).
```
por
```markdown
  (velocidade, silêncio, hábito, `sementes` e `clima`, ~11 min).
```
**Editar:** `CODEMAP.md`, seção "Cérebro SNN", depois da linha `- **Entrada:** ...` (o parágrafo de 2 linhas),
acrescentar:
```markdown
- **Clima:** os sentidos aceitam `tempo` (nome de `rede.tipo_de`, ou `None` sem previsão) e `graus` (inteiro). Na
  fase 1, o `main.py` passa `rede.tipo_de(rede.wx(epoch))` quando `wx` não é `None`.
```

### C3. Commit Fase C
```bash
git add CALIBRACAO.md CODEMAP.md
git commit -m "docs(issue-4): fase C - CALIBRACAO e CODEMAP (#4)"
```

---

## Depois das fases

Review, `04-acceptance.md`, merge e fechamento seguem o `/sdd-execute` (Etapas 4 a 7). Comando final antes do merge:
`python3 -m companion.sim.aceite todos` → `ACEITE OK` (~11 min).
