# main.py - Capigoshi (bichinho virtual) para Waveshare ESP32-S3-Touch-LCD-1.83 em MicroPython
#
# Modos (menu puxado do topo):
#   Cuidar  (pet)       voce cuida: comer, brincar, banho, remedio.
#   Olhar   (companion) o bichinho vive sozinho seguindo a rotina do dia.
#   Passear (explore)   side-scroller: segure um lado da tela para andar, toque curto pula.
# Hora Real segue o relogio; Simulada comeca da hora real e passa o dia em 30/15/10 min.
# Sacudir a placa ou gritar perto: acordado ele adora, dormindo leva um susto.
# No Cuidar e no Olhar ele "vive" (vida.py): 21 movimentos, falas, reacoes a toque, colo,
# sacudida e barulho, e chora se ficar 10 min sem atencao.
# Direcao visual: design_handoff_capigoshi_1c (desenho.py).

import time, math, json, random, gc
from machine import I2C, Pin
import hw
import desenho as d
import vida as V
from hw import W, H

# ------------------------------------------------------------ ajustes
TICK_PET_SEG = 60           # no Pet, os status mudam a cada 1 minuto (de hora do jogo)
LIMIAR_GRITO = 12000        # barulho minimo (maior = menos sensivel); tambem se adapta ao ambiente
PISO_MULT = 8               # barulho = volume passa 8x o ruido de fundo
BARULHO_SEGUIDOS = 3        # leituras seguidas acima do limite (ignora estalo, batida e clique)
LIMIAR_SACUDIDA = 0.9       # sensibilidade a sacudida, em g
MOSTRAR_VOLUME = False      # True imprime o volume do microfone (para calibrar)
PINO_BOTAO = 0              # botao fisico (BOOT): fecha o menu e volta do Passear
DORME, ACORDA = 22, 6       # o bichinho dorme das 22:00 as 6:00 (em todos os modos)
ACORDADO_MS = 60000         # grito ou sacudida enquanto dorme: acorda por 1 minuto
V.ACORDA_MS = ACORDADO_MS
BATERIA_FRACA = 10          # % da bateria em que a tela pisca o aviso

# Ritmo do Pet, por minuto de jogo (de 100 a 30 de fome leva umas 4 horas)
FOME_MIN, ALEGRIA_MIN, ENERGIA_MIN = 0.25, 0.2, 0.15
FOME_DORMINDO, ENERGIA_DORMINDO = 0.1, 1.2
CHANCE_COCO, CHANCE_DOENCA = 0.012, 0.015

# ------------------------------------------------------------ hardware
i2c = I2C(0, scl=Pin(14), sda=Pin(15), freq=400000)
tela = hw.Tela()
d.usar(tela.fb)
toque = hw.Toque(i2c)
mov = hw.Movimento(i2c)
relogio = hw.Relogio(i2c)
som = hw.Som(i2c)
bateria = hw.Bateria(i2c)
try:
    botao = Pin(PINO_BOTAO, Pin.IN, Pin.PULL_UP)
except Exception:
    botao = None
gc.collect()


# ------------------------------------------------------------ arquivos
def carregar(nome, padrao):
    try:
        with open(nome) as f:
            padrao.update(json.load(f))
    except Exception:
        pass
    return padrao


def salvar(nome, dados):
    try:
        with open(nome, 'w') as f:
            json.dump(dados, f)
    except Exception as e:
        print('Erro ao salvar', nome, e)


cfg = carregar('config.json', {'modo': 'pet', 'som': True, 'personagem': 'capi',
                               'hora': 'real', 'vel': 2, 'casa': 'pet'})
if cfg['personagem'] not in d.ELENCO:
    cfg['personagem'] = 'capi'
if cfg['modo'] not in ('pet', 'companion', 'explore'):
    cfg['modo'] = 'pet'
if cfg['vel'] not in (1, 2, 3):
    cfg['vel'] = 2
som.ligado = cfg['som']

PET_PADRAO = {'fome': 80, 'alegria': 80, 'energia': 80, 'saude': 100, 'cocos': 0,
              'doente': False, 'dormindo': False, 'cochilo': False, 'epoch': 0,
              'idade_min': 0.0, 'vida_adulto': 15, 'morto': False}

# Ciclo de vida, em dias do jogo (com hora Real sao dias de verdade)
DIA_MIN = 1440
DIAS_OVO, DIAS_FILHOTE, DIAS_IDOSO = 1, 3, 5
VIDA_TOTAL = (23, 40)       # dias de vida, sorteados quando o ovo aparece (filhote + adulto + idoso)
VIDA_ADULTO = (VIDA_TOTAL[0] - DIAS_FILHOTE - DIAS_IDOSO, VIDA_TOTAL[1] - DIAS_FILHOTE - DIAS_IDOSO)
OVO_MINUTOS = 10            # o ovo choca em 10 minutos de verdade (com hora Real ou Simulada)
AQUECER_SEG = 20            # cada toque no ovo adianta 20 s
FATOR_OVO = DIAS_OVO * DIA_MIN / OVO_MINUTOS
AQUECER_MIN = AQUECER_SEG / 60 * FATOR_OVO


def arquivo_pet(id):
    return 'capi.json'      # um bichinho por vez: trocar de personagem comeca do zero


pet = carregar(arquivo_pet(cfg['personagem']), dict(PET_PADRAO))
vt = 0                      # relogio continuo da vida (ms); nao da a volta como ticks_ms
L = V.nova(cfg['personagem'], vt)
vida_out = None             # pose do quadro devolvida por V.passo
toque_vida = None           # [x, y, no_corpo, arrastou] do toque em andamento


def lim(v):
    return 0 if v < 0 else (100 if v > 100 else v)


def nome():
    return d.NOMES[cfg['personagem']]


# ------------------------------------------------------------ Wi-Fi opcional (acerta a hora)
def sincronizar_hora():
    try:
        with open('wifi.json') as f:
            w = json.load(f)
    except Exception:
        return False
    try:
        import network, ntptime
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        sta.connect(w['ssid'], w['senha'])
        for _ in range(40):
            if sta.isconnected():
                break
            time.sleep_ms(250)
        ok = sta.isconnected()
        if ok:
            ntptime.settime()
            t = time.localtime(time.time() + w.get('fuso', -3) * 3600)
            relogio.acertar(t[0], t[1], t[2], t[3], t[4], t[5])
        sta.active(False)
        return ok
    except Exception as e:
        print('Nao consegui acertar a hora pela internet:', e)
        return False


