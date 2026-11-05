# Testes de aceite da fase 0 (secao 11). Uso: python3 -m companion.sim.aceite [velocidade|silencio|habito|sementes|todos]
import sys
import time
from companion import actions as A
from companion.sim.rodar import simular, CENARIOS, sons_por_hora

INICIO = 6 * 3600                                  # o simulador comeca as 6h do dia 0
ALVO_HABITO = (A.INDICE['pedir_carinho'], A.INDICE['chamar_baixo'])
LIMITE_SEMANA_S = 180                              # calibrado: 1 min e inviavel em Python puro a 20 Hz


def velocidade():
    t0 = time.time()
    simular(CENARIOS['semana'](), 7)
    dt = time.time() - t0
    print('velocidade: 7 dias em %.0f s (limite %d s)' % (dt, LIMITE_SEMANA_S))
    return dt <= LIMITE_SEMANA_S


def silencio():
    cer, acoes = simular(CENARIOS['silencio'](), 3, falante=6)
    inicio = sons_por_hora(acoes, INICIO, INICIO + 6 * 3600, cer)
    dia3 = sons_por_hora(acoes, INICIO + 2 * 86400, INICIO + 3 * 86400, cer)
    print('silencio: %.1f sons/h nas 6 primeiras horas, %.1f sons/h no dia 3 (meta < 2)' % (inicio, dia3))
    return inicio > 2 and dia3 < 2


def dias_habito(semente):
    cer, acoes = simular(CENARIOS['habito'](), 7, semente)
    bons = 0
    for dia in range(7):
        base = dia * 86400
        j0, j1 = base + 18 * 3600 + 50 * 60, base + 19 * 3600 + 10 * 60
        na_janela = sum(1 for s, a in acoes if j0 <= s < j1 and a in ALVO_HABITO)
        fora = sum(1 for s, a in acoes if base + 8 * 3600 <= s < base + 22 * 3600 and not j0 <= s < j1
                   and a in ALVO_HABITO)
        taxa_j, taxa_f = na_janela * 3.0, fora / (14 - 1 / 3)
        ok = na_janela >= 1 and taxa_j >= 2 * taxa_f
        bons += ok
        print('habito dia %d: %.1f/h na janela 18h50-19h10, %.1f/h fora %s' % (dia + 1, taxa_j, taxa_f,
                                                                               'ok' if ok else '-'))
    return bons


def habito():
    bons = dias_habito(1)
    print('habito: %d de 7 dias (meta 5)' % bons)
    return bons >= 5


def sementes():
    """Robustez do habito (issue #3): sementes 1 a 4, media >= 5 dias e nenhuma abaixo de 4."""
    dias = [dias_habito(s) for s in (1, 2, 3, 4)]
    print('sementes: %s dias, media %.2f (meta media >= 5, minimo >= 4)' % (dias, sum(dias) / 4))
    return sum(dias) >= 20 and min(dias) >= 4


if __name__ == '__main__':
    from companion import config as C
    for kv in sys.argv[2:]:                         # ajuste de calibracao: NOME=valor
        k, v = kv.split('=')
        setattr(C, k, int(v))
    qual = sys.argv[1] if len(sys.argv) > 1 else 'todos'
    testes = {'velocidade': velocidade, 'silencio': silencio, 'habito': habito, 'sementes': sementes}
    nomes = list(testes) if qual == 'todos' else [qual]
    falhou = [n for n in nomes if not testes[n]()]
    print('FALHOU: ' + ', '.join(falhou) if falhou else 'ACEITE OK')
    sys.exit(1 if falhou else 0)
