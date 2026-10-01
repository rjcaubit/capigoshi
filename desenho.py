# desenho.py - direcao visual "1c Diorama" do Capigoshi
# Traducao de design_handoff_capigoshi_1c/capigoshi-render.js (fonte de verdade).
# So usa primitivas do framebuf: fill_rect, rect, ellipse (cheia/contorno/metade),
# poly, pixel, line e texto 8x8. Cores em RGB e convertidas para RGB565 em C().
import math, framebuf
from array import array
from hw import cor, W, H

GROUND, FEET = 196, 205
CHAR_SCALE = 0.74

_fb = None


def usar(fb):
    global _fb
    _fb = fb


# ------------------------------------------------------------ cores
_cache = {}


def C(c):
    v = _cache.get(c)
    if v is None:
        v = cor(c[0], c[1], c[2])
        _cache[c] = v
    return v


def ri(v):
    """Arredonda como Math.round do JS (o framebuf so aceita inteiros)."""
    return int(math.floor(v + 0.5))


def escuro(c, f=0.55):
    return (ri(c[0] * f), ri(c[1] * f), ri(c[2] * f))


def claro(c, f=0.3):
    return (ri(c[0] + (255 - c[0]) * f), ri(c[1] + (255 - c[1]) * f), ri(c[2] + (255 - c[2]) * f))


def mistura(a, b, f=0.5):
    return (ri(a[0] + (b[0] - a[0]) * f), ri(a[1] + (b[1] - a[1]) * f), ri(a[2] + (b[2] - a[2]) * f))


def OL(c):
    return escuro(c, 0.5)               # contorno 1c: a cor da forma x 0,5


INK = (40, 30, 40)
CREME = (255, 247, 232)
TEXTO = (58, 42, 16)
BRANCO = (255, 255, 255)
VERMELHO = (226, 75, 74)
AMARELO = (255, 200, 32)
TRACK = (228, 212, 190)
STAT = {'fome': (255, 138, 42), 'alegria': (226, 80, 138),
        'energia': (58, 138, 232), 'saude': (46, 176, 96)}
TRAY = (52, 42, 54)
TRAY_BTN = (86, 72, 92)
TRAY_BAR = (96, 84, 100)
MADEIRA = (130, 88, 44)
MADEIRA_CL = (190, 140, 90)
BOL_OL = (128, 104, 86)                 # contorno dos baloes
ACC = (242, 140, 90)                    # laranja do menu
MUTEDM = (176, 156, 176)                # rotulo do menu
COCO = (90, 58, 26)

MARROM = (168, 112, 70); ESCURO = (122, 79, 46); MASCARA = (186, 128, 89)
CREME_C = (230, 192, 154); ROSA = (224, 158, 134); BOCHECHA = (214, 140, 118)
ENJOADA = (160, 190, 120); OLHO = (34, 21, 11); BOCA = (110, 40, 30)
PATO = (255, 200, 40); PATO_ESC = (205, 145, 20); LARANJA = (255, 140, 30)
LARANJA_CL = (255, 170, 90); ROXO = (128, 40, 128); LILAS = (190, 165, 230)
OLHO_PATO = (60, 40, 30)
CINZA = (205, 205, 214); CINZA_ESC = (125, 125, 138); ROSA_EL = (245, 165, 185)
PRETO = (20, 16, 20)

POLVO = (150, 108, 214); POLVO_ESC = (104, 70, 168); POLVO_CL = (196, 168, 240); ROSA_N = (244, 150, 190)
CAL = (252, 212, 84); CAL_ESC = (214, 166, 44); CAL_CL = (255, 236, 160)
CAL_BOCH = (238, 92, 66); CAL_BICO = (236, 126, 70)
CAR = (214, 148, 78); CAR_ESC = (160, 98, 44); CAR_CL = (252, 224, 182); CAR_ORELHA = (136, 82, 38)
GATO = (58, 54, 70); GATO_CL = (226, 222, 234); GATO_IRIS = (200, 232, 90)
ET = (112, 200, 92); ET_ESC = (58, 138, 62); ET_CL = (190, 240, 120)
SAPO = (150, 200, 56); SAPO_ESC = (96, 146, 36); SAPO_CL = (214, 232, 140)


# ------------------------------------------------------------ primitivas
_MASK = (15, 3, 12)                     # 0 inteira, 1 metade de cima, 2 metade de baixo


# Transformacao do personagem "vivo" (esticar, espelhar, girar). Na placa a escala multiplica
# o raio e a posicao de cada primitiva, o espelho inverte o x e o giro (so na cambalhota)
# gira o centro de cada primitiva em volta do meio do corpo. None = desenho normal.
_T = None


def transformar(X, Y, kx, ky, rot=0.0, cy=0.0):
    global _T
    _T = (X, Y, kx, ky, rot, cy, math.cos(rot), math.sin(rot)) if (kx != 1 or ky != 1 or rot) else None


def sem_transformar():
    global _T
    _T = None


def _p(x, y):
    X, Y, kx, ky, rot, cy, cs, sn = _T
    a, b = X + (x - X) * kx, Y + (y - Y) * ky
    if rot:
        ax, by = a - X, b - cy
        return X + ax * cs - by * sn, cy + ax * sn + by * cs
    return a, b


def rect(x, y, w, h, c):
    if _T:
        if _T[4]:                                   # girando: gira o centro, mantem o tamanho
            cx, cy = _p(x + w / 2, y + h / 2)
            w, h = abs(w * _T[2]), abs(h * _T[3])
            x, y = cx - w / 2, cy - h / 2
        else:
            x0, y0 = _p(x, y)
            x1, y1 = _p(x + w, y + h)
            x, y, w, h = min(x0, x1), min(y0, y1), max(1, abs(x1 - x0)), max(1, abs(y1 - y0))
    _fb.fill_rect(ri(x), ri(y), ri(w), ri(h), C(c))


def px(x, y, c):
    if _T:
        x, y = _p(x, y)
    _fb.pixel(ri(x), ri(y), C(c))


def hl(x, y, w, c):
    rect(x, y, w, 1, c)


def vl(x, y, h, c):
    rect(x, y, 1, h, c)


def linha(x1, y1, x2, y2, c):
    if _T:
        x1, y1 = _p(x1, y1)
        x2, y2 = _p(x2, y2)
    _fb.line(ri(x1), ri(y1), ri(x2), ri(y2), C(c))


def ell(x, y, rx, ry, c, cheia=True, m=0):
    if _T:
        x, y = _p(x, y)
        rx, ry = rx * abs(_T[2]), ry * _T[3]
    _fb.ellipse(ri(x), ri(y), ri(max(0.5, rx)), ri(max(0.5, ry)), C(c), cheia, _MASK[m])


def arco(x, y, rx, ry, c, m, g=2):
    for i in range(g):
        ell(x, y, rx - i, ry - i, c, False, m)


def poly(x, y, pts, c):
    a = array('h', bytes(2 * len(pts)))
    for i in range(0, len(pts), 2):
        qx, qy = x + pts[i], y + pts[i + 1]
        if _T:
            qx, qy = _p(qx, qy)
        a[i] = ri(qx)
        a[i + 1] = ri(qy)
    _fb.poly(0, 0, a, C(c), True)


