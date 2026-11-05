# Recompensa (secao 6.3 e 6.4): eventos do dono e custos internos viram R, com modulacao por drive e habituacao.
from array import array
from companion import config as C
from companion import actions as A

EVENTO_R = {
    'estrela': C.R_ESTRELA, 'carinho': C.R_CARINHO, 'jogo_fim': C.R_JOGO, 'jogo_repetiu': C.R_JOGO + C.R_JOGO_REPETIU,
    'social_ok': C.R_SOCIAL, 'shh': C.R_SHH, 'sacudida_leve': C.R_SACUDIDA_LEVE,
    'sacudida_forte': C.R_SACUDIDA_FORTE, 'desligou': C.R_DESLIGOU,
}
EVENTO_DRIVE = {'carinho': C.D_AFETO, 'comida': C.D_FOME, 'jogo_fim': C.D_TEDIO, 'jogo_repetiu': C.D_TEDIO}
TOQUES = ('carinho', 'estrela', 'toque', 'comida', 'jogo_fim', 'jogo_repetiu')
TOQUES_DIRETOS = ('carinho', 'estrela', 'toque')     # so estes contam como 'tocou enquanto estava quieta'
SEM_HABITUACAO = (A.FISIO,)
SEMPRE = ('jogo_fim', 'jogo_repetiu', 'social_ok', 'sacudida_forte')   # nao dependem da janela de 3 s


class Recompensa:
    def __init__(self):
        self.n = array('H', [0] * A.N_ACOES)      # execucoes recentes x10 (6.4)
        self.acao = A.QUIETA
        self.t_acao = -10 ** 9                     # ms do inicio da ultima acao
        self.n_acao = 0                            # habituacao da acao atual quando comecou
        self.esperando_toque = None                # (acao, prazo ms, inicio ms, habituacao no inicio)
        self.esperando_som = None                  # (acao, prazo ms)
        self.ultimo = (0, '')                      # (R, motivo) para o log e o raio-X

    def habituacao(self):
        """A cada 10 min: contador perde 1/6 (aproxima 'execucoes na ultima hora')."""
        n = self.n
        for i in range(A.N_ACOES):
            n[i] -= n[i] // 6 + (1 if 0 < n[i] < 6 else 0)

    def _fator_n(self, acao):
        return 0 if A.CATALOGO[acao][1] in SEM_HABITUACAO else self.n[acao] // 10

    def acao_iniciada(self, acao, t_ms, silencio):
        """Devolve o R imediato (custo de som) e arma os prazos de 'ignorado' e 'som sem resposta'."""
        self.acao, self.t_acao = acao, t_ms
        n = self.n_acao = self._fator_n(acao)      # execucoes anteriores; a atual nao conta
        self.n[acao] += C.HABITUA_MIN
        R = 0
        if A.CATALOGO[acao][2]:
            R = C.R_CUSTO_SOM * (3 + n) // 3
            if silencio:
                R += C.R_SOM_SILENCIO
            self.esperando_som = (acao, t_ms + C.JANELA_SOM)
        if acao in A.PEDIDOS:
            self.esperando_toque = (acao, t_ms + C.JANELA_IGNORADO, t_ms, n)
        return R

    def evento(self, nome, t_ms, drives):
        """Reacao do dono. Chamar antes de mexer nos drives (a modulacao usa o drive de antes).
        Devolve lista de (R, acao que recebe o credito); o chamado atendido credita o chamado, nao a acao atual."""
        acao = self.acao
        pedido = None
        if nome in TOQUES:
            self.esperando_som = None
            pedido = self.esperando_toque
            self.esperando_toque = None
        saida = []
        R = 0
        dt = t_ms - self.t_acao
        if nome == 'carinho':
            R = C.R_CARINHO if dt <= C.JANELA_CARINHO else 0
        elif nome == 'comida':
            R = C.R_COMIDA if acao == A.INDICE['pedir_comida'] else 0
        elif nome in EVENTO_R:
            janela = C.JANELA_DESLIGOU if nome == 'desligou' else C.JANELA_CARINHO
            R = EVENTO_R[nome] if nome in SEMPRE or dt <= janela else 0
        if nome in EVENTO_DRIVE and R > 0:
            R = R * (100 + drives.get(EVENTO_DRIVE[nome])) // 100
        if R > 0:
            R = R * 3 // (3 + self.n_acao)
        atendeu = pedido and pedido[0] in A.CHAMADOS and t_ms - pedido[2] <= C.JANELA_RESPOSTA
        if atendeu:
            saida.append((C.R_RESPONDEU * 3 // (3 + pedido[3]), pedido[0]))
        if nome in TOQUES_DIRETOS and acao == A.QUIETA and R == 0 and not atendeu:
            R = C.R_TOQUE_QUIETA
        if R:
            saida.append((R, acao))
        if saida:
            self.ultimo = (saida[-1][0], nome)
        return saida

    def passo(self, t_ms):
        """Chamado a cada segundo: prazos vencidos viram R negativo. Devolve lista de (R, acao, motivo)."""
        saida = []
        if self.esperando_som and t_ms >= self.esperando_som[1]:
            saida.append((C.R_SOM_SEM_RESPOSTA, self.esperando_som[0], 'som_sem_resposta'))
            self.esperando_som = None
        if self.esperando_toque and t_ms >= self.esperando_toque[1]:
            saida.append((C.R_IGNORADO, self.esperando_toque[0], 'ignorado'))
            self.esperando_toque = None
        if saida:
            self.ultimo = (saida[-1][0], saida[-1][2])
        return saida
