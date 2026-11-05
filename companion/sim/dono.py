# Dono simulado (secao 10): configuravel por probabilidades e horarios. Devolve eventos agendados.
import random
from companion import actions as A

PEDE_CARINHO = tuple(A.INDICE[n] for n in ('pedir_carinho', 'pedir_abraco', 'fazer_charme', 'chamar_baixo',
                                           'chamar_alto', 'chamar_atencao_silenciosa'))
JOGOS = tuple(i for i, a in enumerate(A.CATALOGO) if a[1] == A.BRINCA)


class Dono:
    def __init__(self, p_som=0.5, p_pedido=0.5, presente=((7, 8), (18, 22)), carinho_hora=None,
                 refeicoes=(8, 12, 19), p_toque_hora=2, p_jogo=0.5):
        self.p_som = p_som                  # chance de responder a uma acao com som
        self.p_pedido = p_pedido            # chance de atender um pedido silencioso
        self.presente = presente            # faixas de hora em que esta por perto
        self.carinho_hora = carinho_hora    # hora fixa em que chega e atende pedidos de carinho (teste do habito)
        self.refeicoes = refeicoes
        self.p_toque_hora = p_toque_hora    # toques espontaneos por hora quando presente
        self.p_jogo = p_jogo

    def esta(self, minuto):
        h = minuto // 60
        if self.carinho_hora is not None and self.carinho_hora * 60 <= minuto < self.carinho_hora * 60 + 15:
            return True
        for a, b in self.presente:
            if a <= h < b:
                return True
        return False

    def reagir(self, acao, minuto):
        """Acao que a Capi acabou de comecar -> lista de (atraso s, evento)."""
        if not self.esta(minuto):
            return []
        cat, som = A.CATALOGO[acao][1], A.CATALOGO[acao][2]
        habito = self.carinho_hora is not None and self.carinho_hora * 60 <= minuto < self.carinho_hora * 60 + 15
        if acao in PEDE_CARINHO and (habito or random.random() < self.p_pedido * (0 if som and self.p_som == 0 else 1)):
            return [(2, 'carinho')]
        if som:
            return [(5, 'toque')] if random.random() < self.p_som else []
        if acao == A.INDICE['pedir_comida'] and random.random() < self.p_pedido:
            return [(3, 'comida')]
        if acao in JOGOS and random.random() < self.p_jogo:
            return [(A.CATALOGO[acao][5], 'jogo_fim')]
        return []

    def espontaneo(self, minuto, seg_do_minuto):
        """Eventos que nao dependem da acao: refeicoes e toques ao acaso."""
        ev = []
        if seg_do_minuto == 0 and minuto % 60 == 0 and minuto // 60 in self.refeicoes:
            ev.append('comida')
        if self.esta(minuto) and random.getrandbits(12) < 4096 * self.p_toque_hora // 3600:
            ev.append('toque')
        return ev
