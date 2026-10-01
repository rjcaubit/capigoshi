# Handoff: Capigoshi — direção 1c "Diorama"

## Visão geral
Redesign da tela do Capigoshi (bichinho virtual de bolso, tela touch 1,83" de 240 × 284 px, retrato, cantos de vidro com raio ≈ 30 px). Cobre a cena com as 6 fases do dia, o elenco de 9 personagens com 11 expressões + doente, o HUD do modo Pet, o sistema de balões de fala, o menu de ajustes puxado do topo com hora real/simulada, e as features do Companion (rotina, ciclo de vida, clima, vizinhos, eventos).

## Sobre os arquivos
Os arquivos deste pacote são **referências de design feitas em HTML/JS**, não código de produção. A tarefa é **recriar o design no firmware existente** (MicroPython: `main.py`, `desenho.py`, `hw.py`) com as primitivas do framebuf da placa.

- `capigoshi-render.js`: renderizador de referência. Só usa rect, ellipse (cheia, contorno, metade de cima `mask=1`, metade de baixo `mask=2`), poly, pixel, hline/vline e texto 8 × 8, e toda cor passa por `q565()`. **Fonte de verdade** de coordenadas, cores e ordem de desenho.
- `Capigoshi 1c Diorama.dc.html`: página da direção 1c, com todas as telas animadas e o protótipo interativo do menu. Abra num navegador (precisa de `support.js` e `capigoshi-render.js` na mesma pasta).
- `Capigoshi Redesign.dc.html`: as 3 direções originais (1a, 1b, 1c), a grade/áreas seguras e o documento de features.

## Fidelidade
**Alta fidelidade.** Cores, coordenadas e tamanhos são finais. A única liberdade é arredondar valores fracionários para o inteiro mais próximo onde o framebuf exigir.

## Regras técnicas
- Tela 240 × 284. Vidro come 30 px de cada canto: nada importante em y < 30 ou y > 254 perto das bordas laterais.
- Sem imagens, sem gradiente, sem transparência. Cores sólidas RGB565.
- Fonte bitmap 8 × 8 sem acentos; 2× (16 px) só para hora e mensagem curta.
- Animação só por deslocamento (pulo, balanço, corrida saltitante, boiar).
- Contorno 1c: antes de cada forma "de silhueta", desenhar a mesma forma com +1 px de raio na cor `cor × 0,5` (por canal). Partes internas (máscara, bochecha, olho) não levam contorno.

## Telas

### 1. Cena (todas as telas de jogo)
| Elemento | Especificação |
|---|---|
| Céu | 4 faixas: y 0–60 céu alto, 60–110 céu meio, 110–150 mistura (meio + horizonte) / 2, 150–196 horizonte |
| Estrelas | Só em Madrugada, Crepúsculo e Noite. 30 pixels, x = (i·53+11) mod 240, y = 34 + (i·37) mod 120, piscam por fase |
| Sol | Arco: x = 120 − 100·cos a, y = 170 − 105·sin a, a = (h−6)/13,5·π, 6h–19h30. Raio 11, contorno 1 px |
| Lua | Mesmo arco de 19h30 a 6h. Halo r 15 (céu alto clareado 12 %), disco r 9 0xF79B, recorte r 8 em (+4, −3) na cor do céu |
| Montanhas | 3 triângulos: (−10..90, pico 40,−52), (70..180, pico 125,−66), (150..250, pico 198,−44), base y 196, cor relevo longe; neve = relevo longe clareado 50 % em triângulos 14 × 9 nos picos |
| Colinas | Elipses (40, 204) 90 × 24 e (200, 206) 80 × 20, cor relevo perto |
| Chão | y 196–284 grama; y 240–284 grama escura |
| Lago | Elipse (202, 214) 34 × 9 com contorno; ondinha em contorno que anda 3 px a cada 500 ms |
| Capim | Tufos de 3 linhas em x 18/44/96/150 (y 200) e x 12/60/118/176/226 (y 258, altura 1,4×) |
| Nuvens | Só de dia, sem contorno, 3 elipses; atravessam a tela devagar |
| Relógio (Companion) | Texto 2× centralizado, y 12, creme com sombra de 1 px |

### 2. Personagens
- Pés em y = 205, x = 110 parado; passeia entre x 44 e 200; boia no lago em y = 211 ± 4.
- Escala global `CHAR_SCALE = 0,74` sobre as medidas originais (≈ 60 × 96 px).
- Visitante (vizinho): escala 0,9 × 0,74, fica em x 172 (ou 52 se o principal estiver à direita).
- Funções: `capi`, `pato`, `elefante` (originais) e `polvo`, `calopsita`, `cachorro`, `gato`, `et`, `sapinho` (novos), todas com `(g, cx, pe, o)`, onde `o = {eyes, mouth, sick, s, ol}`. Retornam `{eyes, head, top, half}`.
- Olhos: normal, feliz (meia elipse de cima, 2 px), fechados (traço 2 px), susto (branco com pupila pequena), sono (olho normal com pálpebra na cor do corpo cobrindo a metade de cima).
- Bocas: sorriso (meia elipse de baixo; Caramelo e Gato usam boca em "w" = 2 meias elipses), triste, aberta, meia, o, dormindo.
- Doente: bochecha `0xA5EF` + termômetro (3 × 12 branco, bulbo vermelho r 3).
- Gato preto: olhos com íris verde 0xCF4B e pupila em fenda; linhas (fechado, feliz, boca) em cor clara 0xE6FD; contorno 0x6B50 para não sumir à noite.

### 3. Pet: HUD em bandeja
- Bandeja: retângulo 0, 224, 240 × 60, cor bandeja.
- Medidores em y 229: para i = 0..3, ícone 8 × 8 em x = 30 + 46i, barra em x + 11, y 231, 29 × 4 (fundo "barra vazia bandeja", preenchimento na cor do medidor; vermelho alerta quando < 25).
- Botões: retângulos arredondados 42 × 30, raio 7, x = 28 + 46i, y 244, cor "botão bandeja", ícone centralizado (capim verde-claro, bola laranja, gota azul, pílula vermelho/branco). Toque: 4 colunas de x 28 a 212.
- Cocô no gramado em x = 24 + 16i, y 206–211.

### 4. Balões de fala
| Tipo | Forma | Uso |
|---|---|---|
| Fala | Retângulo arredondado (raio 3) creme 0xFFBD, contorno 0x834A, padding 6, altura 16 (1 linha) / 26 (2 linhas). Rabicho triangular 8 × 6 apontando para o centro da cabeça | Frases do bichinho |
| Conversa | Duas falas, uma de cada personagem, alternando a cada 2,6 s. Quem fala abre/fecha a boca a cada 180 ms | Vizinho visita |
| Pensamento | Bolinhas r 2 e r 3 subindo da cabeça + nuvem 32 × 26 raio 10 com ícone; balança 1 px a cada 500 ms | Vontades, sonhos |
| Grito | Estrela de 18 pontas amarela 0xFE44, contorno 0x834A, texto 2×; alterna 2 rotações a cada 140 ms | Sacudida, grito |
| Chamado | Círculo creme 13 × 12 ao lado da cabeça (x = cx + half + 4), rabicho para a cabeça, ícone dentro | Pet pede algo |
| Chamado urgente | Igual, contorno vermelho 0xE249 + selo vermelho r 5 com "!" | Doente, saúde baixa. Som a cada 30 s |
| Sistema | Pílula cor bandeja, altura 18, raio 9, texto creme, centralizada em y 36 | Avisos do aparelho |

Regras: 8 px acima de `top`; limitado a x 8–232; máx. 2 linhas × 14 caracteres; sem acentos. Duração da fala: 400 ms + 80 ms por letra, mínimo 2,5 s. Prioridade: urgente > grito > fala > chamado > pensamento > sistema. Um balão por personagem por vez.

Ícones de pensamento/chamado: `capim`, `zzz`, `coracao`, `bola`, `banho`, `remedio`, `peixe`, `nota` (ver `thinkIcon()`).

### 5. Menu de ajustes (puxar de cima)
- Fechado: alça creme 28 × 4, raio 2, em (106, 3).
- Gesto: começa com toque em y < 48. Painel acompanha o dedo (borda inferior = y do dedo + 14). Ao soltar: abre se borda > 130, senão fecha. Animação de encaixe: borda += (alvo − borda) × 0,35 por quadro. Fecha também arrastando a alça para cima, tocando nela ou com o botão físico.
- Painel: cor bandeja de y 0 a 272, cantos de baixo raio 10, linha 0x18121A de 1 px sob a borda. O conteúdo desce junto (translação = borda − 272), com recorte em y < borda.
- Conteúdo (coordenadas com o painel aberto):
  - "Ajustes" centralizado, y 12, creme. Wi-Fi (3 barras) em x 36, som em x 196.
  - "modo" (rótulo 0xB4F6) em (20, 29). 3 botões 64 × 30, raio 6, x = 20 + 68i, y 40: **Cuidar** (Pet), **Olhar** (Companion), **Passear** (side-scroller). Selecionado: laranja 0xF46B com texto tinta; não selecionado: botão bandeja com texto creme.
  - "personagem" em (20, 78). Cartão 70 × 60 em (85, 89) com contorno laranja 2 px; escolhido desenhado no centro (escala 0,45, olhos felizes, pés em y 144); anterior e próximo em x 56 e 184 (escala 0,3, pés em y 142); setas triangulares em x 14 e 226, y 119; nome centralizado em y 156.
  - "hora" em (20, 171). Botões **Real** e **Simulada**, 98 × 26, x 20 e 122, y 182.
  - Simulada: 3 botões **1x 2x 3x**, 64 × 22, x = 20 + 68i, y 214; legenda "dia em 30/15/10 min" centralizada em y 244.
  - Real: "agora HH:MM" em y 218 e "segue o relogio" em y 234.
  - Alça 40 × 4 em (100, 256).
- Áreas de toque: `menuHit()` no renderizador.
- Ordem do carrossel: capi, elefante, pato, polvo, calopsita, cachorro, gato, et, sapinho. No Pet, trocar de personagem pede confirmação (cada bichinho tem idade e medidores próprios).

### 6. Passeio (side-scroller)
Segurar a metade direita/esquerda da tela anda; toque curto pula; o cenário rola em passos de 8 px; árvores em 2 planos (paralaxe 1/2); moedas e placas. Etiquetas "campo 2" e contador de moedas no topo, dentro da área segura. Botão físico volta para casa. Ver `explore()`.

## Interações e comportamento
- Toque no personagem: carinho (corações). Sacudida/grito acordado: festa + balão de grito. Dormindo: susto ("!" vermelho, olhos de susto, boca "o").
- Hora simulada: começa da hora real atual; avança `24 h / (min × 60 s)`; trocar a velocidade reinicia a partir da hora simulada atual. Pet em simulada: fome/alegria/energia decaem × (1440 / min) em relação ao real.
- Rotina do Companion (hora virtual): 0h dorme · 6h30 espreguiça · 7h come · 9h passeia · 12h come · 13h nada no lago · 15h30 passeia · 18h pôr do sol · 19h30 passeia · 21h30 dorme.
- Ciclo de vida: ovo (1 dia real, toque aquece) → filhote (3 dias, escala 0,62) → adulto (10–20 dias) → idoso (5 dias, sobrancelhas brancas, bengala, metade da velocidade) → despedida à noite: vira estrela com o nome no céu do Companion; novo ovo de manhã.
- Features do Companion (clima, estações, vizinhos, festas, eventos raros, construções): ver seção "Companion" em `Capigoshi Redesign.dc.html`.

## Estado
```
cfg = { modo: 'pet'|'companion'|'explore', personagem: id, hora: 'real'|'sim', vel: 1|2|3, som: bool }   # persistir
sim = { h0: float, t0_ms: int }                                    # início da hora simulada
menu = { borda: 0..272, alvo: 0|272, arrastando: bool }
pet = { fome, alegria, energia, saude, cocos, doente, dormindo, idade_dias, fase_vida }
fala = { texto, ate_ms, quem }   # um por personagem
```

## Tokens de design

### Paleta das 6 fases (RGB565)

| Fase | Horas | Céu alto | Céu meio | Horizonte | Relevo longe | Relevo perto | Grama | Grama escura | Lago |
|---|---|---|---|---|---|---|---|---|---|
| Madrugada | 0–5 | 0x0886 | 0x10E8 | 0x214B | 0x1909 | 0x11E6 | 0x1A46 | 0x11A4 | 0x220F |
| Amanhecer | 5–7.5 | 0xECB0 | 0xFD90 | 0xFEB5 | 0xC432 | 0x3C6A | 0x450B | 0x2BA8 | 0x85BB |
| Dia | 7.5–17 | 0x5D9F | 0x865F | 0xAEFF | 0x6DBA | 0x2CAA | 0x2D8C | 0x1BE8 | 0x5D5D |
| Por do sol | 17–19.5 | 0xEB6C | 0xFCAB | 0xFE70 | 0xBB4F | 0x3409 | 0x3CAA | 0x2347 | 0xF50F |
| Crepusculo | 19.5–21 | 0x316D | 0x5A30 | 0xA351 | 0x49CF | 0x1AA7 | 0x2328 | 0x1A26 | 0x5292 |
| Noite | 21–24 | 0x0886 | 0x10C7 | 0x190A | 0x10C8 | 0x11C5 | 0x1225 | 0x0984 | 0x19ED |

### Cores fixas de interface

| Nome | RGB565 (hex web) |
|---|---|
| creme (balão, texto claro) | 0xFFBD (#fff7ef) |
| tinta | 0x28E5 (#291c29) |
| texto | 0x3942 (#392810) |
| trilho barra | 0xE6B7 (#e7d7bd) |
| fome | 0xFC45 (#ff8a29) |
| alegria | 0xE291 (#e7518c) |
| energia | 0x3C5D (#398aef) |
| saúde | 0x2D8C (#29b263) |
| alerta | 0xE249 (#e7494a) |
| bandeja | 0x3146 (#312831) |
| botão bandeja | 0x524B (#52495a) |
| barra vazia bandeja | 0x62AC (#635563) |
| contorno balão | 0x834A (#846952) |
| acento menu (laranja) | 0xF46B (#f78e5a) |
| rótulo menu | 0xB4F6 (#b59eb5) |
| amarelo grito | 0xFE44 (#ffcb21) |

### Personagens

| Personagem | id | Cores principais (RGB565) |
|---|---|---|
| Capi | `capi` | 0xAB88 · 0x7A65 · 0xBC0B · 0xE613 · 0xFE44 |
| Elefante | `elefante` | 0xCE7A · 0x7BF1 · 0xF537 · 0x1082 · 0xFFFF |
| Pato | `pato` | 0xFE45 · 0xCC82 · 0x8150 · 0xBD3C · 0xFC63 |
| Polvo | `polvo` | 0x937A · 0x6A35 · 0xC55E · 0xF4B7 · 0x1082 |
| Calopsita | `calopsita` | 0xFEAA · 0xD525 · 0xFF74 · 0xEAE8 · 0xEBE8 |
| Caramelo | `cachorro` | 0xD4A9 · 0xA305 · 0xFF16 · 0x8A84 · 0x1082 |
| Gato | `gato` | 0x39A8 · 0x20E5 · 0xE6FD · 0xCF4B · 0xF4B7 |
| ET | `et` | 0x764B · 0x3C47 · 0xBF8F · 0xFD35 · 0x1082 |
| Sapinho | `sapinho` | 0x9647 · 0x6484 · 0xD751 · 0xF4AB · 0x1082 |


## Arquivos
- `capigoshi-render.js`: renderizador de referência (fonte de verdade).
- `Capigoshi 1c Diorama.dc.html`: direção 1c, elenco, balões, menu (protótipo interativo).
- `Capigoshi Redesign.dc.html`: 3 direções, grade/áreas seguras, documento de features.
- `support.js`: runtime necessário para abrir os `.dc.html` no navegador.
- `PROMPT.md`: prompt pronto para colar no Claude Code.
