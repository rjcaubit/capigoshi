Cole isto no Claude Code, na pasta do firmware do Capigoshi (main.py, desenho.py, hw.py), com esta pasta de handoff copiada para dentro do repositório.

---

Você vai atualizar o firmware do Capigoshi (bichinho virtual para crianças de 6 a 11 anos) para a direção visual "1c Diorama". A especificação completa está em `design_handoff_capigoshi_1c/README.md`. A referência visual exata é `capigoshi-render.js`: um renderizador em JS que usa só as primitivas do framebuf (rect, fill_rect, ellipse cheia/contorno/metade, poly, pixel, hline, texto 8×8) e quantiza toda cor para RGB565. Trate esse arquivo como fonte de verdade de coordenadas, cores e ordem de desenho, e traduza para MicroPython. Não copie o HTML; ele é só referência. Abra `Capigoshi 1c Diorama.dc.html` no navegador para ver tudo funcionando.

Hardware: tela 240 × 284 retrato com cantos de vidro de raio 30 px, touch, acelerômetro, microfone, alto-falante (ES8311), relógio real, Wi-Fi, um botão físico.

Faça nesta ordem, com um commit por etapa, e rode no aparelho (ou no simulador) antes de seguir:

1. **Paleta e cena.** Substitua o céu interpolado por 6 fases fechadas (tabela no README): 4 faixas de céu (y 0/60/110/150/196), montanhas em triângulo com neve, colinas, chão em 2 tons (faixa escura a partir de y 240), lago em (202, 214) raios 34 × 9 com contorno. Contorno de 1 px na cor da forma × 0,5. Sem degradê: a troca de fase é instantânea. Remova a faixa amarela de cabeçalho e o rodapé verde; a cena ocupa a tela inteira.

2. **Escala dos personagens.** Todos desenhados a 0,74 do tamanho atual (constante `CHAR_SCALE`), pés em y = 205. Sombra elíptica 20 × 3 sob os pés.

3. **Elenco de 9.** Mantenha Capi, Pato e Elefante como estão e acrescente Polvo, Calopsita, Caramelo (cachorro), Gato preto, ET e Sapinho, seguindo as funções `polvo()`, `calopsita()`, `cachorro()`, `gato()`, `et()`, `sapinho()` do renderizador e os helpers `eyesG()`, `mouthG()`, `beak()`. Cada personagem precisa de 5 olhos (normal, feliz, fechados, susto, sono), 6 bocas (sorriso, triste, aberta, meia, o, dormindo) e a versão doente (bochecha `ENJOADA` + termômetro). Os traços vêm de desenhos de criança: preserve, não "corrija". Cada função retorna `top`, `head`, `half` (usados para posicionar balões).

4. **HUD do Pet em bandeja.** Bandeja escura de y 224 até o fim. Medidores: 4 ícones 8 × 8 + barra de 29 × 4 px (vermelho abaixo de 25). Botões: 4 retângulos arredondados 42 × 30, raio 7, em x 28/74/120/166, y 244, só com ícone (capim, bola, gota, pílula).

5. **Balões de fala (7 tipos).** Fala, conversa, pensamento, grito, chamado, chamado urgente e sistema, com tamanhos, cores, tempos e prioridade descritos no README. Funções de referência: `say()`, `think()`, `shout()`, `need()`, `sysMsg()`. Texto sem acento, no máximo 2 linhas × 14 caracteres. Na conversa, um balão por vez (2,6 s cada).

6. **Menu de ajustes puxado do topo.** Arrastar a partir de y < 48 desce o painel junto com o dedo; ao soltar abaixo de y 130 ele abre, acima volta. O conteúdo: Modo (Cuidar = Pet, Olhar = Companion, Passear = side-scroller), carrossel de personagem com setas, Hora Real/Simulada e velocidade 1x/2x/3x (dia em 30/15/10 min), ícones de Wi-Fi e som. Layout em `MENU`, `drawMenu()` e `menuHit()`. Persistir a escolha na flash.

7. **Hora simulada.** Ao escolher Simulada, começar da hora real atual e avançar `24h / (min × 60 s)`. No Pet, fome e sono aceleram na mesma proporção. O padrão do Pet continua Real.

8. **Companion com rotina rica e ciclo de vida.** Implemente o roteiro do dia, as camadas de variação (clima, estação, vizinhos, festas, sensores) e o ciclo ovo → filhote (0,62×) → adulto → idoso → estrela, tudo descrito no README. Pode ficar para depois das etapas 1 a 7.

Regras: nada importante nos 30 px dos cantos; fonte 8 × 8 (2× só para hora e mensagem curta); toda cor passa por RGB565; animação só por deslocamento. Se algo do renderizador JS não tiver equivalente direto no framebuf (por exemplo, `ellipse` com raio fracionário), arredonde para o inteiro mais próximo e me avise onde fez isso.

Quando terminar cada etapa, me mostre uma foto/print da tela e uma lista curta do que ficou diferente da referência.
