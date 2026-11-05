# Aprendizado (secao 6): STDP entrada -> oculta, elegibilidade + R-STDP oculta -> saida,
# normalizacao, limiar adaptativo e esquecimento. Saida -> saida e oculta -> oculta sao fixas.
from array import array
from companion import config as C
from companion.snn import TRACO, RECENTE
from companion import nucleo as N

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
        self.marcas = {}                           # acao -> ocultos excitatorios ativos quando ela comecou
        self._qi = array('H', [0] * max(NI, NH))   # buffers do nucleo: indice e traco dos recentes
        self._qx = array('H', [0] * max(NI, NH))
        self._bh = array('H', [0] * NH)

    def passo(self):
        """Depois de rede.passo(): STDP na entrada e elegibilidade na saida."""
        r = self.rede
        t = r.t
        if t - self.t_decai >= C.ELIG_PASSO:      # decai antes de somar: trava longa nao zera o que entra agora
            self.decair(t)
        w, qi, qx = r.w_ih, self._qi, self._qx
        if r.spk_h:                                # pos disparou: potencia quem veio antes (limite suave)
            n = N.recentes(r.ult_in, NI, t, 0, TRACO, qi, qx)
            bh = self._bh
            for j, h in enumerate(r.spk_h):
                bh[j] = h
            N.potenciar(w, qi, qx, n, bh, len(r.spk_h), NH)
        if r.n_in:                                 # pre disparou: deprime quem disparou antes
            n = N.recentes(r.ult_h, NH, t, 1, TRACO, qi, qx)
            if n:
                N.deprimir(w, r.spk_in, r.n_in, qi, qx, n, NH)
        no, e = r.no, self.e
        if r.spk_o:                                # saida disparou: elegibilidade sobe nos ocultos recentes
            n = N.recentes(r.ult_h, NE, t, 0, TRACO, qi, qx)
            for o in r.spk_o:
                self.ativas.add(o)
                N.elig_sobe(e, qi, qx, n, o, no)
        if r.spk_h and self.ativas:                # oculto disparou depois da saida: elegibilidade desce
            ult = r.ult_o
            for o in self.ativas:
                dt = t - ult[o]
                if 0 < dt < RECENTE:
                    d = (C.A_MINUS * TRACO[dt]) >> 1
                    for h in r.spk_h:
                        if h < NE:
                            e[h * no + o] -= d

    def decair(self, t):
        """Aplica o decaimento acumulado desde t_decai (6.2), so nas colunas ativas."""
        n = (t - self.t_decai) // C.ELIG_PASSO
        if n <= 0:
            return
        self.t_decai += n * C.ELIG_PASSO
        no, e = self.rede.no, self.e
        mortas = [o for o in self.ativas if not N.decair_col(e, o, no, NE, n)]
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

    def marcar(self, acao):
        """Guarda os ocultos excitatorios dos ultimos RECENTE ticks. O castigo atrasado (ignorado, 60 s) chega
        quando a elegibilidade ja zerou; sem a marca, a rede nunca aprende a parar de pedir."""
        r = self.rede
        t, ult = r.t, r.ult_h
        self.marcas[acao] = tuple(h for h in range(NE) if t - ult[h] < RECENTE)

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

    def homeostase(self):
        """A cada NORM_TICKS (6.5): normaliza a entrada de cada oculto e ajusta o limiar."""
        r = self.rede
        N.normalizar(r.w_ih, r.soma_h, NI, NH)
        for h in range(NH):
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
                if d:                              # arredonda para longe de zero: anda ao menos 1 por dia
                    passo = (abs(d) * C.ESQUECE_PCT + 99) // 100
                    w[k] += passo if d > 0 else -passo
