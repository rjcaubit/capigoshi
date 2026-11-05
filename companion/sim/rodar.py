# Simulador (secao 10): roda o cerebro em velocidade acelerada com um dono simulado.
# Uso: python3 -m companion.sim.rodar [silencio|habito|semana] [dias] [semente]
import sys
import time
import random
from companion import actions as A
from companion import config as C
from companion.cerebro import Cerebro
from companion.sim.dono import Dono
from companion.sim.mundo import Mundo

CENARIOS = {
    'semana': lambda: Dono(),
    'silencio': lambda: Dono(p_som=0.0, p_pedido=0.3),
    'barulho': lambda: Dono(p_som=1.0, p_pedido=0.3),
    'habito': lambda: Dono(p_som=0.0, p_pedido=0.0, presente=(), carinho_hora=19, p_toque_hora=0,
                             refeicoes=(8, 12, 21)),     # refeicao fora da janela das 19h
}


def tornar_falante(cer, fator):
    """Capi que nasce barulhenta (o problema de hoje): pesos das acoes com som multiplicados por fator."""
    no, w = cer.rede.no, cer.rede.w_ho
    for h in range(C.N_EXC):
        for o in A.COM_SOM:
            w[h * no + o] = min(C.W_MAX, w[h * no + o] * fator)


def simular(dono, dias, semente=1, inicio_h=6, falante=0):
    random.seed(semente)
    cer = Cerebro(semente)
    if falante:
        tornar_falante(cer, falante)
    mundo = Mundo()
    agenda = []                                # (segundo, evento)
    acoes = []                                 # (segundo, acao) de cada decisao nova
    comida_ate = -1
    fim = int(dias * 86400)
    s0 = inicio_h * 3600
    for seg in range(s0, s0 + fim):
        minuto = (seg // 60) % 1440
        for ev in dono.espontaneo(minuto, seg % 60):
            agenda.append((seg, ev))
        pend = [e for e in agenda if e[0] <= seg]
        if pend:
            agenda = [e for e in agenda if e[0] > seg]
            for _, ev in pend:
                if ev in ('carinho', 'toque', 'comida', 'estrela'):
                    mundo.tocar(seg)
                if ev == 'comida':
                    comida_ate = seg + 60
                cer.evento(ev, seg * 1000)
        s = mundo.sentidos(seg, seg < comida_ate)
        antes = len(cer.log)
        cer.segundo(s, seg * 1000)
        for item in cer.log[antes:]:
            if item[0] == 'A':
                acoes.append((item[1], item[2]))
                for atraso, ev in dono.reagir(item[2], minuto):
                    agenda.append((seg + atraso, ev))
        if len(cer.log) > 1000:
            del cer.log[:500]
    return cer, acoes


def sons_por_hora(acoes, de_s, ate_s, cer):
    n = sum(1 for s, a in acoes if de_s <= s < ate_s and A.CATALOGO[a][2])
    return n * 3600 / (ate_s - de_s)


if __name__ == '__main__':
    nome = sys.argv[1] if len(sys.argv) > 1 else 'semana'
    dias = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    sem = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    t0 = time.time()
    cer, acoes = simular(CENARIOS[nome](), dias, sem)
    dt = time.time() - t0
    print('%s: %d dias em %.1f s, %d ticks, %d decisoes' % (nome, dias, dt, cer.ticks_rodados, len(acoes)))
    s0 = 6 * 3600
    for dia in range(dias):
        a, b = s0 + dia * 86400, s0 + (dia + 1) * 86400
        print('dia %d: %.1f sons/h' % (dia + 1, sons_por_hora(acoes, a, b, cer)))
