# Tasks — Cérebro SNN da Capi, fase 0: simulador em CPython

**Issue:** #2
**Baseado em:** `02-spec.md`
**Total:** 36 tasks, ~2 h 30 min de execução, mais ~10 min de simulação na fase C e até ~40 min de simulação na fase D

Convenções: comandos rodam na raiz do repositório. O código das tasks foi rodado no planejamento (protótipo no
scratchpad): os 19 testes unitários passam, o teste do silêncio passa, a semana roda em ~100 s e a fumaça do
MicroPython passa. O teste do hábito **não** passou no protótipo; é a fase D.

---

## FASE A — Pacote, catálogo, drives e recompensa

### A1. Criar a branch a partir da main
```bash
git status --short            # esperado: só "?? sdd/ISSUE_2/"
git switch main && git pull --ff-only && git switch -c feature/sdd-issue-2
```
**Esperado:** `Switched to a new branch 'feature/sdd-issue-2'`; `sdd/ISSUE_2/` continua lá (arquivo não rastreado
acompanha a troca de branch).

### A2. Criar as pastas do pacote
```bash
mkdir -p companion/sim companion/testes
touch companion/__init__.py companion/sim/__init__.py companion/testes/__init__.py
```
**Esperado:** `ls companion` mostra `__init__.py sim testes`.

### A3. Criar `companion/config.py`
Constantes da fonte com a seção em comentário; as marcadas "calibrado" divergem da fonte (motivo no `02-spec.md`). As marcadas "calibracao do habito" nascem neutras e são os botões da fase D.

**Criar:** `companion/config.py`
```python
# Constantes do cerebro SNN (fonte: sdd/ISSUE_2/00-fonte.md). O numero da secao vai no comentario.
# Tudo inteiro: fracoes viram x10 ou deslocamento de bits. Calibracoes ficam anotadas em CALIBRACAO.md.

# 2. Modelo neural
N_IN = 100                 # 3. tabela de sentidos (a secao 2 dizia ~80; vale a soma da tabela)
N_EXC = 80                 # 2. ocultos excitatorios
N_INIB = 16                # 2. ocultos inibitorios
N_HID = N_EXC + N_INIB
V_REST = 0                 # 2.
V_TH = 1000                # 2. limiar inicial (adaptativo so nos ocultos, 6.5)
V_RESET = -200             # 2.
TAU_SHIFT = 4              # 2. vazamento 1/16 por tick
REFRAC = 2                 # 2. ticks sem integrar
W_MAX = 255                # 2.
I_SCALE = 2                # 2. corrente = soma(w) >> I_SCALE
I_OUT_MUL = 6              # calibrado: corrente da saida = soma(w) * I_OUT_MUL (com >> 2 nenhuma saida chegava ao limiar)
NOISE = 30                 # 2. ruido +-NOISE por tick
NOISE_ADULTA = 15          # 6.5 ruido quando afeto > 60
TICK_MS = 50               # 2.
DECIDE_TICKS = 20          # 2.
MIN_SPIKES = 4             # 2.
LATERAL = 80               # 2. inibicao lateral fixa entre saidas
W_IH_INI = (20, 80)        # 2. entrada -> oculta (faixa das ligacoes fortes)
IH_FORTES = 25             # calibrado: % das ligacoes entrada->oculta que nascem fortes; o resto nasce em 0..W_IH_FRACO
W_IH_FRACO = 5             # calibrado: com todas em 20..80 nenhum oculto ficava seletivo a hora
OCULTOS_TEMPO = 0          # calibracao do habito: ocultos 0..N-1 so ouvem hora, dia e luz (inicial = 0, desligado)
W_HH_EXC = (10, 40)        # 2. oculta -> oculta excitatorio
W_HH_INIB = (40, 120)      # 2. oculta -> oculta inibitorio (sinal negativo)
HH_DENS = 10               # 2. % das combinacoes oculta -> oculta
HH_DENS_INIB = 10          # calibracao do habito: % das ligacoes que saem dos inibitorios (inicial = HH_DENS)
W_HO_INI = (30, 60)        # 2. oculta -> saida

# 3. Sentidos
P_MAX = 128                # 3. 0,5 em 1/256: chance de spike = ativacao(0..255) * P_MAX >> 8
P_MAX_HORA = 128           # calibracao do habito: P_MAX so do grupo 'hora' (inicial = P_MAX)
RAJADA = 3                 # 3. spikes de um evento

# 4. Drives (x10)
D_FOME, D_ENERGIA, D_HUMOR, D_TEDIO, D_AFETO, D_CURIOSIDADE, D_ESTRESSE = range(7)
DRIVES = ('fome', 'energia', 'humor', 'tedio', 'afeto', 'curiosidade', 'estresse')
DRIVE_INI = (300, 800, 0, 200, 300, 500, 0)
DRIVE_MIN = (0, 0, -1000, 0, 0, 0, 0)
DRIVE_MAX = (1000, 1000, 1000, 1000, 1000, 1000, 1000)
FOME_MIN = 10              # 4. +1/min
ENERGIA_ACORDADA = -5      # 4. -0,5/min
ENERGIA_DORMINDO = 30      # 4. +3/min
HUMOR_REGRIDE = 10         # 4. 1/min em direcao a 0
TEDIO_MIN = 10             # 4. +1/min sem interacao
AFETO_MIN = -2             # 4. -0,02/min vira -0,2 a cada 10 min (ver drives.py)
CURIOSIDADE_MIN = -10      # 4.
ESTRESSE_MIN = -20         # 4.
COMER = -400               # 4.
BRINCAR_TEDIO = -300       # 4.
AFETO_POSITIVA = 2         # 4. +0,2 por interacao positiva
AFETO_PISO = 500           # 4. depois de passar de 60, nunca abaixo de 50
NOVIDADE_CURIOSIDADE = 150 # 4.
ESTRESSE_SACUDIDA = 300    # 4.
ESTRESSE_BARULHO = 100     # 4.
ESTRESSE_RALHAR = 150      # 4.
ENERGIA_SONO_FORCADO = 200 # 1./4. regra fixa: < 20 forca dormir
ENERGIA_CARAS = 400        # 4. < 40 bloqueia acoes de custo >= 3
ACORDA_ENERGIA = 900       # 5. dormir dura ate energia >= 90
SILENCIO = (22, 8)         # 4. horario de silencio (configuravel no portal na fase 3)

# Ligacao direta drive -> saida (2., 4.): (drive, limiar x10, nome da acao, corrente por tick)
DIRETO = (
    (D_FOME, 800, 'pedir_comida', 500),
    (D_ESTRESSE, 800, 'esconder_rosto', 500),
)

# 6. Aprendizado
A_PLUS = 2                 # 6.1
A_MINUS = 3                # 6.1
W_FRAC = 4                 # calibrado: pesos entrada->oculta guardados x16 (resolucao fina do STDP)
STDP_SHIFT = 14            # calibrado: dw+ = A_PLUS*x*(WMAX16-w) >> STDP_SHIFT; dw- = A_MINUS*x*w >> STDP_SHIFT
TRACO_SHIFT = 4            # 6.1 traco decai 1/16 por tick
ELIG_PASSO = 16            # 6.2 decaimento da elegibilidade aplicado em lote a cada 16 ticks
ELIG_MUL, ELIG_SHIFT = 7, 5  # 6.2 (63/64)^16 = 0,778 ~ 1 - 7/32
R_SHIFT = 10               # 6.2 dw = eta * R * e >> R_SHIFT
ETA_FILHOTE = 4            # 6.2 primeiros 7 dias
ETA_ADULTA = 2             # 6.2
DIAS_FILHOTE = 7           # 6.2
NORM_TICKS = 100           # 6.5
LIMIAR_ALTO = 30           # 6.5 % de ticks com spike
LIMIAR_BAIXO = 1           # 6.5
LIMIAR_PASSO = 2           # 6.5 % por ajuste
TH_MIN, TH_MAX = 500, 4000 # calibrado: limites do limiar adaptativo
ESQUECE_PCT = 1            # 6.5 % por dia em direcao ao inicial
PISO_SOCIAL = 5            # 6.5 piso dos pesos oculta->saida de Social e Fisiologica

# 6.3 Recompensas
R_ESTRELA = 20
R_CARINHO = 10
R_COMIDA = 15              # x (1 + fome/100)
R_RESPONDEU = 8
R_JOGO = 12
R_JOGO_REPETIU = 5
R_SOCIAL = 5
R_TOQUE_QUIETA = -2
R_IGNORADO = -5
R_SOM_SEM_RESPOSTA = -6
R_SOM_SILENCIO = -10
R_SHH = -15
R_SACUDIDA_LEVE = -8
R_SACUDIDA_FORTE = -12
R_DESLIGOU = -4
R_CUSTO_SOM = -3           # 6.4 custo intrinseco
JANELA_CARINHO = 3000      # ms
JANELA_RESPOSTA = 10000    # ms
JANELA_IGNORADO = 60000    # ms
JANELA_SOM = 30000         # ms
JANELA_DESLIGOU = 5000     # ms
HABITUA_MIN = 10           # 6.4 contador x10 decai 1/6 a cada 10 min (~ultima hora)
```
**Verificar:** `python3 -c "from companion import config as C; print(C.N_IN, C.N_HID)"` imprime `100 96`.

