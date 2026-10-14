# Testa e grava as telas das novidades: amigos por perto e presentes, clima de verdade,
# portal do Wi-Fi, botoes (BOOT segurado e BOOT + PWR) e o Naufrago.
# Uso: cd previa && micropython novidades.py   (depois: python3 montar.py)
import sys
sys.path.insert(0, '.')
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


def preparar(modo, hora, id='capi', x=110, sim=True, vel=1):
    cfg['modo'] = modo
    cfg['hora'] = 'sim' if sim else 'real'
    cfg['vel'] = vel
    main.sim_h0, main.sim_t0 = hora, T.agora
    cfg['personagem'] = id
    main.capi_x = main.alvo_x = float(x)
    main.visita = ''
    main.proxima_visita = T.agora + 10 ** 9
    main.anim = ''
    main.baloes.clear()
    main.menu_borda, main.menu_alvo, main.menu_pend = 0.0, 0, None
    main.sis_txt = ''
    for k, v in main.PET_PADRAO.items():
        main.pet[k] = v
    main.pet['idade_min'] = 6 * main.DIA_MIN
    main.L.clear(); main.L.update(main.V.nova(id, main.vt)); main.vida_out = None


def gravar(nome):
    main.passo(T.agora, 1)
    with open('out/%s.565' % nome, 'wb') as f:
        f.write(main.tela.buf)


def toque(x, y, ms=60, depois=260):
    hw.ENTRADA['toque'] = (x, y); avancar(ms)
    hw.ENTRADA['toque'] = None; avancar(depois)


import rede, portal, os

class Radio:
    def __init__(self): self.fila, self.peers_table, self.enviados = [], {}, []
    def recv(self, t): return self.fila.pop(0) if self.fila else (None, None)
    def send(self, mac, msg, sync): self.enviados.append(msg)

hw.ENTRADA['epoch'] = 800000000
rede.iniciar()
assert rede.sta is None and rede.situacao() == 0
R = rede.en = Radio(); rede.eu = b'\x01' * 6
B = b'\x02' * 6
def ping(rssi, char=b'pato'):
    R.peers_table[B] = [rssi, 0]; R.fila.append((B, b'CGP' + char))
def segundos(n, rssi=None, passo=40):
    for _ in range(n):
        if rssi is not None: ping(rssi)
        avancar(1000, passo)

# --- amigos
preparar('pet', 10, 'capi', sim=False)
main.presentes[:] = []
segundos(3, -70)
assert main.amigo_perto is None, 'longe nao e amigo perto'
assert any(m[:3] == b'CGP' and m[3:] == b'capi' for m in R.enviados), 'devia avisar que esta aqui'
ale = main.pet['alegria']
segundos(6, -38)
assert main.amigo_perto == 'pato', main.amigo_perto
assert main.pet['alegria'] > ale
print('chegou amigo: fala', main.L['bubble'] and main.L['bubble'][1], '| movimento', main.L['move'] and main.L['move']['id'])
movs = set()
R.enviados.clear()
for _ in range(330):                    # 5 min e meio encostados
    ping(-38); avancar(1000, 100)
    if main.L['move']: movs.add(main.L['move']['id'])
