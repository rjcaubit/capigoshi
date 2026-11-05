# CODEMAP — Capigoshi

Índice canônico do código que roda na placa (Waveshare ESP32-S3-Touch-LCD-1.83, MicroPython 1.25).
Fica na raiz, e não em `docs/`, porque `docs/` é o site publicado no GitHub Pages.

## Índice rápido

| Arquivo | Linhas | Papel | Depende de |
|---|---|---|---|
| `main.py` | ~1450 | Jogo: estado do bichinho, modos (Cuidar/Olhar/Passear), menu, toque, botão BOOT, laço principal | `hw`, `desenho`, `vida`, `rede`, `portal` |
| `hw.py` | ~410 | Drivers: `Tela` (ST7789), `Toque` (CST816D), `Movimento` (QMI8658), `Relogio` (PCF85063), `Bateria` (AXP2101 + tecla PWR), `Som` (ES8311 alto-falante + ES7210 microfones, I2S(0) compartilhado, 16 kHz estéreo) | `machine`, `framebuf` |
| `desenho.py` | ~1400 | Tudo que é desenhado: cenário, personagens (`ELENCO`), balões, menu, telas de Wi-Fi. Texto só ASCII em fonte 8x8 | `hw` (cores e tamanho) |
| `vida.py` | ~680 | Motor de comportamento: 23 movimentos (`MOVES`), falas (`FRASES`, `MOVE_FALAS`), reações a toque, colo, sacudida e barulho | — |
| `rede.py` | ~390 | Wi-Fi intermitente (hora e clima a cada 30 min) e amigos por ESP-NOW no canal 1 | `network`, `espnow`, `ntptime` |
| `portal.py` | ~260 | Configuração do Wi-Fi pelo celular (rede aberta + QR code + página), grava `wifi.json` | `network`, `socket` |
| `companion/` | ~1230 | Cérebro SNN do modo Companion (issue #2, fase 0 — ainda não ligado ao `main.py`): `config`, `actions` (catálogo das 100 ações), `encoder`, `snn`, `learn`, `drives`, `reward`, `relogio` (hora → saída, issue #3), `cerebro`; `sim/` simulador e aceites; `testes/` unittest | — (só `array` e `random`) |
| `CALIBRACAO.md` | — | Constantes do cérebro que mudaram em relação à fonte e por quê | — |
| `sons/` | — | Sons `.raw` 16 kHz 16 bits estéreo; `sons/extra/` fora do git (Pixabay) | — |
| `deploy.sh` | — | Grava o MicroPython (apaga a flash) e copia os arquivos | `esptool.py`, `mpremote` |
| `docs/` | — | Site publicado (GitHub Pages): `index.html`, `celular.html` | — |
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

`config.json`, `capi.json` (e um por personagem), `clima.json`, `presentes.json`, `wifi.json` (fora do git).

## Cérebro SNN (`companion/`)

- **Entrada:** `Cerebro.segundo(sentidos, agora_ms)` uma vez por segundo, de dentro do laço (sem `Timer`); devolve o
  índice da ação em `actions.CATALOGO`. Reações do dono entram por `Cerebro.evento(nome, agora_ms)`.
- **Testes:** `python3 -m unittest discover -s companion/testes -t .` e `python3 -m companion.sim.aceite todos`
  (velocidade, silêncio, hábito e `sementes`, ~7 min).
- **Fonte das regras:** `sdd/ISSUE_2/00-fonte.md`; divergências em `CALIBRACAO.md`.