### A4. Criar `companion/actions.py`
Catálogo das 100 ações (seção 5 da fonte), pré-condições compiladas, cooldown, trava e escolha com desempate pelo potencial.

**Criar:** `companion/actions.py`
```python
# Catalogo das 100 acoes (secao 5): unica fonte de verdade. O indice na tupla e o neuronio de saida.
# (nome, categoria, som, precondicao, custo, duracao s, cooldown s). Duracao -1 = ate uma condicao.
# Precondicao: '|' separa alternativas (OU) e ',' junta termos (E); termo = campo<n, campo>n ou campo.
from companion import config as C

META, FISIO, EXPR, CORPO, SOM, SOCIAL, BRINCA, EXPLORA, OUTRA = range(9)
CATEGORIAS = ('Meta', 'Fisiologica', 'Expressao', 'Corpo', 'Som', 'Social', 'Brincadeira', 'Exploracao', 'Outra Capi')

CATALOGO = (
    ('ficar_quieta', META, 0, '', 0, 1, 0),
    ('ficar_quieta_longa', META, 0, '', 0, 300, 0),
    ('ouvir_dono', META, 1, 'voz', 1, -1, 10),
    ('pedir_para_carregar', META, 0, 'bateria<25', 0, 5, 600),
    ('avisar_bateria', META, 1, 'bateria<10', 0, 3, 1800),
    ('baixar_brilho', META, 0, 'noite', 0, 2, 300),
    ('dormir_tela', META, 0, 'sem_toque>600', 0, 2, 300),
    ('mostrar_hora', META, 0, '', 0, 5, 60),
    ('mostrar_clima', META, 0, 'wifi', 0, 6, 600),
    ('mostrar_humor', META, 0, '', 0, 4, 60),
    ('dormir', FISIO, 0, 'energia<40|noite', 0, -1, 60),
    ('cochilar', FISIO, 0, 'energia<60', 0, 120, 300),
    ('acordar', FISIO, 0, 'dormindo,estimulo', 0, 3, 0),
    ('espreguicar', FISIO, 0, 'acordou', 1, 3, 60),
    ('bocejar', FISIO, 0, 'energia<50', 0, 2, 60),
    ('comer', FISIO, 0, 'comida', 0, 5, 0),
    ('beliscar', FISIO, 0, 'comida,fome<40', 0, 3, 60),
    ('pedir_comida', FISIO, 0, 'fome>50', 0, 4, 120),
    ('recusar_comida', FISIO, 0, 'comida,fome<20', 0, 2, 0),
    ('cocar', FISIO, 0, '', 1, 2, 60),
    ('sorrir', EXPR, 0, '', 0, 2, 10),
    ('sorriso_largo', EXPR, 0, 'humor>30', 0, 2, 20),
    ('careta', EXPR, 0, '', 0, 2, 20),
    ('bico', EXPR, 0, 'humor<0', 0, 3, 30),
    ('olhos_brilhando', EXPR, 0, 'curiosidade>40', 0, 2, 20),
    ('piscar', EXPR, 0, '', 0, 1, 5),
    ('olhar_de_lado', EXPR, 0, '', 0, 2, 10),
    ('surpresa', EXPR, 0, 'evento', 0, 2, 20),
    ('cara_de_tedio', EXPR, 0, 'tedio>50', 0, 3, 30),
    ('bravinha', EXPR, 0, 'humor<-30', 0, 3, 30),
    ('lagrimazinha', EXPR, 0, 'humor<-50', 0, 4, 120),
    ('rir', EXPR, 1, 'humor>40', 0, 2, 30),
    ('dancinha', CORPO, 0, 'energia>40', 2, 4, 30),
    ('danca_longa', CORPO, 1, 'energia>60,humor>20', 4, 10, 300),
    ('pular', CORPO, 0, 'energia>40', 2, 2, 20),
    ('girar', CORPO, 0, 'energia>30', 1, 2, 20),
    ('deitar', CORPO, 0, '', 0, 5, 30),
    ('rolar', CORPO, 0, 'deitada', 1, 3, 30),
    ('balancar', CORPO, 0, '', 0, 4, 20),
    ('esconder_rosto', CORPO, 0, 'estresse>30', 0, 4, 30),
    ('tremer', CORPO, 0, 'estresse>50', 1, 3, 30),
    ('acenar', CORPO, 0, '', 0, 2, 20),
    ('ronronar', SOM, 1, 'carinho', 0, 3, 30),
    ('cantarolar', SOM, 1, 'humor>10', 1, 4, 120),
    ('cantar_musica', SOM, 1, 'humor>30,energia>40', 2, 15, 900),
    ('assobiar', SOM, 1, '', 1, 3, 180),
    ('gritinho_alegria', SOM, 1, 'grande', 1, 1, 60),
    ('resmungar', SOM, 1, 'humor<-20', 0, 2, 120),
    ('suspirar', SOM, 1, 'tedio>40', 0, 2, 120),
    ('chamar_baixo', SOM, 1, 'sem_toque>300', 0, 2, 300),
    ('chamar_alto', SOM, 1, 'sem_toque>1800', 1, 2, 900),
    ('alarme_fome', SOM, 1, 'fome>90', 0, 3, 600),
    ('risada', SOM, 1, 'humor>50', 0, 2, 60),
    ('beep_curto', SOM, 1, '', 0, 1, 60),
    ('pedir_carinho', SOCIAL, 0, '', 0, 5, 60),
    ('pedir_brincar', SOCIAL, 0, 'tedio>40,energia>40', 0, 5, 120),
    ('chamar_atencao_silenciosa', SOCIAL, 0, 'sem_toque>300', 0, 6, 120),
    ('mostrar_curiosidade', SOCIAL, 0, 'curiosidade>40', 0, 12, 300),
    ('contar_piada', SOCIAL, 0, 'humor>20', 0, 10, 600),
    ('pedir_abraco', SOCIAL, 0, 'afeto>30', 0, 5, 300),
    ('dar_presente', SOCIAL, 0, 'afeto>50', 1, 6, 1800),
    ('elogiar_dono', SOCIAL, 0, 'recompensa', 0, 4, 300),
    ('agradecer', SOCIAL, 0, 'recebeu', 0, 2, 30),
    ('emburrar', SOCIAL, 0, 'humor<-30', 0, 30, 300),
    ('ignorar_toque', SOCIAL, 0, 'humor<-50', 0, 10, 300),
    ('fazer_charme', SOCIAL, 0, 'afeto>20', 0, 4, 120),
    ('pedir_desculpa', SOCIAL, 0, 'punicao', 0, 4, 120),
    ('dar_boa_noite', SOCIAL, 0, 'hora>19,hora<23', 0, 4, 43200),
    ('dar_bom_dia', SOCIAL, 0, 'hora>5,hora<10', 0, 4, 43200),
    ('esconde_esconde', BRINCA, 0, 'tedio>30', 1, 30, 300),
    ('foge_do_dedo', BRINCA, 0, 'toque', 2, 20, 300),
    ('adivinha_a_mao', BRINCA, 0, '', 1, 20, 600),
    ('sequencia_de_toques', BRINCA, 0, 'energia>40', 1, 40, 600),
    ('pedra_papel_tesoura', BRINCA, 0, '', 1, 20, 600),
    ('contar_junto', BRINCA, 0, '', 1, 15, 600),
    ('corrida_de_inclinar', BRINCA, 0, 'imu,energia>50', 3, 30, 600),
    ('equilibrar', BRINCA, 0, 'imu', 2, 20, 600),
    ('encher_balao', BRINCA, 0, 'mic', 1, 15, 600),
    ('cantar_junto', BRINCA, 1, 'mic,humor>30', 2, 20, 1800),
    ('olhar_em_volta', EXPLORA, 0, '', 0, 3, 20),
    ('farejar', EXPLORA, 0, 'curiosidade>30', 0, 3, 60),
    ('investigar_toque', EXPLORA, 0, 'fora', 0, 4, 60),
    ('baguncar_tela', EXPLORA, 0, 'tedio>70', 1, 6, 600),
    ('esconder_item', EXPLORA, 0, 'tedio>60', 1, 5, 900),
    ('rabiscar', EXPLORA, 0, 'tedio>50', 1, 8, 600),
    ('mudar_de_canto', EXPLORA, 0, '', 0, 2, 60),
    ('espiar', EXPLORA, 0, '', 0, 3, 60),
    ('derrubar_coisa', EXPLORA, 1, 'tedio>80', 1, 4, 1800),
    ('imitar_dono', EXPLORA, 0, 'padrao', 0, 6, 300),
    ('acenar_para_outra', OUTRA, 0, 'outra', 0, 2, 60),
    ('aproximar', OUTRA, 0, 'outra', 0, 4, 60),
    ('conversar', OUTRA, 1, 'outra,afs>10', 1, 10, 300),
    ('pega_pega_duplo', OUTRA, 0, 'outra,energia>40,outra_energia>40', 3, 30, 600),
    ('ensinar', OUTRA, 0, 'outra,afs>40', 1, 5, 3600),
    ('ciume', OUTRA, 0, 'tocada', 0, 6, 300),
    ('dividir_comida', OUTRA, 0, 'comida,outra', 0, 5, 600),
    ('dormir_juntas', OUTRA, 0, 'outra,energia<40,outra_energia<40,afs>30', 0, -1, 3600),
    ('danca_dupla', OUTRA, 1, 'outra,humor>30', 3, 12, 900),
    ('apresentar', OUTRA, 0, 'dna_novo', 0, 6, 0),
    ('ignorar_outra', OUTRA, 0, 'outra,humor<-20', 0, 10, 300),
)
N_ACOES = len(CATALOGO)
INDICE = {a[0]: i for i, a in enumerate(CATALOGO)}
QUIETA = 0
COM_SOM = tuple(i for i, a in enumerate(CATALOGO) if a[2])
PEDIDOS = tuple(INDICE[n] for n in ('pedir_para_carregar', 'pedir_comida', 'pedir_carinho', 'pedir_brincar',
                                    'pedir_abraco', 'chamar_baixo', 'chamar_alto', 'chamar_atencao_silenciosa'))
CHAMADOS = tuple(INDICE[n] for n in ('chamar_baixo', 'chamar_alto', 'chamar_atencao_silenciosa'))


def _termo(t):
    for op in '<>':
        if op in t:
            campo, n = t.split(op)
            return (campo, op, int(n))
    return (t, '', 0)


# precondicoes compiladas uma vez: tupla de alternativas, cada uma tupla de termos
PRECOND = tuple(tuple(tuple(_termo(t) for t in alt.split(',')) for alt in a[3].split('|')) if a[3] else ()
                for a in CATALOGO)


def pode(i, ctx):
    alts = PRECOND[i]
    if not alts:
        return True
    for alt in alts:
        ok = True
        for campo, op, n in alt:
            v = ctx.get(campo, 0)
            if (op == '<' and not v < n) or (op == '>' and not v > n) or (op == '' and not v):
                ok = False
                break
        if ok:
            return True
    return False


class Acoes:
    """Pre-condicoes, cooldown, trava (lock), custo de energia e selecao (secoes 2 e 5)."""

    def __init__(self):
        self.ultima_vez = [-10 ** 9] * N_ACOES     # segundo da ultima execucao
        self.atual = QUIETA
        self.fim = 0                               # segundo em que a trava acaba (-1 = ate condicao)

    def disponiveis(self, ctx, agora_s, mascara):
        """Preenche mascara[i] = 1 para as acoes que podem vencer agora."""
        energia = ctx.get('energia', 100)
        for i in range(N_ACOES):
            a = CATALOGO[i]
            ok = agora_s - self.ultima_vez[i] >= a[6] and pode(i, ctx)
            if ok and a[4] >= 3 and energia * 10 < C.ENERGIA_CARAS:
                ok = False
            mascara[i] = 1 if ok else 0
        mascara[QUIETA] = 1

    def escolher(self, contagem, mascara, potencial):
        """Mais spikes na janela vence; empate decide pelo potencial no fim da janela (calibrado: com
        'empate -> ficar_quieta' as saidas sincronizadas empatavam quase sempre). Abaixo de MIN_SPIKES: quieta."""
        melhor, n_melhor, v_melhor = QUIETA, 0, -10 ** 9
        for i in range(N_ACOES):
            if not mascara[i]:
                continue
            c = contagem[i]
            if c > n_melhor or (c == n_melhor and potencial[i] > v_melhor):
                melhor, n_melhor, v_melhor = i, c, potencial[i]
        return melhor if n_melhor >= C.MIN_SPIKES else QUIETA

    def travada(self, agora_s):
        return self.fim == -1 or agora_s < self.fim

    def executar(self, i, agora_s):
        self.atual = i
        self.ultima_vez[i] = agora_s
        dur = CATALOGO[i][5]
        self.fim = -1 if dur < 0 else agora_s + dur
        return CATALOGO[i][4]                      # custo de energia

    def destravar(self):
        self.fim = 0
```
**Verificar:** `python3 -c "from companion import actions as A; print(A.N_ACOES, len(A.COM_SOM))"` imprime `100 20`.