# ------------------------------------------------------------ hora real e simulada
def hora_real():
    t = relogio.ler()
    return (t[3] + t[4] / 60 + t[5] / 3600) if t else 12.0


sim_h0, sim_t0 = 12.0, 0


def iniciar_sim(h):
    global sim_h0, sim_t0
    sim_h0, sim_t0 = h, time.ticks_ms()


def hora_atual():
    global sim_h0, sim_t0
    if cfg['hora'] != 'sim':
        return hora_real()
    seg = time.ticks_diff(time.ticks_ms(), sim_t0) / 1000
    h = (sim_h0 + seg * 24 / (d.VEL_MIN[cfg['vel']] * 60)) % 24
    if seg > 3600:                       # reancora: ticks_ms da volta em alguns dias
        sim_h0, sim_t0 = h, time.ticks_ms()
    return h


def fator_tempo():
    """Quantas vezes o tempo do jogo corre mais rapido que o real."""
    return 1440 / d.VEL_MIN[cfg['vel']] if cfg['hora'] == 'sim' else 1


def relogio_txt(h):
    return '%02d:%02d' % (int(h), int(h * 60) % 60)


# ------------------------------------------------------------ estado
anim, anim_ini = '', 0
tocando = False
toque_ini = (0, 0, 0)
toque_ult = (0, 0)
ultimo_toque = 0
ultima_reacao = 0
ultimo_urgente = 0
ultimo_save = time.ticks_ms()
acc_pet = 0
grito_seguidos = 0
botao_antes = 1
piso_mic = 2000.0           # ruido de fundo do microfone (se adapta)
toque_visto = 0             # ultimo quadro em que o dedo estava na tela
bat_pct, bat_carregando, bat_lida, bat_avisou = None, False, -60000, False

# menu
menu_borda, menu_alvo, menu_arrasta = 0.0, 0, False
menu_pend = None                       # personagem escolhido nas setas, ainda sem confirmar
menu_conf = None                       # 'trocar' ou 'zerar': pergunta 'comeca do zero'

# baloes: um por personagem ('p' principal, 'v' vizinho)
PRIOR = {'urgente': 5, 'grito': 4, 'fala': 3, 'chamado': 2, 'pensa': 1}
baloes = {}
sis_txt, sis_ate = '', 0

# companion
capi_x, alvo_x = 110.0, 110.0
capi_modo, proximo_modo_t = 'anda', 0
visita, visita_ini, visita_x, visita_falou = '', 0, 0, False
proxima_visita = time.ticks_add(time.ticks_ms(), 20000)
viz_x = 172
viz_turno = -1              # ultima fala da conversa que ja tocou a voz

# passear
ex_off, ex_moedas, ex_pulo, ex_passo = 0, 0, -10000, 0
ex_auto = 0                 # 1 = anda sozinho para a direita, -1 para a esquerda
ex_toques = []              # toques curtos recentes (tempo, lado)
TOQUE_JANELA = 350          # ms entre toques para contar como sequencia
ex_mundo = [180 + n * 70 + (n % 3) * 22 for n in range(12)]


def iniciar_anim(n):
    global anim, anim_ini
    anim, anim_ini = n, time.ticks_ms()


def balao(quem, tipo, conteudo, ms=None):
    agora = time.ticks_ms()
    if ms is None:
        ms = max(2500, 400 + 80 * len(conteudo))
    atual = baloes.get(quem)
    if atual and time.ticks_diff(atual[2], agora) > 0 and PRIOR[atual[0]] > PRIOR[tipo]:
        return
    baloes[quem] = [tipo, conteudo, time.ticks_add(agora, ms)]


def falar(texto):
    if vida_ativa():
        V.falar(L, vt, texto)
    else:
        balao('p', 'fala', texto)
        tocar_voz()


def tocar_voz():
    """Voz de 'minion' quando ele fala: sorteia uma das amostras sons/fala1..4.raw."""
    som.tocar('fala%d' % random.randint(1, 4))


def vida_ativa():
    """O bichinho 'vive' (movimentos sorteados e reacoes) no Cuidar e no passeio/sono do Olhar."""
    if cfg['modo'] == 'explore' or anim or fase_vida() in ('ovo', 'estrela'):
        return False
    if cfg['modo'] == 'companion':
        return visita not in d.ELENCO and atividade_companion() in ('passeando', 'dormindo')
    return True


def sono_vida():
    if cfg['modo'] == 'pet':
        return pet['dormindo']
    return atividade_companion() == 'dormindo'


def sistema(texto, ms=2500):
    global sis_txt, sis_ate
    sis_txt, sis_ate = texto, time.ticks_add(time.ticks_ms(), ms)


def hora_de_dormir(h):
    return h >= DORME or h < ACORDA


def dormindo():
    if fase_vida() in ('ovo', 'estrela'):
        return False
    if vt < L['awakeUntil']:
        return False                          # acordou com grito/sacudida/toque: fica 1 min de pe
    if cfg['modo'] == 'companion':
        return atividade_companion() == 'dormindo'
    if cfg['modo'] == 'pet':
        return pet['dormindo']
    return hora_de_dormir(hora_atual())


# ------------------------------------------------------------ modo PET
def noite_pet():
    return hora_de_dormir(hora_atual())


def tick_pet(offline=False):
    if fase_vida() in ('ovo', 'estrela'):
        return
    noite = noite_pet()
    if pet['dormindo']:
        pet['fome'] -= FOME_DORMINDO
        pet['energia'] += ENERGIA_DORMINDO
        acordar = (not noite and not pet['cochilo']) or (pet['cochilo'] and pet['energia'] >= 60)
        if acordar and not offline:
            pet['dormindo'] = pet['cochilo'] = False
            falar('Bom dia!')
            som.tocar('feliz')
    else:
        pet['fome'] -= FOME_MIN
        pet['alegria'] -= ALEGRIA_MIN
        pet['energia'] -= ENERGIA_MIN
        if pet['cocos'] < 3 and random.random() < CHANCE_COCO:
            pet['cocos'] += 1
        if noite or pet['energia'] < 8:
            pet['dormindo'] = True
            pet['cochilo'] = not noite
            if not offline:
                falar('Boa noite!' if noite else 'Cochilo...')
                som.tocar('bocejo')
    if not pet['doente'] and (pet['cocos'] >= 2 or pet['fome'] < 15) and random.random() < CHANCE_DOENCA:
        pet['doente'] = True
        if not offline:
            falar('To dodoi...')
            som.tocar('triste')
    perda = pet['cocos'] * 0.2 + (0.6 if pet['fome'] < 15 else 0) + (0.6 if pet['doente'] else 0)
    pet['saude'] += -perda if perda else 0.3
    if offline:
        pet['saude'] = max(pet['saude'], 15)     # nada de ruim acontece com a placa desligada
    for k in ('fome', 'alegria', 'energia', 'saude'):
        pet[k] = lim(pet[k])


