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

# Solidao (issue #3): afeto abaixo do limiar empurra pedir_carinho; e o que faz a Capi explorar ate achar a hora
SOLIDAO = (D_AFETO, 200, 'pedir_carinho', 1000)

# Via hora -> saida (issue #3, companion/relogio.py)
RELOGIO_BINS = 72          # celulas de 20 min
RELOGIO_K_POS = 24         # dw = eta * R * K, premio
RELOGIO_K = 8              # castigo
RELOGIO_MAX = 1500         # |peso| maximo (corrente por tick)
MARCA_K = 1                # castigo atrasado nos ocultos marcados: dw = eta * R * MARCA_K >> 2

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