### A5. Criar `companion/drives.py`
Os 7 drives ×10, atualização por minuto, piso do afeto e avanço por tempo desligado (seção 4).

**Criar:** `companion/drives.py`
```python
# Os 7 drives (secao 4), em inteiros x10 (fome 0..1000, humor -1000..1000). Atualizados a cada minuto.
from array import array
from companion import config as C


class Drives:
    def __init__(self):
        self.d = array('h', C.DRIVE_INI)
        self.dormindo = False
        self.interagiu = False            # houve interacao neste minuto (o tedio nao sobe)
        self.afeto_ja_60 = False
        self._min = 0

    def _soma(self, i, x):
        self.d[i] = max(C.DRIVE_MIN[i], min(C.DRIVE_MAX[i], self.d[i] + x))
        if i == C.D_AFETO:
            if self.d[i] > 600:
                self.afeto_ja_60 = True
            if self.afeto_ja_60 and self.d[i] < C.AFETO_PISO:
                self.d[i] = C.AFETO_PISO

    def minuto(self):
        self._min += 1
        d = self.d
        self._soma(C.D_FOME, C.FOME_MIN)
        self._soma(C.D_ENERGIA, C.ENERGIA_DORMINDO if self.dormindo else C.ENERGIA_ACORDADA)
        h = d[C.D_HUMOR]
        self._soma(C.D_HUMOR, -min(C.HUMOR_REGRIDE, h) if h > 0 else min(C.HUMOR_REGRIDE, -h))
        if d[C.D_FOME] > 800:
            self._soma(C.D_HUMOR, -10)
        if not self.interagiu and not self.dormindo:
            self._soma(C.D_TEDIO, C.TEDIO_MIN)
        self.interagiu = False
        if self._min % 10 == 0:
            self._soma(C.D_AFETO, C.AFETO_MIN)
        self._soma(C.D_CURIOSIDADE, C.CURIOSIDADE_MIN)
        self._soma(C.D_ESTRESSE, C.ESTRESSE_MIN)

    def avancar(self, minutos, dormindo):
        """Placa desligada (secao 4): aplica os minutos de uma vez."""
        self.dormindo = dormindo
        for _ in range(minutos):
            self.minuto()

    def recompensa(self, R):
        """Cada recompensa R soma R/2 ao humor (x10: R*5); positiva tambem fortalece o vinculo."""
        self._soma(C.D_HUMOR, R * 5)
        if R > 0:
            self.interagiu = True
            self._soma(C.D_AFETO, C.AFETO_POSITIVA)

    def get(self, i):
        return self.d[i] // 10

    def para_rede(self):
        """0..100 por drive (humor -100..100 vira 0..100) para o codificador."""
        d = self.d
        return [(d[i] + 1000) // 20 if i == C.D_HUMOR else d[i] // 10 for i in range(7)]
```
**Verificar:** `python3 -c "from companion.drives import Drives; d=Drives(); d.minuto(); print(list(d.d))"` imprime `[310, 795, 0, 210, 300, 490, 0]`.

### A6. Criar `companion/reward.py`
Eventos do dono → R (tabela 6.3), custo de som e habituação (6.4), prazos de "som sem resposta" e "ignorado".

