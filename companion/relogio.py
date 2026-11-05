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
