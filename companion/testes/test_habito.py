# Testes da issue #3: via hora -> saida, marca do castigo atrasado e solidao.
import unittest
from array import array
from companion import config as C
from companion import actions as A
from companion.relogio import Relogio, celulas
from companion.cerebro import Cerebro

PC = A.INDICE['pedir_carinho']


class TestRelogio(unittest.TestCase):
    def test_celulas(self):
        self.assertEqual(celulas(19 * 60), (57, 58, 0))
        self.assertEqual(celulas(19 * 60 + 5), (57, 58, 5))
        self.assertEqual(celulas(23 * 60 + 50), (71, 0, 10))       # meia-noite fecha o circulo

    def test_premio_na_hora_certa(self):
        r = Relogio(A.N_ACOES)
        r.recompensa(10, PC, 19 * 60, 4)                            # 4 * 10 * 24 = 960, todo na celula 57
        self.assertEqual(r.w[57 * A.N_ACOES + PC], 960)
        self.assertEqual(r.w[58 * A.N_ACOES + PC], 0)
        d = array('h', [0] * A.N_ACOES)
        r.corrente(19 * 60, d)
        self.assertEqual(d[PC], 960)
        d[PC] = 0
        r.corrente(19 * 60 + 10, d)                                 # meio caminho para a celula 58
        self.assertEqual(d[PC], 480)
        d[PC] = 0
        r.corrente(10 * 60, d)
        self.assertEqual(d[PC], 0)

    def test_castigo_e_limite(self):
        r = Relogio(A.N_ACOES)
        r.recompensa(-5, PC, 10 * 60 + 5, 4)                        # 4 * -5 * 8 = -160: 3/4 na 30, 1/4 na 31
        self.assertEqual(r.w[30 * A.N_ACOES + PC], -120)
        self.assertEqual(r.w[31 * A.N_ACOES + PC], -40)
        for _ in range(50):
            r.recompensa(-5, PC, 10 * 60, 4)
        self.assertEqual(r.w[30 * A.N_ACOES + PC], -C.RELOGIO_MAX)

    def test_esquecer(self):
        r = Relogio(A.N_ACOES)
        r.w[0], r.w[1], r.w[2] = 1000, -50, 0
        r.esquecer()
        self.assertEqual((r.w[0], r.w[1], r.w[2]), (990, -49, 0))


class TestMarca(unittest.TestCase):
    def test_castigo_atrasado_so_nos_marcados(self):
        c = Cerebro(1)
        apr, r, no = c.apr, c.rede, A.N_ACOES
        apr.marcas[PC] = (0, 1)
        antes = [r.w_ho[h * no + PC] for h in range(3)]
        apr.recompensa_atrasada(-5, PC, 4)                          # (4 * -5 * 1) >> 2 = -5
        self.assertEqual(r.w_ho[0 * no + PC], max(apr.pisos[PC], antes[0] - 5))
        self.assertEqual(r.w_ho[1 * no + PC], max(apr.pisos[PC], antes[1] - 5))
        self.assertEqual(r.w_ho[2 * no + PC], antes[2])
        piscar = A.INDICE['piscar']                                 # CT05: sem marca, nada muda
        coluna = [r.w_ho[h * no + piscar] for h in range(C.N_EXC)]
        apr.recompensa_atrasada(-6, piscar, 4)
        self.assertEqual([r.w_ho[h * no + piscar] for h in range(C.N_EXC)], coluna)

    def test_ignorado_usa_minuto_do_inicio(self):
        c = Cerebro(1)
        c.minuto = 10 * 60
        c._executar(PC, {'minuto': 10 * 60}, 36000 * 1000)
        self.assertIn(PC, c.apr.marcas)
        c.minuto = 10 * 60 + 1                                      # o ignorado chega 60 s depois
        c._aplicar(-5, PC, 'ignorado', 36060 * 1000)
        self.assertLess(c.relogio.w[30 * A.N_ACOES + PC], 0)


class TestSolidao(unittest.TestCase):
    def _corrente(self, afeto):
        c = Cerebro(1)
        c.drives.d[C.D_AFETO] = afeto
        s = {'minuto': 600, 'fim_semana': 0, 'toques_60s': 0, 'sem_toque': 0, 'orient': 0, 'som_nivel': 0,
             'noite': 0, 'bateria': 80, 'carregando': 0, 'outra': 0, 'outra_estado': 0, 'novidade': 0}
        c._decidir(s, 600 * 60 * 1000)
        return c.rede.direto[PC]

    def test_solidao(self):
        self.assertEqual(self._corrente(100), C.SOLIDAO[3])
        self.assertEqual(self._corrente(500), 0)


if __name__ == '__main__':
    unittest.main()