**Criar:** `companion/reward.py`
```python
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
SEM_HABITUACAO = (A.FISIO,)
SEMPRE = ('jogo_fim', 'jogo_repetiu', 'social_ok', 'sacudida_forte')   # nao dependem da janela de 3 s


class Recompensa:
    def __init__(self):
        self.n = array('H', [0] * A.N_ACOES)      # execucoes recentes x10 (6.4)
        self.acao = A.QUIETA
        self.t_acao = -10 ** 9                     # ms do inicio da ultima acao
        self.n_acao = 0                            # habituacao da acao atual quando comecou
        self.esperando_toque = None                # (acao, prazo ms, R se o prazo vencer)
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
            self.esperando_toque = (acao, t_ms + C.JANELA_IGNORADO)
        return R

    def evento(self, nome, t_ms, drives):
        """Reacao do dono. Devolve (R, acao que recebe o credito)."""
        acao = self.acao
        if nome in TOQUES:
            self.esperando_som = None
            pedido = self.esperando_toque
            self.esperando_toque = None
        else:
            pedido = None
        R = 0
        dt = t_ms - self.t_acao
        if nome == 'carinho':
            R = C.R_CARINHO if dt <= C.JANELA_CARINHO else 0
        elif nome == 'comida':
            R = C.R_COMIDA if acao == A.INDICE['pedir_comida'] else 0
        elif nome in EVENTO_R:
            janela = C.JANELA_DESLIGOU if nome == 'desligou' else C.JANELA_CARINHO
            R = EVENTO_R[nome] if nome in SEMPRE or dt <= janela else 0
        if pedido and acao in A.CHAMADOS and dt <= C.JANELA_RESPOSTA:
            R += C.R_RESPONDEU
        if nome in TOQUES and acao == A.QUIETA and R == 0:
            R = C.R_TOQUE_QUIETA
        if nome in EVENTO_DRIVE and R > 0:
            R = R * (100 + drives.get(EVENTO_DRIVE[nome])) // 100
        if R > 0:
            R = R * 3 // (3 + self.n_acao)
        self.ultimo = (R, nome)
        return R, acao

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
```
**Verificar:** `python3 -c "from companion.reward import Recompensa; from companion import actions as A; print(Recompensa().acao_iniciada(A.INDICE['beep_curto'], 0, True))"` imprime `-13`.

### A7. Criar `companion/testes/test_regras.py`
Testes do catálogo, drives e recompensa.

**Criar:** `companion/testes/test_regras.py`
```python
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
```
**Verificar:** `python3 -m unittest companion.testes.test_regras` → `Ran 11 tests ... OK`.

### A8. Commit da fase A
```bash
git add companion/__init__.py companion/sim/__init__.py companion/testes/__init__.py companion/config.py \
        companion/actions.py companion/drives.py companion/reward.py companion/testes/test_regras.py sdd/ISSUE_2/
git commit -m "feat(issue-2): fase A - catalogo de acoes, drives e recompensa (#2)"
```

---

## FASE B — Rede LIF e aprendizado

### B1. Criar `companion/encoder.py`
Sentidos → 100 neurônios de entrada (tabela da seção 3): população em tenda, binário e rajada.

**Criar:** `companion/encoder.py`
```python
# Sentidos -> neuronios de entrada (secao 3). Valores continuos: codificacao por populacao com curva em tenda
# (aproxima a gaussiana sem tabela). Eventos: rajada de RAJADA spikes num neuronio dedicado.
import random
from array import array
from companion import config as C

# (nome, primeiro neuronio, quantidade) na ordem da tabela da secao 3; soma = 100
GRUPOS = (('hora', 8), ('dia', 2), ('toque_reg', 4), ('toque_tipo', 4), ('toque_freq', 4), ('sem_toque', 6),
          ('mov', 4), ('orient', 3), ('som_nivel', 4), ('som_evento', 3), ('luz', 2), ('bateria', 5),
          ('outra', 3), ('outra_estado', 6), ('novidade', 3), ('drives', 28), ('ultima', 8), ('resposta', 3))
BASE = {}
_b = 0
for _n, _q in GRUPOS:
    BASE[_n] = _b
    _b += _q
assert _b == C.N_IN


def _log2(x):
    n = 0
    while x > 1:
        x >>= 1
        n += 1
    return n


class Codificador:
    def __init__(self):
        self.ativ = array('H', [0] * C.N_IN)     # 0..255, vale ate o proximo codificar()
        self.rajada = array('B', [0] * C.N_IN)
        self.p_max = array('H', [C.P_MAX_HORA if i < 8 else C.P_MAX for i in range(C.N_IN)])  # 'hora' = 0..7

    def _pop(self, grupo, n, x, lo, hi, circular=False):
        b = BASE[grupo]
        passo = (hi - lo) // (n if circular else n - 1)
        for k in range(n):
            c = lo + k * passo
            d = abs(x - c)
            if circular and d > (hi - lo) // 2:
                d = (hi - lo) - d
            self.ativ[b + k] = 255 * (passo - d) // passo if d < passo else 0

    def _bin(self, grupo, k, ligado):
        self.ativ[BASE[grupo] + k] = 255 if ligado else 0

    def evento(self, grupo, k):
        if k is not None and k >= 0:
            self.rajada[BASE[grupo] + k] = C.RAJADA

    def codificar(self, s):
        """s: dicionario de sentidos (ver sim/sentidos.py). Chamado uma vez por segundo."""
        self._pop('hora', 8, s['minuto'], 0, 1440, True)
        self._bin('dia', 0, not s['fim_semana'])
        self._bin('dia', 1, s['fim_semana'])
        self.evento('toque_reg', s.get('toque_reg'))
        self.evento('toque_tipo', s.get('toque_tipo'))
        self._pop('toque_freq', 4, min(s['toques_60s'], 20), 0, 21)
        self._pop('sem_toque', 6, min(_log2(s['sem_toque'] + 1), 14), 0, 15)
        self.evento('mov', s.get('mov'))
        self._pop('orient', 3, s['orient'], 0, 3)
        self._pop('som_nivel', 4, s['som_nivel'], 0, 101)
        self.evento('som_evento', s.get('som_evento'))
        self._bin('luz', 0, not s['noite'])
        self._bin('luz', 1, s['noite'])
        b = BASE['bateria']
        for k in range(4):
            c = k * 33
            d = abs(s['bateria'] - c)
            self.ativ[b + k] = 255 * (33 - d) // 33 if d < 33 else 0
        self.ativ[b + 4] = 255 if s['carregando'] else 0
        self._pop('outra', 3, s['outra'], 0, 3)
        for k in range(6):
            if s['outra_estado'] >> k & 1:
                self.evento('outra_estado', k)
        self._pop('novidade', 3, s['novidade'], 0, 101)
        for i, v in enumerate(s['drives']):           # 0..100 (humor ja mapeado de -100..100)
            b = BASE['drives'] + 4 * i
            for k in range(4):
                d = abs(v - k * 33)
                self.ativ[b + k] = 255 * (33 - d) // 33 if d < 33 else 0
        h = (s['ultima'] * 37) & 255
        for k in range(8):
            self._bin('ultima', k, h >> k & 1)
        self.evento('resposta', s.get('resposta'))

    def spikes(self, saida):
        """Sorteia os spikes deste tick; devolve quantos entraram em saida (lista de indices)."""
        n = 0
        ativ, raj, pm = self.ativ, self.rajada, self.p_max
        lim = random.getrandbits
        for i in range(C.N_IN):
            if raj[i]:
                raj[i] -= 1
                saida[n] = i
                n += 1
            elif ativ[i] and lim(8) < (ativ[i] * pm[i]) >> 8:
                saida[n] = i
                n += 1
        return n
```
**Verificar:** `python3 -c "from companion.encoder import BASE; print(BASE['drives'], BASE['resposta'])"` imprime `61 97`.

### B2. Criar `companion/snn.py`
Rede LIF inteira: entrada esparsa ×16, recorrência CSR, saída com inibição lateral e máscara de pré-condição.

