# hw.py - drivers da Waveshare ESP32-S3-Touch-LCD-1.83 em MicroPython puro
# Tela ST7789 (SPI) | Toque CST816D | Sensor QMI8658 | Relogio PCF85063
# Alto-falante ES8311 | Microfones ES7210
import time, struct, math, framebuf
from array import array
from machine import Pin, SPI, PWM, I2S

W, H = 240, 284


def cor(r, g, b):
    """RGB -> RGB565 ja com os bytes trocados (a tela espera big-endian)."""
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return ((c & 0xFF) << 8) | (c >> 8)


# ---------------------------------------------------------------- Tela
class Tela:
    def __init__(self):
        self.spi = SPI(1, baudrate=40_000_000, polarity=0, phase=0,
                       sck=Pin(6), mosi=Pin(7))
        self.dc = Pin(4, Pin.OUT, value=0)
        self.cs = Pin(5, Pin.OUT, value=1)
        self.rst = Pin(38, Pin.OUT, value=1)
        self.luz = PWM(Pin(40), freq=2000, duty_u16=0)
        self.buf = bytearray(W * H * 2)          # 136 KB: precisa do firmware com PSRAM
        self.fb = framebuf.FrameBuffer(self.buf, W, H, framebuf.RGB565)
        self._iniciar()

    def _cmd(self, c, dados=None):
        self.cs(0)
        self.dc(0)
        self.spi.write(bytes([c]))
        if dados:
            self.dc(1)
            self.spi.write(dados)
        self.cs(1)

    def _iniciar(self):
        self.rst(0); time.sleep_ms(20); self.rst(1); time.sleep_ms(120)
        self._cmd(0x01); time.sleep_ms(150)      # reset por software
        self._cmd(0x11); time.sleep_ms(120)      # sai do modo sono
        self._cmd(0x3A, b'\x55')                 # 16 bits por pixel
        self._cmd(0x36, b'\x00')                 # orientacao retrato
        self._cmd(0x21)                          # cores invertidas (painel IPS)
        self._cmd(0x13)
        self._cmd(0x29); time.sleep_ms(20)       # liga a tela
        self._cmd(0x2A, bytes([0, 0, 0, W - 1]))
        self._cmd(0x2B, bytes([0, 0, (H - 1) >> 8, (H - 1) & 0xFF]))
        self.brilho(80)

    def brilho(self, pct):
        self.luz.duty_u16(int(65535 * pct / 100))

    def mostrar(self):
        self.cs(0)
        self.dc(0)
        self.spi.write(b'\x2C')
        self.dc(1)
        self.spi.write(self.buf)
        self.cs(1)


# ---------------------------------------------------------------- Toque
class Toque:
    END = 0x15

    def __init__(self, i2c):
        self.i2c = i2c
        rst = Pin(39, Pin.OUT, value=1)
        rst(0); time.sleep_ms(10); rst(1); time.sleep_ms(60)
        try:
            i2c.writeto_mem(self.END, 0xFE, b'\x01')  # nao deixar o chip dormir
        except OSError:
            pass

    def ler(self):
        """Retorna (x, y) enquanto o dedo estiver na tela, ou None."""
        try:
            b = self.i2c.readfrom_mem(self.END, 0x02, 5)
        except OSError:
            return None
        if b[0] == 0:
            return None
        x = ((b[1] & 0x0F) << 8) | b[2]
        y = ((b[3] & 0x0F) << 8) | b[4]
        if x >= W or y >= H:
            return None
        return x, y


# ---------------------------------------------------------------- Sensor de movimento
class Movimento:
    END = 0x6B

    def __init__(self, i2c):
        self.i2c = i2c
        self.ok = False
        try:
            if i2c.readfrom_mem(self.END, 0x00, 1)[0] == 0x05:
                i2c.writeto_mem(self.END, 0x02, b'\x40')  # auto-incremento
                i2c.writeto_mem(self.END, 0x03, b'\x15')  # +-4g, 250 Hz
                i2c.writeto_mem(self.END, 0x08, b'\x01')  # liga acelerometro
                self.ok = True
        except OSError:
            pass

    def forca_g(self):
        """Aceleracao total em g (parado = 1.0)."""
        if not self.ok:
            return 1.0
        try:
            ax, ay, az = struct.unpack('<hhh', self.i2c.readfrom_mem(self.END, 0x35, 6))
        except OSError:
            return 1.0
        return math.sqrt(ax * ax + ay * ay + az * az) / 8192


