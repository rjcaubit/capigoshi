# rede.py - o bichinho na internet e perto dos amigos.
#   Internet (opcional, precisa de wifi.json): de 30 em 30 min entra no Wi-Fi, acerta a hora,
#     pega o tempo que faz la fora (Open-Meteo, de graca e sem chave) e sai do Wi-Fi.
#   Amigos (sem internet): pelo radio ESP-NOW cada placa avisa "estou aqui" uma vez por segundo.
#     Sinal bem forte = as duas estao encostadas: fazem festa e trocam presentes.
# O Wi-Fi so fica ligado por alguns segundos de cada vez porque o ESP-NOW precisa que as duas
# placas estejam no mesmo canal (o 1); conectada ao roteador a placa iria para o canal dele.
import time, json, random

try:
    import network
except ImportError:
    network = None                      # MicroPython do computador (previa): sem radio

# ------------------------------------------------------------ ajustes
RSSI_PERTO = -45            # dBm: acima disso estao "bem pertinho" (uns dois palmos)
RSSI_LONGE = -58            # abaixo disso se afastaram
PING_MS = 1000
SUMIU_MS = 5000             # sem noticia por 5 s: foi embora
PRESENTES_POR_VISITA = 5    # 1 por minuto por 5 minutos
PRESENTE_MS = 60000
DESCANSO_MS = 600000        # depois dos 5 presentes, 10 min ate comecar outra rodada
CLIMA_MS = 1800000          # busca o tempo a cada 30 min
TENTAR_MS = 600000          # sem conseguir conectar: tenta de novo em 10 min
CONECTAR_MS = 15000
CLIMA_VALE_S = 3 * 3600     # previsao com mais de 3 h nao vale mais
CANAL = 1
TODOS = b'\xff\xff\xff\xff\xff\xff'
PRESENTES = ('caixa', 'flor', 'coracao', 'estrela', 'bola', 'capim')

sta = None                  # network.WLAN
en = None                   # espnow.ESPNow
eu = b''                    # meu endereco de radio
wifi = None                 # {'ssid', 'senha'} de wifi.json
internet_ok = False
offline = False             # radio desligado a pedido (3 toques no BOOT)
clima = {'cod': None, 'temp': None, 'vento': 0, 'epoch': 0, 'lat': None, 'lon': None, 'fuso': -3}
pares = {}                  # endereco -> dict do vizinho
_wx = None
_estado = 'parado'          # 'parado' ou 'conectando'
_proxima = 0                # quando tentar a internet de novo (ticks_ms)
_prazo = 0
_avisou_falha = False
_ping = 0
_seq = 0
_iniciado = False


# ------------------------------------------------------------ clima
def wx_de(cod, vento=0):
    """Codigo WMO -> forcas de 0 a 1 (a mesma tabela do Companion)."""
    w = {'nuvem': 0, 'chuva': 0, 'neve': 0, 'raio': 0, 'neblina': 0, 'vento': 0}
    c = int(cod)
    if c == 1:
        w['nuvem'] = 0.2
    elif c == 2:
        w['nuvem'] = 0.5
    elif c == 3:
        w['nuvem'] = 0.9
    elif c in (45, 48):
        w['neblina'] = 0.9; w['nuvem'] = 0.5
    elif 51 <= c <= 57:
        w['chuva'] = 0.3; w['nuvem'] = 0.8
    elif 61 <= c <= 67 or 80 <= c <= 82:
        w['chuva'] = 1 if c in (65, 67, 82) else (0.7 if c in (63, 81) else 0.45)
        w['nuvem'] = 0.9
    elif 71 <= c <= 77 or c in (85, 86):
        w['neve'] = 1 if c in (75, 86) else 0.6
        w['nuvem'] = 0.85
    elif c >= 95:
        w['raio'] = 1; w['chuva'] = 1; w['nuvem'] = 1; w['vento'] = 0.5
    w['vento'] = max(w['vento'], min(1, max(0, ((vento or 0) - 15) / 30)))
    return w


def tipo_de(w):
    """Nome curto do tempo, para a fala do bichinho."""
    if w['raio'] > 0.3:
        return 'tempestade'
    if w['neve'] > 0.3:
        return 'neve'
    if w['chuva'] > 0.2:
        return 'chuva'
    if w['neblina'] > 0.3:
        return 'neblina'
    if w['vento'] > 0.4:
        return 'vento'
    return 'nublado' if w['nuvem'] > 0.6 else 'sol'


def wx(epoch):
    """Clima para desenhar agora, ou None se nao ha previsao recente."""
    if _wx is None or not clima['epoch'] or abs(epoch - clima['epoch']) > CLIMA_VALE_S:
        return None
    return _wx


def _guardar_clima():
    global _wx
    _wx = wx_de(clima['cod'], clima['vento']) if clima['cod'] is not None else None
    try:
        with open('clima.json', 'w') as f:
            json.dump(clima, f)
    except Exception:
        pass


