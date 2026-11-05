# Orquestra o cerebro (secao 9): sentidos -> rede -> acao -> recompensa -> pesos.
# Sem Timer: quem chama (main.passo na placa, sim/ no PC) entrega um segundo de cada vez em segundo().
from array import array
from companion import config as C
from companion import actions as A
from companion.encoder import Codificador
from companion.snn import Rede
from companion.learn import Aprendizado
from companion.drives import Drives
from companion.reward import Recompensa

FORTES = ('sacudida_leve', 'sacudida_forte', 'carinho', 'toque', 'estrela', 'shh', 'comida')
DORMIR = A.INDICE['dormir']
ACORDAR = A.INDICE['acordar']


class Cerebro:
    def __init__(self, semente=1):
        self.semente = semente
        self.cod = Codificador()
        self.rede = Rede(A.N_ACOES, semente)
        pisos = array('h', [C.PISO_SOCIAL if a[1] in (A.SOCIAL, A.FISIO) else 0 for a in A.CATALOGO])
        self.apr = Aprendizado(self.rede, pisos)
        self.drives = Drives()
        self.acoes = A.Acoes()
        self.rec = Recompensa()
        self.mascara = array('B', [0] * A.N_ACOES)
        self.direto_idx = tuple((d, lim, A.INDICE[n], i) for d, lim, n, i in C.DIRETO)
        self.idade_s = 0
        self.t = {}                                # ms do ultimo evento de cada tipo (flags 'recente')
        self.ultima = A.QUIETA
        self.resposta = None
        self.forte = False
        self.log = []                              # ('A', s, acao) e ('R', s, acao, R, motivo), lido pelo sim
        self.ticks_rodados = 0

    # ---- utilidades
    def eta(self):
        return C.ETA_FILHOTE if self.idade_s < C.DIAS_FILHOTE * 86400 else C.ETA_ADULTA

    def _recente(self, nome, agora_ms, janela_ms):
        return agora_ms - self.t.get(nome, -10 ** 12) <= janela_ms

    def contexto(self, s, agora_ms):
        d = self.drives
        hora = s['minuto'] // 60
        return {
            'fome': d.get(C.D_FOME), 'energia': d.get(C.D_ENERGIA), 'humor': d.get(C.D_HUMOR),
            'tedio': d.get(C.D_TEDIO), 'afeto': d.get(C.D_AFETO), 'curiosidade': d.get(C.D_CURIOSIDADE),
            'estresse': d.get(C.D_ESTRESSE), 'bateria': s['bateria'], 'noite': s['noite'], 'hora': hora,
            'sem_toque': s['sem_toque'], 'dormindo': d.dormindo, 'estimulo': self.forte,
            'acordou': self._recente('acordou', agora_ms, 60000), 'comida': s.get('comida', 0),
            'carinho': self._recente('carinho', agora_ms, 10000), 'evento': self._recente('evento', agora_ms, 5000),
            'recompensa': self._recente('recompensa', agora_ms, 10000),
            'grande': self._recente('grande', agora_ms, 5000), 'punicao': self._recente('punicao', agora_ms, 30000),
            'recebeu': self._recente('recebeu', agora_ms, 10000), 'toque': self._recente('toque', agora_ms, 10000),
            'deitada': self.ultima == A.INDICE['deitar'], 'imu': 1, 'mic': 1, 'voz': s.get('voz', 0),
            'wifi': s.get('wifi', 0), 'fora': s.get('fora', 0), 'padrao': s.get('padrao', 0),
            'outra': s['outra'] == 2, 'afs': s.get('afs', 0), 'outra_energia': s.get('outra_energia', 0),
            'tocada': s.get('tocada', 0), 'dna_novo': s.get('dna_novo', 0),
        }

    def silencio(self, minuto):
        h = minuto // 60
        a, b = C.SILENCIO
        return h >= a or h < b

    # ---- recompensa
    def _aplicar(self, R, acao, motivo, agora_ms):
        if not R:
            return
        self.apr.recompensa(R, acao, self.eta())
        self.drives.recompensa(R)
        self.t['recompensa' if R > 0 else 'punicao'] = agora_ms
        if R >= C.R_ESTRELA:
            self.t['grande'] = agora_ms
        self.resposta = 0 if R > 0 else 2
        self.log.append(('R', agora_ms // 1000, acao, R, motivo))

    def evento(self, nome, agora_ms):
        """Reacao do dono ou do mundo: carinho, estrela, shh, toque, comida, sacudida_*, jogo_fim, desligou..."""
        d = self.drives
        self.t[nome] = agora_ms
        self.t['evento'] = agora_ms
        if nome in ('carinho', 'toque', 'estrela', 'comida'):
            self.t['toque'] = agora_ms
            d.interagiu = True
        if nome in ('carinho', 'comida'):
            self.t['recebeu'] = agora_ms
        for R, acao in self.rec.evento(nome, agora_ms, d):     # antes dos drives: modula pelo valor de antes
            self._aplicar(R, acao, nome, agora_ms)
        if nome == 'comida':
            d._soma(C.D_FOME, C.COMER)
        elif nome in ('jogo_fim', 'jogo_repetiu'):
            d._soma(C.D_TEDIO, C.BRINCAR_TEDIO)
        elif nome == 'sacudida_forte':
            d._soma(C.D_ESTRESSE, C.ESTRESSE_SACUDIDA)
        elif nome in ('shh', 'sacudida_leve'):
            d._soma(C.D_ESTRESSE, C.ESTRESSE_RALHAR)
        elif nome == 'barulho':
            d._soma(C.D_ESTRESSE, C.ESTRESSE_BARULHO)
        elif nome == 'novidade':
            d._soma(C.D_CURIOSIDADE, C.NOVIDADE_CURIOSIDADE)
        if nome in FORTES:
            self.forte = True

    # ---- relogio
    def segundo(self, s, agora_ms):
        """Um segundo de vida. s: sentidos (ver sim/mundo.py). Devolve o indice da acao em curso."""
        self.idade_s += 1
        seg = agora_ms // 1000
        d = self.drives
        if seg % 60 == 0:
            d.minuto()
        if seg % 600 == 0:
            self.rec.habituacao()
        if seg % 86400 == 0:
            self.apr.esquecer()
        for R, acao, motivo in self.rec.passo(agora_ms):
            self._aplicar(R, acao, motivo, agora_ms)
        ac = self.acoes
        if ac.atual == DORMIR and d.d[C.D_ENERGIA] >= C.ACORDA_ENERGIA:
            self._acordar(agora_ms)
        if d.dormindo and self.forte and d.d[C.D_ENERGIA] >= C.ENERGIA_SONO_FORCADO:
            self._acordar(agora_ms)
            self.forte = False
            return self._executar(ACORDAR, s, agora_ms)
        if d.dormindo:
            self.forte = False                     # estimulo durante sono profundo nao fica guardado para depois
        if ac.travada(seg) and not (self.forte and not d.dormindo):
            self.rede.t += C.DECIDE_TICKS          # o tempo da rede anda mesmo sem simular (traco envelhece)
            return ac.atual
        if d.d[C.D_ENERGIA] < C.ENERGIA_SONO_FORCADO:
            return self._executar(DORMIR, s, agora_ms)       # regra fixa (secao 1)
        return self._decidir(s, agora_ms)

    def _acordar(self, agora_ms):
        self.drives.dormindo = False
        self.acoes.destravar()
        self.t['acordou'] = agora_ms

    def _decidir(self, s, agora_ms):
        seg = agora_ms // 1000
        ctx = self.contexto(s, agora_ms)
        self.forte = False
        self.acoes.disponiveis(ctx, seg, self.mascara)
        d = self.drives
        ruido = C.NOISE_ADULTA if d.d[C.D_AFETO] > 600 else C.NOISE      # 6.5: adulta e mais previsivel
        if ruido != self.rede.ruido:
            self.rede.novo_ruido(ruido)
        dire = self.rede.direto
        for o in range(A.N_ACOES):
            dire[o] = 0
        for di, lim, o, corr in self.direto_idx:
            if d.d[di] > lim:
                dire[o] = corr
        s['drives'] = d.para_rede()
        s['ultima'] = self.ultima
        s['resposta'] = self.resposta
        self.resposta = None
        self.cod.codificar(s)
        r, apr = self.rede, self.apr
        r.zerar_contagem()
        for _ in range(C.DECIDE_TICKS):
            r.passo(self.cod, self.mascara)
            apr.passo()
            if r.t % C.NORM_TICKS == 0:
                apr.homeostase()
        self.ticks_rodados += C.DECIDE_TICKS
        acao = self.acoes.escolher(r.contagem, self.mascara, r.v_o)
        return self._executar(acao, s, agora_ms)

    def _executar(self, acao, s, agora_ms):
        seg = agora_ms // 1000
        custo = self.acoes.executar(acao, seg)
        self.drives._soma(C.D_ENERGIA, -custo * 10)
        if acao == DORMIR:
            self.drives.dormindo = True
        self.ultima = acao
        R = self.rec.acao_iniciada(acao, agora_ms, self.silencio(s['minuto']))
        self._aplicar(R, acao, 'custo_som', agora_ms)
        self.log.append(('A', seg, acao))
        return acao
