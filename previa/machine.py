# machine falso para rodar o firmware no MicroPython unix
class Pin:
    IN = 0; OUT = 1; PULL_UP = 2
    def __init__(self, *a, **k): self.v = 1
    def __call__(self, v=None): return self.v
    def value(self, v=None): return self.v
class I2C:
    def __init__(self, *a, **k): pass
    def scan(self): return []
class SPI:
    def __init__(self, *a, **k): pass
class PWM:
    def __init__(self, *a, **k): pass
    def duty_u16(self, v): pass
class I2S:
    def __init__(self, *a, **k): pass
