# Fumaca de portabilidade: roda 1 h simulada no MicroPython unix. Uso: micropython companion/sim/fumaca.py
import sys
sys.path.insert(0, '.')
from companion.sim import rodar
from companion.sim.dono import Dono

cer, acoes = rodar.simular(Dono(), 1 / 24)
print('micropython ok', cer.ticks_rodados, len(acoes))
