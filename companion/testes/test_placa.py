# Testes da ponte cerebro <-> placa (companion/placa.py) e da tabela de expressao das 100 acoes.
import os
import shutil
import tempfile
import unittest
from companion import config as C
from companion import actions as A
from companion import placa as P
from companion.expressao import EXPRESSAO
import vida as V

SONS = ('amor', 'banho', 'bocejo', 'clique', 'comer', 'feliz', 'festa', 'moeda', 'piu', 'remedio', 'susto', 'triste')
MEIA_NOITE = 10 * 86400                            # um dia qualquer, alinhado com a meia-noite local


def leitura(minuto=600):
    return {'minuto': minuto, 'fim_semana': False, 'noite': False, 'bateria': 80, 'carregando': 0,
            'som_nivel': 10, 'tempo': 'sol', 'graus': 25, 'outra': 0}


class TestExpressao(unittest.TestCase):
    def test_toda_acao_tem_expressao(self):
        self.assertEqual(sorted(EXPRESSAO), sorted(a[0] for a in A.CATALOGO))

    def test_movimentos_e_sons_existem(self):
        for nome, (mov, fala, som) in EXPRESSAO.items():
            self.assertTrue(mov is None or mov in V.MOVES, nome)
            self.assertTrue(som is None or som in SONS, nome)
            self.assertTrue(os.path.exists(os.path.join('sons', som + '.raw')) if som else True, nome)

    def test_falas_cabem_no_balao(self):
        for nome, (mov, fala, som) in EXPRESSAO.items():
            if fala in (None, 'hora', 'clima', 'humor'):
                continue
            linhas = fala.split('|')
            self.assertLessEqual(len(linhas), 2, nome)
            for l in linhas:
                self.assertLessEqual(len(l), 14, nome + ': ' + l)
                self.assertTrue(all(32 <= ord(c) < 127 for c in l), nome)

    def test_falas_dinamicas(self):
        p = P.Ponte(MEIA_NOITE, pasta=self.pasta, semente=3)
        self.assertEqual(p.expressao(A.INDICE['mostrar_hora'], '14:05')[1], 'sao 14:05')
        self.assertEqual(p.expressao(A.INDICE['mostrar_clima'], '', 'sol, 25|graus')[1], 'sol, 25|graus')
        self.assertIn('to', p.expressao(A.INDICE['mostrar_humor'])[1])

    def setUp(self):
        self.pasta = tempfile.mkdtemp() + '/'

    def tearDown(self):
        shutil.rmtree(self.pasta)


class TestPonte(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.mkdtemp() + '/'

    def tearDown(self):
        shutil.rmtree(self.pasta)

    def test_um_segundo_por_vez_e_recupera_atraso(self):
        p = P.Ponte(MEIA_NOITE, pasta=self.pasta, semente=3)
        p.passo(MEIA_NOITE, leitura())
        self.assertEqual(p.cer.idade_s, 1)
        p.passo(MEIA_NOITE + 5, leitura())            # 5 s atrasada: recupera POR_PASSO por quadro
        self.assertEqual(p.cer.idade_s, 1 + P.POR_PASSO)
        for _ in range(5):
            p.passo(MEIA_NOITE + 5, leitura())
        self.assertEqual(p.cer.idade_s, 6)
        p.passo(MEIA_NOITE + 5 + P.ATRASO_MAX_S + 10, leitura())   # parada longa: pula para agora
        self.assertEqual(p.seg, MEIA_NOITE + 5 + P.ATRASO_MAX_S + 10)

    def test_acoes_novas_e_evento_vira_sentido(self):
        p = P.Ponte(MEIA_NOITE, pasta=self.pasta, semente=3)
        novas = []
        for s in range(MEIA_NOITE, MEIA_NOITE + 120):
            novas += p.passo(s, leitura())
        self.assertTrue(novas)
        self.assertTrue(all(0 <= a < A.N_ACOES for a in novas))
        p.evento('carinho', MEIA_NOITE + 120)
        self.assertEqual(p.ev['toque_reg'], P.REG_CORPO)
        s = p._sentidos(MEIA_NOITE + 121, leitura())
        self.assertEqual(s['toque_tipo'], P.TOQUE_CURTO)
        self.assertEqual(s['toques_60s'], 1)
        p.passo(MEIA_NOITE + 121, leitura())
        self.assertEqual(p.ev, {})                    # o evento vale so para um segundo

    def test_brain_bin_ida_e_volta(self):
        p = P.Ponte(MEIA_NOITE, pasta=self.pasta, semente=7)
        for s in range(MEIA_NOITE, MEIA_NOITE + 300):
            p.passo(s, leitura())
            if s % 40 == 0:
                p.evento('carinho', s)
        p.salvar(MEIA_NOITE + 300)
        q = P.Ponte(MEIA_NOITE + 300, pasta=self.pasta)
        for a, b in zip(P._blocos(p.cer), P._blocos(q.cer)):
            self.assertEqual(list(a), list(b))
        self.assertEqual(q.cer.semente, 7)
        self.assertEqual(q.cer.idade_s, p.cer.idade_s)
        self.assertEqual(list(q.cer.rede.w_ho0), list(p.cer.rede.w_ho0))   # o que nasceu vem da semente

    def test_desligada_avanca_drives_e_idade(self):
        p = P.Ponte(MEIA_NOITE, pasta=self.pasta, semente=7)
        p.passo(MEIA_NOITE, leitura())
        fome = p.cer.drives.d[C.D_FOME]
        p.salvar(MEIA_NOITE)
        q = P.Ponte(MEIA_NOITE + 3 * 3600, pasta=self.pasta)
        self.assertEqual(q.cer.idade_s, 1 + 3 * 3600)
        self.assertGreater(q.cer.drives.d[C.D_FOME], fome)

    def test_arquivo_estragado_usa_a_copia(self):
        p = P.Ponte(MEIA_NOITE, pasta=self.pasta, semente=7)
        p.salvar(MEIA_NOITE)
        p.cer.idade_s = 999
        p.salvar(MEIA_NOITE + 10)                     # brain.bak fica com a gravacao anterior
        with open(self.pasta + P.ARQ, 'r+b') as f:
            f.seek(100)
            f.write(b'\xff\xff\xff')
        q = P.Ponte(MEIA_NOITE + 10, pasta=self.pasta)
        self.assertEqual(q.cer.semente, 7)
        self.assertNotEqual(q.cer.idade_s, 999)

    def test_sem_arquivo_nasce_com_semente_nova(self):
        p = P.Ponte(MEIA_NOITE, pasta=self.pasta)
        self.assertTrue(1 <= p.cer.semente <= 65535)
        self.assertEqual(p.cer.idade_s, 0)

    def test_dormir_salva(self):
        p = P.Ponte(MEIA_NOITE, pasta=self.pasta, semente=7)
        p.cer.drives.d[C.D_ENERGIA] = 0               # regra fixa: energia baixa dorme
        p.passo(MEIA_NOITE, leitura())
        self.assertTrue(p.dormindo())
        self.assertTrue(os.path.exists(self.pasta + P.ARQ))


if __name__ == '__main__':
    unittest.main()
