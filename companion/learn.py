# Aprendizado (secao 6): STDP entrada -> oculta, elegibilidade + R-STDP oculta -> saida,
# normalizacao, limiar adaptativo e esquecimento. Saida -> saida e oculta -> oculta sao fixas.
from array import array
from companion import config as C
from companion.snn import TRACO, RECENTE

NI, NH, NE = C.N_IN, C.N_HID, C.N_EXC


class Aprendizado:
    def __init__(self, rede, pisos):
        """pisos[o]: menor peso permitido na coluna o (PISO_SOCIAL para Social e Fisiologica, senao 0)."""
        self.rede = rede
        no = rede.no
        self.e = array('i', [0] * (NE * no))     # elegibilidade [h * no + o]
        self.ativas = set()                        # colunas com elegibilidade diferente de zero
        self.pisos = pisos
        self.t_decai = 0                           # ultimo tick em que a elegibilidade decaiu

    def passo(self):
        """Depois de rede.passo(): STDP na entrada e elegibilidade na saida."""
        r = self.rede
        t = r.t
        w = r.w_ih
        wm = C.W_MAX << C.W_FRAC
        if r.spk_h:                                # pos disparou: potencia quem veio antes (limite suave)
            ult = r.ult_in
            pre = [(i, TRACO[t - ult[i]]) for i in r.recentes(r.rec_in) if t - ult[i] < RECENTE]
            for h in r.spk_h:
                for i, x in pre:
                    k = i * NH + h
                    w[k] += (C.A_PLUS * x * (wm - w[k])) >> C.STDP_SHIFT
        if r.n_in:                                 # pre disparou: deprime quem disparou antes
            ult = r.ult_h
            pos = [(h, TRACO[t - ult[h]]) for h in r.recentes(r.rec_h) if 0 < t - ult[h] < RECENTE]
            if pos:
                for k in range(r.n_in):
                    b = r.spk_in[k] * NH
                    for h, x in pos:
                        w[b + h] -= (C.A_MINUS * x * w[b + h]) >> C.STDP_SHIFT
        no, e = r.no, self.e
        if r.spk_o:                                # saida disparou: elegibilidade sobe nos ocultos recentes
            ult = r.ult_h
            pre = [h for h in r.recentes(r.rec_h) if h < NE]
            for o in r.spk_o:
                self.ativas.add(o)
                for h in pre:
                    dt = t - ult[h]
                    if dt < RECENTE:
                        e[h * no + o] += (C.A_PLUS * TRACO[dt]) >> 1
        if r.spk_h and self.ativas:                # oculto disparou depois da saida: elegibilidade desce
            ult = r.ult_o
            for o in self.ativas:
                dt = t - ult[o]
                if 0 < dt < RECENTE:
                    d = (C.A_MINUS * TRACO[dt]) >> 1
                    for h in r.spk_h:
                        if h < NE:
                            e[h * no + o] -= d
        if t - self.t_decai >= C.ELIG_PASSO:
            self.decair(t)

    def decair(self, t):
        """Aplica o decaimento acumulado desde t_decai (6.2), so nas colunas ativas."""
        n = (t - self.t_decai) // C.ELIG_PASSO
        if n <= 0:
            return
        self.t_decai += n * C.ELIG_PASSO
        no, e = self.rede.no, self.e
        mortas = []
        for o in self.ativas:
            vivo = False
            for h in range(NE):
                k = h * no + o
                x = e[k]
                if x:
                    if n > 20:
                        x = 0
                    else:
                        for _ in range(n):
                            x -= (x * C.ELIG_MUL) >> C.ELIG_SHIFT
                            if -8 < x < 8:
                                x = 0
                                break
                    e[k] = x
                    vivo = vivo or x != 0
            if not vivo:
                mortas.append(o)
        for o in mortas:
            self.ativas.discard(o)

    def recompensa(self, R, acao, eta):
        """R-STDP (6.2): dw = eta * R * e >> R_SHIFT, so na coluna da acao executada."""
        r = self.rede
        self.decair(r.t)
        no, e, w = r.no, self.e, r.w_ho
        piso = self.pisos[acao]
        for h in range(NE):
            k = h * no + acao
            if e[k]:
                x = w[k] + ((eta * R * e[k]) >> C.R_SHIFT)
                w[k] = C.W_MAX if x > C.W_MAX else (piso if x < piso else x)

    def homeostase(self):
        """A cada NORM_TICKS (6.5): normaliza a entrada de cada oculto e ajusta o limiar."""
        r = self.rede
        w = r.w_ih
        for h in range(NH):
            s = 0
            for i in range(NI):
                s += w[i * NH + h]
            if s:
                for i in range(NI):
                    k = i * NH + h
                    w[k] = w[k] * r.soma_h[h] // s
            c = r.cnt_h[h]
            if c * 100 > C.LIMIAR_ALTO * C.NORM_TICKS:
                r.th_h[h] = min(C.TH_MAX, r.th_h[h] + r.th_h[h] * C.LIMIAR_PASSO // 100)
            elif c * 100 < C.LIMIAR_BAIXO * C.NORM_TICKS:
                r.th_h[h] = max(C.TH_MIN, r.th_h[h] - r.th_h[h] * C.LIMIAR_PASSO // 100)
            r.cnt_h[h] = 0

    def esquecer(self):
        """Uma vez por dia (6.5): pesos plasticos andam 1% de volta ao valor de nascenca."""
        r = self.rede
        for w, w0 in ((r.w_ih, r.w_ih0), (r.w_ho, r.w_ho0)):
            for k in range(len(w)):
                d = w0[k] - w[k]
                w[k] += d * C.ESQUECE_PCT // 100 if d > 0 else -((-d) * C.ESQUECE_PCT // 100)
