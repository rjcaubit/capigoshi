# Clima (issue #4): tipo do tempo (rede.tipo_de) e graus viram indice de tempo e efeito nos drives. Sem float.
from companion import config as C

TEMPOS = ('sol', 'nublado', 'chuva', 'tempestade')
GRUPO = {'sol': 0, 'nublado': 1, 'neblina': 1, 'vento': 1, 'chuva': 2, 'neve': 2, 'tempestade': 3}


def indice(tipo):
    """Nome de rede.tipo_de -> 0..3, ou None sem previsao."""
    return GRUPO.get(tipo) if tipo else None


def efeito(tipo, graus):
    """(alvo do humor, % de puxada, energia/min, curiosidade/min) x10 para este clima."""
    k = indice(tipo)
    if k is None:
        return 0, 0, 0, 0
    e = C.CLIMA_ENERGIA[k]
    if graus is not None and graus < C.FRIO:
        e += C.FRIO_ENERGIA
    return C.CLIMA_HUMOR[k], C.CLIMA_PUXA_PCT, e, C.CLIMA_CURIOSIDADE[k]
