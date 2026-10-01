# Roda o firmware de verdade (main.py + desenho.py) no MicroPython unix e grava telas.
# Uso: cd previa && micropython rodar.py   (depois: python3 montar.py)
import sys
sys.path.append('..')
import hw
import time as _t


class Relogio:
    agora = 100000

    def ticks_ms(self): return self.agora
    def ticks_diff(self, a, b): return a - b
    def ticks_add(self, a, b): return a + b
    def sleep_ms(self, ms): self.agora += ms
    def localtime(self, *a): return _t.localtime(*a)
    def time(self): return _t.time()
    def mktime(self, t): return _t.mktime(t)


T = Relogio()
import main
main.time = T
d = main.d
cfg = main.cfg


def avancar(ms, passo=40):
    fim = T.agora + ms
    while T.agora < fim:
        T.agora += passo
        main.passo(T.agora, passo)


def gravar(nome):
    main.passo(T.agora, 1)          # um quadro de verdade (vida, sensores, desenho)
    with open('out/%s.565' % nome, 'wb') as f:
        f.write(main.tela.buf)
    print('tela', nome)


def preparar(modo, hora, id='capi', x=110):
    cfg['modo'] = modo
    cfg['hora'] = 'sim'
    cfg['vel'] = 1
    main.sim_h0, main.sim_t0 = hora, T.agora
    cfg['personagem'] = id
    main.capi_x = main.alvo_x = float(x)
    main.capi_modo = 'anda'
    main.visita = ''
    main.proxima_visita = T.agora + 10 ** 9
    main.anim = ''
    main.baloes.clear()
    main.menu_borda, main.menu_alvo, main.menu_pend = 0.0, 0, None
    main.sis_txt = ''
    for k, v in main.PET_PADRAO.items():
        main.pet[k] = v
    main.pet['idade_min'] = 6 * main.DIA_MIN          # adulto, para as telas antigas
    main.L.clear(); main.L.update(main.V.nova(id, main.vt)); main.vida_out = None


# 1. cena nas 6 fases (Olhar)
for nome, h, x in (('fase_madrugada', 3, 110), ('fase_amanhecer', 6.2, 110), ('fase_dia', 10, 150),
                   ('fase_banho', 13.2, 200), ('fase_pordosol', 17.6, 110), ('fase_crepusculo', 19.2, 90),
                   ('fase_noite', 23, 110)):
    preparar('companion', h, 'capi', x)
    T.agora += 1000
    gravar(nome)

# 2. elenco de 9, dia, Olhar
for id in d.ELENCO:
    preparar('companion', 10, id, 110)
    T.agora = 200000 + 200        # fora da piscadinha
    gravar('elenco_' + id)

