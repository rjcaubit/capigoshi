# Testes da rede e do aprendizado (fase 0, secao 11): LIF, STDP e R-STDP.
import unittest
from companion import config as C
from companion.snn import Rede, RECENTE, NH, NE
from companion.learn import Aprendizado


class EntradaFixa:
    """Codificador falso: os mesmos neuronios de entrada disparam em todo tick."""
    def __init__(self, indices):
        self.indices = indices

    def spikes(self, saida):
        for k, i in enumerate(self.indices):
            saida[k] = i
        return len(self.indices)


def rede_limpa(w_in):
    r = Rede(5, 1)
    r.novo_ruido(0)
    for k in range(len(r.w_ih)):
        r.w_ih[k] = w_in << C.W_FRAC
    for k in range(len(r.hh_w)):
        r.hh_w[k] = 0
    return r


class TestLIF(unittest.TestCase):
    def test_spike_no_tick_previsto(self):
        r = rede_limpa(80)
        mascara = bytearray(5)
        cod = EntradaFixa(list(range(10)))
        I = (10 * 80 << C.W_FRAC) >> (C.I_SCALE + C.W_FRAC)   # 200 por tick: v de equilibrio 3200 > V_TH
        v, previsto = C.V_REST, 0
        while v < C.V_TH:
            previsto += 1
            v += I - ((v - C.V_REST) >> C.TAU_SHIFT)
        for t in range(1, previsto + 1):
            r.passo(cod, mascara)
            if t < previsto:
                self.assertEqual(r.spk_h, [], 'disparou cedo no tick %d' % t)
        self.assertEqual(len(r.spk_h), NH)
        self.assertEqual(r.v_h[0], C.V_RESET)

    def test_refratario(self):
        r = rede_limpa(255)
        mascara = bytearray(5)
        cod = EntradaFixa(list(range(20)))
        r.passo(cod, mascara)
        self.assertEqual(len(r.spk_h), NH)          # corrente enorme: dispara no primeiro tick
        for _ in range(C.REFRAC):
            r.passo(cod, mascara)
            self.assertEqual(r.spk_h, [])           # nao integra durante o refratario
        r.passo(cod, mascara)
        self.assertEqual(len(r.spk_h), NH)


def preparar(r, t):
    r.t = t
    r.spk_h, r.spk_o, r.n_in = [], [], 0
    r.rec_in = [[] for _ in range(RECENTE)]
    r.rec_h = [[] for _ in range(RECENTE)]
    r.rec_o = [[] for _ in range(RECENTE)]


class TestSTDP(unittest.TestCase):
    def test_pre_antes_do_pos_potencia(self):
        r = rede_limpa(50)
        a = Aprendizado(r, [0] * 5)
        preparar(r, 10)
        r.ult_in[5] = 8
        r.rec_in[8 % RECENTE] = [5]
        r.spk_h = [3]
        r.ult_h[3] = 10
        r.rec_h[10 % RECENTE] = [3]
        antes = r.w_ih[5 * NH + 3]
        a.passo()
        self.assertGreater(r.w_ih[5 * NH + 3], antes)

    def test_pos_antes_do_pre_deprime(self):
        r = rede_limpa(50)
        a = Aprendizado(r, [0] * 5)
        preparar(r, 10)
        r.ult_h[3] = 8
        r.rec_h[8 % RECENTE] = [3]
        r.spk_in[0] = 5
        r.n_in = 1
        r.ult_in[5] = 10
        r.rec_in[10 % RECENTE] = [5]
        antes = r.w_ih[5 * NH + 3]
        a.passo()
        self.assertLess(r.w_ih[5 * NH + 3], antes)


class TestRSTDP(unittest.TestCase):
    def _elegivel(self):
        r = rede_limpa(50)
        a = Aprendizado(r, [0] * 5)
        preparar(r, 10)
        r.ult_h[2] = 9
        r.rec_h[9 % RECENTE] = [2]
        r.spk_o = [1]
        r.ult_o[1] = 10
        a.passo()
        self.assertGreater(a.e[2 * r.no + 1], 0)
        return r, a

    def test_recompensa_dentro_da_janela_sobe_peso(self):
        r, a = self._elegivel()
        antes = r.w_ho[2 * r.no + 1]
        r.t += 20                                    # 1 s depois
        a.recompensa(10, 1, C.ETA_FILHOTE)
        self.assertGreater(r.w_ho[2 * r.no + 1], antes)

    def test_recompensa_fora_da_janela_nao_muda(self):
        r, a = self._elegivel()
        antes = r.w_ho[2 * r.no + 1]
        r.t += 400                                   # 20 s depois: elegibilidade zerada
        a.recompensa(10, 1, C.ETA_FILHOTE)
        self.assertEqual(r.w_ho[2 * r.no + 1], antes)

    def test_so_a_coluna_da_acao_muda(self):
        r, a = self._elegivel()
        antes = r.w_ho[2 * r.no + 3]
        r.t += 20
        a.recompensa(10, 1, C.ETA_FILHOTE)
        self.assertEqual(r.w_ho[2 * r.no + 3], antes)

    def test_punicao_desce_ate_o_piso(self):
        r = rede_limpa(50)
        a = Aprendizado(r, [5] * 5)
        preparar(r, 10)
        r.ult_h[2] = 9
        r.rec_h[9 % RECENTE] = [2]
        r.spk_o = [1]
        r.ult_o[1] = 10
        a.passo()
        for _ in range(50):
            a.recompensa(-15, 1, C.ETA_FILHOTE)
        self.assertEqual(r.w_ho[2 * r.no + 1], 5)


if __name__ == '__main__':
    unittest.main()