**Criar:** `companion/snn.py`
```python
# Rede LIF em inteiros (secao 2): entrada -> oculta (densa), oculta -> oculta (esparsa, CSR),
# oculta excitatoria -> saida (densa) e inibicao lateral fixa entre saidas. Sem float.
import random
from array import array
from companion import config as C
from companion.encoder import BASE

NI, NH, NE = C.N_IN, C.N_HID, C.N_EXC
RECENTE = 16                      # ticks guardados para o STDP (alem disso o traco ja nao muda peso)

# traco pre/pos: 255 * (15/16)^dt, zero a partir de RECENTE (6.1: decai 1/16 por tick)
TRACO = array('H', [0] * (RECENTE + 1))
_x = 255 << 8
for _d in range(RECENTE):
    TRACO[_d] = _x >> 8
    _x -= _x >> C.TRACO_SHIFT


class Rede:
    def __init__(self, n_saidas, semente):
        random.seed(semente)
        ri = random.randint
        self.no = no = n_saidas
        self.t = 0
        self.w_ih = array('h', [(ri(*C.W_IH_INI) if random.getrandbits(7) < 128 * C.IH_FORTES // 100
                                 else ri(0, C.W_IH_FRACO)) << C.W_FRAC for _ in range(NI * NH)])  # [i * NH + h], x16
        self.w_ho = array('h', [ri(*C.W_HO_INI) for _ in range(NE * no)])     # [h * no + o]
        tempo = [BASE[g] + k for g, n in (('hora', 8), ('dia', 2), ('luz', 2)) for k in range(n)]
        for h in range(C.OCULTOS_TEMPO):
            for i in range(NI):
                self.w_ih[i * NH + h] = (C.W_MAX << C.W_FRAC) if i in tempo else 0
        self.w_ih0 = array('h', self.w_ih)
        self.soma_h = array('i', [sum(self.w_ih[i * NH + h] for i in range(NI)) for h in range(NH)])  # alvo da normalizacao
        self.w_ho0 = array('h', self.w_ho)
        ini, pos, w = array('H', [0] * (NH + 1)), array('H'), array('h')
        for h in range(NH):
            ini[h] = len(pos)
            for k in range(NH):
                if k != h and random.getrandbits(7) < 128 * (C.HH_DENS if h < NE else C.HH_DENS_INIB) // 100:
                    pos.append(k)
                    w.append(ri(*C.W_HH_EXC) if h < NE else -ri(*C.W_HH_INIB))
        ini[NH] = len(pos)
        self.hh_ini, self.hh_pos, self.hh_w = ini, pos, w
        self.v_h = array('i', [C.V_REST] * NH)
        self.v_o = array('i', [C.V_REST] * no)
        self.ref_h = array('B', [0] * NH)
        self.ref_o = array('B', [0] * no)
        self.th_h = array('i', [C.V_TH] * NH)
        self.cnt_h = array('H', [0] * NH)        # spikes desde a ultima homeostase (6.5)
        self.ult_in = array('i', [-RECENTE] * NI)
        self.ult_h = array('i', [-RECENTE] * NH)
        self.ult_o = array('i', [-RECENTE] * no)
        self.spk_in = array('H', [0] * NI)
        self.n_in = 0
        self.spk_h = []                            # spikes ocultos deste tick
        self.spk_o = []                            # spikes de saida deste tick
        self.rec_in, self.rec_h, self.rec_o = [[] for _ in range(RECENTE)], [[] for _ in range(RECENTE)], \
            [[] for _ in range(RECENTE)]
        self.direto = array('h', [0] * no)        # corrente fixa drive -> saida
        self.ruido = C.NOISE
        self._rtab = array('h', [ri(-C.NOISE, C.NOISE) for _ in range(1024)])
        self._rk = 0
        self.contagem = array('H', [0] * no)

    def novo_ruido(self, amplitude):
        self.ruido = amplitude
        ri = random.randint
        for k in range(1024):
            self._rtab[k] = ri(-amplitude, amplitude)

    def passo(self, cod, mascara):
        """Um tick de 50 ms. cod: Codificador; mascara[o] = 0 deixa a saida o calada."""
        t = self.t = self.t + 1
        n_in = self.n_in = cod.spikes(self.spk_in)
        spk_in, ult_in = self.spk_in, self.ult_in
        I = [0] * NH
        w_ih = self.w_ih
        for k in range(n_in):
            i = spk_in[k]
            ult_in[i] = t
            b = i * NH
            for h in range(NH):
                I[h] += w_ih[b + h]
        ini, pos, whh = self.hh_ini, self.hh_pos, self.hh_w
        for h in self.spk_h:                      # recorrencia: spikes ocultos do tick anterior
            for k in range(ini[h], ini[h + 1]):
                I[pos[k]] += whh[k] << C.W_FRAC
        rt, rk = self._rtab, self._rk + random.getrandbits(4)
        v, ref, th, cnt, ult_h = self.v_h, self.ref_h, self.th_h, self.cnt_h, self.ult_h
        spk_h = []
        for h in range(NH):
            if ref[h]:
                ref[h] -= 1
                continue
            vv = v[h]
            vv += (I[h] >> (C.I_SCALE + C.W_FRAC)) - ((vv - C.V_REST) >> C.TAU_SHIFT) + rt[(rk + h) & 1023]
            if vv >= th[h]:
                vv = C.V_RESET
                ref[h] = C.REFRAC
                cnt[h] += 1
                ult_h[h] = t
                spk_h.append(h)
            v[h] = vv
        no = self.no
        J = [0] * no
        w_ho = self.w_ho
        for h in spk_h:
            if h < NE:
                b = h * no
                for o in range(no):
                    J[o] += w_ho[b + o]
        lat = C.LATERAL * len(self.spk_o)
        v, ref, ult_o, cont, dire = self.v_o, self.ref_o, self.ult_o, self.contagem, self.direto
        anteriores = self.spk_o
        spk_o = []
        rk += NH
        for o in range(no):
            if not mascara[o]:
                v[o] = C.V_REST
                continue
            if ref[o]:
                ref[o] -= 1
                continue
            vv = v[o]
            inib = lat - C.LATERAL if o in anteriores else lat
            vv += J[o] * C.I_OUT_MUL + dire[o] - inib - ((vv - C.V_REST) >> C.TAU_SHIFT) + rt[(rk + o) & 1023]
            if vv >= C.V_TH:
                vv = C.V_RESET
                ref[o] = C.REFRAC
                ult_o[o] = t
                cont[o] += 1
                spk_o.append(o)
            v[o] = vv
        self._rk = rk & 1023
        self.spk_h, self.spk_o = spk_h, spk_o
        s = t % RECENTE
        self.rec_in[s] = [spk_in[k] for k in range(n_in)]
        self.rec_h[s] = spk_h
        self.rec_o[s] = spk_o

    def zerar_contagem(self):
        c = self.contagem
        for o in range(self.no):
            c[o] = 0

    def recentes(self, rec):
        """Indices que dispararam nos ultimos RECENTE ticks (sem repeticao)."""
        vistos = set()
        for lista in rec:
            vistos.update(lista)
        return vistos
```
**Verificar:** `python3 -c "from companion.snn import Rede; r=Rede(100,1); print(len(r.w_ih), len(r.w_ho))"` imprime `9600 8000`.

### B3. Criar `companion/learn.py`
STDP de limite suave, elegibilidade em lote, R-STDP na coluna da ação, homeostase e esquecimento.