# 3. expressoes do elenco (olhos x bocas) desenhadas direto
import framebuf
for id in d.ELENCO:
    ph = d.fase_de(10)
    d.rect(0, 0, 240, 284, ph['ceu'][1])
    combos = (('normal', 'sorriso'), ('feliz', 'aberta'), ('fechados', 'dormindo'),
              ('susto', 'o'), ('sono', 'triste'), ('normal', 'meia'))
    for i, (o, b) in enumerate(combos):
        cx, pe = 40 + (i % 3) * 80, 130 + (i // 3) * 130
        d.personagem(id, cx, pe, o, b, doente=(i == 4))
        d.texto(o[:5], cx - 20, pe + 4, d.INK)
    with open('out/expr_%s.565' % id, 'wb') as f:
        f.write(main.tela.buf)
    print('tela expr', id)

# 4. Pet: HUD, chamados e baloes
preparar('pet', 10, 'capi')
gravar('pet_normal')
preparar('pet', 10, 'pato'); main.pet['fome'] = 20; main.pet['cocos'] = 2
gravar('pet_chamado_fome')
preparar('pet', 10, 'elefante'); main.pet['doente'] = True; main.pet['saude'] = 18
gravar('pet_urgente')
preparar('pet', 10, 'cachorro'); main.falar('To cheio!')
gravar('balao_fala')
preparar('pet', 10, 'gato'); main.balao('p', 'grito', 'OBA!'); main.iniciar_anim('festa')
T.agora += 300
gravar('balao_grito')
preparar('companion', 10, 'polvo'); main.capi_modo = 'para'; main.balao('p', 'pensa', 'peixe')
gravar('balao_pensa')
preparar('pet', 10, 'et'); main.sistema('Hora certa!')
gravar('balao_sistema')

# 5. conversa com vizinho
preparar('companion', 10, 'capi', 140)
main.visita, main.visita_ini, main.viz_x = 'sapinho', T.agora, 52
T.agora += 500
gravar('conversa_1')
T.agora += main.VIZ_TURNO
gravar('conversa_2')

# 6. menu puxado do topo (gesto de verdade pelo toque falso)
preparar('companion', 15, 'calopsita')
hw.ENTRADA['toque'] = (120, 20); avancar(40)
hw.ENTRADA['toque'] = (120, 110); avancar(40)
gravar('menu_arrastando')
hw.ENTRADA['toque'] = (120, 200); avancar(40)
hw.ENTRADA['toque'] = None; avancar(800)
gravar('menu_aberto_sim')
hw.ENTRADA['toque'] = (60, 195); avancar(40); hw.ENTRADA['toque'] = None; avancar(200)   # Real
gravar('menu_aberto_real')
preparar('pet', 10, 'capi')
main.menu_borda, main.menu_alvo = 272.0, 272
hw.ENTRADA['toque'] = (220, 120); avancar(40); hw.ENTRADA['toque'] = None; avancar(200)  # seta
gravar('menu_pet_confirmar')

# 7. passear
preparar('explore', 16, 'sapinho')
hw.ENTRADA['toque'] = (200, 150); avancar(1500)
hw.ENTRADA['toque'] = None; avancar(100)
hw.ENTRADA['toque'] = (200, 150); avancar(40); hw.ENTRADA['toque'] = None; avancar(240)
gravar('passear')

# 7b. passear: 3 toques rapidos na direita -> anda sozinho; mais 3 -> para; dorme a noite
def toque_curto(x):
    hw.ENTRADA['toque'] = (x, 150); avancar(40); hw.ENTRADA['toque'] = None; avancar(120)

preparar('explore', 16, 'cachorro')
for _ in range(3):
    toque_curto(200)
avancar(500)
assert main.ex_auto == 1, 'devia andar sozinho'
off1 = main.ex_off; avancar(2000)
assert main.ex_off > off1 + 100, 'nao andou sozinho'
gravar('passear_auto')
for _ in range(3):
    toque_curto(200)
avancar(500)
assert main.ex_auto == 0, 'devia parar'
preparar('explore', 23, 'cachorro')
gravar('passear_dormindo')
hw.ENTRADA['g'] = 3.0; avancar(40); hw.ENTRADA['g'] = 1.0
assert not main.dormindo(), 'sacudida devia acordar'
avancar(500); gravar('passear_acordou')
avancar(61000)
assert main.dormindo(), 'devia voltar a dormir depois de 1 min'
print('passear: auto, parar, dormir e acordar 1 min ok')

# 7c. sono das 22 as 6 e acordar 1 min no Pet e no Olhar
for m in ('pet', 'companion'):
    for h, esperado in ((21.9, False), (22.1, True), (5.9, True), (6.1, False)):
        preparar(m, h, 'capi', 110)
        if m == 'pet':
            main.pet['dormindo'] = main.noite_pet()
        assert main.dormindo() == esperado, (m, h)
    preparar(m, 23, 'capi', 110)
    if m == 'pet':
        main.pet['dormindo'] = True
    main.ultima_reacao = -10 ** 6
    hw.ENTRADA['g'] = 3.0; avancar(40); hw.ENTRADA['g'] = 1.0
    assert not main.dormindo()
    avancar(30000); assert not main.dormindo()
    avancar(31000); assert main.dormindo()
print('sono 22h-6h e acordar 1 min ok')
preparar('pet', 23, 'capi'); main.pet['dormindo'] = True; main.ultima_reacao = -10 ** 6
hw.ENTRADA['g'] = 3.0; avancar(40); hw.ENTRADA['g'] = 1.0; avancar(3000)
gravar('pet_acordado_noite')

# 7d. menu em hora Real com os botoes de acertar o relogio
preparar('companion', 10, 'capi')
cfg['hora'] = 'real'
main.menu_borda, main.menu_alvo = 272.0, 272
assert d.menu_toque(30, 220, 'real') == ('ajuste', -1)
assert d.menu_toque(200, 220, 'real') == ('ajuste', 1)
assert d.menu_toque(120, 258, 'real') == ('fechar', None)
gravar('menu_relogio')

# 7e. ritmo do Pet: 4 horas de jogo sem cuidar
preparar('pet', 9, 'capi')
cfg['hora'] = 'real'
for _ in range(240):
    main.tick_pet()
print('Pet depois de 4 h sem cuidar:', dict((k, round(main.pet[k])) for k in ('fome', 'alegria', 'energia', 'saude')),
      'cocos', main.pet['cocos'], 'doente', main.pet['doente'])

# 9. ciclo de vida
D = main.DIA_MIN
def vida(nome, id, idade, modo='companion', hora=10, **extra):
    preparar(modo, hora, id, 110)
    main.pet['idade_min'] = idade
    for k, v in extra.items():
        main.pet[k] = v
    T.agora += 500
    gravar(nome)

vida('vida_ovo', 'pato', 0.1 * D)
vida('vida_ovo_rachado', 'pato', 0.7 * D, 'pet')
vida('vida_filhote', 'pato', 2 * D, 'pet')
vida('vida_adulto', 'pato', 10 * D)
vida('vida_idoso', 'pato', 22 * D, vida_adulto=15)
cfg['estrelas'] = ['Capi', 'Gato', 'Pato']
vida('vida_estrela', 'pato', 25 * D, 'companion', 23, morto=True)

# aquecer o ovo pelo toque
preparar('pet', 10, 'sapinho'); main.pet['idade_min'] = 0.0
hw.ENTRADA['toque'] = (110, 180); avancar(40); hw.ENTRADA['toque'] = None; avancar(300)
assert main.pet['idade_min'] >= main.AQUECER_MIN, 'toque devia aquecer o ovo'
gravar('vida_aquecendo')

# fluxo completo em hora simulada 3x: nasce, cresce, envelhece, vira estrela a noite e volta ovo de manha
preparar('companion', 8, 'gato'); main.pet['idade_min'] = 0.0; main.pet['vida_adulto'] = 10
cfg['vel'] = 3; main.sim_h0, main.sim_t0 = 8.0, T.agora
fases = []
for _ in range(200000):
    T.agora += 1000
    main.envelhecer(1000)
    f = main.fase_vida()
    if not fases or fases[-1] != f:
        fases.append(f)
    if fases[-1] == 'ovo' and len(fases) > 1:
        break
print('ciclo:', ' -> '.join(fases))
assert fases == ['ovo', 'filhote', 'adulto', 'idoso', 'estrela', 'ovo'], fases
print('estrelas no ceu:', cfg['estrelas'])

# menu: trocar de personagem e zerar pedem confirmacao e comecam do zero
preparar('companion', 10, 'capi')
main.menu_borda, main.menu_alvo = 272.0, 272
hw.ENTRADA['toque'] = (220, 120); avancar(40); hw.ENTRADA['toque'] = None; avancar(200)
assert main.menu_conf == 'trocar' and main.menu_pend == 'elefante'
gravar('menu_confirma_trocar')
hw.ENTRADA['toque'] = (60, 220); avancar(40); hw.ENTRADA['toque'] = None; avancar(200)
assert cfg['personagem'] == 'elefante' and main.fase_vida() == 'ovo', 'trocar devia virar ovo'
gravar('menu_depois_trocar')
main.pet['idade_min'] = 6 * D
hw.ENTRADA['toque'] = (40, 256); avancar(40); hw.ENTRADA['toque'] = None; avancar(200)
assert main.menu_conf == 'zerar'
gravar('menu_confirma_zerar')
hw.ENTRADA['toque'] = (170, 220); avancar(40); hw.ENTRADA['toque'] = None; avancar(200)
assert main.menu_conf is None and main.fase_vida() == 'adulto', 'Nao devia cancelar'
print('menu: confirmar troca, zerar e cancelar ok')

# 9b. ovo choca em 10 min de verdade, com hora Real e Simulada
for modo_hora in ('real', 'sim'):
    preparar('companion', 10, 'capi'); cfg['hora'] = modo_hora; main.pet['idade_min'] = 0.0
    t = 0
    while main.fase_vida() == 'ovo':
        T.agora += 1000; t += 1; main.envelhecer(1000)
    assert 590 <= t <= 610, (modo_hora, t)
print('ovo choca em 10 min (real e simulada) ok; toques para nascer na hora:', int(main.DIAS_OVO * main.DIA_MIN / main.AQUECER_MIN))

# 10. bateria fraca pisca
for m, nome in (('pet', 'bateria_pet'), ('companion', 'bateria_olhar')):
    preparar(m, 10, 'capi')
    hw.ENTRADA['bateria'] = 9
    main.bat_lida = T.agora - 20000
    avancar(40)
    assert main.bat_avisou, 'devia avisar bateria fraca'
    T.agora = (T.agora // 1000) * 1000 + 100      # fase visivel da piscada
    gravar(nome)
hw.ENTRADA['carregando'] = True; main.bat_lida = T.agora - 20000; avancar(40)
assert not main.bat_avisou, 'carregando nao avisa'
hw.ENTRADA['bateria'] = 80; hw.ENTRADA['carregando'] = False; main.bat_lida = T.agora - 20000; avancar(40)
print('bateria: aviso a 9%, some carregando ok')

# 11. vida: cada movimento no meio do caminho
V = main.V
for mv in sorted(V.MOVES):
    preparar('companion', 10.5, 'cachorro', 110)
    main.L['nextIdle'] = main.vt + 10 ** 9
    V.tocar(main.L, main.vt, mv, say=None)
    avancar(int(V.MOVES[mv][0] * (0.5 if mv not in ('esconder', 'cavar') else 0.4)))
    gravar('mov_' + mv)
print('movimentos desenhados:', len(V.MOVES))

# colo: segura o bichinho e levanta
preparar('pet', 10, 'gato')
main.L['nextIdle'] = main.vt + 10 ** 9
hw.ENTRADA['toque'] = (110, 170); avancar(40)
hw.ENTRADA['toque'] = (120, 120); avancar(40)
hw.ENTRADA['toque'] = (130, 90); avancar(1200)
assert main.L['grab'], 'devia estar no colo'
gravar('vida_colo')
hw.ENTRADA['toque'] = None; avancar(300)
assert not main.L['grab']
# barulho: microfone alto
preparar('companion', 10, 'pato'); main.L['nextIdle'] = main.vt + 10 ** 9
hw.ENTRADA['mic'] = 30000; avancar(160); hw.ENTRADA['mic'] = 0; avancar(400)
assert main.L['move'] and main.L['move']['id'] == 'susto', main.L['move']
gravar('vida_barulho')
# carinho
preparar('pet', 10, 'polvo'); main.L['nextIdle'] = main.vt + 10 ** 9
hw.ENTRADA['toque'] = (110, 170); avancar(40); hw.ENTRADA['toque'] = None; avancar(600)
assert main.L['move']['id'] in ('rir', 'comemorar', 'cambalhota'), main.L['move']
gravar('vida_carinho')
# sacudida acordado e dormindo
preparar('companion', 11, 'elefante'); main.L['nextIdle'] = main.vt + 10 ** 9
hw.ENTRADA['g'] = 3.0; avancar(800); hw.ENTRADA['g'] = 1.0
gravar('vida_sacudido')
avancar(1200)
assert main.L['move'] and main.L['move']['id'] == 'tonto'
# 10 minutos rodando sozinho no Olhar e no Cuidar: nada quebra e ele faz varias coisas
vistos = set()
for m in ('companion', 'pet'):
    preparar(m, 9.5, 'capi')
    cfg['hora'] = 'real'
    for _ in range(600 * 10):
        T.agora += 100; main.passo(T.agora, 100)
        if main.L['move']:
            vistos.add(main.L['move']['id'])
print('10 min sozinho: movimentos que apareceram:', len(vistos), sorted(vistos))

# 8. um minuto inteiro de jogo em cada modo, so para ver se nada quebra
for m in ('pet', 'companion', 'explore'):
    preparar(m, 12.9, 'capi')
    main.proxima_visita = T.agora + 2000
    cfg['vel'] = 3
    avancar(60000)
print('fim: 60 s de jogo em cada modo sem erro')
