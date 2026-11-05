# Rede LIF em inteiros (secao 2): entrada -> oculta (densa), oculta -> oculta (esparsa, CSR),
# oculta excitatoria -> saida (densa) e inibicao lateral fixa entre saidas. Sem float.
import random
from array import array
from companion import config as C
from companion.encoder import BASE

NI, NH, NE = C.N_IN, C.N_HID, C.N_EXC
NF = C.N_IN_FONTE                 # entradas da fonte; as do clima (issue #4) sao sorteadas no fim do __init__
RECENTE = 16                      # ticks guardados para o STDP (alem disso o traco ja nao muda peso)

# traco pre/pos: 255 * (15/16)^dt, zero a partir de RECENTE (6.1: decai 1/16 por tick)
TRACO = array('H', [0] * (RECENTE + 1))
_x = 255 << 8
for _d in range(RECENTE):
    TRACO[_d] = _x >> 8
    _x -= _x >> C.TRACO_SHIFT


class Rede:
    def __init__(self, n_saidas, semente):
        random.seed(semente)
        ri = random.randint
        self.no = no = n_saidas
        self.t = 0
        self.w_ih = array('h', [(ri(*C.W_IH_INI) if random.getrandbits(7) < 128 * C.IH_FORTES // 100
                                 else ri(0, C.W_IH_FRACO)) << C.W_FRAC for _ in range(NF * NH)])  # [i * NH + h], x16
        self.w_ho = array('h', [ri(*C.W_HO_INI) for _ in range(NE * no)])     # [h * no + o]
        tempo = [BASE[g] + k for g, n in (('hora', 8), ('dia', 2), ('luz', 2)) for k in range(n)]
        for h in range(C.OCULTOS_TEMPO):
            for i in range(NF):
                self.w_ih[i * NH + h] = (C.W_MAX << C.W_FRAC) if i in tempo else 0
        self.w_ho0 = array('h', self.w_ho)
        ini, pos, w = array('H', [0] * (NH + 1)), array('H'), array('h')
        for h in range(NH):
            ini[h] = len(pos)
            for k in range(NH):
                if k != h and random.getrandbits(7) < 128 * (C.HH_DENS if h < NE else C.HH_DENS_INIB) // 100:
                    pos.append(k)
                    w.append(ri(*C.W_HH_EXC) if h < NE else -ri(*C.W_HH_INIB))
        ini[NH] = len(pos)
        self.hh_ini, self.hh_pos, self.hh_w = ini, pos, w
        self.v_h = array('i', [C.V_REST] * NH)
        self.v_o = array('i', [C.V_REST] * no)
        self.ref_h = array('B', [0] * NH)
        self.ref_o = array('B', [0] * no)
        self.th_h = array('i', [C.V_TH] * NH)
        self.cnt_h = array('H', [0] * NH)        # spikes desde a ultima homeostase (6.5)
        self.ult_in = array('i', [-RECENTE] * NI)
        self.ult_h = array('i', [-RECENTE] * NH)
        self.ult_o = array('i', [-RECENTE] * no)
        self.spk_in = array('H', [0] * NI)
        self.n_in = 0
        self.spk_h = []                            # spikes ocultos deste tick
        self.spk_o = []                            # spikes de saida deste tick
        self.rec_in, self.rec_h, self.rec_o = [[] for _ in range(RECENTE)], [[] for _ in range(RECENTE)], \
            [[] for _ in range(RECENTE)]
        self.direto = array('h', [0] * no)        # corrente fixa drive -> saida
        self.ruido = C.NOISE
        self._rtab = array('h', [ri(-C.NOISE, C.NOISE) for _ in range(1024)])
        self._rk = 0
        for _ in range((NI - NF) * NH):            # clima: sorteado por ultimo, a rede da fonte nao muda
            self.w_ih.append((ri(*C.W_IH_INI) if random.getrandbits(7) < 128 * C.IH_FORTES // 100
                              else ri(0, C.W_IH_FRACO)) << C.W_FRAC)
        for h in range(C.OCULTOS_TEMPO):          # ocultos de tempo tambem nao ouvem o clima
            for i in range(NF, NI):
                self.w_ih[i * NH + h] = 0
        self.w_ih0 = array('h', self.w_ih)
        self.soma_h = array('i', [sum(self.w_ih[i * NH + h] for i in range(NI)) for h in range(NH)])  # alvo da normalizacao
        self.contagem = array('H', [0] * no)

    def novo_ruido(self, amplitude):
        self.ruido = amplitude
        ri = random.randint
        for k in range(1024):
            self._rtab[k] = ri(-amplitude, amplitude)

    def passo(self, cod, mascara):
        """Um tick de 50 ms. cod: Codificador; mascara[o] = 0 deixa a saida o calada."""
        t = self.t = self.t + 1
        n_in = self.n_in = cod.spikes(self.spk_in)
        spk_in, ult_in = self.spk_in, self.ult_in
        I = [0] * NH
        w_ih = self.w_ih
        for k in range(n_in):
            i = spk_in[k]
            ult_in[i] = t
            b = i * NH
            for h in range(NH):
                I[h] += w_ih[b + h]
        ini, pos, whh = self.hh_ini, self.hh_pos, self.hh_w
        for h in self.spk_h:                      # recorrencia: spikes ocultos do tick anterior
            for k in range(ini[h], ini[h + 1]):
                I[pos[k]] += whh[k] << C.W_FRAC
        rt, rk = self._rtab, self._rk + random.getrandbits(4)
        v, ref, th, cnt, ult_h = self.v_h, self.ref_h, self.th_h, self.cnt_h, self.ult_h
        spk_h = []
        for h in range(NH):
            if ref[h]:
                ref[h] -= 1
                continue
            vv = v[h]
            vv += (I[h] >> (C.I_SCALE + C.W_FRAC)) - ((vv - C.V_REST) >> C.TAU_SHIFT) + rt[(rk + h) & 1023]
            if vv >= th[h]:
                vv = C.V_RESET
                ref[h] = C.REFRAC
                cnt[h] += 1
                ult_h[h] = t
                spk_h.append(h)
            v[h] = vv
        no = self.no
        J = [0] * no
        w_ho = self.w_ho
        for h in spk_h:
            if h < NE:
                b = h * no
                for o in range(no):
                    J[o] += w_ho[b + o]
        lat = C.LATERAL * len(self.spk_o)
        v, ref, ult_o, cont, dire = self.v_o, self.ref_o, self.ult_o, self.contagem, self.direto
        anteriores = self.spk_o
        spk_o = []
        rk += NH
        for o in range(no):
            if not mascara[o]:
                v[o] = C.V_REST
                continue
            if ref[o]:
                ref[o] -= 1
                continue
            vv = v[o]
            inib = lat - C.LATERAL if o in anteriores else lat
            vv += J[o] * C.I_OUT_MUL + dire[o] - inib - ((vv - C.V_REST) >> C.TAU_SHIFT) + rt[(rk + o) & 1023]
            if vv >= C.V_TH:
                vv = C.V_RESET
                ref[o] = C.REFRAC
                ult_o[o] = t
                cont[o] += 1
                spk_o.append(o)
            v[o] = vv
        self._rk = rk & 1023
        self.spk_h, self.spk_o = spk_h, spk_o
        s = t % RECENTE
        self.rec_in[s] = [spk_in[k] for k in range(n_in)]
        self.rec_h[s] = spk_h
        self.rec_o[s] = spk_o

    def zerar_contagem(self):
        c = self.contagem
        for o in range(self.no):
            c[o] = 0

    def recentes(self, rec):
        """Indices que dispararam nos ultimos RECENTE ticks (sem repeticao)."""
        vistos = set()
        for lista in rec:
            vistos.update(lista)
        return vistos