def _get(host, caminho):
    """GET simples por HTTP (sem TLS, para caber folgado na memoria). Devolve o JSON."""
    import socket
    s = socket.socket()
    try:
        s.settimeout(6)
        s.connect(socket.getaddrinfo(host, 80)[0][-1])
        s.send(('GET %s HTTP/1.0\r\nHost: %s\r\nUser-Agent: capigoshi\r\nConnection: close\r\n\r\n'
                % (caminho, host)).encode())
        dados = b''
        while len(dados) < 6000:
            p = s.recv(512)
            if not p:
                break
            dados += p
    finally:
        s.close()
    i = dados.find(b'\r\n\r\n')
    if i < 0 or dados[9:12] != b'200':
        raise OSError('resposta ruim de ' + host)
    return json.loads(dados[i + 4:])


def baixar_clima():
    """Descobre mais ou menos onde a placa esta (pelo endereco de internet) e pega o tempo de la."""
    if clima['lat'] is None:
        g = _get('ip-api.com', '/json/?fields=status,lat,lon')
        if g.get('status') != 'success':
            raise OSError('nao achei o lugar')
        clima['lat'], clima['lon'] = g['lat'], g['lon']
    r = _get('api.open-meteo.com', '/v1/forecast?latitude=%s&longitude=%s'
             '&current=temperature_2m,weather_code,wind_speed_10m&timezone=auto' % (clima['lat'], clima['lon']))
    c = r['current']
    clima['cod'], clima['temp'], clima['vento'] = c['weather_code'], c['temperature_2m'], c['wind_speed_10m']
    clima['fuso'] = r.get('utc_offset_seconds', -10800) / 3600


def _hora_da_internet():
    import ntptime
    ntptime.settime()
    return time.localtime(time.time() + int(clima['fuso'] * 3600))[:6]


# ------------------------------------------------------------ ligar
def iniciar():
    """Chame uma vez ao ligar. Sem radio (previa) ou sem wifi.json, o resto continua funcionando."""
    global sta, en, eu, wifi, _iniciado, _proxima
    _iniciado = True
    try:
        with open('clima.json') as f:
            clima.update(json.load(f))
        _guardar_clima()
    except Exception:
        pass
    ler_wifi()
    _proxima = time.ticks_add(time.ticks_ms(), 3000)
    if network is None:
        return
    try:
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        eu = sta.config('mac')
        _canal_dos_amigos()
        import espnow
        en = espnow.ESPNow()
        en.active(True)
        en.add_peer(TODOS)
    except Exception as e:
        print('Radio indisponivel:', e)
        en = None


def ler_wifi():
    global wifi
    try:
        with open('wifi.json') as f:
            w = json.load(f)
        wifi = w if w.get('ssid') else None
        if wifi and 'fuso' in wifi and not clima['epoch']:
            clima['fuso'] = wifi['fuso']
    except Exception:
        wifi = None


def situacao():
    """0 = sem Wi-Fi configurado ou offline, 1 = configurado, 2 = ja falou com a internet."""
    if offline:
        return 0
    return 2 if internet_ok else (1 if wifi else 0)


def ficar_offline(sim):
    """Desliga (ou religa) o radio inteiro: nada de internet nem de amigos por perto."""
    global offline, _estado, _proxima
    offline = sim
    _estado = 'parado'
    pares.clear()
    if sta is None:
        return
    try:
        if sim:
            sta.disconnect()
            if en is not None:
                en.active(False)
            sta.active(False)
        else:
            sta.active(True)
            _canal_dos_amigos()
            if en is not None:
                en.active(True)
                try:
                    en.add_peer(TODOS)
                except Exception:
                    pass                            # ja estava na lista
            _proxima = time.ticks_add(time.ticks_ms(), 2000)
    except Exception as e:
        print('Radio:', e)


def _canal_dos_amigos():
    try:
        sta.disconnect()                            # tambem para de tentar, se nao tinha conseguido
    except Exception:
        pass
    try:
        sta.config(channel=CANAL)
    except Exception:
        pass


def desligar_wifi():
    """Antes de abrir o portal de configuracao."""
    global _estado
    _estado = 'parado'
    if sta:
        _canal_dos_amigos()


# ------------------------------------------------------------ amigos
def amigo():
    """Personagem do amigo que esta mais pertinho agora, ou None."""
    melhor = None
    for p in pares.values():
        if p['perto'] and (melhor is None or p['rssi'] > melhor['rssi']):
            melhor = p
    return melhor['char'] if melhor else None


def _par(mac, agora):
    p = pares.get(mac)
    if p is None:
        if len(pares) >= 12:                        # feira de ciencias: esquece o mais antigo
            velho = min(pares, key=lambda m: pares[m]['visto'])
            pares.pop(velho)
        p = pares[mac] = {'rssi': -90.0, 'visto': agora, 'perto': False, 'char': 'capi', 'seguidos': 0,
                          'rodada': None, 'dados': 0, 'proximo': 0, 'seq': -1}
    return p


