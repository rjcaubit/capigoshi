<p align="center">
  <img src="docs/img/capigoshi-vivo.gif" width="240" alt="A Capi dançando, dando cambalhota e comemorando na tela do Capigoshi">
</p>

<h1 align="center">Capigoshi</h1>

<p align="center">
  Um bichinho virtual de bolso com um pequeno cérebro de neurônios, feito em MicroPython para uma plaquinha com tela touch.<br>
  Ele nasce de um ovo, cresce, brinca, dorme, aprende os seus hábitos e um dia vira estrela.
</p>

<p align="center">
  <a href="https://capigoshi.mundocapi.com">Site</a> ·
  <a href="https://capigoshi.mundocapi.com/cerebro.html">Como o cérebro funciona</a> ·
  <a href="#começando">Começando</a> ·
  <a href="#como-brincar">Como brincar</a> ·
  <a href="#o-cérebro">O cérebro</a> ·
  <a href="README.md">English</a> ·
  <a href="CONTRIBUTING.md">Contribuir</a> ·
  <a href="LICENSE">Licença MIT</a>
</p>

> 🇺🇸 **Read in English:** [README.md](README.md)

---

## O que é

O Capigoshi é um tamagotchi moderno que mora numa placa de 1,83" com tela touch, acelerômetro,
microfone, alto-falante e relógio. Tudo o que aparece na tela é desenhado por código, com elipses,
retângulos, triângulos e texto 8 × 8. Não há nenhuma imagem guardada na placa.

**Novo na v1.5:** no modo **Olhar**, quem manda no bichinho é uma **rede neural de spikes** (neurônios
LIF em números inteiros, com STDP e STDP modulado por recompensa) rodando dentro do próprio ESP32-S3. A
cada segundo ela escolhe uma de 100 ações e aprende com você: o que você elogia, ele repete, no horário em
que você elogia; o que você ignora ou repreende, ele vai deixando de fazer. A memória sobrevive quando a
placa desliga, e dá para abrir um **raio-X** do cérebro no celular.

<p align="center"><img src="docs/img/elenco.png" alt="Os personagens: Capi, Elefante, Pato, Polvo, Calopsita, Caramelo, Gato, ET e Sapinho"></p>

- **10 personagens:** Capi, Elefante, Pato, Polvo, Calopsita, Caramelo, Gato, ET, Sapinho e Náufrago.
  Os nove primeiros foram criados pelo João, de 9 anos, e os traços dele foram mantidos, não "corrigidos".
- **Ele está vivo:** respira, sorteia um de 21 movimentos conforme a hora (dançar, cambalhota,
  cheirar flor, esconder num buraco, espirrar…) e fala com voz de minion.
- **Ele reage:**
  - **toque:** carinho;
  - **segurar e arrastar:** colo;
  - **sacudir a placa:** fica tonto;
  - **barulho:** leva susto;
  - **10 min sem atenção:** chora e chama.
- **Ciclo de vida:** o ovo choca em 10 min. Depois vêm filhote, adulto e idoso (bengala e
  sobrancelhas brancas). Entre 23 e 40 dias depois, numa noite, ele vira estrela com o nome no céu, e de
  manhã aparece um ovo novo.
- **Diorama do dia:** 6 fases de céu, com sol e lua em arco, estrelas, nuvens, montanhas e lago.
  Ele dorme das 22h às 6h.
- **Três modos:**
  - **Cuidar:** fome, alegria, energia, saúde, cocô e doença.
  - **Olhar:** ele vive sozinho, guiado pelo cérebro, com rotina e visitas.
  - **Passear:** um side-scroller com moedas.
- **Internet, se você quiser:** Wi-Fi configurado pelo celular (QR code, como lâmpada inteligente), hora
  e clima pela internet, e duas placas encostadas se reconhecem e trocam presentes, sem precisar de internet.

| Cuidar | Olhar (conversa com vizinho) | Passear | Menu puxado do topo |
|:--:|:--:|:--:|:--:|
| ![Modo Cuidar](docs/img/tela_pet_chamado_fome.png) | ![Modo Olhar](docs/img/tela_conversa_1.png) | ![Modo Passear](docs/img/tela_passear_auto.png) | ![Menu](docs/img/tela_menu_aberto_sim.png) |

## Feito pelo João

