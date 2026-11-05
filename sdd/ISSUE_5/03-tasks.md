# Tasks — Raio-X do cérebro (etapa 1, simulador)

**Issue:** #5
**Baseado em:** `02-spec.md`
**Total:** 17 tasks, cerca de 45 min de execução mais 11 min dos aceites

**Convenções:**
- Os comandos rodam na raiz do repositório.
- Todo o código abaixo rodou no planejamento numa cópia de `companion/`:
  - 45 testes OK;
  - `micropython ok 4780 239 1300`;
  - `E2E OK` (23 checagens).
- Os arquivos longos estão prontos em `sdd/ISSUE_5/prototipo/` e são copiados como estão.
- A pasta `firmware/`, não rastreada, é da issue #1: não mexer nela.

---

## FASE A — O cérebro guarda e resume o que sabe

### A1. Criar a branch
```bash
git status --short            # esperado: "?? firmware/" e "?? sdd/ISSUE_5/"
git switch main && git pull --ff-only && git switch -c feature/sdd-issue-5
```
**Esperado:** `Switched to a new branch 'feature/sdd-issue-5'`.

### A2. Constantes em `companion/config.py`
**Editar:** `companion/config.py:110`. Antes de `# 6.3 Recompensas`, inserir:
```python
# Raio-X (issue #5, Cerebro.resumo e companion/raiox.html)
RAIOX_RECS = 200           # 10. ultimas recompensas guardadas
RAIOX_HORAS = 48           # drives de hora em hora (o simulador aumenta para cobrir todos os dias)
RAIOX_TOP = 10             # tamanho das listas (mais feitas, gosta, evita)
RAIOX_HABITO = 200         # |peso| do relogio a partir do qual a celula conta como habito

```
**Verificar:**
```bash
python3 -c "from companion import config as C; print(C.RAIOX_RECS, C.RAIOX_HABITO)"
```
Esperado: `200 200`.

### A3. Estado do raio-X no `Cerebro.__init__`
**Editar:** `companion/cerebro.py:42`. Depois de `self.ticks_rodados = 0`, inserir:
```python
        self.agora_s = 0                           # raio-X (issue #5): segundo do ultimo segundo()
        self.tempo, self.graus = None, None        # ultima previsao recebida
        self.recs = []                             # (s, acao, R, motivo), as ultimas RAIOX_RECS
        self.horas = []                            # drives x10 de hora em hora, as ultimas RAIOX_HORAS
        self.vezes = array('I', [0] * A.N_ACOES)       # decisoes de cada acao desde a meia-noite
        self.vezes_ontem = array('I', [0] * A.N_ACOES)
```

### A4. Guardar as recompensas em `_aplicar`
**Editar:** `companion/cerebro.py:89`. Depois de `self.log.append(('R', agora_ms // 1000, acao, R, motivo))`, inserir:
```python
        self.recs.append((agora_ms // 1000, acao, R, motivo))
        if len(self.recs) > C.RAIOX_RECS:
            del self.recs[0]
```

### A5. Clima, horas e virada do dia em `segundo`
**Editar:** `companion/cerebro.py:123-132`. Trocar
```python
        seg = agora_ms // 1000
        d = self.drives
        if seg % 60 == 0:
            d.clima = K.efeito(s.get('tempo'), s.get('graus'))
            d.minuto()
```
por
```python
        seg = self.agora_s = agora_ms // 1000
        d = self.drives
        if seg % 60 == 0:
            self.tempo, self.graus = s.get('tempo'), s.get('graus')
            d.clima = K.efeito(self.tempo, self.graus)
            d.minuto()
        if seg % 3600 == 0:
            self.horas.append(list(d.d))
            if len(self.horas) > C.RAIOX_HORAS:
                del self.horas[0]
```
E, logo abaixo, trocar
```python
            self.apr.esquecer()
            self.relogio.esquecer()
```
por
```python
            self.apr.esquecer()
            self.relogio.esquecer()
            for o in range(A.N_ACOES):
                self.vezes_ontem[o] = self.vezes[o]
                self.vezes[o] = 0
```

### A6. Contar as decisões em `_executar`
**Editar:** o fim de `_executar` (`companion/cerebro.py:203`). Trocar
```python
        self.log.append(('A', seg, acao))
        return acao
```
por
```python
        self.log.append(('A', seg, acao))
        self.vezes[acao] += 1
        return acao
```