**Criar:** `companion/learn.py`
```python
# Aprendizado (secao 6): STDP entrada -> oculta, elegibilidade + R-STDP oculta -> saida,
# normalizacao, limiar adaptativo e esquecimento. Saida -> saida e oculta -> oculta sao fixas.
from array import array
from companion import config as C
from companion.snn import TRACO, RECENTE

NI, NH, NE = C.N_IN, C.N_HID, C.N_EXC


class Aprendizado:
    def __init__(self, rede, pisos):
        """pisos[o]: menor peso permitido na coluna o (PISO_SOCIAL para Social e Fisiologica, senao 0)."""
        self.rede = rede
        no = rede.no
        self.e = array('i', [0] * (NE * no))     # elegibilidade [h * no + o]
        self.ativas = set()                        # colunas com elegibilidade diferente de zero
        self.pisos = pisos
        self.t_decai = 0                           # ultimo tick em que a elegibilidade decaiu

    def passo(self):
        """Depois de rede.passo(): STDP na entrada e elegibilidade na saida."""
        r = self.rede
        t = r.t
        w = r.w_ih
        wm = C.W_MAX << C.W_FRAC
        if r.spk_h:                                # pos disparou: potencia quem veio antes (limite suave)
            ult = r.ult_in
            pre = [(i, TRACO[t - ult[i]]) for i in r.recentes(r.rec_in) if t - ult[i] < RECENTE]
            for h in r.spk_h:
                for i, x in pre:
                    k = i * NH + h
                    w[k] += (C.A_PLUS * x * (wm - w[k])) >> C.STDP_SHIFT
        if r.n_in:                                 # pre disparou: deprime quem disparou antes
            ult = r.ult_h
            pos = [(h, TRACO[t - ult[h]]) for h in r.recentes(r.rec_h) if 0 < t - ult[h] < RECENTE]
            if pos:
                for k in range(r.n_in):
                    b = r.spk_in[k] * NH
                    for h, x in pos:
                        w[b + h] -= (C.A_MINUS * x * w[b + h]) >> C.STDP_SHIFT
        no, e = r.no, self.e
        if r.spk_o:                                # saida disparou: elegibilidade sobe nos ocultos recentes
            ult = r.ult_h
            pre = [h for h in r.recentes(r.rec_h) if h < NE]
            for o in r.spk_o:
                self.ativas.add(o)
                for h in pre:
                    dt = t - ult[h]
                    if dt < RECENTE:
                        e[h * no + o] += (C.A_PLUS * TRACO[dt]) >> 1
        if r.spk_h and self.ativas:                # oculto disparou depois da saida: elegibilidade desce
            ult = r.ult_o
            for o in self.ativas:
                dt = t - ult[o]
                if 0 < dt < RECENTE:
                    d = (C.A_MINUS * TRACO[dt]) >> 1
                    for h in r.spk_h:
                        if h < NE:
                            e[h * no + o] -= d
        if t - self.t_decai >= C.ELIG_PASSO:
            self.decair(t)

    def decair(self, t):
        """Aplica o decaimento acumulado desde t_decai (6.2), so nas colunas ativas."""
        n = (t - self.t_decai) // C.ELIG_PASSO
        if n <= 0:
            return
        self.t_decai += n * C.ELIG_PASSO
        no, e = self.rede.no, self.e
        mortas = []
        for o in self.ativas:
            vivo = False
            for h in range(NE):
                k = h * no + o
                x = e[k]
                if x:
                    if n > 20:
                        x = 0
                    else:
                        for _ in range(n):
                            x -= (x * C.ELIG_MUL) >> C.ELIG_SHIFT
                            if -8 < x < 8:
                                x = 0
                                break
                    e[k] = x
                    vivo = vivo or x != 0
            if not vivo:
                mortas.append(o)
        for o in mortas:
            self.ativas.discard(o)

    def recompensa(self, R, acao, eta):
        """R-STDP (6.2): dw = eta * R * e >> R_SHIFT, so na coluna da acao executada."""
        r = self.rede
        self.decair(r.t)
        no, e, w = r.no, self.e, r.w_ho
        piso = self.pisos[acao]
        for h in range(NE):
            k = h * no + acao
            if e[k]:
                x = w[k] + ((eta * R * e[k]) >> C.R_SHIFT)
                w[k] = C.W_MAX if x > C.W_MAX else (piso if x < piso else x)

    def homeostase(self):
        """A cada NORM_TICKS (6.5): normaliza a entrada de cada oculto e ajusta o limiar."""
        r = self.rede
        w = r.w_ih
        for h in range(NH):
            s = 0
            for i in range(NI):
                s += w[i * NH + h]
            if s:
                for i in range(NI):
                    k = i * NH + h
                    w[k] = w[k] * r.soma_h[h] // s
            c = r.cnt_h[h]
            if c * 100 > C.LIMIAR_ALTO * C.NORM_TICKS:
                r.th_h[h] = min(C.TH_MAX, r.th_h[h] + r.th_h[h] * C.LIMIAR_PASSO // 100)
            elif c * 100 < C.LIMIAR_BAIXO * C.NORM_TICKS:
                r.th_h[h] = max(C.TH_MIN, r.th_h[h] - r.th_h[h] * C.LIMIAR_PASSO // 100)
            r.cnt_h[h] = 0

    def esquecer(self):
        """Uma vez por dia (6.5): pesos plasticos andam 1% de volta ao valor de nascenca."""
        r = self.rede
        for w, w0 in ((r.w_ih, r.w_ih0), (r.w_ho, r.w_ho0)):
            for k in range(len(w)):
                d = w0[k] - w[k]
                w[k] += d * C.ESQUECE_PCT // 100 if d > 0 else -((-d) * C.ESQUECE_PCT // 100)
```
**Verificar:** `python3 -c "import companion.learn"` sem erro.

### B4. Criar `companion/testes/test_snn.py`
Testes de LIF, STDP e R-STDP exigidos pela fonte (seção 11, fase 0).

**Criar:** `companion/testes/test_snn.py`
```python
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
```
**Verificar:** próximo passo.

### B5. Rodar todos os unitários
```bash
python3 -m unittest discover -s companion/testes -t .
```
**Esperado:** `Ran 19 tests in 0.0Xs` e `OK`.

### B6. Commit da fase B
```bash
git add companion/encoder.py companion/snn.py companion/learn.py companion/testes/test_snn.py
git commit -m "feat(issue-2): fase B - rede LIF, STDP e R-STDP com testes (#2)"
```

---

## FASE C — Cérebro e simulador

### C1. Criar `companion/cerebro.py`
Orquestrador: `segundo()` sem Timer, rede só simula fora da trava, regra fixa de sono, eventos do dono.

**Criar:** `companion/cerebro.py`
```python
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
        self.log = []                              # (s, acao, top3, R) da ultima decisao, lido pelo sim
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
        R, acao = self.rec.evento(nome, agora_ms, d)
        self._aplicar(R, acao, nome, agora_ms)
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
```
**Verificar:** `python3 -c "from companion.cerebro import Cerebro; Cerebro(1)"` sem erro.

### C2. Criar `companion/sim/mundo.py`
Sensores falsos: monta o dicionário de sentidos.

**Criar:** `companion/sim/mundo.py`
```python
# Sensores falsos: monta o dicionario de sentidos que a placa montaria (sensors.py na fase 1).
class Mundo:
    def __init__(self, dia_semana=0):
        self.dia0 = dia_semana
        self.ultimo_toque = 0
        self.toques = []

    def tocar(self, seg):
        self.ultimo_toque = seg
        self.toques.append(seg)

    def sentidos(self, seg, comida=False):
        minuto = (seg // 60) % 1440
        dia = (self.dia0 + seg // 86400) % 7
        self.toques = [t for t in self.toques if seg - t < 60]
        recente = self.toques and self.toques[-1] == seg
        return {
            'minuto': minuto, 'fim_semana': dia >= 5, 'toque_reg': 0 if recente else None,
            'toque_tipo': 0 if recente else None, 'toques_60s': len(self.toques),
            'sem_toque': seg - self.ultimo_toque, 'mov': None, 'orient': 0, 'som_nivel': 10,
            'som_evento': None, 'noite': minuto < 6 * 60 or minuto >= 18 * 60, 'bateria': 80, 'carregando': 0,
            'outra': 0, 'outra_estado': 0, 'novidade': 0, 'comida': comida,
        }
```
**Verificar:** `python3 -c "import companion.sim.mundo"` sem erro.

### C3. Criar `companion/sim/dono.py`
Dono simulado configurável (presença, resposta a sons e pedidos, refeições, hora do carinho).

**Criar:** `companion/sim/dono.py`
```python
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
```
**Verificar:** `python3 -c "import companion.sim.dono"` sem erro.

### C4. Criar `companion/sim/rodar.py`
Laço do simulador (1 s por passo) e os cenários; `tornar_falante` para o teste do silêncio.

