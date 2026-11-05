# Ponte entre o cerebro e a placa (fases 1 e 2 da fonte, secao 11): sentidos reais, um segundo de vida por vez,
# eventos do dono e persistencia em brain.bin. Nao importa nada da placa (hw, main): quem chama entrega os valores,
# entao roda igual no CPython (testes) e no MicroPython.
import os
import struct
from array import array
from companion import config as C
from companion import actions as A
from companion.cerebro import Cerebro, DORMIR, ACORDAR
from companion.expressao import EXPRESSAO

ARQ, BAK, TMP = 'brain.bin', 'brain.bak', 'brain.tmp'
MAGICO = b'CAPB'
VERSAO = 1
CAB = '<4sHIIIIBB'                 # magico, versao, semente, idade_s, segundo salvo, ticks, dormindo, afeto_ja_60
TIPOS = ('h', 'h', 'i', 'h', 'h', 'H', 'I', 'I')
SALVAR_S = 600                     # secao 9: grava a cada 10 min e ao dormir
ATRASO_MAX_S = 30                  # mais atrasado que isso (portal do Wi-Fi, gravacao): pula para agora
POR_PASSO = 2                      # segundos atrasados recuperados por quadro (cada um pode custar uma decisao)
DESLIGADA_MAX_MIN = 1440           # tempo desligada que os drives recuperam de uma vez (secao 4)
NOMES = tuple(a[0] for a in A.CATALOGO)
TOQUE_CURTO, TOQUE_LONGO, TOQUE_COLO = 0, 1, 2             # sentido toque_tipo
REG_CORPO, REG_FORA = 0, 1                                 # sentido toque_reg
MOV_LEVE, MOV_FORTE = 0, 1                                 # sentido mov
SOM_BARULHO = 0                                            # sentido som_evento


def _crc(dados):
    try:
        from binascii import crc32
    except ImportError:
        from zlib import crc32
    return crc32(dados) & 0xffffffff


def _blocos(cer):
    r = cer.rede
    return (r.w_ih, r.w_ho, r.th_h, cer.relogio.w, cer.drives.d, cer.rec.n, cer.vezes, cer.vezes_ontem)


def gravar(cer, agora_s, pasta=''):
    """brain.bin: cabecalho, blocos (tamanho + bytes) e crc32 no fim. Escreve em brain.tmp e troca, guardando a
    copia anterior em brain.bak: uma queda de energia no meio deixa sempre um arquivo inteiro."""
    d = cer.drives
    buf = bytearray(struct.pack(CAB, MAGICO, VERSAO, cer.semente, cer.idade_s, agora_s, cer.ticks_rodados,
                                1 if d.dormindo else 0, 1 if d.afeto_ja_60 else 0))
    for b in _blocos(cer):
        x = bytes(b)
        buf += struct.pack('<I', len(x))
        buf += x
    buf += struct.pack('<I', _crc(buf))
    with open(pasta + TMP, 'wb') as f:
        f.write(buf)
    try:
        os.remove(pasta + BAK)
    except OSError:
        pass
    try:
        os.rename(pasta + ARQ, pasta + BAK)
    except OSError:
        pass
    os.rename(pasta + TMP, pasta + ARQ)
    return len(buf)


def _ler(nome):
    """Cerebro do arquivo e o segundo em que foi salvo, ou None se faltar, estiver corrompido ou for de outra versao."""
    try:
        with open(nome, 'rb') as f:
            dados = f.read()
    except OSError:
        return None
    n = struct.calcsize(CAB)
    if len(dados) < n + 4 or struct.unpack('<I', dados[-4:])[0] != _crc(dados[:-4]):
        return None
    mag, ver, semente, idade, salvo, ticks, dorm, af60 = struct.unpack(CAB, dados[:n])
    if mag != MAGICO or ver != VERSAO:
        return None
    cer = Cerebro(semente)
    p = n
    for b, tipo in zip(_blocos(cer), TIPOS):
        tam = struct.unpack('<I', dados[p:p + 4])[0]
        novo = array(tipo, dados[p + 4:p + 4 + tam])
        if len(novo) != len(b):
            return None
        for k in range(len(b)):
            b[k] = novo[k]
        p += 4 + tam
    cer.idade_s, cer.ticks_rodados = idade, ticks
    cer.drives.dormindo, cer.drives.afeto_ja_60 = bool(dorm), bool(af60)
    return cer, salvo


def carregar(pasta=''):
    """(cerebro, segundo salvo) de brain.bin, ou da copia brain.bak se o principal estiver estragado."""
    return _ler(pasta + ARQ) or _ler(pasta + BAK)


def semente_nova():
    return int.from_bytes(os.urandom(2), 'little') % 65535 + 1


