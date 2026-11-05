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
from companion.relogio import Relogio
from companion import clima as K

FORTES = ('sacudida_leve', 'sacudida_forte', 'carinho', 'toque', 'estrela', 'shh', 'comida')
DORMIR = A.INDICE['dormir']
ACORDAR = A.INDICE['acordar']
ATRASADOS = ('ignorado', 'som_sem_resposta')      # chegam depois que a elegibilidade zerou


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
        self.solidao = (C.SOLIDAO[0], C.SOLIDAO[1], A.INDICE[C.SOLIDAO[2]], C.SOLIDAO[3])
        self.relogio = Relogio(A.N_ACOES)
        self.minuto = 0                            # minuto do dia do ultimo segundo()
        self.min_acao = array('H', [0] * A.N_ACOES)   # minuto em que cada acao comecou (credito do relogio)
        self.idade_s = 0
        self.t = {}                                # ms do ultimo evento de cada tipo (flags 'recente')
        self.ultima = A.QUIETA
        self.resposta = None
        self.forte = False
        self.log = []                              # ('A', s, acao) e ('R', s, acao, R, motivo), lido pelo sim
        self.ticks_rodados = 0
        self.agora_s = 0                           # raio-X (issue #5): segundo do ultimo segundo()
        self.tempo, self.graus = None, None        # ultima previsao recebida
        self.recs = []                             # (s, acao, R, motivo), as ultimas RAIOX_RECS
        self.horas = []                            # drives x10 de hora em hora, as ultimas RAIOX_HORAS
        self.vezes = array('I', [0] * A.N_ACOES)       # decisoes de cada acao desde a meia-noite
        self.vezes_ontem = array('I', [0] * A.N_ACOES)

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
        eta = self.eta()
        self.apr.recompensa(R, acao, eta)
        if motivo in ATRASADOS:
            self.apr.recompensa_atrasada(R, acao, eta)
        self.relogio.recompensa(R, acao, self.min_acao[acao], eta)
        self.drives.recompensa(R)
        self.t['recompensa' if R > 0 else 'punicao'] = agora_ms
        if R >= C.R_ESTRELA:
            self.t['grande'] = agora_ms
        self.resposta = 0 if R > 0 else 2
        self.log.append(('R', agora_ms // 1000, acao, R, motivo))
        self.recs.append((agora_ms // 1000, acao, R, motivo))
        if len(self.recs) > C.RAIOX_RECS:
            del self.recs[0]

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
        self.minuto = s['minuto']
        seg = self.agora_s = agora_ms // 1000
        d = self.drives
        if seg % 60 == 0:
            self.tempo, self.graus = s.get('tempo'), s.get('graus')
            d.clima = K.efeito(self.tempo, self.graus)
            d.minuto()
        if seg % 3600 == 0:
            self.horas.append(list(d.d))
            if len(self.horas) > C.RAIOX_HORAS:
                del self.horas[0]
        if seg % 600 == 0:
            self.rec.habituacao()
        if seg % 86400 == 0:
            self.apr.esquecer()
            self.relogio.esquecer()
            for o in range(A.N_ACOES):
                self.vezes_ontem[o] = self.vezes[o]
                self.vezes[o] = 0
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
        self.relogio.corrente(self.minuto, dire)
        for di, lim, o, corr in self.direto_idx:  # sobrescreve o relogio (somar piorou o habito na calibracao)
            if d.d[di] > lim:
                dire[o] = corr
        di, lim, o, corr = self.solidao
        if d.d[di] < lim:
            dire[o] += corr
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
        self.min_acao[acao] = self.minuto
        if acao in A.PEDIDOS:
            self.apr.marcar(acao)
        R = self.rec.acao_iniciada(acao, agora_ms, self.silencio(s['minuto']))
        self._aplicar(R, acao, 'custo_som', agora_ms)
        self.log.append(('A', seg, acao))
        self.vezes[acao] += 1
        return acao

    # ---- raio-X (issue #5)
    def resumo(self):
        """O que o cerebro sabe agora, so com int, str, None, list e dict (vira JSON). Nao muda estado."""
        d, r, rel = self.drives, self.rede, self.relogio
        no, ne, top = r.no, C.N_EXC, C.RAIOX_TOP
        nome = [a[0] for a in A.CATALOGO]
        delta = [0] * no                           # oculta->saida: quanto cada acao ganhou desde que nasceu
        w, w0 = r.w_ho, r.w_ho0
        for h in range(ne):
            b = h * no
            for o in range(no):
                delta[o] += w[b + o] - w0[b + o]
        ordem = sorted(range(no), key=lambda o: delta[o])
        habitos, evitas = [], []                   # [celula, acao, peso] do relogio, o mais forte de cada celula
        rw = rel.w
        for c in range(C.RELOGIO_BINS):
            b = c * no
            mx = mn = 0
            for o in range(no):
                if rw[b + o] > rw[b + mx]:
                    mx = o
                if rw[b + o] < rw[b + mn]:
                    mn = o
            if rw[b + mx] >= C.RAIOX_HABITO:
                habitos.append([c, nome[mx], rw[b + mx]])
            if rw[b + mn] <= -C.RAIOX_HABITO:
                evitas.append([c, nome[mn], rw[b + mn]])
        mudou = nasceu = 0                         # entrada->oculta: % que o STDP mexeu
        for k in range(len(r.w_ih)):
            mudou += abs(r.w_ih[k] - r.w_ih0[k])
            nasceu += r.w_ih0[k]
        th = sorted(r.th_h)

        def mais(v):
            o = sorted(range(no), key=lambda i: -v[i])[:top]
            return [[nome[i], v[i]] for i in o if v[i]]

        return {
            'versao': 1, 'semente': self.semente, 'idade_s': self.idade_s, 'agora_s': self.agora_s,
            'minuto': self.minuto, 'acao': nome[self.acoes.atual], 'dormindo': d.dormindo,
            'drives': [[C.DRIVES[i], d.d[i]] for i in range(7)],
            'clima': {'tempo': self.tempo, 'graus': None if self.graus is None else int(self.graus),
                      'alvo': d.clima[0]},
            'hoje': mais(self.vezes), 'ontem': mais(self.vezes_ontem),
            'gosta': [[nome[o], delta[o]] for o in reversed(ordem[-top:]) if delta[o] > 0],
            'evita': [[nome[o], delta[o]] for o in ordem[:top] if delta[o] < 0],
            'relogio': {'passo_min': 1440 // C.RELOGIO_BINS, 'max': C.RELOGIO_MAX, 'habitos': habitos,
                        'evita': evitas},
            'recompensas': [[s, nome[a], R, m] for s, a, R, m in self.recs],
            'horas': [list(x) for x in self.horas],
            'rede': {'eta': self.eta(), 'ruido': r.ruido, 'ticks': self.ticks_rodados,
                     'ih_mudou_pct': mudou * 100 // nasceu if nasceu else 0,
                     'limiar': [th[0], th[len(th) // 2], th[-1]]},
        }
