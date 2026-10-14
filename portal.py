# portal.py - configurar o Wi-Fi pelo celular, do jeito das lampadas e cameras inteligentes.
# A placa vira uma rede aberta chamada "Capigoshi" e mostra um QR code. O celular le o QR,
# entra na rede e a pagina de configuracao abre sozinha (ou em 192.168.4.1). Ali a pessoa
# escolhe a rede de casa e digita a senha; a placa grava wifi.json e reinicia ja conectada.
import time, json
import desenho as d

REDE = 'Capigoshi'
IP = '192.168.4.1'
ESPERA_MS = 300000          # 5 min sem ninguem configurar: desiste e volta ao jogo
PORTA_WEB, PORTA_DNS = 80, 53

# QR code de "WIFI:T:nopass;S:Capigoshi;;" (versao 2, correcao L, 25 x 25).
# Um inteiro por linha; o bit mais alto e o quadradinho da esquerda. Se mudar REDE, gere outro.
QR = (0x1fc517f, 0x1054341, 0x174145d, 0x175de5d, 0x174875d, 0x105b241, 0x1fd557f, 0xe000,
      0x1f7bdaa, 0xf358a1, 0x1c5437f, 0x1c03473, 0x136efd8, 0x118b32d, 0x1440f53, 0x17134fa,
      0x1256df7, 0x1b91f, 0x1fdcd5f, 0x1045712, 0x175fff0, 0x175a5d3, 0x175daa9, 0x1059559,
      0x1fdbc97)

PASSO_1 = ('1. aponte a camera', 'do celular pro QR', '> rede: ' + REDE, 'BOOT cancela')
PASSO_2 = ('2. escolha sua rede', 'na pagina que abriu', '> ou abra ' + IP, 'BOOT cancela')

_CSS = ('body{margin:0;padding:20px 16px 40px;background:#bfe6ff;color:#3a2a10;'
        'font:18px/1.4 system-ui,sans-serif}main{max-width:420px;margin:0 auto}'
        'h1{font-size:1.7rem;margin:0 0 4px}p{margin:0 0 16px}'
        '.c{background:#fff6e4;border-radius:22px;padding:18px;box-shadow:0 6px 0 #7a4f2e}'
        'label{display:block;font-weight:700;margin:14px 0 6px}'
        'input{width:100%;box-sizing:border-box;min-height:48px;padding:10px 12px;font-size:18px;'
        'border:2px solid #7a4f2e;border-radius:12px;background:#fff}'
        '.r{display:flex;flex-wrap:wrap;gap:8px}'
        '.r button{min-height:44px;padding:0 14px;border:2px solid #7a4f2e;border-radius:999px;'
        'background:#fff;font-size:16px;color:#3a2a10}'
        '.ok{width:100%;min-height:54px;margin-top:20px;border:0;border-radius:14px;background:#1fb061;'
        'color:#fff;font-size:20px;font-weight:700;box-shadow:0 5px 0 #147842}'
        '.e{background:#e24b4a;color:#fff;border-radius:12px;padding:10px 12px}')


