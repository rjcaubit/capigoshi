# Como contribuir

Obrigado por querer ajudar o Capigoshi! Este guia mostra como montar o ambiente, quais regras o projeto
segue e como mandar sua contribuição.

## Antes de começar

- **Bugs e ideias:** abra uma issue. Para bug, conte o que aconteceu, o que esperava e, se puder, mande
  uma foto da tela.
- **Mudanças grandes** (um modo novo, mudar o comportamento da vida): abra uma issue primeiro para
  conversar.
- **Idioma:** português ou inglês, como preferir.

## Ambiente

```bash
brew install micropython          # MicroPython "unix", o mesmo framebuf da placa
pip install pillow mpremote esptool
cd previa && micropython rodar.py && python3 montar.py
```

O `previa/rodar.py` roda o firmware de verdade com o hardware simulado, gera as telas em
`previa/png/` e confere as regras do jogo. **Antes de mandar um PR, ele precisa terminar sem
`AssertionError`.** Se você mudou algo visual, olhe as folhas `previa/png/_folha_*.png` e anexe uma
delas no PR.

## Regras do projeto

- **Só primitivas do `framebuf`:** `fill_rect`, `rect`, `ellipse` (cheia, contorno ou metade),
  `poly`, `pixel`, `line` e `text`. Nada de imagens ou bitmaps na placa.
- **Coordenadas inteiras.** O `framebuf` não aceita `float`; use os helpers do `desenho.py`
  (`ell`, `rect`, `poly`…), que já arredondam.
- **Tela de 240 × 284 com cantos de vidro de raio 30 px.** Nada importante nos cantos.
- **Texto sem acento e curto.** A fonte 8 × 8 não tem acentos. Balões têm no máximo 2 linhas de 14
  letras (`|` quebra a linha).
- **Não trave o laço.** Nada de `time.sleep` no jogo. O som já toca sem bloquear.
- **Pouca memória.** Evite criar listas grandes a cada quadro.
- **`vida.py` não desenha nem acessa hardware.** Ele só decide o que o bichinho faz, o que facilita
  testar.
- **Comentários e nomes em português**, curtos, explicando o *porquê*.

## Novos personagens

Personagens desenhados por crianças são o coração do projeto. Para adicionar um:

1. Escreva a função em `desenho.py` no mesmo formato de `polvo()` ou `sapinho()`. Ela precisa ter os
   5 olhos (normal, feliz, fechados, susto, sono), as 6 bocas (sorriso, triste, aberta, meia, o,
   dormindo) e a versão doente (bochecha `ENJOADA` + `termometro`), e devolver
   `(cabeça, topo, meia largura, olhos)`.
2. Registre a função em `ELENCO`, `NOMES` e `_FUNCS`. Ponha a altura em `HTOP`, tanto no `desenho.py`
   quanto no `vida.py`.
3. Escreva frases próprias em `FRASES_CHAR`, no `vida.py`.
4. Rode a prévia: a folha `_folha_expressoes.png` mostra todas as expressões.

Se o personagem veio de um desenho de criança, não mande a foto do desenho, nem o nome ou a imagem
da criança. Basta descrever os traços no PR.

## Sons

Use só sons com licença que permita redistribuir, como CC0, CC-BY (com crédito no `CREDITOS.md`) ou
sons feitos por você. Formato da placa: `.raw` a 16 kHz, 16 bits, estéreo, curto (até cerca de 1,5 s):

```bash
ffmpeg -i entrada.wav -ar 16000 -ac 2 -f s16le sons/nome.raw
```

Sons do Pixabay não podem ir para o repositório. Eles entram pelo `sons/pixabay.sh`.

## Pull requests

1. Crie um branch a partir de `main`.
2. Faça mudanças pequenas e focadas, com mensagem de commit explicando o porquê.
3. Rode a prévia e anexe uma tela, se mudou algo visível.
4. Ao abrir o PR, você concorda em licenciar sua contribuição sob a [licença MIT](LICENSE).