dados = [m for m in R.enviados if m[:3] == b'CGG']
assert len(dados) == 10 and all(m[3:9] == B for m in dados), len(dados)     # 5 presentes, cada um mandado 2x
print('em 5 min mandou', len(dados) // 2, 'presentes; pulou de:', sorted(movs))
segundos(120, -38, 200)
assert len([m for m in R.enviados if m[:3] == b'CGG']) == 10, 'depois dos 5, descansa'
# presentes que chegam
for seq, k in ((1, 0), (2, 1), (3, 2)):
    msg = b'CGG' + rede.eu + bytes((seq, k))
    R.fila.append((B, msg)); R.fila.append((B, msg))
R.fila.append((B, b'CGG' + b'\x09' * 6 + bytes((9, 0))))       # presente para outra placa: nao e meu
ping(-38); avancar(400)
assert [p[0] for p in main.presentes] == ['caixa', 'flor', 'coracao'], main.presentes
for seq in range(10, 18):
    R.fila.append((B, b'CGG' + rede.eu + bytes((seq, seq))))
ping(-38); avancar(400)
assert len(main.presentes) == main.PRESENTES_MAX
main.L['x'] = 120.0; main.L['move'] = None; main.L['bubble'] = None
main.V.tocar(main.L, main.vt, 'pular', shout='presente!')
ping(-38); avancar(300)
gravar('novo_amigo_pet')
cfg['modo'] = 'companion'; ping(-38); avancar(300); gravar('novo_amigo_olhar'); cfg['modo'] = 'pet'
# dormindo: o amigo acorda
preparar('pet', 23, 'capi'); main.pet['dormindo'] = True
segundos(6, -38)
assert not main.dormindo(), 'amigo perto devia acordar'
# foi embora
segundos(3, -75)
assert main.amigo_perto is None
segundos(6, -38); assert main.amigo_perto == 'pato'
avancar(8000); assert main.amigo_perto is None, 'sumiu do radio: foi embora'
# presentes somem em 3 h
n = len(main.presentes)
hw.ENTRADA['epoch'] += 2 * 3600; avancar(11000); assert len(main.presentes) == n
hw.ENTRADA['epoch'] += 3600 + 60; avancar(11000); assert main.presentes == [], main.presentes
print('amigos e presentes ok')
# ovo nao faz festa nem manda presente
preparar('pet', 10, 'capi'); main.pet['idade_min'] = 0.0
R.enviados.clear(); segundos(7, -38)
assert main.amigo_perto is None and not R.enviados
os.remove('presentes.json')

# --- clima
def tempo(cod, vento, graus, hora, nome, modo='companion', id='capi'):
    preparar(modo, hora, id)
    rede.clima.update({'cod': cod, 'vento': vento, 'temp': graus, 'epoch': hw.ENTRADA['epoch']})
    rede._guardar_clima()
    T.agora += 4321; avancar(200)
    gravar(nome)
for cod, tipo in ((0, 'sol'), (3, 'nublado'), (63, 'chuva'), (96, 'tempestade'), (73, 'neve'), (45, 'neblina')):
    assert rede.tipo_de(rede.wx_de(cod)) == tipo, (cod, tipo)
assert rede.tipo_de(rede.wx_de(1, 50)) == 'vento'
tempo(0, 5, 27, 10, 'novo_tempo_sol')
tempo(3, 8, 19, 10, 'novo_tempo_nublado')
tempo(63, 10, 18, 10, 'novo_tempo_chuva', 'pet')
tempo(96, 30, 21, 15, 'novo_tempo_tempestade')
T.agora += 9000 - (T.agora % 9000) + 20; gravar('novo_tempo_raio')
tempo(73, 5, -2, 10, 'novo_tempo_neve')
tempo(2, 55, 22, 10, 'novo_tempo_vento')
tempo(45, 2, 12, 7.5, 'novo_tempo_neblina')
tempo(65, 20, 16, 23, 'novo_tempo_chuva_noite')
tempo(63, 10, 18, 16, 'novo_tempo_passear', 'explore')
# fala do tempo
preparar('pet', 10, 'capi'); main.prox_fala_clima = 0; main.L['nextIdle'] = main.vt + 10 ** 6
rede.clima.update({'cod': 63, 'temp': 18}); rede._guardar_clima()
avancar(200)
print('fala da chuva:', main.L['bubble'] and main.L['bubble'][1], '| pend', main.L['pend'] and main.L['pend'][1])
assert main.L['move'] and main.prox_fala_clima > main.vt
# previsao velha nao vale
hw.ENTRADA['epoch'] += 4 * 3600; avancar(100); assert main.wx_agora is None
os.remove('clima.json')

# --- portal
r, salvo = portal.tratar(b'GET /generate_204 HTTP/1.1\r\nHost: x\r\n\r\n', ['Casa <1>', 'Vizinho'])
assert salvo is None and b'Casa &lt;1&gt;' in r and r.startswith(b'HTTP/1.0 200')
r, salvo = portal.tratar(b'POST /salvar HTTP/1.1\r\nContent-Length: 9\r\n\r\nssid=Casa+Caf%C3%A9&senha=a%26b%3D12345', [])
assert salvo == {'ssid': 'Casa Caf\xe9', 'senha': 'a&b=12345'}, salvo
r, salvo = portal.tratar(b'POST /salvar HTTP/1.1\r\n\r\nssid=Casa&senha=123', [])
assert salvo is None and b'8 a 63' in r
r, salvo = portal.tratar(b'POST /salvar HTTP/1.1\r\n\r\nssid=Aberta&senha=', [])
assert salvo == {'ssid': 'Aberta', 'senha': ''}
r, salvo = portal.tratar(b'POST /salvar HTTP/1.1\r\n\r\nssid=&senha=12345678', [])
assert salvo is None
q = b'\xab\xcd\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x07example\x03com\x00\x00\x01\x00\x01'
a = portal.resposta_dns(q)
assert a[:2] == b'\xab\xcd' and a[-4:] == bytes((192, 168, 4, 1)) and a[6:8] == b'\x00\x01'
d.tela_wifi(portal.QR, portal.PASSO_1); open('out/novo_wifi_1.565', 'wb').write(main.tela.buf)
d.tela_wifi(portal.QR, portal.PASSO_2, True); open('out/novo_wifi_2.565', 'wb').write(main.tela.buf)
print('portal ok')

# --- botoes: BOOT segurado 3 s, BOOT + PWR, toque curto
chamou = []
main.abrir_wifi = lambda: chamou.append(1)
preparar('explore', 10, 'capi'); cfg['casa'] = 'pet'
main.botao.v = 0; avancar(2800); assert not chamou
avancar(400); assert chamou == [1]
avancar(3000); assert chamou == [1], 'so uma vez por aperto'
main.botao.v = 1; avancar(100); assert cfg['modo'] == 'explore', 'aperto longo nao volta do Passear'
main.botao.v = 0; avancar(200); hw.ENTRADA['pwr'] = True; avancar(80); hw.ENTRADA['pwr'] = False
assert chamou == [1, 1], 'BOOT + PWR abre o Wi-Fi na hora'
main.botao.v = 1; avancar(100)
main.botao.v = 0; avancar(200); main.botao.v = 1; avancar(100)
assert cfg['modo'] == 'pet' and chamou == [1, 1], 'toque curto continua voltando do Passear'
assert d.menu_toque(40, 14, 'real') == ('wifi', None) and d.menu_toque(200, 14, 'real') == ('som', None)
# 3 toques no BOOT: offline (sem ping, sem amigos); mais 3: online
def clique(): main.botao.v = 0; avancar(120); main.botao.v = 1; avancar(120)
preparar('pet', 10, 'capi'); cfg['offline'] = False; avancar(1500)
clique(); clique(); avancar(1500); clique(); assert not rede.offline, 'toques espacados nao contam'
avancar(1500)
clique(); clique(); clique()
assert rede.offline and cfg['offline'] and rede.situacao() == 0
R.enviados.clear(); segundos(7, -38)
assert main.amigo_perto is None and not R.enviados, 'offline: radio calado'
gravar('novo_offline_aviso')
clique(); clique(); clique()
assert not rede.offline and not cfg['offline']
segundos(7, -38); assert main.amigo_perto == 'pato' and R.enviados
segundos(3, -80); avancar(8000)
print('botoes ok')

# --- naufrago
assert 'naufrago' in d.ELENCO and len(d.ELENCO) == 10
preparar('companion', 10, 'naufrago'); T.agora = T.agora - T.agora % 3800 + 400; gravar('novo_naufrago')
ph = d.fase_de(10); d.rect(0, 0, 240, 284, ph['ceu'][1])
combos = (('normal', 'sorriso'), ('feliz', 'aberta'), ('fechados', 'dormindo'), ('susto', 'o'), ('sono', 'triste'), ('normal', 'meia'))
for i, (o, b) in enumerate(combos):
    d.personagem('naufrago', 40 + (i % 3) * 80, 130 + (i // 3) * 130, o, b, doente=(i == 4))
open('out/novo_naufrago_expr.565', 'wb').write(main.tela.buf)
preparar('pet', 10, 'naufrago'); main.pet['idade_min'] = 2 * main.DIA_MIN; T.agora += 300; gravar('novo_naufrago_filhote')
preparar('companion', 10, 'naufrago'); main.pet['idade_min'] = 22 * main.DIA_MIN; main.pet['vida_adulto'] = 15; T.agora += 300; gravar('novo_naufrago_idoso')
preparar('pet', 10, 'naufrago'); main.menu_borda, main.menu_alvo = 272.0, 272; gravar('novo_menu')
print('tudo ok')
