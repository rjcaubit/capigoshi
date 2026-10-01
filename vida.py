# vida.py - comportamento do bichinho: escolhe movimentos, fala e reage a sacudida,
# barulho, toque e colo. Traducao do motor de "Capigoshi Diorama" (capigoshi-render.js).
# Tempos em ms de um relogio continuo (nao usa ticks_ms, que da a volta em alguns dias).
# Textos sem acento (fonte 8x8), no maximo 2 linhas x 14 letras ('|' quebra a linha).
import math, random

FEET = 205
IGNORADO_MS = 600000        # 10 min sem atencao: chora e chama
ACORDA_MS = 60000           # barulho, sacudida ou toque dormindo: fica 1 min acordado
HTOP = {'capi': 77, 'pato': 95, 'elefante': 75, 'polvo': 71, 'calopsita': 84, 'cachorro': 75,
        'gato': 75, 'et': 81, 'sapinho': 65}
NOMES = {'capi': 'Capi', 'pato': 'Pato', 'elefante': 'Elefante', 'polvo': 'Polvo', 'calopsita': 'Calopsita',
         'cachorro': 'Caramelo', 'gato': 'Gato', 'et': 'ET', 'sapinho': 'Sapinho'}


# ------------------------------------------------------------ curvas
def cl01(v):
    return 0.0 if v < 0 else (1.0 if v > 1 else v)


def seg(u, a, b):
    return cl01((u - a) / (b - a))


def ez(u):
    return u * u * (3 - 2 * u)


def bump(u):
    return math.sin(math.pi * cl01(u))