def acao_pet(i):
    f = fase_vida()
    if f == 'estrela':
        return
    if f == 'ovo':
        falar('Sou um ovo!|Me esquenta')
        return
    if dormindo():
        falar('Shhh... zzz')
        return
    som.tocar('clique')
    if i == 0:
        if pet['fome'] > 92:
            falar('To cheio!')
        else:
            pet['fome'] = lim(pet['fome'] + 25)
            iniciar_anim('comer')
            som.tocar('comer')
    elif i == 1:
        if pet['energia'] < 15:
            falar('Cansado...')
        else:
            pet['alegria'] = lim(pet['alegria'] + 20)
            pet['energia'] = lim(pet['energia'] - 8)
            iniciar_anim('pular')
            som.tocar('feliz')
    elif i == 2:
        pet['cocos'] = 0
        pet['saude'] = lim(pet['saude'] + 3)
        iniciar_anim('banho')
        falar('Que banho bom!')
        som.tocar('banho')
    elif i == 3:
        if pet['doente']:
            pet['doente'] = False
            pet['saude'] = lim(pet['saude'] + 35)
            iniciar_anim('remedio')
            falar('Melhorei!')
            som.tocar('remedio')
        else:
            falar('Nao to doente!')
    salvar(arquivo_pet(cfg['personagem']), pet)


def chamado_pet():
    """O que o bichinho esta pedindo agora: (tipo, icone) ou None."""
    if cfg['modo'] != 'pet' or dormindo() or fase_vida() in ('ovo', 'estrela'):
        return None
    if pet['doente'] or pet['saude'] < 25:
        return ('urgente', 'remedio')
    if pet['fome'] < 30:
        return ('chamado', 'capim')
    if pet['cocos'] >= 2:
        return ('chamado', 'banho')
    if pet['alegria'] < 30:
        return ('chamado', 'bola')
    if pet['energia'] < 20:
        return ('pensa', 'zzz')
    return None


def recuperar_tempo_desligado():
    agora = relogio.epoch()
    if agora and pet['epoch'] and agora > pet['epoch']:
        total = (agora - pet['epoch']) // 60
        if fase_vida() == 'ovo':               # ovo continua chocando no ritmo de 10 min
            pet['idade_min'] = min(pet['idade_min'] + total * FATOR_OVO, DIAS_OVO * DIA_MIN)
        elif not pet['morto']:                 # envelhece desligado, mas nunca se despede desligado
            pet['idade_min'] = min(pet['idade_min'] + total, fim_da_vida() - 1)
        minutos = min(total, 8 * 60)
        for _ in range(minutos):
            tick_pet(offline=True)
        if minutos > 10:
            falar('Senti saudade!')
        pet['dormindo'] = noite_pet()
        pet['cochilo'] = False


# ------------------------------------------------------------ ciclo de vida
def fim_da_vida():
    return (DIAS_OVO + DIAS_FILHOTE + pet['vida_adulto'] + DIAS_IDOSO) * DIA_MIN


def fase_vida():
    if pet['morto']:
        return 'estrela'
    dias = pet['idade_min'] / DIA_MIN
    if dias < DIAS_OVO:
        return 'ovo'
    if dias < DIAS_OVO + DIAS_FILHOTE:
        return 'filhote'
    if dias < DIAS_OVO + DIAS_FILHOTE + pet['vida_adulto']:
        return 'adulto'
    return 'idoso'


