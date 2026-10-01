# hw falso: framebuf real, entradas controladas pelo roteiro de previa
import framebuf
W, H = 240, 284
def cor(r, g, b):
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)
ENTRADA = {'toque': None, 'g': 1.0, 'relogio': (2026, 9, 30, 10, 0, 0), 'bateria': 80, 'carregando': False}
class Tela:
    def __init__(self):
        self.buf = bytearray(W * H * 2)
        self.fb = framebuf.FrameBuffer(self.buf, W, H, framebuf.RGB565)
    def mostrar(self): pass
class Toque:
    def __init__(self, i2c): pass
    def ler(self): return ENTRADA['toque']
class Movimento:
    def __init__(self, i2c): pass
    def forca_g(self): return ENTRADA['g']
class Relogio:
    def __init__(self, i2c): self.ok = True
    def ler(self): return ENTRADA['relogio']
    def acertar(self, *a): pass
    def epoch(self): return 0
    def somar_minutos(self, m): pass
class Som:
    def __init__(self, i2c): self.ligado = True
    def tocar(self, nome): pass
    def atualizar(self): pass
    def volume_mic(self): return ENTRADA.get('mic', 0)
class Bateria:
    def __init__(self, i2c): self.ok = True
    def porcentagem(self): return ENTRADA['bateria']
    def carregando(self): return ENTRADA['carregando']
