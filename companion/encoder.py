# Sentidos -> neuronios de entrada (secao 3). Valores continuos: codificacao por populacao com curva em tenda
# (aproxima a gaussiana sem tabela). Eventos: rajada de RAJADA spikes num neuronio dedicado.
import random
from array import array
from companion import config as C
from companion import clima as K

# (nome, quantidade) na ordem da tabela da secao 3 (soma 100), mais clima e temperatura (issue #4); soma = N_IN
GRUPOS = (('hora', 8), ('dia', 2), ('toque_reg', 4), ('toque_tipo', 4), ('toque_freq', 4), ('sem_toque', 6),
          ('mov', 4), ('orient', 3), ('som_nivel', 4), ('som_evento', 3), ('luz', 2), ('bateria', 5),
          ('outra', 3), ('outra_estado', 6), ('novidade', 3), ('drives', 28), ('ultima', 8), ('resposta', 3),
          ('clima', 4), ('temperatura', 3))
BASE = {}
_b = 0
for _n, _q in GRUPOS:
    BASE[_n] = _b
    _b += _q
assert _b == C.N_IN


def _log2(x):
    n = 0
    while x > 1:
        x >>= 1
        n += 1
    return n


class Codificador:
    def __init__(self):
        self.ativ = array('H', [0] * C.N_IN)     # 0..255, vale ate o proximo codificar()
        self.rajada = array('B', [0] * C.N_IN)
        self.p_max = array('H', [C.P_MAX_HORA if i < 8 else C.P_MAX for i in range(C.N_IN)])  # 'hora' = 0..7

    def _pop(self, grupo, n, x, lo, hi, circular=False):
        b = BASE[grupo]
        passo = (hi - lo) // (n if circular else n - 1)
        for k in range(n):
            c = lo + k * passo
            d = abs(x - c)
            if circular and d > (hi - lo) // 2:
                d = (hi - lo) - d
            self.ativ[b + k] = 255 * (passo - d) // passo if d < passo else 0

    def _bin(self, grupo, k, ligado):
        self.ativ[BASE[grupo] + k] = 255 if ligado else 0

    def evento(self, grupo, k):
        if k is not None and k >= 0:
            self.rajada[BASE[grupo] + k] = C.RAJADA

    def codificar(self, s):
        """s: dicionario de sentidos (ver sim/mundo.py). Chamado uma vez por segundo."""
        self._pop('hora', 8, s['minuto'], 0, 1440, True)
        self._bin('dia', 0, not s['fim_semana'])
        self._bin('dia', 1, s['fim_semana'])
        self.evento('toque_reg', s.get('toque_reg'))
        self.evento('toque_tipo', s.get('toque_tipo'))
        self._pop('toque_freq', 4, min(s['toques_60s'], 20), 0, 21)
        self._pop('sem_toque', 6, min(_log2(s['sem_toque'] + 1), 14), 0, 15)
        self.evento('mov', s.get('mov'))
        self._pop('orient', 3, s['orient'], 0, 3)
        self._pop('som_nivel', 4, s['som_nivel'], 0, 101)
        self.evento('som_evento', s.get('som_evento'))
        self._bin('luz', 0, not s['noite'])
        self._bin('luz', 1, s['noite'])
        b = BASE['bateria']
        for k in range(4):
            c = k * 33
            d = abs(s['bateria'] - c)
            self.ativ[b + k] = 255 * (33 - d) // 33 if d < 33 else 0
        self.ativ[b + 4] = 255 if s['carregando'] else 0
        self._pop('outra', 3, s['outra'], 0, 3)
        for k in range(6):
            if s['outra_estado'] >> k & 1:
                self.evento('outra_estado', k)
        self._pop('novidade', 3, s['novidade'], 0, 101)
        for i, v in enumerate(s['drives']):           # 0..100 (humor ja mapeado de -100..100)
            b = BASE['drives'] + 4 * i
            for k in range(4):
                d = abs(v - k * 33)
                self.ativ[b + k] = 255 * (33 - d) // 33 if d < 33 else 0
        h = (s['ultima'] * 37) & 255
        for k in range(8):
            self._bin('ultima', k, h >> k & 1)
        self.evento('resposta', s.get('resposta'))
        k = K.indice(s.get('tempo'))               # sem previsao: grupo calado (nenhum sorteio a mais)
        for j in range(4):
            self._bin('clima', j, j == k)
        g = s.get('graus')
        b = BASE['temperatura']
        for j in range(3):
            self.ativ[b + j] = 0
        if g is not None:
            self._pop('temperatura', 3, max(5, min(35, int(g))), 5, 36)   # int: rede.clima['temp'] e float

    def spikes(self, saida):
        """Sorteia os spikes deste tick; devolve quantos entraram em saida (lista de indices)."""
        n = 0
        ativ, raj, pm = self.ativ, self.rajada, self.p_max
        lim = random.getrandbits
        for i in range(C.N_IN):
            if raj[i]:
                raj[i] -= 1
                saida[n] = i
                n += 1
            elif ativ[i] and lim(8) < (ativ[i] * pm[i]) >> 8:
                saida[n] = i
                n += 1
        return n
