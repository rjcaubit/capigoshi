# Raio-X no simulador (issue #5): roda um cenario e grava a pagina do cerebro com o resumo() do fim.
# Uso: python3 -m companion.sim.raiox [cenario] [dias] [semente] [chuva]
import os
import sys
import json
from companion import config as C
from companion.sim.rodar import simular, CENARIOS
from companion.sim.aceite import TEMPOS_CHUVA

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELO = os.path.join(os.path.dirname(AQUI), 'raiox.html')
SAIDA = os.path.join(AQUI, 'saida')
MARCA = '/*DADOS*/null'


def pagina(resumo):
    """A pagina do raio-X com o resumo embutido (a mesma que o portal da placa vai servir com /brain.json)."""
    with open(MODELO, encoding='utf-8') as f:
        html = f.read()
    return html.replace(MARCA, json.dumps(resumo).replace('</', '<\\/'), 1)


def texto(r):
    """Resumo para o terminal."""
    linhas = ['idade %.1f dias, fazendo %s%s' % (r['idade_s'] / 86400, r['acao'], ' (dormindo)' if r['dormindo'] else '')]
    linhas.append('drives: ' + ', '.join('%s %d' % (n, v // 10) for n, v in r['drives']))
    passo = r['relogio']['passo_min']
    for c, acao, w in r['relogio']['habitos']:
        m = c * passo
        linhas.append('habito %02dh%02d: %s (%d)' % (m // 60, m % 60, acao, w))
    linhas.append('gosta: ' + ', '.join('%s %+d' % (a, x) for a, x in r['gosta']))
    linhas.append('evita: ' + ', '.join('%s %+d' % (a, x) for a, x in r['evita']))
    linhas.append('hoje: ' + ', '.join('%s %d' % (a, n) for a, n in r['hoje']))
    linhas.append('%d recompensas guardadas, entrada mudou %d%%' % (len(r['recompensas']), r['rede']['ih_mudou_pct']))
    return '\n'.join(linhas)


def main(argv):
    cenario = argv[0] if argv else 'semana'
    dias = int(argv[1]) if len(argv) > 1 else 7
    semente = int(argv[2]) if len(argv) > 2 else 1
    chuva = len(argv) > 3 and argv[3] == 'chuva'
    C.RAIOX_HORAS = max(C.RAIOX_HORAS, dias * 24)
    cer, _ = simular(CENARIOS[cenario](), dias, semente, tempos=TEMPOS_CHUVA if chuva else None)
    r = cer.resumo()
    os.makedirs(SAIDA, exist_ok=True)
    nome = os.path.join(SAIDA, 'raiox-%s-%d%s.html' % (cenario, semente, '-chuva' if chuva else ''))
    with open(nome, 'w', encoding='utf-8') as f:
        f.write(pagina(r))
    print(texto(r))
    print('pagina: ' + nome)


if __name__ == '__main__':
    main(sys.argv[1:])