**Criar:** `companion/sim/rodar.py`
```python
# Simulador (secao 10): roda o cerebro em velocidade acelerada com um dono simulado.
# Uso: python3 -m companion.sim.rodar [silencio|habito|semana] [dias] [semente]
import sys
import time
import random
from companion import actions as A
from companion import config as C
from companion.cerebro import Cerebro
from companion.sim.dono import Dono
from companion.sim.mundo import Mundo

CENARIOS = {
    'semana': lambda: Dono(),
    'silencio': lambda: Dono(p_som=0.0, p_pedido=0.3),
    'barulho': lambda: Dono(p_som=1.0, p_pedido=0.3),
    'habito': lambda: Dono(p_som=0.0, p_pedido=0.0, presente=(), carinho_hora=19, p_toque_hora=0),
}


def tornar_falante(cer, fator):
    """Capi que nasce barulhenta (o problema de hoje): pesos das acoes com som multiplicados por fator."""
    no, w = cer.rede.no, cer.rede.w_ho
    for h in range(C.N_EXC):
        for o in A.COM_SOM:
            w[h * no + o] = min(C.W_MAX, w[h * no + o] * fator)


def simular(dono, dias, semente=1, inicio_h=6, falante=0):
    random.seed(semente)
    cer = Cerebro(semente)
    if falante:
        tornar_falante(cer, falante)
    mundo = Mundo()
    agenda = []                                # (segundo, evento)
    acoes = []                                 # (segundo, acao) de cada decisao nova
    comida_ate = -1
    fim = int(dias * 86400)
    s0 = inicio_h * 3600
    for seg in range(s0, s0 + fim):
        minuto = (seg // 60) % 1440
        for ev in dono.espontaneo(minuto, seg % 60):
            agenda.append((seg, ev))
        pend = [e for e in agenda if e[0] <= seg]
        if pend:
            agenda = [e for e in agenda if e[0] > seg]
            for _, ev in pend:
                if ev in ('carinho', 'toque', 'comida', 'estrela'):
                    mundo.tocar(seg)
                if ev == 'comida':
                    comida_ate = seg + 60
                cer.evento(ev, seg * 1000)
        s = mundo.sentidos(seg, seg < comida_ate)
        antes = len(cer.log)
        cer.segundo(s, seg * 1000)
        for item in cer.log[antes:]:
            if item[0] == 'A':
                acoes.append((item[1], item[2]))
                for atraso, ev in dono.reagir(item[2], minuto):
                    agenda.append((seg + atraso, ev))
        if len(cer.log) > 1000:
            del cer.log[:500]
    return cer, acoes


def sons_por_hora(acoes, de_s, ate_s, cer):
    n = sum(1 for s, a in acoes if de_s <= s < ate_s and A.CATALOGO[a][2])
    return n * 3600 / (ate_s - de_s)


if __name__ == '__main__':
    nome = sys.argv[1] if len(sys.argv) > 1 else 'semana'
    dias = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    sem = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    t0 = time.time()
    cer, acoes = simular(CENARIOS[nome](), dias, sem)
    dt = time.time() - t0
    print('%s: %d dias em %.1f s, %d ticks, %d decisoes' % (nome, dias, dt, cer.ticks_rodados, len(acoes)))
    s0 = 6 * 3600
    for dia in range(dias):
        a, b = s0 + dia * 86400, s0 + (dia + 1) * 86400
        print('dia %d: %.1f sons/h' % (dia + 1, sons_por_hora(acoes, a, b, cer)))
```
**Verificar:** próximo passo.

### C5. Rodar 1 dia do cenário semana
```bash
time python3 -m companion.sim.rodar semana 1
```
**Esperado:** `semana: 1 dias em ~15-20 s, ~65000 ticks, ~3300 decisoes` e `dia 1: <2 sons/h`.

### C6. Criar `companion/sim/aceite.py`
Os três testes de aceite (velocidade, silêncio, hábito); aceita `NOME=valor` para calibrar sem editar o config.

**Criar:** `companion/sim/aceite.py`
```python
# Testes de aceite da fase 0 (secao 11). Uso: python3 -m companion.sim.aceite [velocidade|silencio|habito|todos]
import sys
import time
from companion import actions as A
from companion.sim.rodar import simular, CENARIOS, sons_por_hora

INICIO = 6 * 3600                                  # o simulador comeca as 6h do dia 0
ALVO_HABITO = (A.INDICE['pedir_carinho'], A.INDICE['chamar_baixo'])
LIMITE_SEMANA_S = 180                              # calibrado: 1 min e inviavel em Python puro a 20 Hz


def velocidade():
    t0 = time.time()
    simular(CENARIOS['semana'](), 7)
    dt = time.time() - t0
    print('velocidade: 7 dias em %.0f s (limite %d s)' % (dt, LIMITE_SEMANA_S))
    return dt <= LIMITE_SEMANA_S


def silencio():
    cer, acoes = simular(CENARIOS['silencio'](), 3, falante=6)
    inicio = sons_por_hora(acoes, INICIO, INICIO + 6 * 3600, cer)
    dia3 = sons_por_hora(acoes, INICIO + 2 * 86400, INICIO + 3 * 86400, cer)
    print('silencio: %.1f sons/h nas 6 primeiras horas, %.1f sons/h no dia 3 (meta < 2)' % (inicio, dia3))
    return inicio > 2 and dia3 < 2


def habito(semente=1):
    cer, acoes = simular(CENARIOS['habito'](), 7, semente)
    bons = 0
    for dia in range(7):
        base = dia * 86400
        j0, j1 = base + 18 * 3600 + 50 * 60, base + 19 * 3600 + 10 * 60
        na_janela = sum(1 for s, a in acoes if j0 <= s < j1 and a in ALVO_HABITO)
        fora = sum(1 for s, a in acoes if base + 8 * 3600 <= s < base + 22 * 3600 and not j0 <= s < j1
                   and a in ALVO_HABITO)
        taxa_j, taxa_f = na_janela * 3.0, fora / (14 - 1 / 3)
        ok = na_janela >= 1 and taxa_j >= 2 * taxa_f
        bons += ok
        print('habito dia %d: %.1f/h na janela 18h50-19h10, %.1f/h fora %s' % (dia + 1, taxa_j, taxa_f,
                                                                               'ok' if ok else '-'))
    print('habito: %d de 7 dias (meta 5)' % bons)
    return bons >= 5


if __name__ == '__main__':
    from companion import config as C
    for kv in sys.argv[2:]:                         # ajuste de calibracao: NOME=valor
        k, v = kv.split('=')
        setattr(C, k, int(v))
    qual = sys.argv[1] if len(sys.argv) > 1 else 'todos'
    testes = {'velocidade': velocidade, 'silencio': silencio, 'habito': habito}
    nomes = list(testes) if qual == 'todos' else [qual]
    falhou = [n for n in nomes if not testes[n]()]
    print('FALHOU: ' + ', '.join(falhou) if falhou else 'ACEITE OK')
    sys.exit(1 if falhou else 0)
```
**Verificar:** próximos passos.

### C7. Criar `companion/sim/fumaca.py`
Fumaça de portabilidade para o MicroPython unix.

**Criar:** `companion/sim/fumaca.py`
```python
# Fumaca de portabilidade: roda 1 h simulada no MicroPython unix. Uso: micropython companion/sim/fumaca.py
import sys
sys.path.insert(0, '.')
from companion.sim import rodar
from companion.sim.dono import Dono

cer, acoes = rodar.simular(Dono(), 1 / 24)
print('micropython ok', cer.ticks_rodados, len(acoes))
```
**Verificar:** próximo passo.

### C8. Fumaça no MicroPython
```bash
micropython companion/sim/fumaca.py
```
**Esperado:** `micropython ok <~5000> <~250>`, sem exceção.

### C9. Aceite de velocidade
```bash
python3 -m companion.sim.aceite velocidade
```
**Esperado:** `velocidade: 7 dias em ~100 s (limite 180 s)` e `ACEITE OK`. Se passar de 180 s, rodar
`python3 -m cProfile -s tottime -m companion.sim.rodar semana 1 | head -25` e anotar o topo no `CALIBRACAO.md` antes
de mexer em qualquer coisa.

### C10. Aceite do silêncio
```bash
python3 -m companion.sim.aceite silencio
```
**Esperado:** `silencio: ~12.7 sons/h nas 6 primeiras horas, ~0.5 sons/h no dia 3 (meta < 2)` e `ACEITE OK`.

### C11. Sem float nos módulos do tick
```bash
grep -nE "float|[0-9]\.[0-9]" companion/snn.py companion/learn.py companion/encoder.py companion/drives.py \
     companion/reward.py companion/actions.py | grep -vE "#|\"\"\""
```
**Esperado:** nenhuma linha (os únicos números com ponto estão em comentários e docstrings).

### C12. Commit da fase C
```bash
git add companion/cerebro.py companion/sim/
git commit -m "feat(issue-2): fase C - cerebro, simulador e aceites de velocidade e silencio (#2)"
```

---

## FASE D — Calibração do hábito

O protótipo aprendeu a pedir carinho, mas em todas as horas. Os experimentos abaixo já rodaram no planejamento e
**não** passaram (não repetir):

| Ajuste | Dias ok (meta 5) |
|---|---|
| configuração base | 1 |
| `P_MAX_HORA=255` | 0 |
| `HH_DENS_INIB=40` | 1 |
| `P_MAX_HORA=255 HH_DENS_INIB=40` | 0 |
| `R_IGNORADO=-10` | 1 |
| `IH_FORTES=10` | 0 |
| `IH_FORTES=10 R_IGNORADO=-10` | 1 |
| `OCULTOS_TEMPO=16` (com índice de luz errado, já corrigido) | 1 |
| `OCULTOS_TEMPO=32` (idem) | 1 |
| `OCULTOS_TEMPO=16 ETA_FILHOTE=8` | 0 (aprende em todas as horas: dia 7 com 12/h na janela e 10/h fora) |
| `OCULTOS_TEMPO=16 ETA_FILHOTE=8 R_IGNORADO=-10` | 0 (para de pedir: ~0/h o dia todo) |

