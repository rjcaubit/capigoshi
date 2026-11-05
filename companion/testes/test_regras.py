# Testes do catalogo, dos drives e da recompensa (secoes 4, 5 e 6.3-6.4).
import unittest
from companion import config as C
from companion import actions as A
from companion.drives import Drives
from companion.reward import Recompensa


class TestCatalogo(unittest.TestCase):
    def test_cem_acoes_vinte_com_som(self):
        self.assertEqual(A.N_ACOES, 100)
        self.assertEqual(len(A.COM_SOM), 20)        # a fonte diz 21; a tabela tem 20 (CALIBRACAO.md)
        self.assertEqual(len(set(a[0] for a in A.CATALOGO)), 100)

    def test_precondicao_ou_e(self):
        dormir = A.INDICE['dormir']
        self.assertTrue(A.pode(dormir, {'energia': 30}))
        self.assertTrue(A.pode(dormir, {'energia': 80, 'noite': 1}))
        self.assertFalse(A.pode(dormir, {'energia': 80}))
        danca = A.INDICE['danca_longa']
        self.assertFalse(A.pode(danca, {'energia': 70, 'humor': 10}))
        self.assertTrue(A.pode(danca, {'energia': 70, 'humor': 30}))

    def test_cooldown_e_trava(self):
        ac = A.Acoes()
        m = bytearray(100)
        piscar = A.INDICE['piscar']
        ac.executar(piscar, 100)
        self.assertTrue(ac.travada(100))
        self.assertFalse(ac.travada(101))
        ac.disponiveis({'energia': 80}, 103, m)
        self.assertEqual(m[piscar], 0)              # cooldown de 5 s
        ac.disponiveis({'energia': 80}, 105, m)
        self.assertEqual(m[piscar], 1)

    def test_escolha_minimo_e_empate(self):
        ac = A.Acoes()
        m = bytearray([1] * 100)
        cont = [0] * 100
        v = [0] * 100
        cont[5] = 3
        self.assertEqual(ac.escolher(cont, m, v), A.QUIETA)
        cont[7] = 6
        cont[9] = 6
        v[9] = 100
        self.assertEqual(ac.escolher(cont, m, v), 9)


class TestDrives(unittest.TestCase):
    def test_minuto(self):
        d = Drives()
        f, e = d.d[C.D_FOME], d.d[C.D_ENERGIA]
        d.minuto()
        self.assertEqual(d.d[C.D_FOME], f + 10)
        self.assertEqual(d.d[C.D_ENERGIA], e - 5)

    def test_humor_regride_e_afeto_nao_cai_abaixo_de_50(self):
        d = Drives()
        d.d[C.D_HUMOR] = 25
        d.minuto()
        self.assertEqual(d.d[C.D_HUMOR], 15)
        d.d[C.D_AFETO] = 610
        d._soma(C.D_AFETO, 0)
        d._soma(C.D_AFETO, -300)
        self.assertEqual(d.d[C.D_AFETO], C.AFETO_PISO)


class D:
    def get(self, i):
        return 50


class TestRecompensa(unittest.TestCase):
    def test_custo_de_som_cresce_com_habituacao(self):
        r = Recompensa()
        beep = A.INDICE['beep_curto']
        custos = [r.acao_iniciada(beep, 1000 * k, False) for k in range(7)]
        self.assertEqual(custos[0], -3)
        self.assertLess(custos[6], custos[0])

    def test_silencio_soma_menos_dez(self):
        r = Recompensa()
        self.assertEqual(r.acao_iniciada(A.INDICE['beep_curto'], 0, True), -13)

    def test_som_sem_resposta_e_pedido_ignorado(self):
        r = Recompensa()
        r.acao_iniciada(A.INDICE['chamar_baixo'], 0, False)
        self.assertEqual(r.passo(29000), [])
        self.assertEqual(r.passo(30000)[0][0], C.R_SOM_SEM_RESPOSTA)
        self.assertEqual(r.passo(60000)[0][0], C.R_IGNORADO)

    def test_chamado_atendido(self):
        r = Recompensa()
        chamar = A.INDICE['chamar_baixo']
        r.acao_iniciada(chamar, 0, False)
        R, acao = r.evento('carinho', 2000, D())
        self.assertEqual(acao, chamar)
        self.assertEqual(R, (C.R_CARINHO + C.R_RESPONDEU) * 150 // 100)
        self.assertEqual(r.passo(60000), [])         # atendido: nada de 'ignorado'

    def test_toque_em_quieta(self):
        r = Recompensa()
        r.acao_iniciada(A.QUIETA, 0, False)
        self.assertEqual(r.evento('toque', 500, D())[0], C.R_TOQUE_QUIETA)


if __name__ == '__main__':
    unittest.main()