def legenda_vida():
    f = fase_vida()
    if f == 'ovo':
        return '%s, ovo' % nome()
    if f == 'estrela':
        return '%s, estrela' % nome()
    dias = int(pet['idade_min'] // DIA_MIN)
    return '%s, %d dia%s' % (nome(), dias, '' if dias == 1 else 's')


def novo_ovo(id=None):
    """Comeca do zero: ovo novo (do mesmo bichinho ou de outro)."""
    if id:
        cfg['personagem'] = id
    pet.clear()
    pet.update(PET_PADRAO)
    L.clear()
    L.update(V.nova(cfg['personagem'], vt))
    pet['vida_adulto'] = random.randint(VIDA_ADULTO[0], VIDA_ADULTO[1])
    pet['epoch'] = relogio.epoch()
    baloes.clear()
    salvar(arquivo_pet(cfg['personagem']), pet)
    salvar('config.json', cfg)


def envelhecer(dt):
    antes = fase_vida()
    if antes == 'estrela':
        if not hora_de_dormir(hora_atual()):         # de manha aparece um ovo novo
            novo_ovo()
            sistema('Um ovo novo!')
            som.tocar('feliz')
        return
    pet['idade_min'] += dt / 60000 * (FATOR_OVO if antes == 'ovo' else fator_tempo())
    if antes == 'idoso' and pet['idade_min'] >= fim_da_vida() and hora_de_dormir(hora_atual()):
        pet['morto'] = True                          # despedida a noite: vira estrela no ceu
        cfg['estrelas'] = (cfg.get('estrelas') or [])[-11:] + [nome()]
        salvar(arquivo_pet(cfg['personagem']), pet)
        salvar('config.json', cfg)
        som.tocar('triste')
        return
    agora = fase_vida()
    if agora != antes:
        if agora == 'filhote':
            L.update(V.nova(cfg['personagem'], vt))
            V.tocar(L, vt, 'comemorar', say='oi! nasci!')
            som.tocar('feliz')
        elif agora == 'adulto':
            falar('Cresci!')
            som.tocar('feliz')
        elif agora == 'idoso':
            falar('To velhinho!')
        salvar(arquivo_pet(cfg['personagem']), pet)


# ------------------------------------------------------------ modo COMPANION
# Rotina do Olhar. As atividades "quietas" (espreguicar, comer, nadar, ver o por do sol) duram
# no maximo 30 min; no resto do dia ele passeia, que e quando vive, se mexe e fala.
ROTINA = ((0, 'dormindo'), (ACORDA, 'espreguicando'), (6.5, 'passeando'),
          (7, 'comendo'), (7.5, 'passeando'),
          (12, 'comendo'), (12.5, 'passeando'),
          (13, 'banho'), (13.5, 'passeando'),
          (17.5, 'por do sol'), (18, 'passeando'),      # o sol se poe as 18h
          (DORME, 'dormindo'))
AMIGOS_DIA = ('passarinho', 'tartaruga', 'borboleta', 'sapo', 'vizinho', 'vizinho')
FALAS = {'passarinho': 'Piu pra voce!', 'tartaruga': 'Oi, Tata!',
         'borboleta': 'Que linda!', 'sapo': 'Oi, Sapinho!'}
PENSAMENTOS = ('capim', 'bola', 'nota', 'coracao', 'peixe')
VIZ_TURNO = 2600                       # conversa: um balao por vez


def atividade_companion():
    h = hora_atual()
    atual = ROTINA[0][1]
    for inicio, n in ROTINA:
        if h >= inicio:
            atual = n
    return atual


def conversa():
    """Falas da visita de um vizinho, alternando visitante (v) e principal (p)."""
    return (('v', 'oi, %s!' % nome()), ('p', 'oi! tudo|bem?'),
            ('v', 'vamos|brincar?'), ('p', 'oba!'))


def atualizar_companion(dt, agora):
    global capi_x, alvo_x, visita, visita_ini, visita_x, proxima_visita, visita_falou
    global capi_modo, proximo_modo_t, viz_x
    if fase_vida() in ('ovo', 'estrela'):
        capi_x = alvo_x = 110.0
        return
    ativ = atividade_companion()
    if vida_ativa():
        capi_x = alvo_x = L['x']
        capi_modo = 'anda'
        atualizar_visitas(dt, agora, ativ)
        return
    L['x'] = capi_x
    na_agua = ativ == 'banho' and abs(capi_x - 200) < 32
    em_conversa = visita in d.ELENCO

    if em_conversa:
        alvo_x = capi_x                       # para para conversar
    elif ativ == 'banho':
        if not na_agua:
            alvo_x = 200
            if capi_modo == 'para':
                capi_modo = 'anda'
    elif ativ == 'comendo':
        alvo_x = 60
        if capi_modo == 'para' and abs(capi_x - 60) > 8:
            capi_modo = 'anda'
    elif ativ in ('dormindo', 'por do sol', 'espreguicando'):
        alvo_x = 110
        if capi_modo == 'para' and abs(capi_x - 110) > 8:
            capi_modo = 'anda'
    elif ativ == 'passeando':
        chegou = abs(capi_x - alvo_x) < 3
        if chegou or time.ticks_diff(agora, proximo_modo_t) > 0:
            r = random.random()
            if r < 0.22:                        # para e olha ao redor (as vezes pensando em algo)
                capi_modo = 'para'
                dur = random.randint(1500, 3500)
                proximo_modo_t = time.ticks_add(agora, dur)
                if random.random() < 0.5:
                    balao('p', 'pensa', random.choice(PENSAMENTOS), dur)
            elif r < 0.48:                      # corre!
                capi_modo = 'corre'
                alvo_x = random.randint(44, 200)
                proximo_modo_t = time.ticks_add(agora, random.randint(600, 1800))
            else:                               # caminha devagar
                capi_modo = 'anda'
                alvo_x = random.randint(44, 200)
                proximo_modo_t = time.ticks_add(agora, random.randint(2000, 5500))

    if na_agua:
        if abs(capi_x - alvo_x) < 3 and time.ticks_diff(agora, proximo_modo_t) > 0:
            alvo_x = random.randint(176, 200)   # nada de la pra ca no lago, sem sair da tela
            proximo_modo_t = time.ticks_add(agora, random.randint(1800, 4200))
        passo = dt * 0.014
    elif capi_modo == 'corre':
        passo = dt * 0.060
    elif capi_modo == 'para':
        passo = 0
    else:
        passo = dt * 0.028
    if fase_vida() == 'idoso':
        passo *= 0.5
    if abs(alvo_x - capi_x) > passo:
        capi_x += passo if alvo_x > capi_x else -passo
    atualizar_visitas(dt, agora, ativ)


def atualizar_visitas(dt, agora, ativ):
    global visita, visita_ini, visita_x, proxima_visita, visita_falou, capi_modo, viz_x, viz_turno
    if not visita and time.ticks_diff(agora, proxima_visita) > 0:
        if d.e_noite(hora_atual()):
            visita = 'vagalumes'
        else:
            visita = random.choice(AMIGOS_DIA)
            if visita == 'vizinho':
                if ativ != 'passeando':
                    visita = 'borboleta'
                else:
                    outros = [c for c in d.ELENCO if c != cfg['personagem']]
                    visita = random.choice(outros)
                    viz_x = 52 if capi_x > 110 else 172
                    capi_modo = 'para'
        visita_ini = agora
        visita_falou = False
        viz_turno = -1
        visita_x = 250 if visita == 'tartaruga' else -10
    if visita:
        dur = time.ticks_diff(agora, visita_ini)
        if visita in d.ELENCO:
            i = dur // VIZ_TURNO
            if i != viz_turno and i < len(conversa()):
                viz_turno = i
                tocar_voz()                       # cada fala da conversa tem voz, dos dois lados
            fim = len(conversa()) * VIZ_TURNO + 800
            if dur > fim or dormindo():
                visita = ''
                capi_modo = 'anda'
                proxima_visita = time.ticks_add(agora, random.randint(25000, 60000))
            return
        if visita == 'tartaruga':
            visita_x -= dt * 0.02
        pronta = {'tartaruga': abs(visita_x - capi_x) < 35, 'borboleta': dur > 1500,
                  'sapo': dur > 800, 'passarinho': dur > 3000}.get(visita, False)
        if pronta and not visita_falou and not dormindo():
            visita_falou = True
            falar(FALAS[visita])
            som.tocar('piu' if visita == 'passarinho' else 'feliz')
        if dur > 14000 or visita_x < -30:
            visita = ''
            proxima_visita = time.ticks_add(agora, random.randint(25000, 60000))


def desenhar_visita(agora, cx, topo, ph, na_agua):
    dur = time.ticks_diff(agora, visita_ini)
    if visita == 'passarinho':
        if dur < 3000:
            f = dur / 3000
            x, y = -10 + (cx + 10) * f, 70 + (topo - 76) * f + math.sin(dur / 150) * 5
        elif dur < 10000:
            x, y = cx, topo - 6
        else:
            f = (dur - 10000) / 4000
            x, y = cx + 150 * f, topo - 6 - 90 * f
        d.passarinho(d.ri(x), d.ri(y), agora)
    elif visita == 'tartaruga':
        d.tartaruga(d.ri(visita_x), 208, agora)
    elif visita == 'borboleta':
        d.borboleta(d.ri(cx + 45 * math.sin(dur / 900)), d.ri(topo + 8 + 15 * math.sin(dur / 450)), agora)
    elif visita == 'sapo' and not na_agua:
        d.sapo(196, 208, agora)
    elif visita == 'vagalumes':
        d.vagalumes(agora)


# ------------------------------------------------------------ reacoes: grito e sacudida
def verificar_sensores(agora):
    global ultima_reacao, piso_mic, grito_seguidos
    g = mov.forca_g()
    vol = som.volume_mic()
    if MOSTRAR_VOLUME:
        print('volume do microfone:', vol, 'ruido de fundo:', int(piso_mic))
    sacudiu = abs(g - 1.0) > LIMIAR_SACUDIDA
    alto = vol > max(PISO_MULT * piso_mic, LIMIAR_GRITO)
    if not alto:
        piso_mic = piso_mic * 0.98 + vol * 0.02          # o piso acompanha o ambiente
    grito_seguidos = grito_seguidos + 1 if alto else 0
    barulhou = grito_seguidos >= BARULHO_SEGUIDOS
    if barulhou:
        grito_seguidos = 0
    if not (sacudiu or barulhou) or fase_vida() in ('ovo', 'estrela'):
        return
    if vida_ativa():
        if sacudiu:
            primeiro = vt >= L['shakeUntil']
            era_sono = L['asleep']
            V.sacudir(L, vt, min(1.5, 0.6 + abs(g - 1.0) / 2), 500)
            if primeiro:
                som.tocar('susto' if era_sono else 'feliz')
                pet['alegria'] = lim(pet['alegria'] + (-5 if era_sono else 10))
        else:
            if vt - L['lastNoise'] >= 1500 and vt >= L['shakeUntil']:
                som.tocar('susto')
            V.barulho(L, vt)
        return
    if time.ticks_diff(agora, ultima_reacao) < 3000:
        return
    ultima_reacao = agora
    if dormindo():
        iniciar_anim('susto')
        falar('Que susto!')
        som.tocar('susto')
        pet['alegria'] = lim(pet['alegria'] - 5)
        V.acordar(L, vt)                                  # fica 1 min acordado e volta a dormir
    else:
        iniciar_anim('festa')
        balao('p', 'grito', 'OBA!' if sacudiu else 'UHU!', 2200)
        som.tocar('feliz')
        pet['alegria'] = lim(pet['alegria'] + 10)


# ------------------------------------------------------------ passear
def resolver_toques(agora):
    """Toques curtos em sequencia: 1 ou 2 = pula; 3 no mesmo lado = liga/desliga o andar sozinho."""
    global ex_pulo, ex_auto
    if not ex_toques or time.ticks_diff(agora, ex_toques[-1][0]) < TOQUE_JANELA:
        return
    lados = [l for _, l in ex_toques]
    n = len(lados)
    ex_toques.clear()
    if dormindo() or fase_vida() in ('ovo', 'estrela'):
        return
    if n >= 3 and lados.count(lados[-1]) >= 3:
        ex_auto = 0 if ex_auto else lados[-1]
        som.tocar('clique')
    else:
        ex_pulo = agora
        som.tocar('pulo')


def atualizar_passeio(agora):
    global ex_off, ex_moedas, ex_passo, ex_auto
    resolver_toques(agora)
    if dormindo() or fase_vida() in ('ovo', 'estrela'):
        ex_auto = 0
        return
    segurando = tocando and menu_borda < 1 and time.ticks_diff(agora, toque_ini[2]) > 200
    direcao = (1 if toque_ult[0] >= W // 2 else -1) if segurando else ex_auto
    if not direcao:
        ex_passo = agora
    else:
        passos = time.ticks_diff(agora, ex_passo) // 80      # anda em passos de 8 px a cada 80 ms
        if passos > 0:
            ex_passo = time.ticks_add(ex_passo, passos * 80) if passos < 5 else agora
            ex_off = max(0, ex_off + 8 * direcao * min(passos, 4))
            if ex_off == 0 and ex_auto < 0:
                ex_auto = 0                                   # chegou no comeco do campo
    for wx in ex_mundo:
        if abs(wx - ex_off - 110) < 10:
            ex_mundo.remove(wx)
            ex_moedas += 1
            som.tocar('moeda')
            break
    if ex_mundo[-1] - ex_off < 600:
        ex_mundo.append(ex_mundo[-1] + random.randint(50, 110))
    while ex_mundo and ex_mundo[0] < ex_off - 200:
        ex_mundo.pop(0)


def desenhar_passeio(agora, ph):
    dorme = dormindo()
    f = time.ticks_diff(agora, ex_pulo) / 600
    andando = (ex_auto or (tocando and time.ticks_diff(agora, toque_ini[2]) > 200 and menu_borda < 1)) and not dorme
    pe = d.FEET
    if dorme:
        olhos, boca = 'fechados', 'dormindo'
        pe += int(math.sin(agora / 900))
    else:
        olhos, boca = 'feliz', 'sorriso'
        if anim == 'susto' and time.ticks_diff(agora, anim_ini) < 2200:
            olhos, boca = 'susto', 'o'
        if 0 <= f < 1:
            pe -= int(math.sin(math.pi * f) * 40)
        elif andando:
            pe -= int(abs(math.sin(agora / 90)) * 6)
    d.passeio(ph, ex_off, agora, cfg['personagem'], pe, ex_moedas, ex_off // (W * 4) + 1, ex_mundo,
              olhos, boca, ex_auto, fase_vida())
    if dorme:
        z = (agora // 450) % 3
        d.texto('z', 136 + z * 4, pe - 76 - z * 7, d.CREME, 2)
    atual = baloes.get('p')
    if atual and time.ticks_diff(atual[2], agora) > 0 and atual[0] in ('fala', 'grito'):
        topo = pe - 75
        if atual[0] == 'fala':
            d.fala(atual[1], 110, topo)
        else:
            d.grito(atual[1], 110, topo, agora)


# ------------------------------------------------------------ desenho do jogo
def desenhar_baloes(agora, cx, topo, meia):
    atual = baloes.get('p')
    if atual and time.ticks_diff(atual[2], agora) <= 0:
        atual = None
    if vida_out and vida_ativa():
        if vida_out['shout']:
            atual = ['grito', vida_out['shout'], 0]
        elif vida_out['say'] and (not atual or PRIOR[atual[0]] <= PRIOR['fala']):
            atual = ['fala', vida_out['say'], 0]
    pedido = chamado_pet()
    if pedido and (not atual or PRIOR[pedido[0]] >= PRIOR[atual[0]]):
        atual = [pedido[0], pedido[1], 0]
    if not atual:
        return
    tipo, c = atual[0], atual[1]
    if tipo == 'fala':
        d.fala(c, cx, topo)
    elif tipo == 'grito':
        d.grito(c, cx, topo, agora)
    elif tipo == 'pensa':
        d.pensamento(c, cx, topo, agora)
    else:
        d.chamado(c, cx, topo, meia, agora, tipo == 'urgente')


def desenhar_jogo(agora):
    global anim
    modo = cfg['modo']
    hora = hora_atual()
    ph = d.fase_de(hora)
    d.ceu(ph, hora, agora)
    vida = fase_vida()
    if ph['estrelas'] and cfg.get('estrelas'):
        d.estrelas_antigas(len(cfg['estrelas']) - (1 if vida == 'estrela' else 0), agora)
    if vida == 'estrela':
        d.estrela_nome(nome())
    if modo == 'explore':
        desenhar_passeio(agora, ph)
        return
    d.chao(ph, agora)
    da = time.ticks_diff(agora, anim_ini)
    if anim and da > 2200:
        anim = ''
    if vida == 'estrela':                              # noite de despedida: so o ceu
        if modo == 'companion':
            d.etiqueta(relogio_txt(hora), 8, 2)
        return
    dorme = dormindo()
    if vida_ativa() and vida_out is not None:
        desenhar_vivo(agora, ph, hora, modo)
        return

    cx = int(capi_x) if modo == 'companion' else int(L['x'])
    ativ = atividade_companion() if modo == 'companion' else ''
    na_agua = modo == 'companion' and ativ == 'banho' and abs(capi_x - 200) < 32
    correndo = modo == 'companion' and capi_modo == 'corre' and abs(alvo_x - capi_x) > 2
    andando = modo == 'companion' and abs(alvo_x - capi_x) > 1 and not correndo and not na_agua

    pe = d.FEET
    if dorme:
        pe += int(math.sin(agora / 900))
    elif na_agua:
        pe = 211 + d.ri(math.sin(agora / 700) * 4)   # boia no lago
    else:
        pe += int(math.sin(agora / 300) * 1.5)
    if anim in ('pular', 'festa'):
        pe -= int(abs(math.sin(da / 120)) * 22)
    elif correndo:
        pe -= int(abs(math.sin(agora / 72)) * 6)
    if anim == 'susto':
        pe -= int(max(0, 18 - da / 25))
    if andando:
        pe -= int(abs(math.sin(agora / 110)) * 3)

    olhos, boca = 'normal', 'sorriso'
    doente = pet['doente'] and modo == 'pet'
    triste = modo == 'pet' and (pet['alegria'] < 30 or pet['fome'] < 25)
    comendo = vida != 'ovo' and (anim == 'comer' or (ativ == 'comendo' and not andando))
    if anim == 'susto':
        olhos, boca = 'susto', 'o'
    elif dorme:
        olhos, boca = 'fechados', 'dormindo'
    elif na_agua or correndo:
        olhos, boca = 'feliz', 'sorriso'
    elif modo == 'companion' and capi_modo == 'para' and not anim and visita not in d.ELENCO:
        olhos, boca = 'normal', 'o'
    elif anim in ('festa', 'pular', 'carinho', 'remedio') or ativ == 'por do sol':
        olhos, boca = 'feliz', 'sorriso'
    elif comendo:
        boca = 'aberta' if (agora // 220) % 2 else 'meia'
    elif ativ == 'espreguicando':
        olhos, boca = 'sono', 'o'
    elif doente:
        olhos, boca = 'sono', 'triste'
    elif triste:
        boca = 'triste'

    # conversa com vizinho: quem fala mexe a boca
    viz = visita if (modo == 'companion' and visita in d.ELENCO) else ''
    turno = None
    if viz:
        i = time.ticks_diff(agora, visita_ini) // VIZ_TURNO
        linhas = conversa()
        if i < len(linhas):
            turno = linhas[i]
            if turno[0] == 'p':
                boca = 'aberta' if (agora // 180) % 2 else 'sorriso'
    if olhos == 'normal' and (agora % 3800) < 150:
        olhos = 'fechados'                               # piscadinha

    if vida == 'ovo':
        pe = d.FEET
        if anim == 'aquece' and da < 600:              # tremidinha quando aquece
            cx += int(math.sin(da / 40) * 3)
    elif not na_agua:
        d.sombra(cx, ph, 12 if vida == 'filhote' else 20)
    cab_y, topo, meia = d.personagem(cfg['personagem'], cx, pe, olhos, boca, doente, fase=vida,
                                     racha=pet['idade_min'] >= DIA_MIN * DIAS_OVO / 2, grama=ph['grama'])
    if anim == 'aquece' and da < 900:
        for i in range(2):
            d.coracao(cx - 14 + i * 28, topo - 4 - (da // 30) % 30, d.STAT['fome'])
    if correndo and not dorme:
        d.rastro(cx, 1 if alvo_x > capi_x else -1)
    if na_agua:
        d.agua_nado(cx, meia, ph, agora)
    elif anim == 'banho':
        d.ell(cx, 207, 40, 7, ph['lago'])
        d.bolhas(cx, cab_y + 10, agora, ph['lago'])
    if modo == 'pet':
        d.cocos(pet['cocos'])
    if comendo:
        n = 3 - min(3, da // 500) if anim == 'comer' else 3
        for i in range(n):
            d.capim(cx + meia + 2 + i * 6, d.FEET - 4, ph['grama_e'])
    if anim in ('carinho', 'festa'):
        for i in range(3):
            d.coracao(cx - 28 + i * 28, topo - 4 - (da // 30) % 30)
    if anim == 'remedio' and da < 800:
        d.pilula(cx + 20, cab_y + 15 - da // 60)
    if anim == 'susto':
        d.texto('!', cx + 30, topo - 6, d.VERMELHO, 2)
    if dorme and anim != 'susto':
        z = (agora // 450) % 3
        d.texto('z', cx + meia + z * 4, topo - 4 - z * 7, d.CREME, 2)

    vtopo = None
    if viz:
        d.sombra(viz_x, ph, 16)
        _, vtopo, _ = d.personagem(viz, viz_x, d.FEET + int(math.sin(agora / 260 + 1) * 1.5), 'feliz',
                                   'aberta' if turno and turno[0] == 'v' and (agora // 180) % 2 else 'sorriso',
                                   s=0.9)
    elif modo == 'companion' and visita:
        desenhar_visita(agora, cx, topo, ph, na_agua)

    if turno:
        if turno[0] == 'v':
            d.fala(turno[1], viz_x, vtopo)
        else:
            d.fala(turno[1], cx, topo)
    else:
        desenhar_baloes(agora, cx, topo, meia)

    if modo == 'pet' and vida != 'ovo':
        d.hud_pet(pet)
    elif modo == 'companion':
        d.etiqueta(relogio_txt(hora), 8, 2)


def verificar_bateria(agora):
    global bat_pct, bat_carregando, bat_lida, bat_avisou
    if time.ticks_diff(agora, bat_lida) < 10000:      # le a cada 10 s
        return
    bat_lida = agora
    bat_pct, bat_carregando = bateria.porcentagem(), bateria.carregando()
    fraca = bat_pct is not None and bat_pct <= BATERIA_FRACA and not bat_carregando
    if fraca and not bat_avisou:
        sistema('Bateria fraca!', 4000)
        som.tocar('triste')
    bat_avisou = fraca


def desenhar_vivo(agora, ph, hora, modo):
    """Bichinho vivo: pose do movimento sorteado ou da reacao (vida.py)."""
    lp = vida_out['lp'] or {}
    dorme = vida_out['asleep']
    doente = pet['doente'] and modo == 'pet'
    triste = modo == 'pet' and (pet['alegria'] < 30 or pet['fome'] < 25)
    if dorme:
        olhos, boca = 'fechados', 'dormindo'
    elif doente:
        olhos, boca = 'sono', 'triste'
    else:
        olhos, boca = 'normal', 'triste' if triste else 'sorriso'
    olhos = lp.get('eyes') or olhos
    boca = lp.get('mouth') or boca
    if olhos == 'normal' and (agora % 3800) < 150:
        olhos = 'fechados'                               # piscadinha
    pe = d.FEET + (int(math.sin(agora / 900)) if dorme else 0)
    if modo == 'pet':
        d.cocos(pet['cocos'])
    r = d.personagem_vivo(cfg['personagem'], L['x'], pe, lp, ph, agora, olhos, boca, doente, fase_vida())
    cx, topo, meia = r['cx'], r['top'], r['half']
    if dorme:
        z = (agora // 450) % 3
        d.texto('z', cx + meia + z * 4, topo - 4 - z * 7, d.CREME, 2)
    if modo == 'companion' and visita:
        desenhar_visita(agora, int(cx), topo, ph, False)
    desenhar_baloes(agora, cx, topo, meia)
    if modo == 'pet':
        d.hud_pet(pet)
    else:
        d.etiqueta(relogio_txt(hora), 8, 2)


def desenhar_sobreposicoes(agora):
    if bat_avisou:
        d.bateria_fraca(agora)
    if sis_txt and time.ticks_diff(sis_ate, agora) > 0:
        d.sistema(sis_txt)
    if menu_borda >= 1:
        d.menu(int(menu_borda), cfg['modo'], cfg['personagem'], cfg['hora'], cfg['vel'],
               relogio_txt(hora_real()), cfg['som'], menu_pend, menu_conf, legenda_vida(), fase_vida())
    else:
        d.alca()


# ------------------------------------------------------------ menu de ajustes
def fechar_menu():
    global menu_alvo, menu_pend, menu_conf
    menu_alvo = 0
    menu_pend = menu_conf = None
    salvar('config.json', cfg)


def acao_menu(x, y):
    global menu_pend, menu_conf
    r = d.menu_toque(x, y, cfg['hora'], menu_conf)
    if not r:
        return
    k, v = r
    som.tocar('clique')
    if k == 'som':
        cfg['som'] = som.ligado = not cfg['som']
    elif k == 'modo' and v != cfg['modo']:
        cfg['modo'] = v
        if v != 'explore':
            cfg['casa'] = v
        baloes.clear()
    elif k == 'personagem':
        atual = menu_pend or cfg['personagem']
        prox = d.ELENCO[(d.ELENCO.index(atual) + v) % len(d.ELENCO)]
        menu_pend = None if prox == cfg['personagem'] else prox
        menu_conf = 'trocar' if menu_pend else None      # trocar comeca do zero: pergunta antes
    elif k == 'zerar':
        menu_pend, menu_conf = None, 'zerar'
    elif k == 'sim':
        novo_ovo(menu_pend if menu_conf == 'trocar' else None)
        menu_pend = menu_conf = None
        sistema('Um ovo novo!')
    elif k == 'nao':
        menu_pend = menu_conf = None
    elif k == 'hora' and v != cfg['hora']:
        if v == 'sim':
            iniciar_sim(hora_real())
        cfg['hora'] = v
    elif k == 'ajuste':
        relogio.somar_minutos(v)
    elif k == 'vel' and v != cfg['vel']:
        iniciar_sim(hora_atual())
        cfg['vel'] = v
    elif k == 'fechar':
        fechar_menu()


def animar_menu():
    global menu_borda
    if menu_arrasta:
        return
    menu_borda += (menu_alvo - menu_borda) * 0.35
    if abs(menu_alvo - menu_borda) < 1:
        menu_borda = float(menu_alvo)


# ------------------------------------------------------------ toque
def pressionar(x, y, agora):
    global menu_arrasta, menu_borda, ultimo_toque, toque_vida
    if menu_alvo == 0 and menu_borda < 1:
        if y < 48:                                    # puxar o menu de cima
            menu_arrasta = True
            menu_borda = float(y + 14)
            return
    elif menu_alvo:
        if y >= 250 and (x >= 68 or menu_conf):
            menu_arrasta = True                       # arrastar a alca para cima
        else:
            acao_menu(x, y)
        return
    if time.ticks_diff(agora, ultimo_toque) < 250:
        return
    ultimo_toque = agora
    if cfg['modo'] == 'pet':
        b = d.botao_pet(x, y)
        if b is not None:
            acao_pet(b)
            return
    if cfg['modo'] == 'explore':
        return
    cx = int(capi_x) if cfg['modo'] == 'companion' else int(L['x'])
    if fase_vida() == 'ovo':
        if abs(x - cx) < 34 and 140 < y < 212:          # toque aquece o ovo
            pet['idade_min'] += AQUECER_MIN
            iniciar_anim('aquece')
            som.tocar('amor')
        return
    if vida_ativa():
        lp = (vida_out or {}).get('lp') or {}
        alt = d.HTOP.get(cfg['personagem'], 75) * (0.62 if fase_vida() == 'filhote' else 1) * lp.get('sy', 1)
        ccx = L['x'] + lp.get('dx', 0)
        pe = d.FEET + lp.get('dy', 0)
        toque_vida = [x, y, abs(x - ccx) < 34 and pe - alt - 8 < y < pe + 8, False]
        return                                         # decide no soltar: carinho, toque fora ou colo
    if abs(x - cx) < 40 and 120 < y < 212 and not dormindo() and fase_vida() != 'estrela':
        pet['alegria'] = lim(pet['alegria'] + 3)
        iniciar_anim('carinho')
        som.tocar('amor')


def arrastar(x, y):
    global menu_borda
    if menu_arrasta:
        menu_borda = float(min(d.MENU_FUNDO, max(0, y + 14)))
    if toque_vida:
        if not toque_vida[3] and abs(x - toque_vida[0]) + abs(y - toque_vida[1]) > 5:
            toque_vida[3] = True
        if toque_vida[2] and toque_vida[3] and not L['grab'] and vida_ativa():
            V.pegar(L, vt, toque_vida[0], toque_vida[1])     # segurar e arrastar = colo
        if L['grab']:
            V.arrastar(L, vt, x, y)


def soltar(agora):
    global menu_arrasta, menu_alvo, toque_vida
    if toque_vida:
        t, toque_vida = toque_vida, None
        if L['grab']:
            V.soltar(L, vt)
        elif not t[3] and vida_ativa():
            V.toque(L, vt, t[2])
            if t[2]:
                pet['alegria'] = lim(pet['alegria'] + 3)
                som.tocar('amor')
        return
    if menu_arrasta:
        menu_arrasta = False
        parado = abs(toque_ult[1] - toque_ini[1]) < 6
        if menu_alvo and parado:
            fechar_menu()                             # toque na alca fecha
        elif menu_borda > 130:
            menu_alvo = d.MENU_FUNDO
        else:
            fechar_menu()
        return
    if cfg['modo'] == 'explore' and menu_borda < 1 and time.ticks_diff(agora, toque_ini[2]) < 200:
        ex_toques.append((agora, 1 if toque_ult[0] >= W // 2 else -1))   # resolvido em resolver_toques


def processar_toque(agora):
    global tocando, toque_ini, toque_ult, toque_visto
    p = toque.ler()
    if p is None:
        # o chip de toque as vezes falha uma leitura com o dedo ainda na tela:
        # so considera que soltou depois de 60 ms sem toque (senao o Passear "engasga")
        if tocando and time.ticks_diff(agora, toque_visto) > 60:
            tocando = False
            soltar(agora)
        return
    toque_visto = agora
    x, y = p
    toque_ult = (x, y)
    if not tocando:
        tocando = True
        toque_ini = (x, y, agora)
        pressionar(x, y, agora)
    else:
        arrastar(x, y)


def verificar_botao():
    global botao_antes
    if botao is None:
        return
    v = botao.value()
    if v == 0 and botao_antes == 1:
        if menu_alvo or menu_borda >= 1:
            fechar_menu()
        elif cfg['modo'] == 'explore':
            cfg['modo'] = cfg.get('casa', 'pet')
            salvar('config.json', cfg)
        som.tocar('clique')
    botao_antes = v


# ------------------------------------------------------------ laco principal
def passo(agora, dt):
    global acc_pet, ultimo_save, ultimo_urgente, vt, vida_out
    vt += dt
    som.atualizar()
    processar_toque(agora)
    verificar_botao()
    animar_menu()
    verificar_bateria(agora)
    envelhecer(dt)
    verificar_sensores(agora)
    if cfg['modo'] == 'pet':
        acc_pet += dt * fator_tempo()
        while acc_pet >= TICK_PET_SEG * 1000:
            acc_pet -= TICK_PET_SEG * 1000
            tick_pet()
        pedido = chamado_pet()
        if pedido and pedido[0] == 'urgente' and time.ticks_diff(agora, ultimo_urgente) > 30000:
            ultimo_urgente = agora
            som.tocar('triste')
    elif cfg['modo'] == 'companion':
        atualizar_companion(dt, agora)
    else:
        atualizar_passeio(agora)
    if vida_ativa():
        L['lento'] = fase_vida() == 'idoso'
        antes = L['bubble']
        vida_out = V.passo(L, vt, sono_vida(), V.periodo(hora_atual()))
        b = L['bubble']
        if b and b is not antes and b[0] == 'say':          # comecou uma fala nova
            tocar_voz()
    else:
        vida_out = None
    if time.ticks_diff(agora, ultimo_save) > 60000:
        ultimo_save = agora
        pet['epoch'] = relogio.epoch()
        salvar(arquivo_pet(cfg['personagem']), pet)
    desenhar_jogo(agora)
    desenhar_sobreposicoes(agora)


def principal():
    if sincronizar_hora():
        sistema('Hora certa!')
    if relogio.ler() is None:
        relogio.acertar(2026, 1, 1, 12, 0, 0)
    iniciar_sim(hora_real())
    recuperar_tempo_desligado()
    anterior = ultimo_gc = time.ticks_ms()
    while True:
        agora = time.ticks_ms()
        dt = time.ticks_diff(agora, anterior)
        anterior = agora
        passo(agora, dt)
        tela.mostrar()
        if time.ticks_diff(agora, ultimo_gc) > 1000:     # limpar a memoria a cada quadro custava caro
            ultimo_gc = agora
            gc.collect()


if __name__ == '__main__':
    principal()