Cada task roda um experimento (~100 s). Parar no primeiro que imprimir `ACEITE OK`, aplicar o ajuste (D5) e pular
para a fase E.

### D1. Linha de base
```bash
python3 -m companion.sim.aceite habito | tee /tmp/habito-base.txt
```
**Esperado:** `habito: 1 de 7 dias (meta 5)` e `FALHOU: habito` (confirma o protótipo).

### D2. Ocultos de tempo + inibição forte (esparsidade)
```bash
python3 -m companion.sim.aceite habito OCULTOS_TEMPO=16 HH_DENS_INIB=40 ETA_FILHOTE=8
```
**Esperado:** se `ACEITE OK`, ir para D5 com esses valores.

### D3. D2 com hora mais forte
```bash
python3 -m companion.sim.aceite habito OCULTOS_TEMPO=16 HH_DENS_INIB=40 ETA_FILHOTE=8 P_MAX_HORA=255
```

### D4. Conferir que o ajuste vencedor não quebrou os outros aceites
Com os valores do experimento que passou (exemplo com D2):
```bash
python3 -m companion.sim.aceite silencio OCULTOS_TEMPO=16 HH_DENS_INIB=40 ETA_FILHOTE=8
python3 -m companion.sim.aceite habito OCULTOS_TEMPO=16 HH_DENS_INIB=40 ETA_FILHOTE=8 2>&1 | tail -2
python3 -m companion.sim.aceite habito OCULTOS_TEMPO=16 HH_DENS_INIB=40 ETA_FILHOTE=8 2>&1 | tail -2   # mesma semente
```
**Esperado:** `ACEITE OK` no silêncio e o mesmo `habito: N de 7` nas duas rodadas (determinismo, RNF04).

### D5. Gravar o ajuste no config
**Editar:** `companion/config.py`: trocar o valor de cada constante do experimento vencedor e acrescentar
`(calibrado, ver CALIBRACAO.md)` ao comentário dela. Exemplo para D2:
```python
OCULTOS_TEMPO = 16         # calibrado (ver CALIBRACAO.md): ocultos 0..15 so ouvem hora, dia e luz
HH_DENS_INIB = 40          # calibrado (ver CALIBRACAO.md): % das ligacoes que saem dos inibitorios
ETA_FILHOTE = 8            # 6.2 primeiros 7 dias (calibrado, ver CALIBRACAO.md; fonte: 4)
```
**Verificar:** `python3 -m companion.sim.aceite todos` → `ACEITE OK`; `python3 -m unittest discover -s companion/testes -t .` → `OK`.

### D6. Regra de parada (se D2 e D3 falharem)
Não inventar outro ajuste. Registrar os números de D1 a D3 e da tabela acima no `CALIBRACAO.md` (seção "Hábito — não resolvido"),
fazer a fase E sem o aceite do hábito, comentar na issue #2 com a tabela e voltar para `/sdd-refine 2`. Opções a
levar para a conversa: (a) contar só os dias 3 a 7, já que nos dias 1 e 2 ainda não houve recompensa suficiente;
(b) o dono do teste atender das 18h50 às 19h20, para dar mais recompensas por dia; (c) uma via plástica direta
"hora → saída" ao lado da rede.

### D7. Commit da fase D
```bash
git add companion/config.py
git commit -m "feat(issue-2): fase D - calibracao do habito (#2)"
```
(Se nada mudou no config por causa do D6, pular este commit.)

---

## FASE E — Documentação e aceite final

### E1. Criar `CALIBRACAO.md`
**Criar:** `CALIBRACAO.md` (raiz)
```markdown
# Calibração do cérebro SNN

Toda constante de `companion/config.py` que mudou em relação à fonte (`sdd/ISSUE_2/00-fonte.md`), com o motivo e o
número medido. Antes de gravar na placa, rodar `python3 -m companion.sim.aceite todos`.

## Fase 0 (issue #2, 2026-11)

| Constante | Fonte | Agora | Motivo (medido no simulador) |
|---|---|---|---|
| STDP entrada→oculta | aditivo, A+=2, A-=3, pesos 0..255 | limite suave, pesos x16 (`W_FRAC=4`, `STDP_SHIFT=14`) | Passos inteiros 0/1/2: a depressão venceu, a normalização levou o peso para entradas mudas e em 10 min os ocultos calaram (limiar a 49) |
| Normalização | `SUM_TARGET` fixo | soma inicial de cada oculto | Entrada esparsa tem soma inicial diferente por neurônio |
| Pesos iniciais entrada→oculta | densos 20..80 | 25 % em 20..80, resto 0..5 (`IH_FORTES`, `W_IH_FRACO`) | Uniformes, nenhum oculto ficava seletivo |
| Corrente de saída | `soma(w) >> 2` | `soma(w) * 6` (`I_OUT_MUL`) | Com `>> 2` a contagem máxima na janela era 0 a 1 |
| Empate na decisão | `ficar_quieta` | maior potencial no fim da janela | Saídas sincronizadas empatavam: 100 % `ficar_quieta` |
| Limiar adaptativo | sem limite, todas as camadas | só ocultos, 500..4000 (`TH_MIN`, `TH_MAX`) | Na saída desfaria a punição; sem limite colapsava |
| Elegibilidade | decai 1/64 por tick | x25/32 a cada 16 ticks, só colunas ativas | Mesmo valor, custo de CPU muito menor |
| Habituação | execuções na última hora | contador x10, perde 1/6 a cada 10 min | Inteiro, sem lista |
| Meta de velocidade | 7 dias < 1 min | 7 dias <= 180 s | ~100 s medidos em CPython 3.14 no Mac a 20 Hz |
| Teste do silêncio | Capi normal | Capi falante (som x6) | A normal já nasce com < 1 som/h |
| Teste do hábito | "vencem na janela" | taxa na janela >= 2x a taxa fora, 5 de 7 dias | Do jeito da fonte passa por acaso |

## Erros da fonte

- Seção 2: ~80 entradas; a tabela da seção 3 soma 100.
- Seção 5: 21 ações com som; a tabela tem 20.
- Seção 6.2: R-STDP em saída→saída; a seção 2 diz que é fixa.
- Seção 6.3: "shh" com dois dedos; o CST816D só lê um toque (gesto decidido na fase 2).

## Hábito

(preencher com o resultado da fase D: experimento vencedor e números, ou a tabela de D1 a D3 se nenhum passou)
```
**Verificar:** depois de criar, substituir a última linha pelo resultado real da fase D (copiar as linhas
`habito dia N` e `habito: N de 7` do experimento que passou, ou de D1 a D3).

### E2. Atualizar o índice do `CODEMAP.md`
**Editar:** `CODEMAP.md`, na tabela "Índice rápido", depois da linha de `portal.py`, acrescentar:
```markdown
| `companion/` | ~1230 | Cérebro SNN do modo Companion (issue #2, fase 0 — ainda não ligado ao `main.py`): `config`, `actions` (catálogo das 100 ações), `encoder`, `snn`, `learn`, `drives`, `reward`, `cerebro`; `sim/` simulador e aceites; `testes/` unittest | — (só `array` e `random`) |
| `CALIBRACAO.md` | — | Constantes do cérebro que mudaram em relação à fonte e por quê | — |
```
E no fim do arquivo, nova seção:
```markdown
## Cérebro SNN (`companion/`)

- **Entrada:** `Cerebro.segundo(sentidos, agora_ms)` uma vez por segundo, de dentro do laço (sem `Timer`); devolve o
  índice da ação em `actions.CATALOGO`. Reações do dono entram por `Cerebro.evento(nome, agora_ms)`.
- **Testes:** `python3 -m unittest discover -s companion/testes -t .` e `python3 -m companion.sim.aceite todos`.
- **Fonte das regras:** `sdd/ISSUE_2/00-fonte.md`; divergências em `CALIBRACAO.md`.
```
**Verificar:** `grep -n "companion/" CODEMAP.md` mostra as duas inserções.

### E3. Aceite final
```bash
python3 -m unittest discover -s companion/testes -t .
python3 -m companion.sim.aceite todos
micropython companion/sim/fumaca.py
```
**Esperado:** `OK`; `ACEITE OK` (ou, pelo D6, `FALHOU: habito` registrado); `micropython ok`.

### E4. Commit da fase E
```bash
git add CALIBRACAO.md CODEMAP.md
git commit -m "docs(issue-2): fase E - CALIBRACAO.md e CODEMAP (#2)"
```

### E5. Comentar o resultado na issue
```bash
gh issue comment 2 --body-file /tmp/habito-base.txt
```
Antes, acrescentar ao arquivo as saídas de E3. **Esperado:** link do comentário.
