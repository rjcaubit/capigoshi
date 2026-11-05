# Testes da issue #4: clima como sentido e como alvo do humor.
import unittest
from companion import config as C
from companion import clima as K
from companion.drives import Drives
from companion.encoder import Codificador, BASE
from companion.snn import Rede
from companion.cerebro import Cerebro


def sentidos(tempo=None, graus=None):
    return {'minuto': 600, 'fim_semana': 0, 'toques_60s': 0, 'sem_toque': 0, 'orient': 0, 'som_nivel': 0,
            'noite': 0, 'bateria': 80, 'carregando': 0, 'outra': 0, 'outra_estado': 0, 'novidade': 0,
            'drives': [0] * 7, 'ultima': 0, 'tempo': tempo, 'graus': graus}


class TestClima(unittest.TestCase):
    def test_indice(self):
        self.assertEqual([K.indice(t) for t in ('sol', 'nublado', 'neblina', 'vento', 'chuva', 'neve', 'tempestade')],
                         [0, 1, 1, 1, 2, 2, 3])
        self.assertIsNone(K.indice(None))
        self.assertIsNone(K.indice('granizo'))                    # nome desconhecido: sem previsao

    def test_efeito(self):
        self.assertEqual(K.efeito(None, None), (0, 0, 0, 0))
        self.assertEqual(K.efeito('chuva', 20), (C.CLIMA_HUMOR[2], C.CLIMA_PUXA_PCT, C.CLIMA_ENERGIA[2], 0))
        self.assertEqual(K.efeito('sol', 10)[2], C.CLIMA_ENERGIA[0] + C.FRIO_ENERGIA)     # frio cansa

    def test_humor_vai_para_o_alvo(self):
        d = Drives()
        d.clima = K.efeito('chuva', 20)
        for _ in range(40):                             # 40 min: a fome ainda nao passou de 80
            d.minuto()
        self.assertEqual(d.d[C.D_HUMOR], C.CLIMA_HUMOR[2])
        d.clima = K.efeito(None, None)                  # sem previsao: volta a regredir para 0, 1/min
        d.minuto()
        self.assertEqual(d.d[C.D_HUMOR], C.CLIMA_HUMOR[2] + C.HUMOR_REGRIDE)

    def test_puxada_proporcional(self):
        d = Drives()
        d.d[C.D_HUMOR] = 200
        d.clima = K.efeito('chuva', 20)                 # distancia 550: 10 + 550 * 5 // 100 = 37
        d.minuto()
        self.assertEqual(d.d[C.D_HUMOR], 200 - C.HUMOR_REGRIDE - 550 * C.CLIMA_PUXA_PCT // 100)


class TestEntrada(unittest.TestCase):
    def test_neuronios(self):
        c = Codificador()
        c.codificar(sentidos())
        b, t = BASE['clima'], BASE['temperatura']
        self.assertEqual(list(c.ativ[b:b + 7]), [0] * 7)          # sem previsao: grupo calado
        c.codificar(sentidos('chuva', 5))
        self.assertEqual(list(c.ativ[b:b + 4]), [0, 0, 255, 0])
        self.assertEqual(list(c.ativ[t:t + 3]), [255, 0, 0])
        self.assertEqual(t + 3, C.N_IN)

    def test_rede_da_fonte_nao_muda(self):
        r = Rede(100, 1)
        self.assertEqual(len(r.w_ih), C.N_IN * C.N_HID)
        n = C.N_IN_FONTE * C.N_HID
        self.assertEqual(r.w_ih[:n], Rede(100, 1).w_ih[:n])       # sorteio deterministico por semente

    def test_cerebro_le_o_clima(self):
        c = Cerebro(1)
        s = sentidos('tempestade', 20)
        c.segundo(s, 60 * 1000)
        self.assertEqual(c.drives.clima, K.efeito('tempestade', 20))


if __name__ == '__main__':
    unittest.main()