def _html(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _pagina(redes, erro=''):
    p = ['<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         '<title>Wi-Fi do Capigoshi</title><style>', _CSS, '</style><main>'
         '<h1>Oi! Me põe na internet? 🐾</h1>'
         '<p>Com Wi-Fi eu acerto a hora sozinho e fico sabendo se lá fora chove ou faz sol.</p>']
    if erro:
        p.append('<p class="e">%s</p>' % _html(erro))
    p.append('<form class="c" method="post" action="/salvar">')
    if redes:
        p.append('<label>Redes que eu achei</label><div class="r">')
        for r in redes:
            p.append('<button type="button">%s</button>' % _html(r))
        p.append('</div>')
    p.append('<label for="s">Nome da rede</label>'
             '<input id="s" name="ssid" maxlength="32" required autocapitalize="none" autocorrect="off">'
             '<label for="p">Senha</label>'
             '<input id="p" name="senha" type="password" maxlength="63" placeholder="vazia se a rede for aberta">'
             '<button class="ok">Conectar o bichinho!</button></form></main>'
             '<script>document.querySelectorAll(".r button").forEach(function(b){b.onclick=function(){'
             'document.getElementById("s").value=b.textContent;document.getElementById("p").focus()}})'
             '</script></html>')
    return ''.join(p)


def _pagina_salvo(ssid):
    return ('<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Prontinho!</title><style>' + _CSS + '</style><main><div class="c">'
            '<h1>Prontinho! 🎉</h1><p>Vou reiniciar e entrar na rede <b>' + _html(ssid) + '</b>.</p>'
            '<p>Se eu não conseguir, é só abrir o Wi-Fi do bichinho de novo e conferir a senha.</p>'
            '</div></main></html>')


def _decodificar(s):
    """Campo de formulario (application/x-www-form-urlencoded) para texto."""
    b = bytearray()
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == 0x2B:                               # '+'
            b.append(0x20)
        elif c == 0x25 and i + 2 < n:               # '%XX'
            try:
                b.append(int(bytes(s[i + 1:i + 3]), 16))
                i += 2
            except ValueError:
                b.append(c)
        else:
            b.append(c)
        i += 1
    try:
        return bytes(b).decode()
    except Exception:
        return ''


def formulario(corpo):
    """bytes 'a=1&b=2' -> {'a': '1', 'b': '2'}"""
    campos = {}
    for parte in corpo.split(b'&'):
        k, _, v = parte.partition(b'=')
        if k:
            campos[_decodificar(k)] = _decodificar(v)
    return campos


def resposta_dns(pergunta, ip=IP):
    """Responde qualquer nome com o IP da placa: e o que faz a pagina abrir sozinha no celular."""
    i, n = 12, len(pergunta)
    while i < n and pergunta[i]:                    # pula o nome perguntado (rotulos ate o zero)
        i += pergunta[i] + 1
    i += 5                                          # o zero, o tipo e a classe
    if n < 17 or i > n:
        return None
    return (pergunta[:2] + b'\x81\x80\x00\x01\x00\x01\x00\x00\x00\x00' + pergunta[12:i]
            + b'\xc0\x0c\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04' + bytes(int(x) for x in ip.split('.')))


def tratar(pedido, redes):
    """Pedido HTTP completo (bytes) -> (resposta em bytes, dados do Wi-Fi ou None)."""
    cab, _, corpo = pedido.partition(b'\r\n\r\n')
    linha = cab.split(b'\r\n')[0].split(b' ')
    metodo = linha[0]
    caminho = linha[1] if len(linha) > 1 else b'/'
    salvo = None
    if metodo == b'POST' and caminho.startswith(b'/salvar'):
        f = formulario(corpo)
        ssid, senha = f.get('ssid', '').strip(), f.get('senha', '')
        if not ssid or len(ssid.encode()) > 32:
            html = _pagina(redes, 'Faltou o nome da rede.')
        elif senha and not 8 <= len(senha.encode()) <= 63:
            html = _pagina(redes, 'A senha do Wi-Fi tem de 8 a 63 letras. Confere e tenta de novo?')
        else:
            salvo = {'ssid': ssid, 'senha': senha}
            html = _pagina_salvo(ssid)
    else:
        html = _pagina(redes)
    dados = html.encode()
    return (b'HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nCache-Control: no-store\r\n'
            b'Connection: close\r\nContent-Length: ' + str(len(dados)).encode() + b'\r\n\r\n' + dados), salvo


def _ler_pedido(c):
    dados = b''
    while b'\r\n\r\n' not in dados and len(dados) < 4096:
        p = c.recv(512)
        if not p:
            return dados
        dados += p
    cab, _, corpo = dados.partition(b'\r\n\r\n')
    falta = 0
    for l in cab.split(b'\r\n'):
        if l.lower().startswith(b'content-length:'):
            try:
                falta = min(1024, int(l.split(b':')[1])) - len(corpo)
            except ValueError:
                pass
    while falta > 0:
        p = c.recv(falta)
        if not p:
            break
        dados += p
        falta -= len(p)
    return dados


def _procurar_redes(sta):
    try:
        achadas = sorted(sta.scan(), key=lambda r: -r[3])
    except Exception:
        return []
    nomes = []
    for r in achadas:
        try:
            nome = r[0].decode()
        except Exception:
            continue
        if nome and nome != REDE and nome not in nomes:
            nomes.append(nome)
    return nomes[:10]


def _mostrar(tela, linhas, celular=False):
    d.tela_wifi(QR, linhas, celular)
    tela.mostrar()


def abrir(tela, botao=None):
    """Abre a rede de configuracao e espera. True = gravou wifi.json (quem chamou reinicia a placa);
    False = cancelado pelo botao BOOT ou ninguem configurou em 5 minutos."""
    import network, socket
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    _mostrar(tela, ('procurando', 'redes...'))
    redes = _procurar_redes(sta)
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    try:
        ap.config(ssid=REDE, security=0)
    except Exception:
        ap.config(essid=REDE, authmode=0)           # firmwares antigos
    dns = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    web = socket.socket()
    salvo = None
    try:
        dns.bind(socket.getaddrinfo('0.0.0.0', PORTA_DNS)[0][-1])
        dns.setblocking(False)
        web.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        web.bind(socket.getaddrinfo('0.0.0.0', PORTA_WEB)[0][-1])
        web.listen(2)
        web.setblocking(False)
        _mostrar(tela, PASSO_1)
        inicio = time.ticks_ms()
        tem_celular = False
        soltou = botao is None
        while time.ticks_diff(time.ticks_ms(), inicio) < ESPERA_MS:
            if botao is not None:
                v = botao.value()
                if v == 1:
                    soltou = True
                elif soltou:
                    break                            # apertou BOOT de novo: cancela
            try:
                agora_tem = len(ap.status('stations')) > 0
            except Exception:
                agora_tem = tem_celular
            if agora_tem != tem_celular:
                tem_celular = agora_tem
                _mostrar(tela, PASSO_2 if tem_celular else PASSO_1, tem_celular)
            try:
                pergunta, quem = dns.recvfrom(256)
                r = resposta_dns(pergunta)
                if r:
                    dns.sendto(r, quem)
            except OSError:
                pass
            try:
                c, _ = web.accept()
            except OSError:
                time.sleep_ms(20)
                continue
            try:
                c.settimeout(3)
                resposta, salvo = tratar(_ler_pedido(c), redes)
                c.sendall(resposta)
            except Exception as e:
                print('Portal Wi-Fi:', e)
            finally:
                c.close()
            if salvo:
                with open('wifi.json', 'w') as f:
                    json.dump(salvo, f)
                _mostrar(tela, ('> salvo!', 'reiniciando...'), True)
                time.sleep_ms(1500)                  # da tempo do celular mostrar a pagina
                break
    finally:
        web.close()
        dns.close()
        ap.active(False)
    return salvo is not None