class Ponte:
    ACORDAR = ACORDAR
    QUIETAS = (A.QUIETA, A.INDICE['ficar_quieta_longa'])     # o vida.py passeia devagar no lugar

    def __init__(self, agora_s, pasta='', semente=None):
        """agora_s: segundos do relogio local (relogio.epoch()). Um segundo desses vira um segundo() do cerebro,
        entao a meia-noite e as horas cheias do cerebro batem com as do relogio."""
        self.pasta = pasta
        lido = carregar(pasta)
        if lido:
            self.cer, salvo = lido
            fora = agora_s - salvo
            if fora > 60:                          # desligada: o tempo passou para ela tambem
                self.cer.idade_s += fora
                self.cer.drives.avancar(min(fora // 60, DESLIGADA_MAX_MIN), False)
        else:
            self.cer = Cerebro(semente or semente_nova())
        self.seg = agora_s - 1                     # ultimo segundo entregue ao cerebro
        self.salvo = agora_s
        self.ult_toque = agora_s
        self.toques = []                           # segundos dos ultimos toques (sentido toques_60s)
        self.ev = {}                               # eventos para os sentidos do proximo segundo
        self.comida_ate = 0
        self.atual = A.QUIETA

    # ---- eventos do dono e do mundo
    def evento(self, nome, agora_s):
        """Nome da secao 6.3 (carinho, toque, estrela, shh, comida, sacudida_leve, sacudida_forte, barulho...)."""
        if nome in ('carinho', 'toque', 'estrela', 'shh', 'comida'):
            self.ult_toque = agora_s
            self.toques.append(agora_s)
        if nome == 'comida':
            self.comida_ate = agora_s + 60
        reg = REG_FORA if nome in ('toque', 'shh') else REG_CORPO
        tipo = {'estrela': TOQUE_LONGO, 'shh': TOQUE_LONGO, 'colo': TOQUE_COLO}.get(nome, TOQUE_CURTO)
        if nome in ('carinho', 'toque', 'estrela', 'shh', 'colo'):
            self.ev['toque_reg'], self.ev['toque_tipo'] = reg, tipo
        elif nome in ('sacudida_leve', 'sacudida_forte'):
            self.ev['mov'] = MOV_FORTE if nome == 'sacudida_forte' else MOV_LEVE
        elif nome == 'barulho':
            self.ev['som_evento'] = SOM_BARULHO
        if nome != 'colo':
            self.cer.evento(nome, agora_s * 1000)

    # ---- um quadro do laco principal
    def atrasada(self, agora_s):
        return agora_s > self.seg

    def passo(self, agora_s, leitura):
        """leitura: minuto, fim_semana, noite, bateria, carregando, som_nivel, tempo, graus, outra.
        Entrega ao cerebro os segundos que faltam (no maximo POR_PASSO por quadro) e devolve as acoes que comecaram."""
        if agora_s - self.seg > ATRASO_MAX_S or agora_s < self.seg:   # parada longa ou relogio acertado para tras
            self.seg = agora_s - 1
        novas = []
        cer = self.cer
        for _ in range(POR_PASSO):
            if self.seg >= agora_s:
                break
            self.seg += 1
            antes = len(cer.log)
            self.atual = cer.segundo(self._sentidos(self.seg, leitura), self.seg * 1000)
            for item in cer.log[antes:]:
                if item[0] == 'A':
                    novas.append(item[2])
            cer.log.clear()
            self.ev = {}
        if DORMIR in novas or agora_s - self.salvo >= SALVAR_S:
            self.salvar(agora_s)
        return novas

    def _sentidos(self, seg, l):
        self.toques = [t for t in self.toques if seg - t < 60]
        ev = self.ev
        s = {'minuto': l['minuto'], 'fim_semana': l['fim_semana'], 'toque_reg': ev.get('toque_reg'),
             'toque_tipo': ev.get('toque_tipo'), 'toques_60s': len(self.toques), 'sem_toque': max(0, seg - self.ult_toque),
             'mov': ev.get('mov'), 'orient': 0, 'som_nivel': l['som_nivel'], 'som_evento': ev.get('som_evento'),
             'noite': l['noite'], 'bateria': l['bateria'], 'carregando': l['carregando'], 'outra': l['outra'],
             'outra_estado': 0, 'novidade': 0, 'comida': seg < self.comida_ate, 'tempo': l['tempo'],
             'graus': l['graus'], 'wifi': 1 if l['tempo'] else 0}
        return s

    def salvar(self, agora_s):
        self.salvo = agora_s
        try:
            return gravar(self.cer, agora_s, self.pasta)
        except OSError as e:
            print('brain.bin:', e)
            return 0

    # ---- como a acao aparece
    def dormindo(self):
        return self.cer.drives.dormindo

    def expressao(self, acao, hora_txt='', clima_txt=''):
        """(movimento, fala, som) da acao, com hora, clima e humor resolvidos."""
        mov, fala, som = EXPRESSAO[NOMES[acao]]
        if fala == 'hora':
            fala = 'sao ' + hora_txt if hora_txt else None
        elif fala == 'clima':
            fala = clima_txt or None
        elif fala == 'humor':
            fala = humor_txt(self.cer.drives.get(C.D_HUMOR))
        return mov, fala, som


def humor_txt(h):
    if h > 50:
        return 'to muito|feliz!'
    if h > 15:
        return 'to feliz!'
    if h > -15:
        return 'to de boa'
    if h > -50:
        return 'to meio|triste...'
    return 'to triste...'
