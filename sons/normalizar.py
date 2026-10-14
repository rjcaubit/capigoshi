# Deixa cada som o mais alto possivel sem distorcer: estica ate o pico bater em 90% do limite.
# Uso: python3 sons/normalizar.py sons/*.raw sons/extra/*.raw   (16 bits, estereo, sem cabecalho)
import sys
from array import array

ALVO = 0.90 * 32767

for caminho in sys.argv[1:]:
    a = array('h')
    with open(caminho, 'rb') as f:
        a.frombytes(f.read())
    pico = max(max(a), -min(a)) if a else 0
    if not pico:
        continue
    ganho = ALVO / pico
    if 0.97 < ganho < 1.03:
        print('ja esta no ponto  %s' % caminho)
        continue
    b = array('h', (int(v * ganho) for v in a))
    with open(caminho, 'wb') as f:
        f.write(b.tobytes())
    print('%4.1fx mais alto  %s' % (ganho, caminho))