def jit(ms, p):
    return 1 if (int(ms) // p) % 2 else -1


def _cl(v, a, b):
    return a if v < a else (b if v > b else v)


# ------------------------------------------------------------ os movimentos
# Cada um: f(u 0..1, ms) -> {dx, dy, sx, sy, flip, eyes, mouth, hide, rot, fx}
def m_olhar(u, ms):
    L, R = 0.15 < u < 0.5, 0.5 <= u < 0.85
    o = {'flip': -1 if L else 1, 'dx': -2 if L else (2 if R else 0), 'sx': 0.94 if (L or R) else 1}
    if L or R:
        o['mouth'] = 'o'
    if u > 0.82:
        o['fx'] = ('interroga',)
    return o


def m_espreguicar(u, ms):
    if u < 0.18:
        k = ez(u / 0.18)
        return {'sy': 1 - 0.1 * k, 'sx': 1 + 0.08 * k}
    if u < 0.7:
        k = ez(seg(u, 0.18, 0.32))
        return {'sy': 0.9 + 0.26 * k, 'sx': 1.08 - 0.16 * k, 'eyes': 'fechados', 'mouth': 'o',
                'dx': jit(ms, 60) * 0.6 if u > 0.45 else 0}
    k = ez(seg(u, 0.7, 0.86))
    return {'sy': 1.16 - 0.16 * k, 'sx': 0.92 + 0.08 * k, 'eyes': 'fechados' if k < 1 else 'feliz'}


def m_bocejar(u, ms):
    a = seg(u, 0.15, 0.75)
    if u < 0.15:
        return {'eyes': 'sono', 'mouth': 'o'}
    if u < 0.75:
        return {'eyes': 'fechados', 'mouth': 'aberta', 'sy': 1 + 0.07 * bump(a), 'sx': 1 - 0.03 * bump(a)}
    return {'eyes': 'sono' if u < 0.9 else 'normal', 'mouth': 'meia', 'fx': ('lagrima',) if u < 0.92 else ()}


def m_dancar(u, ms):
    k = 1 - seg(u, 0.92, 1)
    return {'dx': math.sin(ms / 260) * 7 * k, 'flip': 1 if math.sin(ms / 520) >= 0 else -1,
            'dy': -abs(math.cos(ms / 260)) * 5 * k, 'sx': 1 + 0.05 * math.cos(ms / 130) * k,
            'sy': 1 - 0.05 * math.cos(ms / 130) * k, 'eyes': 'feliz',
            'mouth': 'aberta' if (int(ms) // 520) % 2 else 'sorriso', 'fx': ('notas',) if k > 0 else ()}


def m_girar(u, ms):
    a = ez(seg(u, 0.05, 0.85)) * 4 * math.pi
    c = math.cos(a)
    return {'sx': max(0.14, abs(c)), 'flip': -1 if c < 0 else 1, 'dy': -bump(seg(u, 0.05, 0.85)) * 10,
            'eyes': 'feliz', 'mouth': 'aberta' if u < 0.85 else 'sorriso', 'fx': ('brilho',) if u > 0.7 else ()}


def m_comemorar(u, ms):
    h = seg(u, 0, 0.8) * 3
    f = h % 1
    if h >= 3:
        return {'eyes': 'feliz', 'fx': ('confete',) if u < 0.95 else ()}
    land = f < 0.1 or f > 0.9
    return {'dy': -math.sin(math.pi * f) * 18, 'sy': 0.88 if land else 1.04, 'sx': 1.08 if land else 0.97,
            'eyes': 'feliz', 'mouth': 'aberta', 'fx': ('confete',)}


def m_tropecar(u, ms):
    if u < 0.15:
        return {'dx': seg(u, 0, 0.15) * 10, 'dy': -abs(math.sin(ms / 120)) * 2}
    if u < 0.28:
        k = seg(u, 0.15, 0.28)
        return {'dx': 10 + k * 6, 'sx': 1 + 0.1 * k, 'sy': 1 - 0.15 * k, 'dy': -k * 6, 'eyes': 'susto', 'mouth': 'o'}
    if u < 0.65:
        return {'dx': 16, 'sy': 0.62, 'sx': 1.28, 'eyes': 'fechados', 'mouth': 'triste',
                'fx': ('poeira', 'estrelas') if u < 0.45 else ('estrelas',)}
    if u < 0.8:
        k = seg(u, 0.65, 0.8)
        return {'dx': 16, 'sy': 0.62 + 0.38 * ez(k), 'sx': 1.28 - 0.28 * ez(k), 'dy': -bump(k) * 8}
    k = ez(seg(u, 0.8, 1))
    return {'dx': 16 * (1 - k), 'flip': -1 if k < 1 else 1, 'dy': -abs(math.sin(ms / 120)) * 2 if k < 1 else 0}


def m_tremer(u, ms):
    on = u < 0.92
    o = {'dx': jit(ms, 45) * 1.5 if on else 0, 'sy': 0.95 if on else 1, 'sx': 1.03 if on else 1,
         'fx': ('frio',) if on else ()}
    if on:
        o['mouth'] = 'meia'
    return o


def m_cochilar(u, ms):
    if u < 0.2:
        return {'eyes': 'sono', 'mouth': 'meia', 'sy': 1 - 0.04 * seg(u, 0, 0.2)}
    if u < 0.75:
        return {'eyes': 'fechados', 'mouth': 'dormindo', 'sy': 0.96 + 0.025 * math.sin(ms / 450),
                'dy': max(0, math.sin(ms / 700)) * 2, 'fx': ('zz',)}
    if u < 0.83:
        k = seg(u, 0.75, 0.83)
        return {'eyes': 'susto', 'mouth': 'o', 'dy': -bump(k) * 7, 'sy': 1.05}
    return {'eyes': 'sono' if u < 0.93 else 'normal'}


def m_espirrar(u, ms):
    if u < 0.5:
        k = seg(u, 0, 0.5)
        return {'sy': 1 + 0.1 * ez(k), 'sx': 1 - 0.05 * k, 'dx': -3 * k, 'eyes': 'sono' if k < 0.5 else 'fechados',
                'mouth': 'o'}
    if u < 0.62:
        return {'sy': 0.84, 'sx': 1.14, 'dx': 4, 'eyes': 'fechados', 'mouth': 'aberta', 'fx': ('espirro',)}
    k = seg(u, 0.62, 1)
    return {'sy': 0.84 + 0.16 * ez(k), 'sx': 1.14 - 0.14 * ez(k), 'dx': 4 * (1 - ez(k)),
            'eyes': 'susto' if k < 0.5 else 'normal', 'mouth': 'o' if k < 0.5 else 'sorriso',
            'fx': ('espirro',) if k < 0.3 else ()}


def m_soluco(u, ms):
    s = 0
    for c in (0.12, 0.42, 0.72):
        s = max(s, bump(seg(u, c, c + 0.09)))
    return {'dy': -7 * s, 'sy': 1 + 0.08 * s, 'sx': 1 - 0.04 * s, 'eyes': 'susto' if s > 0.2 else 'normal',
            'mouth': 'o' if s > 0.2 else 'meia', 'fx': ('hic',) if s > 0.1 else ()}


def m_rir(u, ms):
    on = u < 0.9
    return {'dy': -abs(math.sin(ms / 85)) * 3 if on else 0, 'sx': 1 + 0.04 * math.sin(ms / 85) if on else 1,
            'eyes': 'feliz', 'mouth': ('aberta' if (int(ms) // 170) % 2 else 'meia') if on else 'sorriso',
            'fx': ('ha',) if on else ()}


def m_chorar(u, ms):
    on = u < 0.9
    return {'eyes': 'fechados' if on else 'normal', 'mouth': 'triste', 'dy': (int(ms) // 380) % 2 if on else 0,
            'sy': 0.97 if on else 1, 'fx': ('lagrimas',) if on else ()}


def m_susto(u, ms):
    if u < 0.08:
        return {'sy': 0.85, 'sx': 1.1, 'eyes': 'susto', 'mouth': 'o'}
    if u < 0.45:
        k = seg(u, 0.08, 0.45)
        return {'dy': -bump(k) * 26, 'sy': 1.12 - 0.12 * k, 'sx': 0.9 + 0.1 * k, 'eyes': 'susto', 'mouth': 'o',
                'fx': ('exclama',)}
    if u < 0.55:
        return {'sy': 0.86, 'sx': 1.1, 'eyes': 'susto', 'mouth': 'o', 'fx': ('exclama',)}
    return {'eyes': 'susto' if u < 0.85 else 'normal', 'mouth': 'o' if u < 0.85 else 'sorriso',
            'dx': jit(ms, 50) * 0.8 if u < 0.8 else 0, 'fx': ('exclama',) if u < 0.8 else ()}


def m_tonto(u, ms):
    k = 1 - seg(u, 0.85, 1)
    return {'dx': math.sin(ms / 320) * 5 * k, 'flip': 1 if math.sin(ms / 640) >= 0 else -1,
            'sx': 1 - 0.05 * abs(math.sin(ms / 320)) * k, 'eyes': 'sono' if k > 0 else 'normal',
            'mouth': 'meia' if k > 0 else 'sorriso', 'fx': ('estrelas',) if u < 0.88 else ()}


def m_chegar_perto(u, ms):
    k = ez(seg(u, 0, 0.3)) * (1 - ez(seg(u, 0.78, 1)))
    s = 1 + 0.8 * k
    return {'sx': s, 'sy': s, 'dy': 20 * k, 'eyes': 'feliz' if 0.3 < u < 0.78 else 'normal',
            'mouth': 'aberta' if 0.32 < u < 0.5 else 'sorriso', 'fx': ('bafo',) if 0.5 < u < 0.78 else ()}


def m_esconder(u, ms):
    if u < 0.12:
        return {'sy': 0.9 + 0.1 * abs(math.sin(ms / 70)), 'eyes': 'fechados', 'mouth': 'meia', 'fx': ('buraco', 'terra')}
    if u < 0.25:
        return {'hide': 0.8 * ez(seg(u, 0.12, 0.25)), 'fx': ('buraco',)}
    if u < 0.75:
        return {'hide': 0.8 - 0.25 * bump(seg(u, 0.38, 0.62)), 'fx': ('buraco',)}
    if u < 0.9:
        k = seg(u, 0.75, 0.9)
        return {'hide': 0.8 * (1 - ez(k)), 'dy': -bump(seg(u, 0.75, 0.95)) * 16, 'eyes': 'feliz', 'mouth': 'aberta',
                'fx': ('buraco', 'terra')}
    return {'dy': -bump(seg(u, 0.75, 0.95)) * 16, 'eyes': 'feliz', 'fx': ('buraco',) if u < 0.96 else ()}


def m_cavar(u, ms):
    if u < 0.75:
        return {'sy': 1 - 0.08 * abs(math.sin(ms / 80)), 'sx': 1 + 0.04 * abs(math.sin(ms / 80)),
                'dx': math.sin(ms / 80), 'mouth': 'meia', 'fx': ('buraco', 'terra')}
    k = seg(u, 0.75, 1)
    return {'dy': -bump(k) * 10, 'eyes': 'feliz', 'mouth': 'aberta', 'fx': ('buraco', 'achado')}


def m_cheirar_flor(u, ms):
    if u < 0.2:
        return {'dx': 6 * ez(u / 0.2), 'fx': ('flor',)}
    if u < 0.7:
        return {'dx': 6, 'sx': 1.05, 'sy': 0.95 + 0.02 * math.sin(ms / 120), 'eyes': 'fechados', 'mouth': 'o',
                'fx': ('flor',)}
    if u < 0.85:
        return {'dx': 6, 'eyes': 'feliz', 'fx': ('flor', 'coracoes')}
    return {'dx': 6 * (1 - ez(seg(u, 0.85, 1))), 'eyes': 'feliz',
            'fx': ('flor', 'coracoes') if u < 0.95 else ('flor',)}


def m_cambalhota(u, ms):
    if u < 0.15:
        k = ez(u / 0.15)
        return {'sy': 1 - 0.14 * k, 'sx': 1 + 0.1 * k, 'eyes': 'fechados', 'mouth': 'meia'}
    if u < 0.55:
        k = seg(u, 0.15, 0.55)
        return {'rot': ez(k) * 2 * math.pi, 'dx': k * 26, 'dy': -bump(k) * 30, 'sx': 0.94, 'sy': 1.04,
                'eyes': 'feliz', 'mouth': 'aberta', 'fx': ('brilho',) if k > 0.6 else ()}
    if u < 0.65:
        return {'dx': 26, 'sy': 0.84, 'sx': 1.14, 'eyes': 'susto', 'mouth': 'o', 'fx': ('poeira',)}
    if u < 0.75:
        return {'dx': 26, 'eyes': 'feliz', 'mouth': 'aberta'}
    k = ez(seg(u, 0.75, 1))
    return {'dx': 26 * (1 - k), 'flip': -1 if k < 1 else 1, 'dy': -abs(math.sin(ms / 140)) * 2.5 if k < 1 else 0,
            'eyes': 'feliz'}


def m_pular(u, ms):
    k = (ms % 820) / 820
    land = k < 0.08 or k > 0.92
    if u >= 1:
        return {'eyes': 'feliz'}
    return {'dy': -bump(k) * 20, 'sy': 0.9 if land else 1.03, 'sx': 1.07 if land else 0.98, 'eyes': 'feliz'}


def m_aterrissar(u, ms):
    k = ez(seg(u, 0.3, 1))
    return {'sy': 0.82 if u < 0.3 else 0.82 + 0.18 * k, 'sx': 1.15 if u < 0.3 else 1.15 - 0.15 * k,
            'eyes': 'susto' if u < 0.6 else 'normal', 'mouth': 'o', 'fx': ('poeira',) if u < 0.5 else ()}


# nome: (duracao ms, funcao)   'andar' e tratado a parte em passo()
MOVES = {
    'andar': (4000, None), 'olhar': (3600, m_olhar), 'espreguicar': (3400, m_espreguicar),
    'bocejar': (3000, m_bocejar), 'dancar': (4200, m_dancar), 'girar': (1800, m_girar),
    'comemorar': (2600, m_comemorar), 'tropecar': (3400, m_tropecar), 'tremer': (3000, m_tremer),
    'cochilar': (4400, m_cochilar), 'espirrar': (2600, m_espirrar), 'soluco': (3200, m_soluco),
    'rir': (2600, m_rir), 'chorar': (3600, m_chorar), 'susto': (1800, m_susto), 'tonto': (3600, m_tonto),
    'chegarPerto': (3200, m_chegar_perto), 'esconder': (4600, m_esconder), 'cavar': (3400, m_cavar),
    'cheirarFlor': (3800, m_cheirar_flor), 'cambalhota': (2400, m_cambalhota), 'pular': (2460, m_pular),
    'aterrissar': (700, m_aterrissar),
}

# fala do proprio movimento: (chance, atraso ms, tipo, frases)
MOVE_FALAS = {
    'andar': (0.3, 0, 'say', ('vou ali|e ja volto', 'passeando...', 'um, dois,|um, dois')),
    'olhar': (0.5, 0, 'say', ('ouvi algo?', 'cade todo|mundo?', 'hmm...')),
    'espreguicar': (0.6, 1500, 'say', ('aaah...|que bom', 'estiiica!')),
    'bocejar': (0.7, 500, 'say', ('aaaahm...', 'que sono...')),
    'dancar': (0.6, 0, 'say', ('la la la!', 'danca|comigo!', 'tum tum tss')),
    'girar': (0.7, 0, 'shout', ('wiii!', 'uiii!')),
    'comemorar': (0.7, 0, 'shout', ('uhuu!', 'viva!', 'eba!')),
    'tropecar': (0.9, 2300, 'say', ('to bem!|to bem!', 'tropecei...', 'quem botou|isso ai?')),
    'tremer': (0.8, 0, 'say', ('brrr...', 'que frio!')),
    'cochilar': (0.6, 800, 'say', ('so 5|minutinhos', 'zzz...')),
    'espirrar': (1.0, 1300, 'shout', ('atchim!',)),
    'soluco': (0.8, 400, 'say', ('hic!', 'hic! que|soluco!')),
    'rir': (0.6, 0, 'say', ('hahaha!', 'hihihi!')),
    'chorar': (0.8, 0, 'say', ('buaaa!', 'quero colo...')),
    'susto': (0.8, 0, 'shout', ('ah!', 'ui!')),
    'tonto': (0.7, 0, 'say', ('to tonto...', 'tudo|girando...')),
    'chegarPerto': (0.9, 900, 'say', ('oi! ta me|vendo?', 'que vidro|sujo...', 'to aqui|dentro!')),
    'esconder': (0.9, 3500, 'shout', ('achou!', 'buu!')),
    'cavar': (0.9, 2600, 'say', ('achei um|tesouro!', 'olha o que|eu achei!')),
    'cheirarFlor': (0.8, 2400, 'say', ('que|cheirinho!', 'uma flor!|pra voce')),
    'cambalhota': (0.8, 1500, 'say', ('tcharam!', 'viu essa?', 'de novo?|de novo!')),
    'pular': (0.4, 0, 'shout', ('upa!', 'boing!')),
}

FRASES = {
    'ocioso': ('que dia|bonito!', 'brinca|comigo?', 'oi, amigo!', 'hmm...', 'que tedio...', 'vamos|passear?',
               'tive uma|ideia!', 'esqueci a|ideia...', 'conta uma|historia?', 'me da um|abraco?', 'olha o ceu!',
               'to com fome?|acho que sim'),
    'manha': ('bom dia!', 'acordei!', 'que solzinho!', 'cafe da|manha?'),
    'dia': ('que calor!', 'hora de|brincar!', 'dia lindo!'),
    'noite': ('que sono...', 'boa noite,|lua!', 'ta escuro...', 'conta|estrelas?'),
    'sacudido': ('socorro!', 'aaaah!', 'para!', 'uoooh!', 'iiih!', 'epa!'),
    'depoisSacudir': ('to tonto...', 'o mundo|ta girando', 'de novo!|de novo!', 'quase|voei!', 'onde eu|to?',
                      'que|terremoto!'),
    'sacudidoMuito': ('to enjoado...', 'chega de|sacudir!', 'minha cabeca|ta rodando'),
    'barulhoGrito': ('ui!', 'ah!', 'epa!'),
    'barulho': ('que foi|isso?!', 'quem ta ai?', 'ai que|susto!', 'trovao?!', 'ouvi alguma|coisa...',
                'shhh!|silencio!'),
    'barulhoDormindo': ('zzz... que?', 'me|acordou...', 'ja e de|manha?', 'sonhei com|um barulho'),
    'barulhoRepetido': ('que|barulheira!', 'meus|ouvidos!', 'fala mais|baixo!'),
    'carinho': ('hihi!', 'cosquinha!', 'faz de novo!', 'gostei!', 'que bom!', 'eba!'),
    'carinhoDemais': ('chega de|cosquinha!', 'ta bom, ta|bom!', 'hahaha|para!'),
    'pego': ('me solta!', 'to voando!', 'que alto!', 'cuidado!'),
    'solto': ('ufa!', 'chao! que|bom', 'de novo?'),
    'ignorado': ('ei! to|aqui!', 'alguem?', 'to sozinho...', 'olha pra|mim!'),
    'voltou': ('voce voltou!', 'que saudade!'),
    'acordou': ('ja e de|manha?', 'hmm...|5 minutinhos'),
    'toqueFora': ('ouvi algo?', 'quem ta ai?', 'hein?'),
    'dormir': ('vou dormir...', 'boa noite!'),
}

FRASES_CHAR = {
    'capi': {'ocioso': ('quero|capim', 'vamos nadar?', 'meus fones|sao novos', 'sossego...', 'ouvindo|musica'),
             'carinho': ('hmmm|que bom', 'capi feliz!')},
    'elefante': {'ocioso': ('trouxe|melancia!', 'prruu!', 'tromba|cheirosa', 'abraco de|elefante!', 'nunca|esqueco nada'),
                 'carinho': ('abraco!', 'prruu!|gostei')},
    'pato': {'ocioso': ('vi um cometa!', 'abracadabra!', 'meu chapeu|e magico', 'quack quack!', 'achei uma|pedrinha'),
             'carinho': ('quack!', 'magia!')},
    'polvo': {'ocioso': ('tenho 8|abracos!', 'blub blub', 'vou mergulhar', 'adoro o lago', 'tinta? hoje|nao'),
              'carinho': ('abraco de|polvo!', 'blub!')},
    'calopsita': {'ocioso': ('fiu fiu!', 'bom dia, bom|dia!', 'canta comigo', 'meu topete|ta lindo?', 'piu!'),
                  'carinho': ('piu piu!', 'fiu!|gostei')},
    'cachorro': {'ocioso': ('bora brincar?', 'joga a bola!', 'au au!', 'cade meu|osso?', 'rabinho|feliz!'),
                 'carinho': ('au! mais!', 'barriguinha!')},
    'gato': {'ocioso': ('quero|sardinha', 'miau...', 'hora da|soneca', 'nao me|perturbe', 'ronron...'),
             'carinho': ('ronron...', 'so mais|um pouco')},
    'et': {'ocioso': ('leve-me ao|seu lider', 'blip blop!', 'saudade de|marte', 'terraqueo|legal!', 'bip bip!'),
           'carinho': ('blip!|gostei', 'cosquinha|alienigena')},
    'sapinho': {'ocioso': ('pula comigo!', 'croac!', 'mosca? onde?', 'o lago e|meu', 'boing boing!'),
                'carinho': ('croac!', 'pulo de|alegria!')},
}

POOLS = {
    'manha': ('espreguicar', 'espreguicar', 'bocejar', 'bocejar', 'andar', 'andar', 'olhar', 'dancar',
              'cheirarFlor', 'pular', 'cavar'),
    'dia': ('andar', 'andar', 'andar', 'olhar', 'olhar', 'dancar', 'girar', 'comemorar', 'cheirarFlor',
            'cheirarFlor', 'cavar', 'esconder', 'chegarPerto', 'espreguicar', 'rir', 'soluco', 'espirrar',
            'tropecar', 'pular', 'pular', 'cambalhota', 'cambalhota'),
    'noite': ('bocejar', 'bocejar', 'cochilar', 'cochilar', 'tremer', 'tremer', 'olhar', 'andar',
              'chegarPerto', 'espirrar'),
}


def periodo(h):
    if 5 <= h < 9:
        return 'manha'
    if 9 <= h < 18:
        return 'dia'
    return 'noite'


def _rnd(a, b):
    return a + random.random() * (b - a)


def _escolher(L, lista):
    if not lista:
        return ''
    s = ''
    for _ in range(5):
        s = random.choice(lista)
        if s not in L['recent']:
            break
    L['recent'].append(s)
    if len(L['recent']) > 8:
        L['recent'].pop(0)
    return s


# ------------------------------------------------------------ estado
def nova(char, agora, x=110.0):
    return {'char': char, 'x': float(x), 'move': None, 'lastMove': '', 'queue': [], 'bubble': None,
            'pend': None, 'recent': [], 'lastTouch': agora, 'nextIdle': agora + 1500, 'taps': [],
            'shakes': [], 'noises': [], 'grab': None, 'fall': None, 'shakeUntil': 0, 'shakeStart': 0,
            'shakeAmp': 1.0, 'awakeUntil': 0, 'asleep': False, 'goingSleep': False, 'lastNoise': -10 ** 9,
            'lastSad': 0}


def falar(L, agora, texto, tipo='say'):
    if not texto:
        return
    n = len(texto.replace('|', ''))
    ate = agora + (1400 if tipo == 'shout' else max(2500, 400 + n * 80))
    L['bubble'] = (tipo, texto, agora, ate)


def tocar(L, agora, id, say=None, shout=None, at=0, auto=False, force=False):
    if id not in MOVES:
        return
    m = {'id': id, 't0': agora, 'dur': MOVES[id][0]}
    if id == 'andar':
        x1 = L['x']
        for _ in range(8):
            if abs(x1 - L['x']) >= 30:
                break
            x1 = 40 + random.random() * 125
        m['x0'], m['x1'] = L['x'], x1
        m['dur'] = max(1400, abs(x1 - L['x']) * 32) * (2 if L.get('lento') else 1)   # idoso anda devagar
    L['move'] = m
    L['lastMove'] = id
    L['pend'] = None
    if shout:
        falar(L, agora, shout, 'shout')
    texto, tipo = say, 'say'
    if not texto and auto and id in MOVE_FALAS:
        p, at_f, tipo_f, lista = MOVE_FALAS[id]
        if force or random.random() < p:
            texto, tipo, at = _escolher(L, lista), tipo_f, at_f
    if texto:
        if at:
            L['pend'] = (agora + at, texto, tipo)
        else:
            falar(L, agora, texto, tipo)


def _ocioso(L, agora, per):
    pool = POOLS.get(per, POOLS['dia'])
    id = pool[0]
    for _ in range(5):
        id = random.choice(pool)
        if id != L['lastMove']:
            break
    r = random.random()
    if r < 0.4:
        tocar(L, agora, id, auto=True)
    elif r < 0.65:
        c = FRASES_CHAR.get(L['char'], {}).get('ocioso', ())
        q = random.random()
        lista = c if (q < 0.5 and c) else (FRASES[per] if q < 0.75 else FRASES['ocioso'])
        tocar(L, agora, id, say=_escolher(L, lista), at=300)
    else:
        tocar(L, agora, id)


def acordar(L, agora, ms=None):
    L['asleep'] = False
    L['goingSleep'] = False
    L['awakeUntil'] = max(L['awakeUntil'], agora + (ms or ACORDA_MS))


# ------------------------------------------------------------ eventos
def sacudir(L, agora, amp=1.0, dur=500):
    if L['fall']:
        return
    primeiro = agora >= L['shakeUntil']
    L['shakeUntil'] = max(L['shakeUntil'], agora + dur)
    L['shakeAmp'] = _cl(amp if primeiro else max(L['shakeAmp'] * 0.9, amp), 0.5, 1.5)
    L['lastTouch'] = agora
    if primeiro and not L['shakeStart']:
        L['shakeStart'] = agora
        L['shakes'] = [x for x in L['shakes'] if agora - x < 30000] + [agora]
        L['move'] = None
        L['queue'] = []
        L['pend'] = None
        acordar(L, agora)
        falar(L, agora, _escolher(L, FRASES['sacudido']), 'shout')


def barulho(L, agora):
    if agora - L['lastNoise'] < 1500 or L['grab'] or agora < L['shakeUntil']:
        return
    L['lastNoise'] = agora
    L['noises'] = [x for x in L['noises'] if agora - x < 12000] + [agora]
    L['lastTouch'] = agora
    if L['asleep'] or L['goingSleep']:
        acordar(L, agora)
        tocar(L, agora, 'susto', shout='hein?!')
        L['queue'] = [{'say': _escolher(L, FRASES['barulhoDormindo'])}]
        return
    muitos = len(L['noises']) >= 3
    tocar(L, agora, 'susto', shout=_escolher(L, FRASES['barulhoGrito']))
    if muitos:
        L['queue'] = [{'say': _escolher(L, FRASES['barulhoRepetido'])}]
    else:
        L['queue'] = [{'id': 'olhar', 'say': _escolher(L, FRASES['barulho'])}]


def toque(L, agora, no_corpo):
    L['lastTouch'] = agora
    if L['asleep']:
        acordar(L, agora)
        L['queue'] = []
        tocar(L, agora, 'espreguicar', say=_escolher(L, FRASES['acordou']))
        return
    if not no_corpo:
        if not L['move']:
            tocar(L, agora, 'olhar', say=_escolher(L, FRASES['toqueFora']))
        return
    L['queue'] = []
    L['taps'] = [x for x in L['taps'] if agora - x < 4000] + [agora]
    if len(L['taps']) == 3 and random.random() < 0.5:
        tocar(L, agora, 'cambalhota', say=_escolher(L, ('olha so|o que sei!', 'tcharam!')))
    elif len(L['taps']) >= 5:
        L['taps'] = []
        tocar(L, agora, 'rir', say=_escolher(L, FRASES['carinhoDemais']))
    elif L['lastSad'] and agora - L['lastSad'] < 20000:
        L['lastSad'] = 0
        tocar(L, agora, 'comemorar', say=_escolher(L, FRASES['voltou']))
    else:
        c = FRASES_CHAR.get(L['char'], {}).get('carinho', ())
        lista = c if (random.random() < 0.5 and c) else FRASES['carinho']
        tocar(L, agora, 'rir' if random.random() < 0.6 else 'comemorar', say=_escolher(L, lista))


def pegar(L, agora, x, y):
    L['grab'] = {'x': x, 'y': y, 'ox': L['x'] - x, 'oy': FEET - y, 't0': agora, 'said': False, 'lx': x,
                 'dir': 0, 'rev': []}
    L['move'] = None
    L['queue'] = []
    L['pend'] = None
    L['lastTouch'] = agora
    acordar(L, agora)


def arrastar(L, agora, x, y):
    G = L['grab']
    if not G:
        return
    vx = x - G['lx']
    G['lx'] = G['x'] = x
    G['y'] = y
    if abs(vx) > 2.5:
        d = 1 if vx > 0 else -1
        if G['dir'] and d != G['dir']:
            G['rev'].append(agora)
        G['dir'] = d
    G['rev'] = [t for t in G['rev'] if agora - t < 700]
    if len(G['rev']) >= 3:                       # vai e volta rapido no colo = sacudir
        sacudir(L, agora, _cl(abs(vx) / 8 + 0.6, 0.6, 1.5), 300)


def soltar(L, agora):
    G = L['grab']
    if not G:
        return
    L['grab'] = None
    L['lastTouch'] = agora
    L['x'] = _cl(G['x'] + G['ox'], 40, 165)
    dy0 = min(0, G['y'] + G['oy'] - FEET)
    if dy0 < -4:
        L['fall'] = {'t0': agora, 'dy0': dy0}
    else:
        tocar(L, agora, 'aterrissar')
    if not L['shakeStart']:
        L['queue'] = [{'say': _escolher(L, FRASES['solto'])}]


def trocar(L, agora, id):
    L['char'] = id
    L['queue'] = []
    L['shakeStart'] = L['shakeUntil'] = 0
    acordar(L, agora, 8000)
    tocar(L, agora, 'comemorar', say='oi, eu sou|%s!' % NOMES.get(id, id))


# ------------------------------------------------------------ passo: devolve a pose do quadro
def _fim(L, agora, out):
    b = L['bubble']
    if b and agora < b[3]:
        if b[0] == 'shout':
            out['shout'] = b[1]
        else:
            out['say'] = b[1]
            lp = out['lp']
            if not L['asleep'] and agora - b[2] < (b[3] - b[2]) * 0.6 and not (lp and lp.get('mouth')):
                if lp is None:
                    lp = out['lp'] = {}
                lp['mouth'] = 'aberta' if (agora // 180) % 2 else 'sorriso'   # boca mexe enquanto fala
    elif b:
        L['bubble'] = None
    out['asleep'] = L['asleep']
    out['x'] = L['x']
    return out


def passo(L, agora, sono, per):
    """sono = e hora de dormir; per = 'manha', 'dia' ou 'noite'."""
    out = {'lp': None, 'move': '', 'say': None, 'shout': None}
    if L['pend'] and agora >= L['pend'][0]:
        falar(L, agora, L['pend'][1], L['pend'][2])
        L['pend'] = None
    if L['grab']:
        G = L['grab']
        x = _cl(G['x'] + G['ox'], 24, 216)
        pe = min(FEET, G['y'] + G['oy'])
        sh = L['shakeAmp'] if agora < L['shakeUntil'] else 0
        if not G['said'] and agora - G['t0'] > 900 and not sh:
            G['said'] = True
            falar(L, agora, _escolher(L, FRASES['pego']))
        out['lp'] = {'dx': x - L['x'] + (math.sin(agora / 28) * 5 * sh if sh else 0),
                     'dy': pe - FEET - abs(math.sin(agora / 180)), 'sx': 0.95, 'sy': 1.07, 'eyes': 'susto',
                     'mouth': 'aberta' if sh else 'o', 'flip': (1 if math.sin(agora / 56) > 0 else -1) if sh else 1,
                     'fx': ('estrelas',) if sh and agora - L['shakeStart'] > 900 else ()}
        out['move'] = 'colo'
        return _fim(L, agora, out)
    if L['fall']:
        F = L['fall']
        dt = agora - F['t0']
        dy = min(0, F['dy0'] + 0.0012 * dt * dt)
        if dy < 0:
            out['lp'] = {'dy': dy, 'eyes': 'susto', 'mouth': 'o', 'sx': 0.96, 'sy': 1.05}
            out['move'] = 'caindo'
            return _fim(L, agora, out)
        L['fall'] = None
        tocar(L, agora, 'aterrissar')
    if agora < L['shakeUntil']:
        a = L['shakeAmp']
        out['lp'] = {'dx': math.sin(agora / 28) * 7 * a, 'dy': -abs(math.sin(agora / 41)) * 10 * a,
                     'flip': 1 if math.sin(agora / 56) > 0 else -1, 'sx': 1 + 0.08 * math.sin(agora / 35),
                     'sy': 1 - 0.08 * math.sin(agora / 35), 'eyes': 'susto', 'mouth': 'aberta',
                     'fx': ('estrelas',) if agora - L['shakeStart'] > 900 else ()}
        out['move'] = 'sacudido'
        return _fim(L, agora, out)
    if L['shakeStart'] and not L['move']:
        muitos = len([x for x in L['shakes'] if agora - x < 30000]) >= 3
        L['shakeStart'] = 0
        tocar(L, agora, 'tonto', say=_escolher(L, FRASES['sacudidoMuito' if muitos else 'depoisSacudir']))
        L['lastTouch'] = agora
    if sono and agora > L['awakeUntil']:
        if L['asleep']:
            out['move'] = 'dormindo'
            return _fim(L, agora, out)
        if not L['move'] and not L['goingSleep'] and not L['queue']:
            L['goingSleep'] = True
            tocar(L, agora, 'bocejar', say=_escolher(L, FRASES['dormir']))
        elif not L['move'] and L['goingSleep']:
            L['goingSleep'] = False
            L['asleep'] = True
            out['move'] = 'dormindo'
            return _fim(L, agora, out)
    else:
        L['asleep'] = False
        if not sono:
            L['goingSleep'] = False
    if L['move']:
        m = L['move']
        ms = agora - m['t0']
        u = min(1.0, ms / m['dur'])
        if m['id'] == 'andar':
            L['x'] = m['x0'] + (m['x1'] - m['x0']) * ez(u)
            lp = {'flip': 1 if m['x1'] > m['x0'] else -1, 'dy': -abs(math.sin(ms / 140)) * 2.5 if u < 1 else 0}
        else:
            lp = MOVES[m['id']][1](u, ms)
        lp['ms'] = ms
        out['lp'] = lp
        out['move'] = m['id']
        if u >= 1:
            L['move'] = None
            L['nextIdle'] = agora + _rnd(1800, 4800)
    elif L['queue']:
        q = L['queue'].pop(0)
        if q.get('id'):
            tocar(L, agora, q['id'], say=q.get('say'))
        else:
            falar(L, agora, q['say'], q.get('kind', 'say'))
            L['nextIdle'] = max(L['nextIdle'], agora + 2600)
    elif agora - L['lastTouch'] > IGNORADO_MS and not sono:
        L['lastTouch'] = agora - IGNORADO_MS // 2
        L['lastSad'] = agora
        tocar(L, agora, 'chorar', say=_escolher(L, FRASES['ignorado']))
    elif agora >= L['nextIdle'] and not L['goingSleep']:
        _ocioso(L, agora, per)
    return _fim(L, agora, out)