def _ouvir(agora, ev):
    while True:
        try:
            mac, msg = en.recv(0)
        except Exception:
            return
        if mac is None:
            return
        if not msg or len(msg) < 3 or msg[:2] != b'CG':
            continue
        mac = bytes(mac)
        p = _par(mac, agora)
        p['visto'] = agora
        if msg[2:3] == b'P':
            try:
                p['char'] = bytes(msg[3:15]).decode()
                forca = en.peers_table[mac][0]
            except Exception:
                continue
            p['rssi'] = forca if p['rssi'] <= -90 else p['rssi'] * 0.5 + forca * 0.5
            if not p['perto']:
                p['seguidos'] = p['seguidos'] + 1 if p['rssi'] >= RSSI_PERTO else 0
                if p['seguidos'] >= 2:
                    p['perto'] = True
                    descansou = p['rodada'] is None or time.ticks_diff(agora, p['rodada']) > DESCANSO_MS
                    if descansou:
                        p['rodada'], p['dados'] = agora, 0
                        p['proximo'] = time.ticks_add(agora, 3000)
                    ev.append(('chegou', p['char']))
            elif p['rssi'] < RSSI_LONGE:
                p['perto'], p['seguidos'] = False, 0
                ev.append(('saiu', p['char']))
        elif msg[2:3] == b'G' and len(msg) >= 11 and bytes(msg[3:9]) == eu:
            if msg[9] != p['seq']:                  # cada presente e mandado 2 vezes: conta um so
                p['seq'] = msg[9]
                ev.append(('presente', PRESENTES[msg[10] % len(PRESENTES)], p['char']))


def _falar(agora, char, acordado, ev):
    global _ping, _seq
    if time.ticks_diff(agora, _ping) < PING_MS:
        return
    _ping = time.ticks_add(agora, random.randint(0, 200))     # um pouquinho fora do compasso
    if acordado:
        try:
            en.send(TODOS, b'CGP' + char.encode(), False)
        except Exception:
            pass
    for mac, p in pares.items():
        if p['perto'] and time.ticks_diff(agora, p['visto']) > SUMIU_MS:
            p['perto'], p['seguidos'], p['rssi'] = False, 0, -90.0
            ev.append(('saiu', p['char']))
        if (acordado and p['perto'] and p['dados'] < PRESENTES_POR_VISITA
                and time.ticks_diff(agora, p['proximo']) >= 0):
            p['dados'] += 1
            p['proximo'] = time.ticks_add(agora, PRESENTE_MS)
            _seq = (_seq + 1) % 256
            k = random.randrange(len(PRESENTES))
            msg = b'CGG' + mac + bytes((_seq, k))
            try:
                en.send(TODOS, msg, False)
                en.send(TODOS, msg, False)
            except Exception:
                pass
            ev.append(('mandei', PRESENTES[k], p['char']))


# ------------------------------------------------------------ internet
def _internet(agora, epoch, ev):
    global _estado, _proxima, _prazo, internet_ok, _avisou_falha
    if _estado == 'parado':
        if time.ticks_diff(agora, _proxima) < 0:
            return
        try:
            sta.connect(wifi['ssid'], wifi.get('senha') or None)
        except Exception as e:
            print('Wi-Fi:', e)
            _proxima = time.ticks_add(agora, TENTAR_MS)
            return
        _estado, _prazo = 'conectando', time.ticks_add(agora, CONECTAR_MS)
        return
    if sta.isconnected():
        novo = False
        try:
            baixar_clima()
            clima['epoch'] = epoch
            novo = True
        except Exception as e:
            print('Clima:', e)
        try:
            t = _hora_da_internet()
            if novo:
                clima['epoch'] = time.mktime(t + (0, 0))   # a hora acabou de mudar: remarca a previsao
            ev.append(('hora', t))
            internet_ok = True
        except Exception as e:
            print('Hora:', e)
        if novo:
            _guardar_clima()
            ev.append(('clima', clima['temp'], tipo_de(_wx)))
        _proxima = time.ticks_add(agora, CLIMA_MS)
    elif time.ticks_diff(agora, _prazo) < 0:
        return
    else:
        _proxima = time.ticks_add(agora, TENTAR_MS)
        if not _avisou_falha:
            _avisou_falha = True
            ev.append(('sem_wifi',))
    _estado = 'parado'
    _canal_dos_amigos()


def passo(agora, epoch, char, acordado=True):
    """Chame a cada quadro (acordado=False para ovo e estrela: so escuta). Devolve os acontecimentos:
    ('chegou', personagem) ('saiu', personagem) ('mandei', presente, personagem)
    ('presente', presente, personagem) ('clima', graus, tipo) ('hora', (a, m, d, h, min, s)) ('sem_wifi',)"""
    ev = []
    if not _iniciado or offline:
        return ev
    if sta is not None and wifi:
        _internet(agora, epoch, ev)
    if en is not None:
        _ouvir(agora, ev)
        _falar(agora, char, acordado, ev)
    return ev
