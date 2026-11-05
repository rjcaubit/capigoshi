# Lacos quentes da rede e do aprendizado, em Python puro: e o que roda no CPython (simulador e testes). Na placa,
# companion/nucleo_viper.py troca estas funcoes pela mesma conta em codigo de maquina (@micropython.viper: o tick
# caiu de ~16 ms para ~3 ms). Os dois dao o mesmo resultado, inteiro por inteiro.
# Arrays: w_ih, w_ho, rt e dire 'h'; I, J, v, th e ult 'i'; spk, cnt e contagem 'H'; ref, mascara e ant 'B'.
import sys
from companion import config as C

SH_H = C.I_SCALE + C.W_FRAC
TAU = C.TAU_SHIFT
V_REST, V_RESET, V_TH, REFRAC = C.V_REST, C.V_RESET, C.V_TH, C.REFRAC
I_OUT_MUL, LATERAL = C.I_OUT_MUL, C.LATERAL
A_PLUS, A_MINUS, STDP_SHIFT = C.A_PLUS, C.A_MINUS, C.STDP_SHIFT
WM = C.W_MAX << C.W_FRAC
ELIG_MUL, ELIG_SHIFT = C.ELIG_MUL, C.ELIG_SHIFT
RECENTE = 16                      # ticks em que o traco ainda mexe no peso (snn.RECENTE vem daqui)


def soma_ih(I, w, spk, n, nh):
    for h in range(nh):
        I[h] = 0
    for k in range(n):
        b = spk[k] * nh
        for h in range(nh):
            I[h] += w[b + h]

def oculta(I, v, ref, th, cnt, ult, rt, out, rk, t, nh):
    n = 0
    for h in range(nh):
        if ref[h]:
            ref[h] -= 1
            continue
        vv = v[h]
        vv += (I[h] >> SH_H) - ((vv - V_REST) >> TAU) + rt[(rk + h) & 1023]
        if vv >= th[h]:
            vv = V_RESET
            ref[h] = REFRAC
            cnt[h] += 1
            ult[h] = t
            out[n] = h
            n += 1
        v[h] = vv
    return n

def soma_ho(J, w, spk, n, no, ne):
    for o in range(no):
        J[o] = 0
    for k in range(n):
        h = spk[k]
        if h < ne:
            b = h * no
            for o in range(no):
                J[o] += w[b + o]

def saida(J, v, ref, ult, cont, dire, masc, rt, ant, out, rk, t, lat, no):
    n = 0
    for o in range(no):
        if not masc[o]:
            v[o] = V_REST
            continue
        if ref[o]:
            ref[o] -= 1
            continue
        inib = lat - LATERAL if ant[o] else lat
        vv = v[o]
        vv += J[o] * I_OUT_MUL + dire[o] - inib - ((vv - V_REST) >> TAU) + rt[(rk + o) & 1023]
        if vv >= V_TH:
            vv = V_RESET
            ref[o] = REFRAC
            ult[o] = t
            cont[o] += 1
            out[n] = o
            n += 1
        v[o] = vv
    return n

def potenciar(w, pi, px, np, spk, ns, nh):
    for j in range(ns):
        h = spk[j]
        for q in range(np):
            k = pi[q] * nh + h
            w[k] += (A_PLUS * px[q] * (WM - w[k])) >> STDP_SHIFT

def deprimir(w, spk, n, ph, px, np, nh):
    for k in range(n):
        b = spk[k] * nh
        for q in range(np):
            i = b + ph[q]
            w[i] -= (A_MINUS * px[q] * w[i]) >> STDP_SHIFT

def normalizar(w, alvo, ni, nh):
    for h in range(nh):
        s = 0
        for i in range(ni):
            s += w[i * nh + h]
        if s:
            a = alvo[h]
            for i in range(ni):
                k = i * nh + h
                x = w[k] * a // s
                w[k] = WM if x > WM else x


def recentes(ult, n, t, minimo, traco, qi, qx):
    """Indices 0..n-1 que dispararam ha dt ticks, minimo <= dt < RECENTE; qx recebe traco[dt]. Devolve quantos."""
    c = 0
    for i in range(n):
        dt = t - ult[i]
        if minimo <= dt < RECENTE:
            qi[c] = i
            qx[c] = traco[dt]
            c += 1
    return c


def elig_sobe(e, qi, qx, n, o, no):
    for q in range(n):
        e[qi[q] * no + o] += (A_PLUS * qx[q]) >> 1


def decair_col(e, o, no, ne, n):
    """Decaimento de n passos na coluna o da elegibilidade; devolve 1 se sobrou algo diferente de zero."""
    vivo = 0
    for h in range(ne):
        k = h * no + o
        x = e[k]
        if x:
            if n > 20:
                x = 0
            else:
                for _ in range(n):
                    x -= (x * ELIG_MUL) >> ELIG_SHIFT
                    if -8 < x < 8:
                        x = 0
                        break
            e[k] = x
            if x:
                vivo = 1
    return vivo


PY = (soma_ih, oculta, soma_ho, saida, potenciar, deprimir, normalizar, recentes, elig_sobe, decair_col)

VIPER = False
if sys.implementation.name == 'micropython':
    try:
        from companion.nucleo_viper import (soma_ih, oculta, soma_ho, saida, potenciar, deprimir, normalizar,
                                            recentes, elig_sobe, decair_col)
        VIPER = True
    except (ImportError, SyntaxError):         # MicroPython sem o emissor viper: fica a versao em Python
        pass
