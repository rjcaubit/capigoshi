# Gera os quadros usados na landing page e no README (rode com: micropython landing.py).
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
V, d, cfg = main.V, main.d, main.cfg


def preparar(modo, hora, id, x=110):
    cfg['modo'], cfg['hora'], cfg['vel'], cfg['personagem'] = modo, 'sim', 1, id
    main.sim_h0, main.sim_t0 = hora, T.agora
    for k, v in main.PET_PADRAO.items():
        main.pet[k] = v
    main.pet['idade_min'] = 6 * main.DIA_MIN
    main.L.clear(); main.L.update(V.nova(id, main.vt, x))
    main.L['nextIdle'] = main.vt + 10 ** 9
    main.visita = ''
    main.proxima_visita = T.agora + 10 ** 9
    main.baloes.clear(); main.anim = ''


def quadro(nome):
    with open('out/%s.565' % nome, 'wb') as f:
        f.write(main.tela.buf)


# animacao do topo: Capi dancando, dando cambalhota e comemorando
preparar('companion', 10.4, 'capi', 96)
roteiro = (('dancar', 'la la la!', 4200), ('cambalhota', None, 2400), ('comemorar', None, 2600))
n = 0
for mv, fala, dur in roteiro:
    V.tocar(main.L, main.vt, mv, say=fala, auto=fala is None, force=True)
    fim = T.agora + dur + 300
    while T.agora < fim:
        T.agora += 100
        main.passo(T.agora, 100)
        quadro('anim_%03d' % n)
        n += 1
print('quadros da animacao:', n)

# elenco, cada um num movimento
poses = {'capi': 'olhar', 'elefante': 'cheirarFlor', 'pato': 'girar', 'polvo': 'rir', 'calopsita': 'dancar',
         'cachorro': 'comemorar', 'gato': 'espreguicar', 'et': 'soluco', 'sapinho': 'pular'}
for id in d.ELENCO:
    preparar('companion', 10.5, id)
    V.tocar(main.L, main.vt, poses[id])
    for _ in range(14):
        T.agora += 100
        main.passo(T.agora, 100)
    quadro('land_elenco_' + id)

# fases do dia e telas de destaque
for nome, h in (('madrugada', 3), ('amanhecer', 6.4), ('dia', 10), ('pordosol', 17.6), ('crepusculo', 19.2), ('noite', 23)):
    preparar('companion', h, 'pato')
    T.agora += 200
    main.passo(T.agora, 100)
    quadro('land_fase_' + nome)
print('ok')

# ciclo de vida da mesma Capi, para a secao "Do ovo a estrela"
D = main.DIA_MIN
for fase, idade, hora, extra in (('ovo', 0.7 * D, 10.5, {}), ('filhote', 2 * D, 10.5, {}),
                                 ('adulto', 10 * D, 10.5, {}), ('idoso', 22 * D, 10.5, {'vida_adulto': 15}),
                                 ('estrela', 26 * D, 23, {'vida_adulto': 15, 'morto': True})):
    preparar('companion', hora, 'capi')
    main.pet['idade_min'] = idade
    for k, v in extra.items():
        main.pet[k] = v
    cfg['estrelas'] = ['Capi']
    T.agora += 200
    main.passo(T.agora, 100)
    quadro('land_ciclo_' + fase)
    print('ciclo', fase, main.fase_vida())
