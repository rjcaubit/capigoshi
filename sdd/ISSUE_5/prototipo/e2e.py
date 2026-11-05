# E2E click-by-click do raio-X (issue #5). Uso: python3 e2e.py <pagina gerada> <pagina vazia> <pasta das capturas>
import os
import sys
from playwright.sync_api import sync_playwright

PAGINA, VAZIA, PASTA = sys.argv[1:4]
os.makedirs(PASTA, exist_ok=True)
falhas = []


def ver(cond, msg):
    print(('ok   ' if cond else 'FALHA ') + msg)
    if not cond:
        falhas.append(msg)


with sync_playwright() as p:
    b = p.chromium.launch()
    for esquema in ('light', 'dark'):
        pg = b.new_page(viewport={'width': 390, 'height': 844}, color_scheme=esquema, has_touch=True)
        erros = []
        pg.on('pageerror', lambda e: erros.append(str(e)))
        pg.on('console', lambda m: erros.append(m.text) if m.type == 'error' else None)
        pg.goto('file://' + os.path.abspath(PAGINA))
        n = 1 if esquema == 'light' else 7
        cap = lambda nome: pg.screenshot(path=os.path.join(PASTA, '%02d-%s-%s.png' % (n + cap.k, esquema, nome)),
                                         full_page=nome == 'pagina')
        cap.k = 0
        cap('pagina')
        ver(pg.evaluate('document.documentElement.scrollWidth') <= 390, esquema + ': sem rolagem lateral em 390 px')
        ver(pg.locator('.cartao').count() >= 7, esquema + ': 7 cartoes ou mais')
        # habito: botao destaca o arco e escreve a dica
        hab = pg.locator('button.hab').first
        if hab.count():
            hab.click()
            ver(hab.get_attribute('aria-pressed') == 'true', esquema + ': habito selecionado')
            ver(pg.locator('#relogio path[stroke="var(--tinta)"]').count() >= 1, esquema + ': arco destacado no relogio')
            ver(pg.locator('.dica').first.inner_text().startswith(('Faz', 'Evita')), esquema + ': dica do habito')
            cap.k = 1
            hab.scroll_into_view_if_needed()
            cap('habito')
        # hoje / ontem
        ontem = pg.get_by_role('button', name='Ontem')
        ontem.click()
        ver(ontem.get_attribute('aria-pressed') == 'true', esquema + ': aba Ontem')
        cap.k = 2
        cap('ontem')
        # ver todas as recompensas
        antes = pg.locator('.rec').count()
        todas = pg.get_by_role('button', name='Ver todas')
        if todas.count():
            todas.click()
            ver(pg.locator('.rec').count() > antes, esquema + ': ver todas abre mais recompensas')
            cap.k = 3
            cap('recompensas')
            pg.get_by_role('button', name='Ver menos').click()
            ver(pg.locator('.rec').count() == antes, esquema + ': ver menos volta')
        # historia: tocar no grafico mostra o valor
        sv = pg.locator('.spark svg').first
        if sv.count():
            sv.scroll_into_view_if_needed()
            caixa = sv.bounding_box()
            pg.touchscreen.tap(caixa['x'] + caixa['width'] / 2, caixa['y'] + 20)
            ver(':' in pg.locator('.spark .dica').first.inner_text(), esquema + ': valor ao tocar no grafico')
            # o dedo que comeca num grafico ainda rola a pagina (touch-action: pan-y)
            antes = pg.evaluate('scrollY')
            cdp = pg.context.new_cdp_session(pg)
            x, y = caixa['x'] + caixa['width'] / 2, caixa['y'] + 24
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
            for k in range(1, 11):
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x, 'y': y + 20 * k}]})
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
            pg.wait_for_timeout(300)
            ver(pg.evaluate('scrollY') != antes, esquema + ': arrastar o dedo sobre o grafico rola a pagina')
            pg.evaluate('scrollTo(0, 0)')
            sv.scroll_into_view_if_needed()
            cap.k = 4
            cap('historia')
        # alvos de toque
        menores = pg.evaluate("[...document.querySelectorAll('button')].filter(b => b.offsetHeight < 44).length")
        ver(menores == 0, esquema + ': botoes com 44 px ou mais')
        ver(not erros, esquema + ': sem erro no console ' + repr(erros))
        pg.close()
    # estado vazio: o modelo sem dados, aberto do disco (o fetch falha)
    pg = b.new_page(viewport={'width': 390, 'height': 844})
    erros = []
    pg.on('pageerror', lambda e: erros.append(str(e)))
    pg.on('console', lambda m: erros.append(m.text) if m.type == 'error' else None)
    pg.goto('file://' + os.path.abspath(VAZIA))
    pg.wait_for_selector('.vazio >> text=Sem dados')
    ver(True, 'estado vazio')
    ver(not erros, 'vazio: sem erro no console ' + repr(erros))
    pg.screenshot(path=os.path.join(PASTA, '13-vazio.png'))
    b.close()

print('E2E OK' if not falhas else 'E2E FALHOU: %d' % len(falhas))
sys.exit(1 if falhas else 0)
