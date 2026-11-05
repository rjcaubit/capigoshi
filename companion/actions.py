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