### A7. `Cerebro.resumo()`
**Editar:** o fim de `companion/cerebro.py`, depois de `_executar`. Acrescentar:
```python

    # ---- raio-X (issue #5)
    def resumo(self):
        """O que o cerebro sabe agora, so com int, str, None, list e dict (vira JSON). Nao muda estado."""
        d, r = self.drives, self.rede
        no, ne, top = r.no, C.N_EXC, C.RAIOX_TOP
        nome = [a[0] for a in A.CATALOGO]
        delta = [0] * no                           # oculta->saida: quanto cada acao ganhou desde que nasceu
        w, w0 = r.w_ho, r.w_ho0
        for h in range(ne):
            b = h * no
            for o in range(no):
                delta[o] += w[b + o] - w0[b + o]
        ordem = sorted(range(no), key=lambda o: delta[o])
        habitos, evitas = [], []                   # [celula, acao, peso] do relogio, o mais forte de cada celula
        rw = self.relogio.w
        for c in range(C.RELOGIO_BINS):
            b = c * no
            mx = mn = 0
            for o in range(no):
                if rw[b + o] > rw[b + mx]:
                    mx = o
                if rw[b + o] < rw[b + mn]:
                    mn = o
            if rw[b + mx] >= C.RAIOX_HABITO:
                habitos.append([c, nome[mx], rw[b + mx]])
            if rw[b + mn] <= -C.RAIOX_HABITO:
                evitas.append([c, nome[mn], rw[b + mn]])
        mudou = nasceu = 0                         # entrada->oculta: % que o STDP mexeu
        for k in range(len(r.w_ih)):
            mudou += abs(r.w_ih[k] - r.w_ih0[k])
            nasceu += r.w_ih0[k]
        th = sorted(r.th_h)

        def mais(v):
            o = sorted(range(no), key=lambda i: -v[i])[:top]
            return [[nome[i], v[i]] for i in o if v[i]]

        return {
            'versao': 1, 'semente': self.semente, 'idade_s': self.idade_s, 'agora_s': self.agora_s,
            'minuto': self.minuto, 'acao': nome[self.acoes.atual], 'dormindo': d.dormindo,
            'drives': [[C.DRIVES[i], d.d[i]] for i in range(7)],
            'clima': {'tempo': self.tempo, 'graus': None if self.graus is None else int(self.graus),
                      'alvo': d.clima[0]},
            'hoje': mais(self.vezes), 'ontem': mais(self.vezes_ontem),
            'gosta': [[nome[o], delta[o]] for o in reversed(ordem[-top:]) if delta[o] > 0],
            'evita': [[nome[o], delta[o]] for o in ordem[:top] if delta[o] < 0],
            'relogio': {'passo_min': 1440 // C.RELOGIO_BINS, 'max': C.RELOGIO_MAX, 'habitos': habitos,
                        'evita': evitas},
            'recompensas': [[s, nome[a], R, m] for s, a, R, m in self.recs],
            'horas': [list(x) for x in self.horas],
            'rede': {'eta': self.eta(), 'ruido': r.ruido, 'ticks': self.ticks_rodados,
                     'ih_mudou_pct': mudou * 100 // nasceu if nasceu else 0,
                     'limiar': [th[0], th[len(th) // 2], th[-1]]},
        }
```
**Verificar:**
```bash
python3 -c "
from companion.sim.rodar import simular; from companion.sim.dono import Dono
c,_=simular(Dono(),1/24); r=c.resumo(); print(sorted(r), r['idade_s'])"
```
Esperado: as 17 chaves e `3600`.

### A8. Testes
```bash
cp sdd/ISSUE_5/prototipo/test_raiox.py companion/testes/test_raiox.py
python3 -m unittest companion.testes.test_raiox 2>&1 | tail -3
```
**Esperado:** `Ran 9 tests` e `OK`. O `test_pagina_embute_o_resumo` só passa depois da B2; até lá, erro de import em
`companion.sim.raiox` é o esperado. Rode de novo depois da B2.

### A9. Fumaça do MicroPython com o resumo
**Substituir** `companion/sim/fumaca.py` por:
```python
# Fumaca de portabilidade: roda 1 h simulada no MicroPython unix. Uso: micropython companion/sim/fumaca.py
import sys
sys.path.insert(0, '.')
import json
from companion.sim import rodar
from companion.sim.dono import Dono

cer, acoes = rodar.simular(Dono(), 1 / 24)
print('micropython ok', cer.ticks_rodados, len(acoes), len(json.dumps(cer.resumo())))
```
**Verificar:**
```bash
micropython companion/sim/fumaca.py
```
Esperado: `micropython ok 4780 239 1300`.

### A10. Commit da fase A
```bash
git add companion/config.py companion/cerebro.py companion/sim/fumaca.py companion/testes/test_raiox.py
git commit -m "feat(issue-5): fase A - Cerebro.resumo e estado do raio-X (#5)"
```

---

## FASE B — Página e gerador

### B1. A página-modelo
```bash
cp sdd/ISSUE_5/prototipo/raiox.html companion/raiox.html
wc -c companion/raiox.html; grep -c "/\*DADOS\*/null" companion/raiox.html; grep -o "https\?://[^'\"]*" companion/raiox.html | sort -u
```
**Esperado:**
- `wc -c`: abaixo de 20000 (o protótipo tem 16340);
- `grep -c`: `1`;
- endereços: só `http://www.w3.org/2000/svg`.

