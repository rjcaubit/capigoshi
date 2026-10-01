# Converte as telas .565 gravadas por rodar.py em PNG (2x, com os cantos do vidro de raio 30).
import glob, os
from PIL import Image, ImageDraw

W, H, E = 240, 284, 2


def ler(path):
    b = open(path, 'rb').read()
    img = Image.new('RGB', (W, H))
    px = img.load()
    for i in range(W * H):
        v = b[2 * i] << 8 | b[2 * i + 1]          # bytes trocados: big-endian para a tela
        r, g, bl = v >> 11, (v >> 5) & 63, v & 31
        px[i % W, i // W] = (r << 3 | r >> 2, g << 2 | g >> 4, bl << 3 | bl >> 2)
    img = img.resize((W * E, H * E), Image.NEAREST)
    mask = Image.new('L', img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, W * E - 1, H * E - 1), 30 * E, fill=255)
    out = Image.new('RGB', img.size, (12, 10, 9))
    out.paste(img, (0, 0), mask)
    return out


os.makedirs('png', exist_ok=True)
for p in sorted(glob.glob('out/*.565')):
    nome = os.path.basename(p)[:-4]
    ler(p).save('png/%s.png' % nome)


def folha(nomes, arquivo, colunas=4):
    ims = [Image.open('png/%s.png' % n) for n in nomes if os.path.exists('png/%s.png' % n)]
    lin = (len(ims) + colunas - 1) // colunas
    pad = 16
    f = Image.new('RGB', (colunas * (W * E + pad) + pad, lin * (H * E + pad + 22) + pad), (236, 230, 220))
    dr = ImageDraw.Draw(f)
    for i, (im, n) in enumerate(zip(ims, nomes)):
        x = pad + (i % colunas) * (W * E + pad)
        y = pad + (i // colunas) * (H * E + pad + 22)
        f.paste(im, (x, y + 22))
        dr.text((x, y + 4), n, fill=(40, 30, 40))
    f.save(arquivo)
    print(arquivo)


todos = [os.path.basename(p)[:-4] for p in sorted(glob.glob('out/*.565'))]
folha([n for n in todos if n.startswith('fase_')], 'png/_folha_fases.png')
folha([n for n in todos if n.startswith('elenco_')], 'png/_folha_elenco.png', 5)
folha([n for n in todos if n.startswith('expr_')], 'png/_folha_expressoes.png', 5)
folha([n for n in todos if n.startswith(('pet_', 'balao_', 'conversa_'))], 'png/_folha_pet_baloes.png')
folha([n for n in todos if n.startswith(('menu_', 'passear'))], 'png/_folha_menu_passeio.png', 5)
