# CODEMAP — Capigoshi

Índice canônico do código que roda na placa (Waveshare ESP32-S3-Touch-LCD-1.83, MicroPython 1.25).
Fica na raiz, e não em `docs/`, porque `docs/` é o site publicado no GitHub Pages.

## Índice rápido

| Arquivo | Linhas | Papel | Depende de |
|---|---|---|---|
| `main.py` | ~1560 | Jogo: estado do bichinho, modos (Cuidar/Olhar/Passear), menu, toque, botão BOOT, laço principal; no Olhar, liga o cérebro (`atualizar_cerebro`, `expressar`) | `hw`, `desenho`, `vida`, `rede`, `portal`, `companion.placa` |
| `hw.py` | ~410 | Drivers: `Tela` (ST7789), `Toque` (CST816D), `Movimento` (QMI8658), `Relogio` (PCF85063), `Bateria` (AXP2101 + tecla PWR), `Som` (ES8311 alto-falante + ES7210 microfones, I2S(0) compartilhado, 16 kHz estéreo) | `machine`, `framebuf` |
| `desenho.py` | ~1400 | Tudo que é desenhado: cenário, personagens (`ELENCO`), balões, menu, telas de Wi-Fi. Texto só ASCII em fonte 8x8 | `hw` (cores e tamanho) |
| `vida.py` | ~680 | Motor de comportamento: 23 movimentos (`MOVES`), falas (`FRASES`, `MOVE_FALAS`), reações a toque, colo, sacudida e barulho | — |
| `rede.py` | ~390 | Wi-Fi intermitente (hora e clima a cada 30 min) e amigos por ESP-NOW no canal 1 | `network`, `espnow`, `ntptime` |
| `portal.py` | ~290 | Configuração do Wi-Fi pelo celular (rede aberta + QR code + página), grava `wifi.json`; com o cérebro ligado, serve o raio-X (`/raiox` e `/brain.json`) | `network`, `socket` |
| `companion/` | ~2000 | Cérebro SNN do modo Olhar (Companion), rodando na placa: `config`, `actions` (catálogo das 100 ações), `encoder`, `snn`, `learn`, `drives`, `reward`, `relogio` (hora → saída, issue #3), `clima` (tempo lá fora → alvo do humor, issue #4), `cerebro` (com `resumo()`, issue #5), `nucleo` + `nucleo_viper` (laços quentes; viper na placa), `placa` (ponte com a placa e `brain.bin`), `expressao` (movimento, fala e som das 100 ações), `raiox.html` (página do raio-X); `sim/` simulador, aceites e `raiox`; `testes/` unittest | — (só `array` e `random`) |
| `CALIBRACAO.md` | — | Constantes do cérebro que mudaram em relação à fonte e por quê | — |
| `sons/` | — | Sons `.raw` 16 kHz 16 bits estéreo; `sons/extra/` fora do git (Pixabay) | — |
| `deploy.sh` | — | Grava o MicroPython (apaga a flash) e copia os arquivos | `esptool.py`, `mpremote` |
| `docs/` | — | Site publicado (GitHub Pages): `index.html` (com a seção do cérebro), `cerebro.html` (matemática e lógica do cérebro, com laboratório do neurônio LIF), `celular.html` | — |
| `README.md` / `README.pt-BR.md` | — | README principal em inglês e versão em português (o `LEIA-ME.md` é o guia antigo, mais detalhado) | — |
| `design_handoff_capigoshi_1c/` | — | Fonte de verdade visual (`capigoshi-render.js`) | — |
| `previa/` | — | Prévia no computador (MicroPython Unix) | — |
| `sdd/ISSUE_{n}/` | — | Specs e tasks do processo SDD | — |

## Pontos de integração

- **Laço principal:** `main.passo(agora, dt)` (`main.py:1385`) chama, em ordem, som, toque, botão, menu, bateria, envelhecimento, sensores, rede, modo atual, vida e desenho.
- **Toque:** `processar_toque` → `pressionar` / `arrastar` / `soltar` (`main.py:1249-1350`). No corpo do bichinho: toque curto = carinho, segurar e arrastar = colo (`toque_vida`).
- **Botão BOOT:** `verificar_botao` (`main.py:1352`): toque curto fecha menu ou volta do Passear, 3 toques = offline, segurar 3 s = portal do Wi-Fi.
- **Falas:** `V.falar(L, vt, texto)` (balão do bichinho, 2 linhas × 14 letras, `|` quebra) e `balao(quem, tipo, texto)` / `sistema(texto)` em `main.py`.
- **Movimentos:** `V.tocar(L, vt, id, say=None)`; `vt` é o relógio contínuo da vida (ms), não `ticks_ms`.
- **Áudio:** `som.tocar(nome)` toca em segundo plano (I2S TX com `irq`) e fecha o microfone; `som.atualizar()` reabre o microfone no fim. `som.volume_mic()` lê o pico do microfone.
- **Rede:** `rede.passo(...)` devolve eventos (`chegou`, `clima`, `hora`...). O Wi-Fi conecta só por alguns segundos e volta ao canal 1 (`_canal_dos_amigos`).

## Arquivos de estado na placa

`config.json`, `capi.json` (e um por personagem), `clima.json`, `presentes.json`, `wifi.json` (fora do git),
`brain.bin` e `brain.bak` (o cérebro: pesos, drives e relógio dos hábitos, com crc32) e `raiox.html` (cópia de
`companion/raiox.html`).

## Cérebro SNN (`companion/`)

- **Entrada:** `Cerebro.segundo(sentidos, agora_ms)` uma vez por segundo, de dentro do laço (sem `Timer`); devolve o
  índice da ação em `actions.CATALOGO`. Reações do dono entram por `Cerebro.evento(nome, agora_ms)`.
- **Clima:** os sentidos aceitam `tempo` (nome de `rede.tipo_de`, ou `None` sem previsão) e `graus` (o codificador trunca
  para inteiro). Na fase 1, o `main.py` passa `rede.tipo_de(rede.wx(epoch))` quando `wx` não é `None`.
- **Raio-X (issue #5):** `Cerebro.resumo()` devolve um dict só com tipos simples (vira JSON): vontades, hábitos do
  relógio, mais feitas hoje e ontem, gosta e evita (`w_ho − w_ho0`), as últimas 200 recompensas e os drives de hora
  em hora. Não muda a decisão. `python3 -m companion.sim.raiox [cenario] [dias] [semente] [chuva]` grava
  `companion/sim/saida/raiox-*.html` (fora do git). A página `companion/raiox.html` não usa nada de fora; sem dados
  embutidos, ela pede `brain.json`, que o `portal.py` serve junto com `/raiox`.
- **Na placa:** `main.atualizar_cerebro` cria a `placa.Ponte` ao entrar no Olhar. O segundo do cérebro é o do
  relógio local (`relogio.epoch()`), então a meia-noite e as horas cheias batem. Cada ação nova vira movimento, fala
  e som (`expressao.py`); o sorteio do `vida.py` dá lugar a `vida.OCIOSO`. Eventos: toque curto no corpo = carinho,
  fora = toque, segurar parado (`SEGURAR_MS`) no corpo = estrela, no fundo = shh, colo, sacudida leve ou forte,
  barulho e comida (ao entrar em "comendo" na rotina). `brain.bin` grava a cada 10 min, ao dormir, ao sair do
  Olhar e ao abrir o portal; ao religar, drives e idade andam o tempo desligada (até 24 h).
- **Velocidade:** `nucleo.py` tem os laços quentes em Python (CPython e testes); na placa, `nucleo_viper.py` troca
  pela mesma conta em `@micropython.viper` (tick de 16 ms para 2,7 ms; decisão de 20 ticks em ~54 ms). Os dois dão
  os mesmos pesos, inteiro por inteiro. O MicroPython unix do Mac ARM não tem viper e usa a versão em Python.
- **Testes:** `python3 -m unittest discover -s companion/testes -t .` e `python3 -m companion.sim.aceite todos`
  (velocidade, silêncio, hábito, `sementes` e `clima`, ~11 min).
- **Fonte das regras:** `sdd/ISSUE_2/00-fonte.md`; divergências em `CALIBRACAO.md`.