# ---------------------------------------------------------------- Relogio
def _bcd(v):
    return (v >> 4) * 10 + (v & 0x0F)


def _dec(v):
    return ((v // 10) << 4) | (v % 10)


class Relogio:
    END = 0x51

    def __init__(self, i2c):
        self.i2c = i2c
        self.ok = self.END in i2c.scan()

    def ler(self):
        """(ano, mes, dia, hora, min, seg) ou None se o relogio nunca foi acertado."""
        if not self.ok:
            return None
        b = self.i2c.readfrom_mem(self.END, 0x04, 7)
        if b[0] & 0x80:
            return None
        ano = 2000 + _bcd(b[6])
        if ano < 2025:
            return None
        return (ano, _bcd(b[5] & 0x1F), _bcd(b[3] & 0x3F),
                _bcd(b[2] & 0x3F), _bcd(b[1] & 0x7F), _bcd(b[0] & 0x7F))

    def acertar(self, ano, mes, dia, hora, minuto, seg=0):
        if not self.ok:
            return
        self.i2c.writeto_mem(self.END, 0x04, bytes([
            _dec(seg), _dec(minuto), _dec(hora), _dec(dia), 0, _dec(mes), _dec(ano - 2000)]))

    def epoch(self):
        t = self.ler()
        return time.mktime(t + (0, 0)) if t else 0

    def somar_minutos(self, m):
        e = self.epoch() or time.mktime((2026, 1, 1, 12, 0, 0, 0, 0))
        t = time.localtime(e + m * 60)
        self.acertar(t[0], t[1], t[2], t[3], t[4], t[5])


# ---------------------------------------------------------------- Bateria (AXP2101)
class Bateria:
    """Chip de energia AXP2101: porcentagem da bateria e se esta carregando.
    Registradores conforme o exemplo 01_AXP2101 da Waveshare e a XPowersLib."""
    END = 0x34

    def __init__(self, i2c):
        self.i2c = i2c
        self.ok = False
        try:
            r = i2c.readfrom_mem(self.END, 0x30, 1)[0]            # canais do ADC
            i2c.writeto_mem(self.END, 0x30, bytes([(r | 0x1D) & ~0x02]))
            self.ok = True
        except OSError:
            pass

    def _r(self, reg):
        return self.i2c.readfrom_mem(self.END, reg, 1)[0]

    def porcentagem(self):
        """0 a 100, ou None sem bateria ou sem o chip."""
        if not self.ok:
            return None
        try:
            if not self._r(0x00) & 0x08:                            # STATUS1 bit 3: bateria presente
                return None
            return min(100, self._r(0xA4))
        except OSError:
            return None

    def carregando(self):
        if not self.ok:
            return False
        try:
            return (self._r(0x01) >> 5) & 0x03 == 1                 # STATUS2: 1 = carregando
        except OSError:
            return False


# ---------------------------------------------------------------- Som e microfone
MELODIAS = {
    'clique':  [(1800, 25)],
    'feliz':   [(784, 80), (988, 80), (1175, 130)],
    'amor':    [(659, 70), (784, 70), (1047, 150)],
    'comer':   [(600, 50), (0, 30), (600, 50), (0, 30), (700, 70)],
    'banho':   [(900, 40), (1300, 40), (1100, 40), (1500, 60)],
    'remedio': [(523, 90), (659, 90), (784, 160)],
    'susto':   [(1400, 60), (900, 60), (500, 140)],
    'bocejo':  [(500, 140), (400, 180)],
    'piu':     [(2600, 40), (0, 30), (3000, 60)],
    'triste':  [(440, 120), (370, 180)],
}


class Som:
    TAXA = 16000
    ES8311 = 0x18
    ES7210 = 0x40

    def __init__(self, i2c):
        self.i2c = i2c
        self.ligado = True
        self.alto_ok = False
        self.mic_ok = False
        self.mic = None
        self.tx = None                            # som tocando em segundo plano
        self.fim = 0
        self._cache = {}
        self.pa = Pin(46, Pin.OUT, value=0)       # amplificador do alto-falante
        try:
            self._iniciar_es8311()
            self.alto_ok = True
        except Exception as e:
            print('Alto-falante indisponivel:', e)
        try:
            # o ES7210 precisa de um clock mestre; geramos com PWM no pino 16
            self.mclk = PWM(Pin(16), freq=self.TAXA * 256, duty_u16=32768)
            self._iniciar_es7210()
            self.mic_ok = True
        except Exception as e:
            print('Microfone indisponivel:', e)
        self._abrir_mic()

    # --- registradores
    def _w(self, end, reg, val):
        self.i2c.writeto_mem(end, reg, bytes([val & 0xFF]))

    def _r(self, end, reg):
        return self.i2c.readfrom_mem(end, reg, 1)[0]

    def _iniciar_es8311(self):
        a, w, r = self.ES8311, self._w, self._r
        w(a, 0x0D, 0xFA); w(a, 0x44, 0x08); w(a, 0x44, 0x08)
        for reg, val in ((0x01, 0x30), (0x02, 0x00), (0x03, 0x10), (0x16, 0x24),
                         (0x04, 0x10), (0x05, 0x00), (0x0B, 0x00), (0x0C, 0x00),
                         (0x10, 0x1F), (0x11, 0x7F), (0x00, 0x80)):
            w(a, reg, val)
        w(a, 0x01, 0xBF)                          # clock interno vindo do BCLK (sem MCLK)
        w(a, 0x06, r(a, 0x06) & ~0x20)
        w(a, 0x13, 0x10); w(a, 0x1B, 0x0A); w(a, 0x1C, 0x6A); w(a, 0x44, 0x58)
        # 16 kHz: divisores
        w(a, 0x02, (r(a, 0x02) & 0x07) | (3 << 3))
        w(a, 0x05, 0x00)
        w(a, 0x03, (r(a, 0x03) & 0x80) | 0x10)
        w(a, 0x04, (r(a, 0x04) & 0x80) | 0x20)
        w(a, 0x07, r(a, 0x07) & 0xC0)
        w(a, 0x08, 0xFF)
        w(a, 0x06, (r(a, 0x06) & 0xE0) | 0x03)
        # 16 bits, I2S, liga o DAC
        w(a, 0x09, (r(a, 0x09) | 0x0C) & 0xBF)
        w(a, 0x0A, (r(a, 0x0A) | 0x0C) & 0xBF)
        for reg, val in ((0x17, 0xBF), (0x0E, 0x02), (0x12, 0x00), (0x14, 0x1A),
                         (0x0D, 0x01), (0x15, 0x40), (0x37, 0x08), (0x45, 0x00),
                         (0x31, 0x00), (0x32, 0xB4)):     # 0x32 = volume
            w(a, reg, val)

    def _iniciar_es7210(self):
        a, w, r = self.ES7210, self._w, self._r
        for reg, val in ((0x00, 0xFF), (0x00, 0x41), (0x01, 0x3F), (0x09, 0x30),
                         (0x0A, 0x30), (0x23, 0x2A), (0x22, 0x0A), (0x20, 0x0A),
                         (0x21, 0x2A)):
            w(a, reg, val)
        w(a, 0x08, r(a, 0x08) & 0xFE)             # modo escravo
        for reg, val in ((0x40, 0x43), (0x41, 0x70), (0x42, 0x70), (0x07, 0x20),
                         (0x02, 0xC1)):
            w(a, reg, val)
        w(a, 0x11, (r(a, 0x11) & 0x1C) | 0x60)    # I2S, 16 bits
        w(a, 0x01, 0x34)                          # clocks dos mics 1 e 2
        w(a, 0x06, 0x00)
        for reg in (0x47, 0x48, 0x49, 0x4A):
            w(a, reg, 0x08)
        w(a, 0x4B, 0x00); w(a, 0x4C, 0xFF)        # liga mic 1 e 2
        for reg in (0x43, 0x44):
            w(a, reg, 0x10 | 10)                  # ganho de 30 dB
        w(a, 0x12, 0x00)
        w(a, 0x40, 0x43); w(a, 0x00, 0x71); w(a, 0x00, 0x41)

    # --- microfone
    def _abrir_mic(self):
        if not self.mic_ok or self.mic:
            return
        try:
            # buffer pequeno: cada leitura pega so ~8 ms de audio recente e nao segura o jogo
            self.mic = I2S(0, sck=Pin(9), ws=Pin(45), sd=Pin(10), mode=I2S.RX,
                           bits=16, format=I2S.STEREO, rate=self.TAXA, ibuf=4096)
            self._amostras = array('h', bytes(512))
        except Exception as e:
            print('Erro ao abrir o microfone:', e)
            self.mic_ok = False

    def _fechar_mic(self):
        if self.mic:
            self.mic.deinit()
            self.mic = None

    def volume_mic(self):
        """Pico do som captado (0 a 32767)."""
        if not self.mic:
            return 0
        try:
            self.mic.readinto(self._amostras)
        except Exception:
            return 0
        return max(max(self._amostras), -min(self._amostras))

    # --- alto-falante
    def _gerar(self, nome):
        partes = []
        for freq, ms in MELODIAS[nome]:
            total = self.TAXA * ms // 1000
            if freq == 0:
                partes.append(bytes(total * 4))
                continue
            periodo = max(2, self.TAXA // freq)
            onda = bytearray(periodo * 4)
            for i in range(periodo):
                v = int(6000 * math.sin(2 * math.pi * i / periodo))
                struct.pack_into('<hh', onda, i * 4, v, v)
            partes.append(bytes(onda) * (total // periodo))
        return b''.join(partes)

    def _carregar(self, nome):
        """sons/extra/<nome>.raw, sons/<nome>.raw (16 kHz, 16 bits, estereo) ou a melodia sintetizada."""
        for pasta in ('sons/extra', 'sons'):           # extra = baixados do Pixabay (fora do git)
            try:
                with open('%s/%s.raw' % (pasta, nome), 'rb') as f:
                    return f.read()
            except OSError:
                pass
        return self._gerar(nome) if nome in MELODIAS else None

    def tocar(self, nome):
        if not (self.ligado and self.alto_ok):
            return
        if nome not in self._cache:
            self._cache[nome] = self._carregar(nome)
        if not self._cache[nome]:
            return
        dados = self._cache[nome]
        self._parar()
        self._fechar_mic()                         # o barramento de audio e compartilhado
        try:
            tx = I2S(0, sck=Pin(9), ws=Pin(45), sd=Pin(8), mode=I2S.TX,
                     bits=16, format=I2S.STEREO, rate=self.TAXA, ibuf=len(dados) + 4000)
            tx.irq(self._sem_espera)               # modo sem bloqueio: o jogo nao para enquanto toca
            self.pa(1)
            tx.write(dados)
            tx.write(bytes(1600))
            self.tx = tx
            self.fim = time.ticks_add(time.ticks_ms(), len(dados) // (self.TAXA * 4 // 1000) + 80)
        except Exception as e:
            print('Erro ao tocar som:', e)
            self._parar()
            self._abrir_mic()

    def _sem_espera(self, i2s):
        pass

    def _parar(self):
        if self.tx:
            try:
                self.tx.deinit()
            except Exception:
                pass
            self.tx = None
        self.pa(0)

    def atualizar(self):
        """Chame a cada quadro: fecha o alto-falante quando o som acaba e volta o microfone."""
        if self.tx and time.ticks_diff(time.ticks_ms(), self.fim) >= 0:
            self._parar()
            self._abrir_mic()
