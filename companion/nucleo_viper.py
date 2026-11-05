# Os lacos de companion/nucleo.py em @micropython.viper (codigo de maquina). So o nucleo importa, e so no
# MicroPython: se o firmware nao tiver o emissor viper (o MicroPython unix do Mac ARM nao tem), nem compila e o
# nucleo fica com a versao em Python. Mesma conta, inteiro por inteiro; ptr16 le sem sinal, por isso o "& 0x8000".
import micropython
from companion.nucleo import SH_H, TAU, V_REST, V_RESET, V_TH, REFRAC, I_OUT_MUL, LATERAL, A_PLUS, A_MINUS, \
    STDP_SHIFT, WM, ELIG_MUL, ELIG_SHIFT, RECENTE


@micropython.viper
def soma_ih(I: ptr32, w: ptr16, spk: ptr16, n: int, nh: int):
    for h in range(nh):
        I[h] = 0
    for k in range(n):
        b = int(spk[k]) * nh
        for h in range(nh):
            x = int(w[b + h])
            if x & 0x8000:
                x -= 0x10000
            I[h] = I[h] + x


@micropython.viper
def oculta(I: ptr32, v: ptr32, ref: ptr8, th: ptr32, cnt: ptr16, ult: ptr32, rt: ptr16, out: ptr16,
           rk: int, t: int, nh: int) -> int:
    sh = int(SH_H)
    tau = int(TAU)
    rest = int(V_REST)
    reset = int(V_RESET)
    refrac = int(REFRAC)
    n = 0
    for h in range(nh):
        if ref[h]:
            ref[h] = ref[h] - 1
            continue
        r = int(rt[(rk + h) & 1023])
        if r & 0x8000:
            r -= 0x10000
        vv = v[h]
        vv += (I[h] >> sh) - ((vv - rest) >> tau) + r
        if vv >= th[h]:
            vv = reset
            ref[h] = refrac
            cnt[h] = cnt[h] + 1
            ult[h] = t
            out[n] = h
            n += 1
        v[h] = vv
    return n


@micropython.viper
def soma_ho(J: ptr32, w: ptr16, spk: ptr16, n: int, no: int, ne: int):
    for o in range(no):
        J[o] = 0
    for k in range(n):
        h = int(spk[k])
        if h < ne:
            b = h * no
            for o in range(no):
                x = int(w[b + o])
                if x & 0x8000:
                    x -= 0x10000
                J[o] = J[o] + x


@micropython.viper
def saida(J: ptr32, v: ptr32, ref: ptr8, ult: ptr32, cont: ptr16, dire: ptr16, masc: ptr8, rt: ptr16,
          ant: ptr8, out: ptr16, rk: int, t: int, lat: int, no: int) -> int:
    tau = int(TAU)
    rest = int(V_REST)
    reset = int(V_RESET)
    refrac = int(REFRAC)
    th = int(V_TH)
    mul = int(I_OUT_MUL)
    lt = int(LATERAL)
    n = 0
    for o in range(no):
        if not masc[o]:
            v[o] = rest
            continue
        if ref[o]:
            ref[o] = ref[o] - 1
            continue
        r = int(rt[(rk + o) & 1023])
        if r & 0x8000:
            r -= 0x10000
        d = int(dire[o])
        if d & 0x8000:
            d -= 0x10000
        inib = lat - lt if ant[o] else lat
        vv = v[o]
        vv += J[o] * mul + d - inib - ((vv - rest) >> tau) + r
        if vv >= th:
            vv = reset
            ref[o] = refrac
            ult[o] = t
            cont[o] = cont[o] + 1
            out[n] = o
            n += 1
        v[o] = vv
    return n


@micropython.viper
def potenciar(w: ptr16, pi: ptr16, px: ptr16, np: int, spk: ptr16, ns: int, nh: int):
    a = int(A_PLUS)
    s = int(STDP_SHIFT)
    wm = int(WM)
    for j in range(ns):
        h = int(spk[j])
        for q in range(np):
            k = int(pi[q]) * nh + h
            x = int(w[k])
            if x & 0x8000:
                x -= 0x10000
            w[k] = x + ((a * int(px[q]) * (wm - x)) >> s)


@micropython.viper
def deprimir(w: ptr16, spk: ptr16, n: int, ph: ptr16, px: ptr16, np: int, nh: int):
    a = int(A_MINUS)
    s = int(STDP_SHIFT)
    for k in range(n):
        b = int(spk[k]) * nh
        for q in range(np):
            i = b + int(ph[q])
            x = int(w[i])
            if x & 0x8000:
                x -= 0x10000
            w[i] = x - ((a * int(px[q]) * x) >> s)


@micropython.viper
def normalizar(w: ptr16, alvo: ptr32, ni: int, nh: int):
    wm = int(WM)
    for h in range(nh):
        s = 0
        for i in range(ni):
            x = int(w[i * nh + h])
            if x & 0x8000:
                x -= 0x10000
            s += x
        if s:
            a = alvo[h]
            for i in range(ni):
                k = i * nh + h
                x = int(w[k])
                if x & 0x8000:
                    x -= 0x10000
                x = x * a // s
                w[k] = wm if x > wm else x


@micropython.viper
def recentes(ult: ptr32, n: int, t: int, minimo: int, traco: ptr16, qi: ptr16, qx: ptr16) -> int:
    lim = int(RECENTE)
    c = 0
    for i in range(n):
        dt = t - ult[i]
        if dt >= minimo and dt < lim:
            qi[c] = i
            qx[c] = traco[dt]
            c += 1
    return c


@micropython.viper
def elig_sobe(e: ptr32, qi: ptr16, qx: ptr16, n: int, o: int, no: int):
    a = int(A_PLUS)
    for q in range(n):
        k = int(qi[q]) * no + o
        e[k] = e[k] + ((a * int(qx[q])) >> 1)


@micropython.viper
def decair_col(e: ptr32, o: int, no: int, ne: int, n: int) -> int:
    mul = int(ELIG_MUL)
    sh = int(ELIG_SHIFT)
    vivo = 0
    for h in range(ne):
        k = h * no + o
        x = e[k]
        if x:
            if n > 20:
                x = 0
            else:
                for _ in range(n):
                    x -= (x * mul) >> sh
                    if x > -8 and x < 8:
                        x = 0
                        break
            e[k] = x
            if x:
                vivo = 1
    return vivo
