# Testes da issue #5: Cerebro.resumo() e a pagina do raio-X.
import json
import unittest
from companion import config as C
from companion import actions as A
from companion.cerebro import Cerebro
from companion.sim.rodar import simular
from companion.sim.dono import Dono
from companion.sim import raiox


class TestRaiox(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cer, cls.acoes = simular(Dono(), 2 / 24, 1)      # 2 h a partir das 6h
        cls.r = cls.cer.resumo()

    def test_chaves_e_json(self):
        r = self.r
        for k in ('versao', 'semente', 'idade_s', 'agora_s', 'minuto', 'acao', 'dormindo', 'drives', 'clima', 'hoje',
                  'ontem', 'gosta', 'evita', 'relogio', 'recompensas', 'horas', 'rede'):
            self.assertIn(k, r)
        self.assertEqual([n for n, _ in r['drives']], list(C.DRIVES))
        self.assertEqual(r['idade_s'], 2 * 3600)
        json.dumps(r)                                        # serializa sem erro

    def test_so_inteiros(self):
        def ver(x):
            if isinstance(x, dict):
                for v in x.values():
                    ver(v)
            elif isinstance(x, (list, tuple)):
                for v in x:
                    ver(v)
            else:
                self.assertTrue(x is None or isinstance(x, (int, str, bool)), repr(x))
        ver(self.r)

    def test_hoje_bate_com_as_decisoes(self):
        n = {}
        for _, a in self.acoes:
            n[a] = n.get(a, 0) + 1
        for nome, vezes in self.r['hoje']:
            self.assertEqual(vezes, n[A.INDICE[nome]])
        self.assertEqual(self.r['hoje'][0][1], max(n.values()))

    def test_horas_e_recompensas(self):
        self.assertEqual(len(self.r['horas']), 2)            # 6h e 7h (o simulador comeca no segundo das 6h)
        self.assertEqual(len(self.r['horas'][0]), 7)
        for s, nome, R, motivo in self.r['recompensas']:
            self.assertIn(nome, A.INDICE)
            self.assertTrue(R)

    def test_limite_das_recompensas(self):
        cer = Cerebro(1)
        for k in range(C.RAIOX_RECS + 5):
            cer._aplicar(-1, 0, 'teste', k * 1000)
        self.assertEqual(len(cer.recs), C.RAIOX_RECS)
        self.assertEqual(cer.recs[0][0], 5)                  # as mais antigas saem primeiro

    def test_virada_do_dia(self):
        cer, _ = simular(Dono(), 20 / 24, 1)                 # 6h ate 2h do dia seguinte
        r = cer.resumo()
        self.assertTrue(r['ontem'])
        self.assertLess(sum(n for _, n in r['hoje']), sum(n for _, n in r['ontem']))

    def test_habito_aparece_no_relogio(self):
        cer = Cerebro(1)
        o = A.INDICE['pedir_carinho']
        cer.relogio.w[57 * cer.rede.no + o] = C.RAIOX_HABITO
        cer.relogio.w[10 * cer.rede.no + o] = -C.RAIOX_HABITO
        r = cer.resumo()['relogio']
        self.assertEqual(r['habitos'], [[57, 'pedir_carinho', C.RAIOX_HABITO]])
        self.assertEqual(r['evita'], [[10, 'pedir_carinho', -C.RAIOX_HABITO]])

    def test_resumo_nao_muda_o_cerebro(self):
        """Chamar resumo() a cada minuto nao altera nenhuma decisao (mesma semente)."""
        _, sem = simular(Dono(), 1 / 24, 3)
        import companion.cerebro as M
        orig = M.Cerebro.segundo

        def segundo(self, s, agora_ms):
            if agora_ms % 60000 == 0:
                self.resumo()
            return orig(self, s, agora_ms)
        M.Cerebro.segundo = segundo
        try:
            _, com = simular(Dono(), 1 / 24, 3)
        finally:
            M.Cerebro.segundo = orig
        self.assertEqual(sem, com)

    def test_pagina_embute_o_resumo(self):
        html = raiox.pagina(self.r)
        self.assertNotIn(raiox.MARCA, html)
        dados = html.split('var D = ')[1].split(';\n')[0]
        self.assertEqual(json.loads(dados), json.loads(json.dumps(self.r)))
        self.assertNotIn('</', dados)                        # nao fecha o <script> antes da hora


if __name__ == '__main__':
    unittest.main()