### B2. O gerador
```bash
cp sdd/ISSUE_5/prototipo/raiox.py companion/sim/raiox.py
python3 -m unittest companion.testes.test_raiox 2>&1 | tail -1
```
**Esperado:** `OK`, com os 9 testes.

### B3. Saída fora do git
**Editar:** `.gitignore`. Depois do bloco `# Saidas da previa e estado salvo pelos testes`, acrescentar:
```
companion/sim/saida/
```
**Verificar:** depois da B4, `git status --short` não deve listar `companion/sim/saida/`.

### B4. Gerar as páginas
```bash
python3 -m companion.sim.raiox semana 3 2 chuva
python3 -m companion.sim.raiox habito 7 1
```
**Esperado:**
- **Primeiro comando:** termina com `pagina: .../companion/sim/saida/raiox-semana-2-chuva.html`, com hábitos de
  `adivinha_a_mao` e de `pedir_comida`.
- **Segundo comando:** cerca de 1 min. Mostra `habito 19h00: pedir_carinho (1453)` e uma lista "evita" que começa
  por `pedir_carinho -3095`.

### B5. Commit da fase B
```bash
git add companion/raiox.html companion/sim/raiox.py .gitignore
git commit -m "feat(issue-5): fase B - pagina do raio-X e gerador no simulador (#5)"
```

---

## FASE C — E2E, aceites e documentação

### C1. E2E click-by-click (CT07)
```bash
python3 sdd/ISSUE_5/prototipo/e2e.py companion/sim/saida/raiox-semana-2-chuva.html companion/raiox.html \
  load-tests/results/issue-5-journey
```
**Esperado:**
- 23 linhas `ok` e `E2E OK`;
- 11 capturas: de `01-light-pagina.png` a `05`, de `07-dark-pagina.png` a `11`, e `13-vazio.png`.

Abra `01-light-pagina.png` e `07-dark-pagina.png` e confira com os olhos três coisas: nenhum rótulo sobreposto, o
relógio redondo, e o ponto da hora de agora no lugar certo (às 05h59 ele fica à direita, perto das 6h).

### C2. README das capturas
**Criar:** `load-tests/results/issue-5-journey/README.md`
```markdown
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

Bugs encontrados: nenhum.
```

### C3. Suíte inteira e portabilidade
```bash
python3 -m unittest discover -s companion/testes -t . 2>&1 | tail -3
micropython companion/sim/fumaca.py
```
**Esperado:** `Ran 45 tests` com `OK`, e `micropython ok 4780 239 1300`.

### C4. Aceites antigos (RNF06)
```bash
time python3 -m companion.sim.aceite todos
```
**Esperado:** em cerca de 11 min, `ACEITE OK`, com os números da issue #4:
- hábito 6 de 7;
- sementes [6, 6, 5, 5];
- silêncio 10,8 → 0,1 sons/h;
- `clima` OK nas 4 sementes.

Se algum número mudar, o `resumo()` ou os contadores mexeram na decisão. Nesse caso, pare e rode o
`test_resumo_nao_muda_o_cerebro`.

### C5. CODEMAP
**Editar:** a linha `companion/` do índice em `CODEMAP.md`.
- Trocar `` | `companion/` | ~1450 | `` por `` | `companion/` | ~1530 | ``. O `main.py` também tem `~1450`; não mexa nele.
- Trocar `` `cerebro`; `sim/` simulador e aceites `` por
  `` `cerebro` (com `resumo()`, issue #5), `raiox.html` (página do raio-X); `sim/` simulador, aceites e `raiox` ``.

**Editar:** a seção `## Cérebro SNN (companion/)`. Depois do item **Clima**, acrescentar:
```markdown
- **Raio-X (issue #5):** `Cerebro.resumo()` devolve um dict só com tipos simples (vira JSON): vontades, hábitos do
  relógio, mais feitas hoje e ontem, gosta e evita (`w_ho − w_ho0`), as últimas 200 recompensas e os drives de hora
  em hora. Não muda a decisão. `python3 -m companion.sim.raiox [cenario] [dias] [semente] [chuva]` grava
  `companion/sim/saida/raiox-*.html` (fora do git). A página `companion/raiox.html` não usa nada de fora; sem dados
  embutidos, ela pede `brain.json`, que é o que o `portal.py` vai servir na etapa 2.
```
**Verificar:**
```bash
grep -n "raiox" CODEMAP.md
```
Esperado: 2 linhas ou mais.

### C6. Commit da fase C
```bash
git add load-tests/results/issue-5-journey CODEMAP.md
git commit -m "docs(issue-5): fase C - E2E do raio-X e CODEMAP (#5)"
```