Os personagens, os movimentos e as ações do Capigoshi foram criados pelo João, de 9 anos. O código só
traduziu cada traço do desenho dele para a tela, sem corrigir nada. Veja cada desenho ao lado do bichinho
que ele virou [na página do projeto](https://capigoshi.mundocapi.com/#joao).

<p align="center"><img src="docs/img/joao-desenhos.jpg" width="520" alt="Os desenhos originais do João: sapinho, calopsita, polvo, cachorro, gato, aquário, ET, elefante e pato"></p>

## O cérebro

No modo Olhar, uma pequena rede neural de spikes decide o que o bichinho faz. Ela usa **só números
inteiros** (nenhum float), cabe em uns 50 KB e roda na placa em tempo real.

```
 107 sentidos ──► 96 neurônios ocultos ──► 100 neurônios de ação ──► a ação com mais spikes em 1 s
 (hora, toque,    (80 excitatórios,         (dançar, pedir comida,
  sacudida,        16 inibitórios,           chamar você, dormir…)
  barulho,         recorrentes)                     ▲
  bateria,                                          │ relógio de hábitos: 72 células de 20 min
  vontades…)                                        │ aprende "o que me elogiam nesta hora"
```

- **Neurônios:** LIF (integra e dispara com vazamento). A cada tick de 50 ms,
  `v ← v + I − (v − v_repouso)/16 + ruído`; passou do limiar, dispara um spike e volta a −200. A cada
  segundo a rede roda 20 ticks, e vence o neurônio de ação que disparou mais.
- **Aprendizado sem professor (STDP):** a entrada que dispara logo antes de um neurônio oculto fica mais
  forte; a que dispara logo depois fica mais fraca.
- **Aprendizado por recompensa (R-STDP):** cada ação deixa um *rastro de elegibilidade* nas sinapses.
  Quando chega uma recompensa `R` (estrela +20, carinho +10, "shh" −15, ser ignorado −5…), os pesos mudam
  `Δw = η · R · e`, só na ação que recebeu o crédito.
- **Relógio de hábitos:** 72 células de 20 minutos, cada uma ligada às 100 ações, aprendem *quando* uma
  ação compensa. É assim que ele aprende a pedir carinho às 19h, se é nessa hora que você brinca com ele.
- **Sete vontades (drives):** fome, energia, humor, tédio, afeto, curiosidade e estresse mudam minuto a
  minuto e voltam para a rede como sentido. Por cima, regras fixas: energia baixa, dorme; fome alta, pede
  comida.
- **Habituação e esquecimento:** a mesma ação premiada várias vezes rende cada vez menos; todo dia cada
  peso anda 1% de volta ao valor de nascença.
- **Na placa:** os laços pesados viram código de máquina com `@micropython.viper` (o tick caiu de 16 ms
  para 2,7 ms). O cérebro fica gravado em `brain.bin` (com CRC e cópia de segurança) a cada 10 minutos e
  quando ele dorme.

👉 A matemática completa, passo a passo, está em **[Como o cérebro funciona](https://capigoshi.mundocapi.com/cerebro.html)**.
As calibrações (cada constante que mudou em relação ao projeto original, e por quê) estão em
[`CALIBRACAO.md`](CALIBRACAO.md).

### Raio-X do cérebro

Segure o **BOOT** por 3 segundos, entre na rede **Capigoshi** pelo celular e toque em **"Ver o raio-X do
meu cérebro"**. Aparecem as vontades, os hábitos de cada horário num relógio de 24 h, o que ele mais fez
hoje e ontem, o que aprendeu a evitar e as últimas recompensas.

<p align="center"><img src="docs/img/raiox_relogio.png" width="300" alt="Raio-X do cérebro no celular: um anel de 24 horas com o hábito aprendido em cada célula de 20 minutos"></p>

## Hardware

- **Placa:** [Waveshare ESP32-S3-Touch-LCD-1.83](https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-1.83)
  - ESP32-S3 com 8 MB de PSRAM
  - tela ST7789 de 240 × 284
  - toque CST816D
  - acelerômetro QMI8658
  - relógio PCF85063
  - áudio ES8311 + ES7210
  - energia AXP2101
- **Bateria de lítio (opcional):** a placa tem conector. Com bateria, o relógio não perde a hora, e
  a tela avisa quando ela chega a 10%.
- **Cabo USB-C.**

## Começando

Você precisa de Python 3 e de um Mac ou Linux (no Windows, use os comandos do passo 3 à mão).

```bash
pip install esptool mpremote
git clone https://github.com/rjcaubit/capigoshi.git && cd capigoshi
```

**1. Coloque a placa em modo de gravação.** Segure **BOOT**, aperte e solte **RST**, e solte **BOOT**.

**2. Grave tudo.**

```bash
bash deploy.sh                 # baixa o MicroPython, grava, copia os arquivos e acerta o relógio
```

O `deploy.sh` apaga a placa antes de gravar (inclusive o bichinho e o que o cérebro aprendeu). Para
atualizar só os arquivos sem perder o bichinho (com a placa ligada normalmente, sem modo de gravação):

```bash
bash deploy.sh --so-arquivos
```

**3. Sem o script:** grave o firmware `ESP32_GENERIC_S3-SPIRAM_OCT` do
[micropython.org](https://micropython.org/download/ESP32_GENERIC_S3/) e copie os arquivos:

```bash
mpremote cp main.py hw.py desenho.py vida.py rede.py portal.py : + cp -r sons : + cp companion/raiox.html :raiox.html
mpremote mkdir :companion
mpremote cp companion/*.py :companion/ + reset
```

### Sons extras (opcional)

A pasta `sons/` já vem com efeitos da Kenney (CC0). A voz de minion e alguns efeitos mais caprichados
são do Pixabay, cuja licença não permite redistribuir o arquivo solto, então eles não vêm no
repositório. Para usá-los:

1. Abra os links listados em [`sons/pixabay.sh`](sons/pixabay.sh) e clique em **Free download** em cada um.
2. Rode `bash sons/pixabay.sh`. Os sons vão para `sons/extra/`, que fica fora do git.

Sem esses arquivos o jogo funciona igual, só fala sem voz.

### Hora e Wi-Fi

O relógio da placa não precisa de internet: o `deploy.sh` acerta a hora com a do seu computador, e o
menu tem os botões **-1m / -1h / +1h / +1m**. Para usar o Wi-Fi, segure o **BOOT** por 3 segundos: a
placa abre uma rede chamada **Capigoshi** e mostra um QR code. Aponte a câmera do celular, escolha a rede
de casa, digite a senha e pronto. Com Wi-Fi, a placa acerta o relógio e pega o clima a cada 30 minutos.

## Como brincar

| Gesto | O que acontece |
|---|---|
| Puxar a tela de cima para baixo | Abre os **Ajustes**: modo, personagem, hora Real ou Simulada (dia em 30, 15 ou 10 min), som, zerar |
| Tocar no bichinho | Carinho. Cinco toques seguidos e ele pede "chega de cosquinha!" |
| Tocar fora dele | Ele olha em volta |
| **No Olhar:** segurar o dedo parado nele por 1 s | ⭐ **Estrela**: elogio para o que ele acabou de fazer (últimos 3 s). Ele comemora e aprende a repetir |
| **No Olhar:** segurar o dedo parado no fundo | 🤫 **Shh**: bronca de leve. Ele se esconde e passa a fazer aquilo menos |
| Segurar e arrastar | Colo. Ele reclama, e cai quando você solta |
| Sacudir a placa | Grita, chacoalha e fica tonto (no Olhar também conta como bronca). Se estiver dormindo, acorda por 1 minuto |
| Barulho perto | Leva susto e olha em volta |
| Ignorar os chamados | Também ensina: chamado que nunca é atendido vai sumindo |
| Tocar no ovo | Aquece e adianta o choco em 20 s |
| Botões do Cuidar | Comer, brincar, banho, remédio |
| Passear | Segure um lado da tela para andar. Toque curto pula. 3 toques rápidos no mesmo lado: anda sozinho |
| Botão BOOT | Fecha o menu e volta do Passear. Segurar 3 s: Wi-Fi e raio-X. 3 toques rápidos: modo offline |

Trocar de personagem ou **zerar** começa do zero, com um ovo novo, e o jogo pergunta antes.

## Ver sem a placa

A pasta [`previa/`](previa/) roda o firmware de verdade (`main.py`, `desenho.py` e `vida.py`, sem
cópia nem imitação) no MicroPython do computador. O hardware é simulado, e as telas saem em PNG:

```bash
brew install micropython        # ou: apt install micropython
cd previa
micropython rodar.py            # roda os cenários e os testes (ciclo de vida, menu, sono, bateria...)
python3 montar.py               # converte as telas em PNG, com os cantos do vidro (precisa do Pillow)
```

O `rodar.py` também funciona como teste automático: se alguma regra do jogo quebrar, ele para com
`AssertionError`.

O cérebro tem simulador e testes próprios, em CPython:

```bash
python3 -m unittest discover -s companion/testes -t .   # testes (rede, aprendizado, ponte com a placa, raio-X)
python3 -m companion.sim.aceite todos                   # aceite: uma semana simulada (velocidade, silêncio, hábito)
python3 -m companion.sim.raiox                          # gera a página do raio-X com um dono simulado
```

## Ajustes

As principais constantes ficam no topo do [`main.py`](main.py):

| Constante | O que controla | Padrão |
|---|---|---|
| `DORME`, `ACORDA` | Horário de sono | 22h e 6h |
| `OVO_MINUTOS` | Quanto tempo o ovo leva para chocar (minutos de verdade) | 10 |
| `VIDA_TOTAL` | Dias de vida, sorteados no ovo | 23 a 40 |
| `FOME_MIN`, `CHANCE_DOENCA`… | Ritmo do modo Cuidar | |
| `LIMIAR_GRITO`, `BARULHO_SEGUIDOS` | Sensibilidade do microfone | |
| `LIMIAR_SACUDIDA` | Força da sacudida, em g | 0,9 |
| `BATERIA_FRACA` | Porcentagem em que a tela avisa | 10% |

No [`vida.py`](vida.py) ficam os movimentos, as falas de cada personagem, o repertório de cada hora do
dia e o tempo até ele chorar de saudade (`IGNORADO_MS`). As constantes do cérebro ficam em
[`companion/config.py`](companion/config.py).

## Estrutura

```
main.py        lógica do jogo: modos, menu, ciclo de vida, sensores, toque, ponte com o cérebro
vida.py        comportamento: 21 movimentos, falas, reações (sem desenho, sem hardware)
desenho.py     tudo o que aparece na tela: cena, personagens, balões, HUD, menu, efeitos
hw.py          drivers: tela, toque, acelerômetro, relógio, áudio e bateria
rede.py        Wi-Fi, hora e clima pela internet, amigos por perto (ESP-NOW)
portal.py      portal de configuração do Wi-Fi e rotas do raio-X do cérebro
companion/     o cérebro de spikes: rede, aprendizado, vontades, recompensas, relógio, ponte com a placa, raio-X
deploy.sh      grava o MicroPython e copia os arquivos, acertando o relógio
sons/          efeitos .raw (16 kHz, 16 bits, estéreo) e o script dos sons do Pixabay
previa/        roda o firmware no computador e gera PNGs (também serve de teste)
docs/          landing page e imagens
design_handoff_capigoshi_1c/   especificação visual "1c Diorama" (cores, coordenadas, renderizador de referência)
```

### Como o desenho funciona

- **Uma fonte de verdade.** O `desenho.py` é a tradução de um renderizador de referência em JS
  (`design_handoff_capigoshi_1c/capigoshi-render.js`), que só usa o que o `framebuf` da placa tem.
- **Cores em RGB565.** Toda cor passa por RGB565.
- **Contorno.** O contorno de cada forma é a mesma forma 1 px maior, na cor da forma × 0,5.
- **Movimentos.** Os movimentos esticam, espelham e giram o personagem com uma transformação aplicada
  a cada primitiva, porque o `framebuf` não tem `scale`, `rotate` nem recorte.
- **Esconder no buraco.** Para esse movimento, o chão é repintado por cima do personagem.

## Se algo não funcionar

- **Imagem deslocada ou com uma faixa:** ajuste a linha `self._cmd(0x2B, ...)` em `hw.py`.
- **Imagem com falhas:** baixe `baudrate=40_000_000` para `24_000_000` em `hw.py`.
- **Sem som ou microfone:** o jogo continua funcionando e mostra o motivo no terminal do Thonny ou do
  `mpremote`. O áudio é configurado registrador por registrador, então é a primeira coisa a conferir.
- **Ele se assusta à toa, ou não ouve nada:** ponha `MOSTRAR_VOLUME = True` no `main.py`, rode pelo
  Thonny e ajuste `LIMIAR_GRITO` olhando os números.
- **A placa não entra em modo de gravação:** segure BOOT, aperte e solte RST, e só então solte BOOT.
  A porta costuma ser `/dev/cu.usbmodem101` no Mac (`bash deploy.sh /dev/sua-porta` para outra).
- **Aviso de bateria nunca aparece:** a placa precisa de bateria ligada no conector. Sem bateria o
  chip de energia responde "sem bateria" e o aviso fica desligado.
- **O cérebro começou do zero:** o `brain.bin` sumiu ou estragou, e o `brain.bak` também. Nasce um
  cérebro novo com outra semente; é o esperado depois de um `deploy.sh` sem `--so-arquivos`.

O guia antigo, mais detalhado, continua em [LEIA-ME.md](LEIA-ME.md).

## Roadmap

- [x] Clima, Wi-Fi pelo celular e amigos por perto (v1.4)
- [x] Um cérebro de spikes que aprende com o dono, com raio-X (v1.5)
- [ ] Espalhar a decisão do cérebro por vários quadros (hoje a animação perde ~50 ms uma vez por segundo)
- [ ] Brincadeiras e ações sociais entre duas Capis guiadas pelo cérebro
- [ ] Estações e festas do ano no modo Olhar
- [ ] Construções no cenário (fogueira, barquinho, cabana)
- [ ] Mais personagens desenhados por crianças. [Mande o seu!](CONTRIBUTING.md#novos-personagens)

## Contribuir

Contribuições são muito bem-vindas: código, personagens, falas, traduções e sons. Leia o
[CONTRIBUTING.md](CONTRIBUTING.md) e o [Código de Conduta](CODE_OF_CONDUCT.md). Issues e PRs em
português ou inglês, tanto faz.

## Créditos e licença

O código está sob a [licença MIT](LICENSE). Sons, fontes e outras peças de terceiros têm licenças
próprias, listadas em [CREDITOS.md](CREDITOS.md).