def rrect(x, y, w, h, r, c):
    x, y, w, h = ri(x), ri(y), ri(w), ri(h)
    r = int(min(r, (w - 1) // 2, (h - 1) // 2))
    k = C(c)
    if r < 1:
        _fb.fill_rect(x, y, w, h, k)
        return
    _fb.fill_rect(x + r, y, w - 2 * r, h, k)
    _fb.fill_rect(x, y + r, w, h - 2 * r, k)
    for ex in (x + r, x + w - 1 - r):
        for ey in (y + r, y + h - 1 - r):
            _fb.ellipse(ex, ey, r, r, k, True)


_mono = bytearray(32 * 8)
_fbm = framebuf.FrameBuffer(_mono, 32 * 8, 8, framebuf.MONO_HLSB)


def texto(s, x, y, c, esc=1):
    x, y = ri(x), ri(y)
    if esc == 1:
        _fb.text(s, x, y, C(c))
        return
    s = s[:32]
    _fbm.fill(0)
    _fbm.text(s, 0, 0, 1)
    k = C(c)
    for py in range(8):
        for pxx in range(len(s) * 8):
            if _fbm.pixel(pxx, py):
                _fb.fill_rect(x + pxx * esc, y + py * esc, esc, esc, k)


def centro(s, y, c, esc=1):
    texto(s, (W - len(s) * 8 * esc) / 2, y, c, esc)


def etiqueta(s, y, esc=1, x=None):
    """Texto creme com sombra de 1 px (tag do estilo 1c)."""
    w = len(s) * 8 * esc + 12
    if x is None:
        x = ri((W - w) / 2)
    texto(s, x + 7, y + 5, escuro(CREME, 0.25), esc)
    texto(s, x + 6, y + 4, CREME, esc)
    return w


# ------------------------------------------------------------ fases do dia
def _fase(nome, ini, fim, ceu, grama, grama_e, lago, longe, perto, estrelas=False):
    return {'nome': nome, 'ini': ini, 'fim': fim, 'ceu': ceu, 'grama': grama, 'grama_e': grama_e,
            'lago': lago, 'longe': longe, 'perto': perto, 'estrelas': estrelas}


NASCER_SOL, POR_SOL = 6, 18      # o sol nasce as 6h e se poe as 18h; a lua faz o arco da noite

FASES = (
    _fase('Madrugada', 0, 5, ((14, 18, 52), (22, 28, 70), (34, 42, 92)), (24, 74, 52), (16, 52, 38),
          (36, 64, 120), (26, 32, 78), (22, 60, 48), True),
    _fase('Amanhecer', 5, 7, ((236, 150, 130), (250, 176, 130), (255, 214, 170)), (70, 160, 90),
          (44, 116, 66), (130, 180, 220), (196, 134, 150), (60, 140, 80)),
    _fase('Dia', 7, 17, ((92, 178, 248), (130, 200, 250), (170, 222, 252)), (46, 176, 96),
          (30, 124, 66), (90, 170, 235), (110, 180, 210), (40, 150, 84)),
    _fase('Por do sol', 17, 18.5, ((236, 110, 96), (250, 150, 90), (255, 204, 130)), (60, 150, 86),
          (36, 106, 60), (240, 160, 120), (186, 104, 120), (50, 130, 74)),
    _fase('Crepusculo', 18.5, 20, ((52, 44, 104), (90, 68, 132), (160, 104, 140)), (36, 100, 66),
          (24, 70, 48), (84, 80, 150), (72, 58, 120), (30, 84, 58), True),
    _fase('Noite', 20, 24, ((14, 18, 52), (18, 24, 62), (28, 34, 80)), (20, 70, 45), (14, 50, 34),
          (30, 60, 110), (20, 26, 68), (18, 56, 42), True),
)


def fase_de(h):
    for f in FASES:
        if f['ini'] <= h < f['fim']:
            return f
    return FASES[5]


def e_noite(h):
    return fase_de(h)['estrelas']


# ------------------------------------------------------------ cena
def nuvem(x, y, c):
    ell(x, y, 12, 6, c); ell(x - 8, y + 2, 8, 5, c); ell(x + 9, y + 2, 8, 5, c)


def capim(x, y, c, h=1):
    for dx, alt in ((-4, 8 * h), (0, 11 * h), (4, 8 * h)):
        meio = int(dx / 2)
        linha(x + meio, y, x + dx, y - alt, c)
        linha(x + meio + 1, y, x + dx + 1, y - alt, c)


def arvore(x, y, c, tam, ol=False):
    rect(x - 2, y - tam, 4, tam, MADEIRA)
    if ol:
        ell(x, y - tam - 6, tam * 0.8 + 1, tam * 0.7 + 1, OL(c))
    ell(x, y - tam - 6, tam * 0.8, tam * 0.7, c)


def ceu(ph, hora, t):
    b = ph['ceu']
    faixas = (b[0], b[1], mistura(b[1], b[2]), b[2])
    cortes = (0, 60, 110, 150, GROUND)
    for i in range(4):
        rect(0, cortes[i], W, cortes[i + 1] - cortes[i], faixas[i])
    if ph['estrelas']:
        for i in range(30):
            f = (t // (380 + i * 61) + i * 7) % (3 + i % 3)
            if f:
                sx, sy = (i * 53 + 11) % W, 34 + (i * 37) % 120
                px(sx, sy, BRANCO)
                if i % 4 == 0 and f > 1:
                    px(sx + 1, sy, BRANCO); px(sx, sy + 1, BRANCO)
    if NASCER_SOL <= hora < POR_SOL:
        a = (hora - NASCER_SOL) / (POR_SOL - NASCER_SOL) * math.pi
        x, y = ri(120 - 100 * math.cos(a)), ri(170 - 105 * math.sin(a))
        sol = (255, 220, 60)
        ell(x, y, 12, 12, OL(sol)); ell(x, y, 11, 11, sol)
    else:
        a = ((hora - POR_SOL) % 24) / (24 - POR_SOL + NASCER_SOL) * math.pi
        x, y = ri(120 - 100 * math.cos(a)), ri(170 - 105 * math.sin(a))
        ell(x, y, 15, 15, claro(b[0], 0.12))
        ell(x, y, 9, 9, (240, 240, 220))
        ell(x + 4, y - 3, 8, 8, b[0])
    if not ph['estrelas']:
        c = claro(b[1], 0.6)
        nuvem(ri((t / 220) % (W + 80)) - 40, 46, c)
        nuvem(ri((t / 300 + 150) % (W + 80)) - 40, 72, c)
    longe, perto = ph['longe'], ph['perto']
    poly(0, GROUND, (-10, 0, 40, -52, 90, 0), longe)
    poly(70, GROUND, (0, 0, 55, -66, 110, 0), longe)
    poly(150, GROUND, (0, 0, 48, -44, 100, 0), longe)
    neve = claro(longe, 0.5)
    poly(125, GROUND - 66, (0, 0, -7, 9, 7, 9), neve)
    poly(40, GROUND - 52, (0, 0, -6, 7, 6, 7), neve)
    ell(40, GROUND + 8, 90, 24, perto)
    ell(200, GROUND + 10, 80, 20, perto)


def chao(ph, t):
    rect(0, GROUND, W, H - GROUND, ph['grama'])
    rect(0, 240, W, H - 240, ph['grama_e'])
    lago = ph['lago']
    ell(202, 214, 35, 10, OL(lago)); ell(202, 214, 34, 9, lago)
    r = (t // 500) % 3
    ell(214 + r * 3, 216, 3 + r, 1.5, claro(lago, 0.4), False)
    for x in (18, 44, 96, 150):
        capim(x, 200, ph['grama_e'])
    for x in (12, 60, 118, 176, 226):
        capim(x, 258, ph['grama'], 1.4)


def cena(ph, hora, t):
    ceu(ph, hora, t)
    chao(ph, t)


# ------------------------------------------------------------ personagens
def termometro(tx, ty):
    rect(tx, ty, 3, 12, BRANCO)
    ell(tx + 1, ty + 12, 3, 3, VERMELHO)
    rect(tx + 1, ty + 5, 1, 7, VERMELHO)


def _rel(cx, pe, s, ol, anel):
    def E(dx, dy, rx, ry, c, fora=False):
        x, y = cx + dx * s, pe + dy * s
        RX, RY = max(1, rx * s), max(1, ry * s)
        oc = ol(c) if ol else (anel(c) if fora and anel else None)
        if oc and fora:
            ell(x, y, RX + 1, RY + 1, oc)
        ell(x, y, RX, RY, c)

    def P(dx, dy, pts, c):
        poly(cx + dx * s, pe + dy * s, [v * s for v in pts], c)

    def R(dx, dy, w, h, c):
        rect(cx + dx * s, pe + dy * s, w * s, max(1, h * s), c)

    def A(dx, dy, rx, ry, c, m, g=2):
        arco(cx + dx * s, pe + dy * s, rx * s, ry * s, c, m, g)
    return E, P, R, A


def capi(cx, pe, olhos, boca, doente, s, ol):
    K = 0.078 * s

    def X(v): return cx + (v - 965) * K
    def Y(v): return pe + (v - 1810) * K
    def R(v): return max(1, v * K)

    def E(x, y, rx, ry, c, fora=False):
        if ol and fora:
            ell(X(x), Y(y), R(rx) + 1, R(ry) + 1, ol(c))
        ell(X(x), Y(y), R(rx), R(ry), c)
    E(965, 1390, 495, 330, MARROM, 1); E(965, 1530, 330, 240, CREME_C)
    E(760, 1330, 100, 75, MARROM, 1); E(1170, 1330, 100, 75, MARROM, 1)
    E(750, 1760, 90, 52, ESCURO, 1); E(1180, 1760, 90, 52, ESCURO, 1)
    E(678, 560, 90, 72, ESCURO, 1); E(678, 560, 45, 38, ROSA)
    E(1253, 560, 90, 72, ESCURO, 1); E(1253, 560, 45, 38, ROSA)
    E(965, 835, 432, 382, MARROM, 1); E(965, 940, 330, 250, MASCARA); E(965, 1050, 197, 145, CREME_C)
    bc = ENJOADA if doente else BOCHECHA
    E(710, 1000, 57, 32, bc); E(1220, 1000, 57, 32, bc)
    for ox in (808, 1122):
        if olhos == 'fechados':
            rect(X(ox - 48), Y(845), R(96), 2, OLHO)
        elif olhos == 'feliz':
            arco(X(ox), Y(880), R(52), R(48), OLHO, 1)
        elif olhos == 'susto':
            E(ox, 845, 80, 85, BRANCO); E(ox, 845, 30, 32, OLHO)
        elif olhos == 'sono':
            E(ox, 845, 57, 63, OLHO); rect(X(ox - 60), Y(780), R(120), R(70), MASCARA)
        else:
            E(ox, 845, 57, 63, OLHO); E(ox + 17, 818, 17, 17, BRANCO)
    E(965, 1003, 45, 28, OLHO)
    bx, by = X(965), Y(1092)
    if boca == 'sorriso':
        arco(bx, by, R(70), R(48), OLHO, 2)
        rect(bx - 3, by + R(40), 2, 3, BRANCO); rect(bx + 1, by + R(40), 2, 3, BRANCO)
    elif boca == 'triste':
        arco(bx, Y(1150), R(60), R(40), OLHO, 1)
    elif boca == 'aberta':
        E(965, 1105, 45, 55, BOCA)
    elif boca == 'meia':
        E(965, 1105, 40, 18, BOCA)
    elif boca == 'o':
        E(965, 1110, 32, 40, BOCA)
    else:
        E(965, 1100, 16, 16, OLHO)
    arco(X(965), Y(700), R(355), R(300), OLHO, 1, 3)
    for x0 in (548, 1278):
        rect(X(x0), Y(610), R(104), R(138), OLHO)
        rect(X(x0 + 22), Y(632), R(60), R(94), AMARELO)
    if doente:
        termometro(X(1300), Y(1040))
    return Y(835), Y(480), R(495), ((X(808), Y(845)), (X(1122), Y(845)))


def pato(cx, pe, olhos, boca, doente, s, ol):
    E, P, R, A = _rel(cx, pe, s, ol, lambda c: PATO_ESC if c == PATO else None)
    E(0, -44, 35, 46, PATO, 1)
    E(-30, -38, 8, 15, PATO_ESC); E(30, -38, 8, 15, PATO_ESC)
    E(-12, -2, 10, 4, LARANJA, 1); E(12, -2, 10, 4, LARANJA, 1)
    E(-36, -70, 9, 16, ROXO, 1); E(36, -70, 9, 16, ROXO, 1)
    bc = ENJOADA if doente else LARANJA_CL
    E(-23, -50, 5, 3, bc); E(23, -50, 5, 3, bc)
    for ox in (-13, 13):
        oy = -62
        if olhos == 'fechados':
            R(ox - 7, oy, 14, 2, OLHO_PATO)
        elif olhos == 'feliz':
            A(ox, oy + 4, 7, 6, OLHO_PATO, 1)
        elif olhos == 'susto':
            E(ox, oy, 10, 10, BRANCO, 1); E(ox, oy, 4, 4, OLHO_PATO)
        elif olhos == 'sono':
            E(ox, oy, 8, 8, OLHO_PATO); R(ox - 9, oy - 9, 18, 9, PATO)
        else:
            E(ox, oy, 8, 8, OLHO_PATO); E(ox - 3, oy - 3, 2, 2, BRANCO)
    by = -50
    if boca == 'aberta':
        P(0, by, (-8, -3, 8, -3, 0, 11), BOCA); P(0, by, (-8, -3, 8, -3, 0, 3), LARANJA)
    elif boca == 'meia':
        P(0, by, (-8, -3, 8, -3, 0, 8), BOCA); P(0, by, (-8, -3, 8, -3, 0, 4), LARANJA)
    elif boca == 'o':
        P(0, by, (-8, -3, 8, -3, 0, 7), LARANJA); E(0, by + 9, 3, 3, BOCA)
    elif boca == 'triste':
        P(0, by, (-8, -3, 8, -3, 0, 7), LARANJA); A(0, by + 14, 6, 4, OLHO_PATO, 1)
    elif boca == 'dormindo':
        P(0, by, (-6, -2, 6, -2, 0, 5), LARANJA)
    else:
        P(0, by, (-8, -3, 8, -3, 0, 7), LARANJA); A(0, by + 8, 7, 4, OLHO_PATO, 2)
    E(0, -82, 42, 12, ROXO, 1); R(-24, -91, 48, 7, LILAS)
    if ol:
        P(0, -85, (-26, 1, 26, 1, 7, -44), ol(ROXO))
    P(0, -85, (-24, 0, 24, 0, 6, -42), ROXO)
    if doente:
        termometro(cx + 30 * s, pe - 58 * s)
    return pe - 62 * s, pe - 128 * s, 35 * s, ((cx - 13 * s, pe - 62 * s), (cx + 13 * s, pe - 62 * s))


def elefante(cx, pe, olhos, boca, doente, s, ol):
    E, P, R, A = _rel(cx, pe, s, ol, lambda c: CINZA_ESC if c == CINZA else None)
    for sg in (-1, 1):
        E(sg * 32, -80, 15, 17, CINZA, 1); E(sg * 33, -80, 9, 11, ROSA_EL)
    E(0, -38, 34, 42, CINZA, 1)
    E(-14, -2, 10, 4, CINZA_ESC, 1); E(14, -2, 10, 4, CINZA_ESC, 1)
    E(0, -72, 30, 28, CINZA, 1)
    bc = ENJOADA if doente else ROSA_EL
    E(-23, -60, 5, 3, bc); E(23, -60, 5, 3, bc)
    for ox in (-12, 12):
        oy = -74
        if olhos == 'fechados':
            R(ox - 8, oy, 16, 2, PRETO)
        elif olhos == 'feliz':
            A(ox, oy + 4, 8, 7, PRETO, 1)
        elif olhos == 'susto':
            E(ox, oy, 10, 10, BRANCO, 1); E(ox, oy, 3, 3, PRETO)
        elif olhos == 'sono':
            E(ox, oy, 10, 10, BRANCO, 1); E(ox + 1, oy + 1, 5, 5, PRETO); R(ox - 11, oy - 11, 22, 11, CINZA)
        else:
            E(ox, oy, 10, 10, BRANCO, 1); E(ox + 1, oy + 1, 5, 5, PRETO); E(ox - 2, oy - 3, 2, 2, BRANCO)
    mx, my = -13, -52
    if boca == 'sorriso':
        A(mx, my, 5, 3, PRETO, 2)
    elif boca == 'triste':
        A(mx, my + 3, 5, 3, PRETO, 1)
    elif boca == 'aberta':
        E(mx, my + 1, 4, 5, BOCA)
    elif boca == 'meia':
        E(mx, my + 1, 4, 2, BOCA)
    elif boca == 'o':
        E(mx, my + 1, 3, 3, BOCA)
    if boca == 'aberta' or olhos == 'feliz':          # tromba levanta
        segs = ((0, -58, 8, 9), (1, -48, 8, 9), (4, -39, 7, 8), (10, -33, 7, 6), (17, -38, 5, 5))
    else:
        segs = ((0, -58, 8, 9), (1, -48, 8, 9), (3, -38, 7, 8), (9, -30, 7, 6), (16, -28, 5, 4))
    for dx, dy, rx, ry in segs:
        E(dx, dy, rx, ry, CINZA, 1)
    if doente:
        termometro(cx + 30 * s, pe - 62 * s)
    return pe - 72 * s, pe - 102 * s, 34 * s, ((cx - 12 * s, pe - 74 * s), (cx + 12 * s, pe - 74 * s))


# --- olhos, bocas e bicos genericos dos personagens novos
def _olhos(E, R, A, pts, olhos, ink, palpebra, gato_iris=None):
    """Desenha e devolve os pontos dos olhos relativos (para as sobrancelhas do idoso)."""
    for ox, oy, k in pts:
        if olhos == 'fechados':
            R(ox - k, oy, 2 * k, 2.4, ink)
        elif olhos == 'feliz':
            A(ox, oy + k * 0.5, k * 0.85, k * 0.75, ink, 1, 2)
        elif olhos == 'susto':
            E(ox, oy, k * 1.15 + 1, k * 1.2 + 1, PRETO)
            E(ox, oy, k * 1.15, k * 1.2, BRANCO)
            E(ox, oy, k * 0.4, k * 0.45, PRETO)
        else:
            if gato_iris:
                E(ox, oy, k * 0.85, k, gato_iris)
                R(ox - 0.9, oy - k * 0.7, 1.8, k * 1.4, PRETO)
                E(ox + k * 0.3, oy - k * 0.42, k * 0.24, k * 0.24, BRANCO)
            else:
                E(ox, oy, k * 0.8, k, PRETO)
                E(ox + k * 0.28, oy - k * 0.4, k * 0.32, k * 0.32, BRANCO)
            if olhos == 'sono':
                R(ox - k - 1.5, oy - k - 1.5, 2 * k + 3, k + 1.5, palpebra)


def _boca(E, A, boca, mx, my, k, ink, w=False):
    if boca == 'sorriso':
        if w:
            A(mx - 2.6 * k, my, 2.6 * k, 2.2 * k, ink, 2, 2)
            A(mx + 2.6 * k, my, 2.6 * k, 2.2 * k, ink, 2, 2)
        else:
            A(mx, my, 4 * k, 3 * k, ink, 2, 2)
    elif boca == 'triste':
        A(mx, my + 3 * k, 4 * k, 3 * k, ink, 1, 2)
    elif boca == 'aberta':
        E(mx, my + 2 * k, 3.6 * k, 4.2 * k, BOCA)
    elif boca == 'meia':
        E(mx, my + 1 * k, 3.6 * k, 1.8 * k, BOCA)
    elif boca == 'o':
        E(mx, my + 1.2 * k, 2.3 * k, 2.7 * k, BOCA)
    else:
        E(mx, my, 1.4 * k, 1.4 * k, ink)


def _bico(E, P, A, boca, by, k, col, ink):
    b = (-6 * k, -2 * k, 6 * k, -2 * k, 0, 6 * k)
    if boca == 'aberta':
        P(0, by, (-6 * k, -2 * k, 6 * k, -2 * k, 0, 10 * k), BOCA)
        P(0, by, (-6 * k, -2 * k, 6 * k, -2 * k, 0, 2.5 * k), col)
    elif boca == 'meia':
        P(0, by, (-6 * k, -2 * k, 6 * k, -2 * k, 0, 8 * k), BOCA)
        P(0, by, (-6 * k, -2 * k, 6 * k, -2 * k, 0, 4 * k), col)
    elif boca == 'o':
        P(0, by, b, col); E(0, by + 8 * k, 2.5 * k, 2.5 * k, BOCA)
    elif boca == 'triste':
        P(0, by, b, col); A(0, by + 12 * k, 5 * k, 3 * k, ink, 1, 2)
    elif boca == 'dormindo':
        P(0, by, (-4.5 * k, -1.5 * k, 4.5 * k, -1.5 * k, 0, 4 * k), col)
    else:
        P(0, by, b, col); A(0, by + 6.5 * k, 6 * k, 3.5 * k, ink, 2, 2)


def polvo(cx, pe, olhos, boca, doente, s, ol):
    E, P, R, A = _rel(cx, pe, s, ol, lambda c: POLVO_ESC if c == POLVO else None)
    for dx, dy, rx, ry in ((-27, -13, 11, 12), (27, -13, 11, 12), (-14, -9, 10, 10), (14, -9, 10, 10), (0, -8, 10, 10)):
        E(dx, dy, rx, ry, POLVO, 1)
    for dx in (-27, -14, 0, 14, 27):
        E(dx, -4, 4, 2.5, POLVO_CL)
    E(0, -56, 38, 40, POLVO, 1); E(-18, -80, 9, 5, POLVO_CL)
    bc = ENJOADA if doente else ROSA_N
    E(-25, -45, 6, 3.5, bc); E(25, -45, 6, 3.5, bc)
    _olhos(E, R, A, ((-13, -58, 8), (13, -58, 8)), olhos, PRETO, POLVO)
    _boca(E, A, boca, 0, -44, 1, PRETO)
    if doente:
        termometro(cx + 32 * s, pe - 58 * s)
    return pe - 56 * s, pe - 96 * s, 38 * s, [(cx + ox * s, pe + oy * s) for ox, oy, _ in ((-13, -58, 8), (13, -58, 8))]


def calopsita(cx, pe, olhos, boca, doente, s, ol):
    E, P, R, A = _rel(cx, pe, s, ol, lambda c: CAL_ESC if c == CAL else None)
    if ol:
        P(0, 0, (8, -34, 38, -2, 26, 3), ol(CAL_ESC))
    P(0, 0, (10, -36, 36, -4, 24, 1), CAL_ESC)                        # cauda
    E(-9, -2, 7, 3, CAL_BICO, 1); E(9, -2, 7, 3, CAL_BICO, 1)
    E(0, -38, 27, 37, CAL, 1); E(0, -28, 17, 22, CAL_CL)
    E(-22, -38, 7, 17, CAL_ESC); E(22, -38, 7, 17, CAL_ESC)
    if ol:
        P(-2, -94, (-6, 6, 6, 6, 3, -22), ol(CAL)); P(5, -92, (-4, 5, 5, 5, 13, -15), ol(CAL))
    P(-2, -94, (-5, 6, 5, 6, 3, -20), CAL); P(5, -92, (-3, 5, 4, 5, 12, -14), CAL_ESC)   # topete
    E(0, -77, 22, 21, CAL, 1)
    bc = ENJOADA if doente else CAL_BOCH
    E(-14, -70, 6.5, 6.5, bc); E(14, -70, 6.5, 6.5, bc)
    _olhos(E, R, A, ((-9, -81, 5), (9, -81, 5)), olhos, PRETO, CAL)
    _bico(E, P, A, boca, -73, 0.8, CAL_BICO, PRETO)
    if doente:
        termometro(cx + 26 * s, pe - 60 * s)
    return pe - 77 * s, pe - 114 * s, 28 * s, [(cx + ox * s, pe + oy * s) for ox, oy, _ in ((-9, -81, 5), (9, -81, 5))]


def cachorro(cx, pe, olhos, boca, doente, s, ol):
    E, P, R, A = _rel(cx, pe, s, ol, lambda c: CAR_ESC if c == CAR else None)
    E(28, -36, 6, 11, CAR, 1); E(31, -46, 4, 4, CAR_CL)                # rabo
    E(-11, -2, 8, 4, CAR_ESC, 1); E(11, -2, 8, 4, CAR_ESC, 1)
    E(0, -32, 27, 32, CAR, 1); E(0, -24, 16, 20, CAR_CL)
    E(-19, -36, 6, 10, CAR_ESC); E(19, -36, 6, 10, CAR_ESC)
    E(0, -74, 30, 27, CAR, 1)
    E(-29, -70, 9, 17, CAR_ORELHA, 1); E(29, -70, 9, 17, CAR_ORELHA, 1)
    E(0, -62, 13, 9, CAR_CL)
    bc = ENJOADA if doente else (240, 150, 150)
    E(-20, -63, 5, 3, bc); E(20, -63, 5, 3, bc)
    _olhos(E, R, A, ((-12, -78, 7), (12, -78, 7)), olhos, PRETO, CAR)
    E(0, -67, 4, 3, PRETO)
    _boca(E, A, boca, 0, -61, 0.8, PRETO, True)
    if doente:
        termometro(cx + 34 * s, pe - 60 * s)
    return pe - 74 * s, pe - 101 * s, 30 * s, [(cx + ox * s, pe + oy * s) for ox, oy, _ in ((-12, -78, 7), (12, -78, 7))]


def gato(cx, pe, olhos, boca, doente, s, ol):
    if ol:
        ol_g = lambda c: (110, 104, 128) if c == GATO else ol(c)   # contorno claro: nao some a noite
    else:
        ol_g = None
    E, P, R, A = _rel(cx, pe, s, ol_g, lambda c: (96, 90, 112) if c == GATO else None)
    E(28, -42, 5, 14, GATO, 1); E(33, -58, 5, 5, GATO, 1)            # rabo
    E(-10, -2, 8, 4, GATO, 1); E(10, -2, 8, 4, GATO, 1)
    E(0, -32, 25, 32, GATO, 1); E(0, -34, 8, 10, GATO_CL)
    anel = ol_g(GATO) if ol_g else (96, 90, 112)
    P(-18, -88, (-12, 14, 10, 14, -6, -14), anel); P(18, -88, (12, 14, -10, 14, 6, -14), anel)
    P(-18, -88, (-10, 13, 8, 13, -6, -12), GATO); P(18, -88, (10, 13, -8, 13, 6, -12), GATO)
    P(-18, -86, (-5, 10, 4, 10, -4, -5), ROSA_N); P(18, -86, (5, 10, -4, 10, 4, -5), ROSA_N)
    E(0, -72, 29, 25, GATO, 1)
    bc = ENJOADA if doente else ROSA_N
    E(-20, -63, 5, 3, bc); E(20, -63, 5, 3, bc)
    _olhos(E, R, A, ((-12, -75, 8), (12, -75, 8)), olhos, GATO_CL, GATO, GATO_IRIS)
    P(0, -67, (-3, 0, 3, 0, 0, 3), ROSA_N)
    for dy in (-65, -61):                                              # bigodes
        R(-33, dy, 9, 1, GATO_CL); R(24, dy, 9, 1, GATO_CL)
    _boca(E, A, boca, 0, -61, 0.8, GATO_CL, True)
    if doente:
        termometro(cx + 32 * s, pe - 60 * s)
    return pe - 72 * s, pe - 102 * s, 29 * s, [(cx + ox * s, pe + oy * s) for ox, oy, _ in ((-12, -75, 8), (12, -75, 8))]


def et(cx, pe, olhos, boca, doente, s, ol):
    E, P, R, A = _rel(cx, pe, s, ol, lambda c: ET_ESC if c == ET else None)
    olc = ol(ET) if ol else ET_ESC
    P(0, -50, (-15, -1, 15, -1, 32, 49, -32, 49), olc)
    P(-12, -45, (1, -1, -28, 18, -21, 26), olc); P(12, -45, (-1, -1, 28, 18, 21, 26), olc)
    P(-12, -44, (0, 0, -26, 18, -20, 24), ET); P(12, -44, (0, 0, 26, 18, 20, 24), ET)
    P(0, -50, (-14, 0, 14, 0, 30, 48, -30, 48), ET)
    for dx in (-19, 0, 19):
        E(dx, -2, 11, 3, ET)
    R(-17, -22, 11, 2, ET_ESC); R(5, -28, 11, 2, ET_ESC); R(-6, -12, 13, 2, ET_ESC)
    R(-14, -104, 2, 18, ET_ESC); R(12, -104, 2, 18, ET_ESC)                # anteninhas
    E(-13, -106, 4.5, 4.5, ET_CL, 1); E(13, -106, 4.5, 4.5, ET_CL, 1)
    E(0, -70, 26, 24, ET, 1)
    bc = ENJOADA if doente else (250, 166, 170)
    E(-18, -61, 4, 2.5, bc); E(18, -61, 4, 2.5, bc)
    _olhos(E, R, A, ((-11, -71, 5.5), (11, -71, 5.5), (0, -83, 4.5)), olhos, PRETO, ET)
    _boca(E, A, boca, 0, -58, 0.75, PRETO)
    if doente:
        termometro(cx + 28 * s, pe - 62 * s)
    return pe - 70 * s, pe - 110 * s, 30 * s, [(cx + ox * s, pe + oy * s) for ox, oy, _ in ((-11, -71, 5.5), (11, -71, 5.5), (0, -83, 4.5))]


def sapinho(cx, pe, olhos, boca, doente, s, ol):
    E, P, R, A = _rel(cx, pe, s, ol, lambda c: SAPO_ESC if c == SAPO else None)
    E(-22, -4, 11, 5, SAPO_ESC, 1); E(22, -4, 11, 5, SAPO_ESC, 1)
    E(-15, -74, 13, 13, SAPO, 1); E(15, -74, 13, 13, SAPO, 1)
    E(0, -38, 35, 34, SAPO, 1); E(0, -24, 21, 17, SAPO_CL)
    E(-11, -6, 7, 4, SAPO_ESC, 1); E(11, -6, 7, 4, SAPO_ESC, 1)
    bc = ENJOADA if doente else (240, 150, 90)
    E(-24, -46, 6, 3.5, bc); E(24, -46, 6, 3.5, bc)
    _olhos(E, R, A, ((-15, -74, 9.5), (15, -74, 9.5)), olhos, PRETO, SAPO)
    if olhos == 'normal':
        E(-18, -70, 1.8, 1.8, BRANCO); E(12, -70, 1.8, 1.8, BRANCO)
    E(-3, -56, 1.2, 1.2, PRETO); E(3, -56, 1.2, 1.2, PRETO)
    _boca(E, A, boca, 0, -49, 1.5, PRETO)
    if doente:
        termometro(cx + 34 * s, pe - 56 * s)
    return pe - 46 * s, pe - 88 * s, 35 * s, [(cx + ox * s, pe + oy * s) for ox, oy, _ in ((-15, -74, 9.5), (15, -74, 9.5))]


ELENCO = ('capi', 'elefante', 'pato', 'polvo', 'calopsita', 'cachorro', 'gato', 'et', 'sapinho')
NOMES = {'capi': 'Capi', 'pato': 'Pato', 'elefante': 'Elefante', 'polvo': 'Polvo', 'calopsita': 'Calopsita',
         'cachorro': 'Caramelo', 'gato': 'Gato', 'et': 'ET', 'sapinho': 'Sapinho'}
_FUNCS = {'capi': capi, 'pato': pato, 'elefante': elefante, 'polvo': polvo, 'calopsita': calopsita,
          'cachorro': cachorro, 'gato': gato, 'et': et, 'sapinho': sapinho}


FASES_VIDA = ('ovo', 'filhote', 'adulto', 'idoso', 'estrela')


def personagem(id, cx, pe, olhos='normal', boca='sorriso', doente=False, contorno=True, s=1.0, cru=False,
               fase='adulto', racha=False, grama=(46, 176, 96)):
    """Desenha e devolve (centro da cabeca, topo, meia largura)."""
    if fase == 'ovo':
        return ovo(cx, pe, racha, grama, contorno)
    if not cru:
        s *= CHAR_SCALE
    if fase == 'filhote':
        s *= 0.62
    global olhos_ult
    cab, topo, meia, olhos_pts = _FUNCS.get(id, capi)(cx, pe, olhos, boca, doente, s, OL if contorno else None)
    olhos_ult = [(_p(ex, ey) if _T else (ex, ey)) for ex, ey in olhos_pts]
    if fase == 'idoso':                       # sobrancelhas brancas e bengala
        for ex, ey in olhos_pts:
            rect(ex - 5, ey - 11, 10, 2, BRANCO)
        bx = cx + meia + 4
        rect(bx, pe - 38, 3, 38, MADEIRA)
        ell(bx + 1, pe - 40, 4, 3, MADEIRA)
    return cab, topo, meia


OVO = (250, 240, 222)


def ovo(cx, pe, racha=False, grama=(46, 176, 96), contorno=True, s=1.0):
    ell(cx, pe - 1, 30 * s, 6 * s, escuro(grama, 0.7))
    if contorno:
        ell(cx, pe - 26 * s, 25 * s, 32 * s, OL(OVO))
    ell(cx, pe - 26 * s, 24 * s, 31 * s, OVO)
    for dx, dy, r in ((-8, -38, 4), (9, -30, 3), (-3, -16, 3), (12, -14, 2)):
        ell(cx + dx * s, pe + dy * s, r * s, r * s, (214, 190, 160))
    if racha:
        p = ((-8, -30), (-3, -26), (-7, -22), (0, -18), (-4, -14))
        for i in range(len(p) - 1):
            linha(cx + p[i][0] * s, pe + p[i][1] * s, cx + p[i + 1][0] * s, pe + p[i + 1][1] * s, INK)
    return pe - 30 * s, pe - 58 * s, 24 * s


def estrela_nome(nome):
    """Despedida: o bichinho vira estrela com o nome no ceu."""
    poly(120, 66, (0, -9, 2, -2, 9, 0, 2, 2, 0, 9, -2, 2, -9, 0, -2, -2), AMARELO)
    px(112, 58, BRANCO); px(129, 75, BRANCO)
    texto(nome, 120 - len(nome) * 4, 82, CREME)


def estrelas_antigas(n, t):
    """Os bichinhos que ja foram, brilhando um pouco mais forte a noite."""
    for i in range(min(n, 12)):
        x, y = 24 + (i * 67) % 192, 40 + (i * 29) % 70
        r = 2 if (t // 700 + i) % 4 else 1
        poly(x, y, (0, -r - 2, 1, -1, r + 2, 0, 1, 1, 0, r + 2, -1, 1, -r - 2, 0, -1, -1), AMARELO)


def sombra(cx, ph, rx=20):
    ell(cx, FEET + 1, rx, 3, ph['grama_e'])


# ------------------------------------------------------------ personagem vivo (movimentos e efeitos)
olhos_ult = []
HTOP = {'capi': 77, 'pato': 95, 'elefante': 75, 'polvo': 71, 'calopsita': 84, 'cachorro': 75,
        'gato': 75, 'et': 81, 'sapinho': 65}
AZUL_L = (110, 180, 250)


def _texto_sombra(s, x, y, c, esc=1):
    texto(s, x + 1, y + 1, escuro(c, 0.3), esc)
    texto(s, x, y, c, esc)


def _coracaozinho(x, y, c):
    ell(x - 2, y, 2, 2, c); ell(x + 2, y, 2, 2, c); poly(x, y + 1, (-4, 0, 4, 0, 0, 4), c)


def _estrela4(x, y, c):
    rect(x - 1, y - 3, 2, 6, c); rect(x - 3, y - 1, 6, 2, c)


def _nota(x, y, c):
    ell(x - 2, y + 4, 3, 2.5, c); rect(x, y - 6, 2, 10, c); rect(x, y - 6, 5, 2, c)


def _fx_antes(f, X, base, bx):
    if f == 'buraco':
        ell(X, base + 1, 24, 5, (96, 62, 32)); ell(X, base + 1, 19, 3, (52, 34, 18))
    elif f == 'flor':
        x, y, v = ri(bx + 36), base - 17, (40, 140, 70)
        vl(x, y, 17, v); ell(x + 3, base - 7, 3, 1.5, v)
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
            ell(x + dx, y + dy, 2.5, 2.5, (244, 130, 170))
        ell(x, y, 1.8, 1.8, AMARELO)


def _fx_depois(f, r, t, ms, base):
    cx, top, head, half = r['cx'], r['top'], r['head'], r['half']
    if f == 'notas':
        for i in range(2):
            q = ((ms / 1400) + i * 0.5) % 1
            x, y = cx + (1 if i else -1) * (half + 6 + q * 6), top + 12 - q * 26
            _nota(x + 1, y + 1, INK); _nota(x, y, CREME)
    elif f == 'coracoes':
        for i in range(2):
            q = ((ms / 1200) + i * 0.5) % 1
            x, y = cx + (1 if i else -1) * (half * 0.6 + 4) + math.sin(q * 6) * 2, top + 4 - q * 22
            _coracaozinho(x, y + 1, escuro(STAT['alegria'], 0.5)); _coracaozinho(x, y, STAT['alegria'])
    elif f == 'estrelas':
        for i in range(3):
            a = t / 260 + i * 2.094
            x, y = cx + math.cos(a) * half * 0.85, top + 5 + math.sin(a) * 4
            _estrela4(x + 1, y + 1, escuro(AMARELO, 0.5)); _estrela4(x, y, AMARELO)
    elif f == 'lagrimas':
        for ex, ey in r['eyes'][:2]:
            sd = -1 if ex < cx else 1
            for j in range(2):
                q = ((ms / 650) + j * 0.5) % 1
                ell(ex + sd * (3 + q * 3), ey + 3 + q * 16, 1.5, 2.2, AZUL_L)
    elif f == 'lagrima':
        ex, ey = r['eyes'][0] if r['eyes'] else (cx - 8, head)
        ell(ex - 4, ey + 3, 1.5, 2, AZUL_L)
    elif f == 'poeira':
        q = (ms % 700) / 700
        for sd in (-1, 1):
            ell(cx + sd * (half * 0.8 + q * 12), base - 2 - q * 3, 5 - q * 2, 3.5 - q * 1.5, (232, 222, 200))
    elif f == 'terra':
        for i in range(6):
            q = ((ms / 520) + i / 6) % 1
            sd = 1 if i % 2 else -1
            rect(cx + sd * (12 + q * 30), base - 3 - math.sin(q * math.pi) * 24, 3, 3, (120, 78, 40))
    elif f == 'exclama':
        _texto_sombra('!', cx + half * 0.5 + 2, top - 20, VERMELHO, 2)
    elif f == 'interroga':
        _texto_sombra('?', cx + half * 0.4, top - 20, CREME, 2)
    elif f == 'espirro':
        d = -1 if r['flip'] < 0 else 1
        for i in range(7):
            q = ((ms / 380) + i / 7) % 1
            rect(cx + d * (10 + q * 34), head + 8 + (i - 3) * q * 3, 2, 2, (210, 235, 255))
    elif f == 'zz':
        z = (t // 450) % 3
        _texto_sombra('z', cx + half + z * 4, top - 4 - z * 7, CREME, 2)
    elif f == 'frio':
        c = (160, 210, 255)
        for sd in (-1, 1):
            for j in range(3):
                if (t // 150 + j) % 2:
                    rect(cx + sd * (half + 4 + j * 3) - (3 if sd < 0 else 0), head - 4 + j * 8, 3, 1, c)
        q = (ms % 1100) / 1100
        if q < 0.6:
            ell(cx + 6 + q * 10, head + 10 - q * 8, 2 + q * 4, 1.5 + q * 2.5, (235, 244, 255))
    elif f == 'brilho':
        for i in range(4):
            a = i * 1.57 + 0.6
            if (t // 120 + i) % 2:
                _estrela4(cx + math.cos(a) * (half + 8), top + 24 + math.sin(a) * (half + 4), BRANCO)
    elif f == 'confete':
        cores = (VERMELHO, AMARELO, STAT['energia'], STAT['saude'], STAT['alegria'])
        for i in range(10):
            q = ((ms / 1300) + i * 0.1) % 1
            rect(cx + ((i * 37) % 64 - 32) + math.sin(q * 6 + i) * 4, top - 24 + q * 60, 3, 2, cores[i % 5])
    elif f == 'ha':
        for i in range(2):
            q = ((ms / 800) + i * 0.5) % 1
            _texto_sombra('ha', cx + half + 2 if i else cx - half - 18, top + 10 - q * 14, CREME)
    elif f == 'hic':
        _texto_sombra('hic', cx + half - 4, top - 2, CREME)
    elif f == 'bafo':
        x0, y0, c = ri(cx - 14), ri(head + 2), C((236, 242, 248))
        for j in range(12):
            for i in range(j & 1, 28, 2):
                _fb.pixel(x0 + i, y0 + j, c)
    elif f == 'achado':
        y = top - 14
        ell(cx, y, 7, 7, escuro(AMARELO, 0.6)); ell(cx, y, 6, 6, AMARELO)
        rect(cx - 1, y - 3, 2, 6, claro(AMARELO, 0.6))
        if (t // 150) % 2:
            _estrela4(cx + 9, y - 6, BRANCO)


def recobrir_chao(ph, x0, x1, base, X, t):
    """'Esconder': repinta o chao abaixo dos pes por cima do personagem (o framebuf nao recorta)."""
    x0, x1 = max(0, ri(x0)), min(W, ri(x1))
    y0 = base + 2
    rect(x0, y0, x1 - x0, 240 - y0, ph['grama'])
    rect(x0, 240, x1 - x0, H - 240, ph['grama_e'])
    ell(X, base + 1, 24, 5, (96, 62, 32), True, 2); ell(X, base + 1, 19, 3, (52, 34, 18), True, 2)
    if x1 > 166:
        lago = ph['lago']
        ell(202, 214, 35, 10, OL(lago)); ell(202, 214, 34, 9, lago)
    for x in (12, 60, 118, 176, 226):
        if x0 - 6 < x < x1 + 6:
            capim(x, 258, ph['grama'], 1.4)


def personagem_vivo(id, cx, pe, lp, ph, t, olhos, boca, doente=False, fase='adulto', base=FEET):
    """Desenha o personagem com a pose do movimento (lp) e os efeitos. Devolve dict com
    cx, top, head, half, eyes e flip, ja transformados."""
    sx, sy, fl = lp.get('sx', 1), lp.get('sy', 1), lp.get('flip', 1)
    alt = HTOP.get(id, 75) * (0.62 if fase == 'filhote' else 1)
    X = cx + lp.get('dx', 0)
    hid = lp.get('hide', 0) * alt
    Y = pe + lp.get('dy', 0) + hid
    fx = lp.get('fx', ())
    ms = lp.get('ms', 0)
    k = max(0.35, 1 + min(0, lp.get('dy', 0)) / 45)
    ell(X, base + 1, max(4, ri((12 if fase == 'filhote' else 20) * k * max(sx, 0.6))), 3, ph['grama_e'])
    for f in fx:
        _fx_antes(f, X, base, cx)
    rot = lp.get('rot', 0) * fl
    cy = Y - alt * 0.45 * sy
    transformar(X, Y, fl * sx, sy, rot, cy)
    cab, topo, meia = personagem(id, X, Y, olhos, boca, doente, fase=fase)
    if _T:
        topo = _p(X, topo)[1]
        cab = _p(X, cab)[1]
    sem_transformar()
    if hid > 0:
        recobrir_chao(ph, X - 48, X + 48, base, X, t)
    r = {'cx': X, 'top': topo, 'head': cab, 'half': meia * sx, 'eyes': olhos_ult, 'flip': fl, 'pe': Y}
    for f in fx:
        _fx_depois(f, r, t, ms, base)
    return r


# ------------------------------------------------------------ visitantes e efeitos
def passarinho(x, y, t):
    az = (70, 140, 230)
    ell(x, y, 7, 5, az); ell(x + 6, y - 4, 4, 4, az); px(x + 7, y - 5, INK)
    poly(x + 9, y - 4, (0, 0, 4, 1, 0, 2), AMARELO)
    asa = -4 if (t // 120) % 2 else 2
    ell(x - 1, y + asa / 2, 5, 2, (40, 100, 190))


def tartaruga(x, y, t):
    p = 1 if (t // 250) % 2 else 0
    v = (120, 180, 90)
    ell(x - 7, y + p, 3, 2, v); ell(x + 7, y + 1 - p, 3, 2, v); ell(x - 13, y - 3, 4, 3, v)
    px(x - 15, y - 4, INK)
    ell(x, y - 2, 11, 8, (60, 130, 60), True, 1); ell(x, y - 4, 5, 3, (90, 160, 80))


def borboleta(x, y, t):
    ab = 2 + int(3 * abs(math.sin(t / 90)))
    r = (240, 110, 170)
    ell(x - ab, y - 2, ab, 4, r); ell(x + ab, y - 2, ab, 4, r)
    ell(x - ab, y + 3, ab - 1, 3, (250, 180, 60)); ell(x + ab, y + 3, ab - 1, 3, (250, 180, 60))
    vl(x, y - 4, 9, INK)


def sapo(x, y, t):
    y -= int(abs(math.sin(t / 200)) * 6)
    v = (80, 170, 60)
    ell(x, y, 8, 5, v); ell(x - 4, y - 5, 3, 3, v); ell(x + 4, y - 5, 3, 3, v)
    px(x - 4, y - 5, INK); px(x + 4, y - 5, INK)


def vagalumes(t):
    for i in range(7):
        if (t // 300 + i) % 3:
            rect(ri(30 + i * 30 + 10 * math.sin(t / 700 + i)), ri(120 + 30 * math.sin(t / 900 + i * 2)),
                 2, 2, (255, 250, 120))


def coracao(x, y, c=(255, 80, 120)):
    ell(x - 3, y, 3, 3, c); ell(x + 3, y, 3, 3, c)
    poly(x, y, (-6, 1, 6, 1, 0, 8), c)


def pilula(x, y):
    ell(x - 3, y, 4, 3, VERMELHO); ell(x + 3, y, 4, 3, BRANCO)


def bolhas(x, y, t, c):
    for i in range(6):
        a = t / 160 + i
        ell(x + math.cos(a) * 40, y + math.sin(a * 1.3) * 25, 3, 3, c, False)


def agua_nado(cx, meia, ph, t):
    lago = ph['lago']
    ell(cx, 214, meia + 8, 8, lago)
    for i in range(4):
        a = t / 210 + i * 1.4
        ox, oy = ri(cx + math.cos(a) * (12 + i * 3)), ri(213 + math.sin(a * 1.5) * 3)
        if 168 < ox < 238:
            ell(ox, oy, 3 + i, 2, claro(lago, 0.4), False)


def rastro(cx, dirx):
    for i in range(3):
        bx, comp = ri(cx - dirx * (17 + i * 7)), 6 + i * 4
        if 0 < bx < W - comp:
            hl(bx, 193 - i * 6, comp, (255, 228, 140))


def cocos(n):
    for i in range(n):
        x = 24 + i * 16
        ell(x, 211, 5, 4, COCO); ell(x, 206, 3, 3, COCO)


# ------------------------------------------------------------ icones
def icone_hud(k, x, y, c):
    if k == 'fome':
        rect(x + 1, y + 2, 1, 6, c); rect(x + 3, y, 2, 8, c); rect(x + 6, y + 2, 1, 6, c)
    elif k == 'alegria':
        ell(x + 2, y + 2, 2, 2, c); ell(x + 6, y + 2, 2, 2, c); poly(x, y, (0, 3, 8, 3, 4, 8), c)
    elif k == 'energia':
        poly(x, y, (4, 0, 8, 0, 5, 3, 8, 3, 2, 8, 3, 4, 0, 4), c)
    else:
        rect(x + 3, y, 2, 8, c); rect(x, y + 3, 8, 2, c)


def icone_botao(i, cx, cy, mono=None):
    if i == 0:
        capim(cx, cy + 7, mono or (30, 124, 66), 1.2)
    elif i == 1:
        ell(cx, cy, 8, 8, mono or (255, 154, 31))
        arco(cx, cy, 8, 8, escuro(mono, 0.6) if mono else (210, 90, 30), 2, 2)
        ell(cx - 3, cy - 3, 2, 2, BRANCO)
    elif i == 2:
        a = mono or (90, 170, 235)
        ell(cx, cy + 3, 6, 6, a); poly(cx, cy, (-6, 3, 6, 3, 0, -9), a); ell(cx - 2, cy + 3, 1.5, 1.5, BRANCO)
    else:
        ell(cx - 3, cy, 4, 3, mono or VERMELHO); ell(cx + 3, cy, 4, 3, BRANCO)


def icone_balao(k, x, y):
    if k == 'capim':
        capim(x, y + 7, (30, 124, 66), 1.1)
    elif k == 'zzz':
        texto('z', x - 7, y - 1, STAT['energia']); texto('z', x, y - 6, STAT['energia'])
    elif k == 'coracao':
        c = STAT['alegria']
        ell(x - 3, y - 2, 3.5, 3.5, c); ell(x + 3, y - 2, 3.5, 3.5, c); poly(x, y - 1, (-6.5, 0, 6.5, 0, 0, 7), c)
    elif k == 'bola':
        icone_botao(1, x, y)
    elif k == 'banho':
        icone_botao(2, x, y)
    elif k == 'remedio':
        icone_botao(3, x, y)
    elif k == 'peixe':
        c = (240, 140, 90)
        ell(x - 2, y, 7, 4, c); poly(x + 4, y, (0, 0, 6, -5, 6, 5), c); px(x - 6, y - 1, INK)
    elif k == 'nota':
        ell(x - 2, y + 4, 3, 2.5, INK); vl(x, y - 6, 10, INK); rect(x, y - 6, 5, 2, INK)


# ------------------------------------------------------------ baloes
def fala(s, cx, top):
    """Balao de fala. '|' quebra linha (max. 2 linhas x 14 letras)."""
    L = s.split('|')
    w = max(len(l) for l in L) * 8 + 12
    h = len(L) * 10 + 6
    x = ri(max(8, min(W - 8 - w, cx - w / 2)))
    y = ri(top - h - 8)
    tx = ri(max(x + 8, min(x + w - 8, cx)))
    rrect(x - 1, y - 1, w + 2, h + 2, 4, BOL_OL); poly(tx, y + h, (-5, 0, 5, 0, 0, 7), BOL_OL)
    rrect(x, y, w, h, 3, CREME); poly(tx, y + h - 1, (-4, 0, 4, 0, 0, 6), CREME)
    for i, l in enumerate(L):
        texto(l, x + 6 + (w - 12 - len(l) * 8) // 2, y + 4 + i * 10, TEXTO)


def pensamento(k, cx, top, t):
    bx = min(W - 26, cx + 30)
    by = top - 22 + ri(math.sin(t / 500))
    for x, y, r in ((cx + 12, top - 2, 2), (cx + 19, top - 8, 3)):
        ell(x, y, r + 1, r + 1, BOL_OL); ell(x, y, r, r, CREME)
    rrect(bx - 17, by - 14, 34, 28, 11, BOL_OL); rrect(bx - 16, by - 13, 32, 26, 10, CREME)
    icone_balao(k, bx, by)


def grito(s, cx, top, t):
    w, h = len(s) * 16 + 22, 30
    x = ri(max(10 + w / 2, min(W - 10 - w / 2, cx)))
    y = ri(top - 18)
    j = (t // 140) % 2
    pts, pts_ol = [], []
    for i in range(18):
        a = i / 18 * 2 * math.pi + j * 0.17
        r = 1 if i % 2 else 1.3
        px_, py_ = math.cos(a) * w / 2 * r * 0.82, math.sin(a) * h / 2 * r
        pts += (px_, py_); pts_ol += (px_ * 1.08, py_ * 1.08)
    poly(x, y, pts_ol, BOL_OL); poly(x, y, pts, AMARELO)
    texto(s, x - len(s) * 8, y - 7, TEXTO, 2)


def chamado(k, cx, top, meia, t, urgente=False):
    x = ri(min(W - 24, cx + meia + 4))
    y = ri(top + 8 + (t // 400) % 2)
    ol = VERMELHO if urgente else BOL_OL
    ell(x, y, 14, 13, ol); poly(x - 6, y + 8, (0, 0, 8, 0, -6, 9), ol)
    ell(x, y, 13, 12, CREME); poly(x - 5, y + 7, (0, 0, 6, 0, -5, 7), CREME)
    icone_balao(k, x, y)
    if urgente:
        ell(x + 11, y - 10, 5, 5, VERMELHO); texto('!', x + 8, y - 14, BRANCO)


def sistema(s):
    w = len(s) * 8 + 20
    x = ri((W - w) / 2)
    rrect(x, 36, w, 18, 9, TRAY)
    texto(s, x + 10, 41, CREME)


def bateria_fraca(t):
    """Bateria vermelha piscando no canto de cima, fora da curva do vidro."""
    if (t // 500) % 2:
        return
    x, y = 194, 34
    rrect(x - 2, y - 2, 30, 16, 4, TRAY)
    _fb.rect(x, y, 22, 12, C(VERMELHO))
    _fb.rect(x + 1, y + 1, 20, 10, C(VERMELHO))
    rect(x + 22, y + 4, 3, 4, VERMELHO)
    rect(x + 3, y + 3, 4, 6, VERMELHO)


# ------------------------------------------------------------ Pet: HUD em bandeja
MEDIDORES = ('fome', 'alegria', 'energia', 'saude')


def hud_pet(valores):
    rect(0, 224, W, H - 224, TRAY)
    for i, k in enumerate(MEDIDORES):
        x = 30 + i * 46
        v = valores[k]
        icone_hud(k, x, 229, CREME)
        rect(x + 11, 231, 29, 4, TRAY_BAR)
        rect(x + 11, 231, ri(29 * v / 100), 4, VERMELHO if v < 25 else STAT[k])
    for i in range(4):
        x = 28 + i * 46
        rrect(x, 244, 42, 30, 7, TRAY_BTN)
        icone_botao(i, x + 21, 259, (170, 230, 170) if i == 0 else None)


def botao_pet(x, y):
    """Indice do botao tocado (0 a 3) ou None."""
    if y >= 240 and 28 <= x < 212:
        return min(3, (x - 28) // 46)
    return None


# ------------------------------------------------------------ menu de ajustes
MENU_FUNDO = 272
MODOS = (('pet', 'Cuidar'), ('companion', 'Olhar'), ('explore', 'Passear'))
VEL_MIN = {1: 30, 2: 15, 3: 10}
AJUSTES_ROT = ('-1m', '-1h', '+1h', '+1m')       # acertar o relogio sem internet
AJUSTES_MIN = (-1, -60, 60, 1)


def _seg(x, y, w, h, rot, ligado, fundo=TRAY_BTN):
    rrect(x, y, w, h, 6, ACC if ligado else fundo)
    texto(rot, x + ri((w - len(rot) * 8) / 2), y + ri((h - 8) / 2), INK if ligado else CREME)


def alca():
    rrect(106, 3, 28, 4, 2, CREME)


def menu(borda, modo, id, hora_modo, vel, relogio, som_ligado, pendente=None, confirma=None,
         legenda='', fase='adulto'):
    """Painel de ajustes com a borda de baixo em y = borda (0 a 272).
    pendente = personagem escolhido nas setas e ainda nao confirmado;
    confirma = 'trocar' ou 'zerar' mostra a pergunta 'comeca do zero' no lugar da hora."""
    o = borda - MENU_FUNDO                     # tudo desce junto com o painel
    rect(0, o, W, MENU_FUNDO - 10, TRAY)
    rrect(0, o + MENU_FUNDO - 22, W, 22, 10, TRAY)
    centro('Ajustes', o + 12, CREME)
    onda = CREME if som_ligado else MUTEDM
    rect(196, o + 13, 3, 5, CREME); poly(198, o + 15, (0, -1, 6, -5, 6, 8, 0, 4), CREME)
    rect(206, o + 13, 1, 5, onda); rect(209, o + 11, 1, 9, onda)
    if not som_ligado:
        linha(194, o + 22, 211, o + 9, VERMELHO)
    for i in range(3):
        rect(36 + i * 4, o + 19 - i * 3, 3, 3 + i * 3, CREME if i < 2 else MUTEDM)
    texto('modo', 20, o + 29, MUTEDM)
    for i, (mid, rot) in enumerate(MODOS):
        _seg(20 + i * 68, o + 40, 64, 30, rot, modo == mid)
    texto('personagem', 20, o + 78, MUTEDM)
    mostra = pendente or id
    n = len(ELENCO)
    idx = ELENCO.index(mostra) if mostra in ELENCO else 0
    for k, x in ((-1, 56), (1, 184)):
        personagem(ELENCO[(idx + k) % n], x, o + 142, contorno=False, s=0.3, cru=True)
    rrect(83, o + 87, 74, 64, 9, ACC); rrect(85, o + 89, 70, 60, 8, TRAY_BTN)
    if not pendente and fase == 'ovo':
        ovo(120, o + 146, contorno=False, grama=TRAY, s=0.75)
    elif pendente or fase != 'estrela':
        personagem(mostra, 120, o + 144, 'feliz', contorno=False,
                   s=0.4 if mostra in ('pato', 'calopsita') else 0.45, cru=True)
    poly(14, o + 119, (0, 0, 8, -7, 8, 7), CREME); poly(226, o + 119, (0, 0, -8, -7, -8, 7), CREME)
    if pendente:
        centro(NOMES[pendente] + '?', o + 156, ACC)
    else:
        centro(legenda or NOMES[id], o + 156, CREME)
    if confirma:
        rrect(16, o + 168, 208, 74, 8, TRAY_BTN)
        if confirma == 'trocar':
            centro('Trocar de bicho?', o + 176, CREME)
            centro('Comeca do zero!', o + 190, ACC)
        else:
            centro('Recomecar?', o + 176, CREME)
            centro('Volta a ser ovo!', o + 190, ACC)
        _seg(24, o + 206, 92, 28, 'Sim', True)
        _seg(124, o + 206, 92, 28, 'Nao', False, TRAY)
    else:
        texto('hora', 20, o + 171, MUTEDM)
        _seg(20, o + 182, 98, 26, 'Real', hora_modo == 'real')
        _seg(122, o + 182, 98, 26, 'Simulada', hora_modo == 'sim')
        if hora_modo == 'sim':
            for i, v in enumerate((1, 2, 3)):
                _seg(20 + i * 68, o + 214, 64, 22, '%dx' % v, vel == v)
            centro('dia em %d min' % VEL_MIN[vel], o + 244, MUTEDM)
        else:
            for i, rot in enumerate(AJUSTES_ROT):
                _seg(20 + i * 51, o + 214, 47, 22, rot, False)
            centro('agora ' + relogio, o + 242, CREME)
        _seg(16, o + 248, 48, 18, 'zerar', False)
        _seg(176, o + 248, 48, 18, 'som' if som_ligado else 'mudo', som_ligado)   # liga/desliga o som
    rrect(100, o + 256, 40, 4, 2, MUTEDM)
    if borda < H:
        hl(0, borda, W, (24, 18, 26))


def menu_toque(x, y, hora_modo, confirma=None):
    """Mesmas areas do menuHit() da referencia, mais som, acerto do relogio, zerar e confirmacao."""
    if y < 26 and x > 186:
        return ('som', None)
    if 40 <= y < 70:
        i = (x - 20) // 68
        if 0 <= i < 3:
            return ('modo', MODOS[i][0])
    if 88 <= y < 164:
        if x < 82:
            return ('personagem', -1)
        if x > 158:
            return ('personagem', 1)
        return ('cartao', None)
    if confirma:
        if 204 <= y < 236:
            return ('sim', None) if x < 120 else ('nao', None)
        if y >= 250:
            return ('fechar', None)
        return None
    if 182 <= y < 208:
        return ('hora', 'real' if x < 120 else 'sim')
    if hora_modo == 'sim' and 214 <= y < 236:
        i = (x - 20) // 68
        if 0 <= i < 3:
            return ('vel', i + 1)
    if hora_modo != 'sim' and 212 <= y < 238 and 20 <= x < 222:
        return ('ajuste', AJUSTES_MIN[min(3, (x - 20) // 51)])
    if y >= 246 and x < 68:
        return ('zerar', None)
    if y >= 246 and x >= 172:
        return ('som', None)
    if y >= 250:
        return ('fechar', None)
    return None


def _volta(x, per):
    return ((x % per) + per) % per


def passeio(ph, off, t, id, pe, moedas, campo, mundo, olhos='feliz', boca='sorriso', auto=0, fase='adulto'):
    """off = deslocamento do mundo em px; mundo = lista de x das moedas ainda no chao;
    auto = direcao do andar sozinho (a seta desse lado fica laranja)."""
    for i in range(6):
        arvore(_volta(i * 60 - off // 2, W + 60) - 30, GROUND, ph['longe'], 10)
    rect(0, GROUND, W, H - GROUND, ph['grama'])
    x = -_volta(off, 16)
    while x < W:
        rect(x, GROUND + 16, 8, 6, ph['grama_e'])
        x += 16
    rect(0, 240, W, H - 240, ph['grama_e'])
    for i in range(4):
        arvore(_volta(i * 90 - off, W + 80) - 40, GROUND, ph['perto'], 16, True)
    sx = _volta(200 - off, W + 80) - 40
    rect(sx, GROUND - 26, 3, 26, MADEIRA)
    rect(sx - 9, GROUND - 30, 21, 10, MADEIRA_CL); _fb.rect(ri(sx - 9), GROUND - 30, 21, 10, C(OL(MADEIRA_CL)))
    for wx in mundo:
        mx = wx - off
        if -10 < mx < W + 10:
            my = GROUND - 34 - abs(math.sin(t / 300 + wx)) * 4
            ell(mx, my, 4, 4, OL(AMARELO)); ell(mx, my, 3, 3, AMARELO)
    if fase != 'estrela':
        ell(110, FEET + 1, 12 if fase == 'filhote' else 26, 4, ph['grama_e'])
        personagem(id, 110, pe, olhos, boca, fase=fase, grama=ph['grama'])
    etiqueta('campo %d' % campo, 8, x=30)
    s = 'x%d' % moedas
    x0 = W - 30 - (len(s) * 8 + 24)
    etiqueta('  ' + s, 8, x=x0)
    ell(x0 + 12, 16, 4, 4, OL(AMARELO)); ell(x0 + 12, 16, 3, 3, AMARELO)
    poly(10, 140, (0, 0, 8, -6, 8, 6), ACC if auto < 0 else CREME)
    poly(230, 140, (0, 0, -8, -6, -8, 6), ACC if auto > 0 else CREME)
