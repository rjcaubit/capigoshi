# Capi para ESP32-S3-Touch-LCD-1.83 (MicroPython)

Arquivos que vão para a placa: `main.py`, `hw.py`, `desenho.py`, `vida.py`, `rede.py`, `portal.py` e a pasta `sons/`.
O Wi-Fi é opcional e se configura pelo celular (veja "Internet e amigos"); quem preferir pode gravar um `wifi.json` a partir do `wifi_exemplo.json`.

## 1. Gravar o MicroPython (uma vez só)

1. Baixe o firmware em https://micropython.org/download/ESP32_GENERIC_S3/
   Escolha a variante **SPIRAM_OCT** (a placa tem 8 MB de PSRAM octal; sem ela a tela não cabe na memória).
2. Instale o gravador: `pip install esptool`
3. Coloque a placa em modo de gravação: segure BOOT, aperte e solte RESET, solte BOOT.
4. Grave (troque COM5 pela sua porta; no Mac/Linux é algo como /dev/ttyACM0):

       esptool.py --chip esp32s3 --port COM5 erase_flash
       esptool.py --chip esp32s3 --port COM5 write_flash -z 0 ESP32_GENERIC_S3-SPIRAM_OCT-xxxx.bin

## 2. Copiar o jogo

Pelo Thonny: abra cada arquivo e use "Salvar como > Dispositivo MicroPython" com o mesmo nome.

Ou pela linha de comando:

    pip install mpremote
    mpremote cp main.py hw.py desenho.py vida.py rede.py portal.py :
    mpremote cp -r sons :
    mpremote reset

O `main.py` roda sozinho toda vez que a placa liga.

Atalho: `bash deploy.sh` grava tudo do zero (apaga os bichinhos salvos). Para só atualizar os arquivos, os sons e a hora, sem apagar nada: `bash deploy.sh --so-arquivos` (a placa ligada normalmente, sem modo de gravação).

## 3. Como funciona

- Puxe a tela de cima para baixo (a partir da alcinha no topo) para abrir os Ajustes: modo **Cuidar** (Pet), **Olhar** (Companion) ou **Passear**, escolha entre 10 personagens, hora **Real** ou **Simulada** (dia em 30, 15 ou 10 min) e som. Solte acima da metade para fechar, ou toque na alça. O botão BOOT também fecha o menu e volta do Passear.
- Ciclo de vida: ovo (choca em 10 minutos de verdade; cada toque no ovo aquece e adianta 20 s, e na metade ele racha) → filhote (3 dias) → adulto (o tempo que faltar para completar de 23 a 40 dias de vida, sorteado) → idoso (5 dias, sobrancelhas brancas e bengala) → numa noite ele vira estrela com o nome no céu, e de manhã aparece um ovo novo. Os dias são do jogo: com hora Real são dias de verdade; com Simulada passam mais rápido. As estrelas dos que já foram continuam no céu à noite.
- Trocar de personagem (setas no menu) ou tocar em **zerar** pergunta antes, porque começa do zero com um ovo novo.
- Passear: segure o lado direito ou esquerdo da tela para andar e pegar moedas; toque curto pula. Três toques rápidos no mesmo lado fazem ele andar sozinho (a seta fica laranja); mais três, ele para.
- Sono: das 22:00 às 6:00 em todos os modos. Gritar ou sacudir acorda por 1 minuto, depois ele volta a dormir.
- Hora sem internet: o `deploy.sh` acerta o relógio da placa com a hora do computador. No menu, em hora Real, os botões -1m / -1h / +1h / +1m corrigem na mão.
- Vida (no Cuidar e no Olhar): o bichinho respira, sorteia um dos 21 movimentos da hora do dia (dançar, cambalhota, cheirar flor, esconder, espirrar...) e às vezes fala. Toque nele: carinho. Toque fora: ele olha em volta. Segure e arraste: colo (vai e volta rápido = sacudir). Barulho: leva susto. Sem atenção por 10 min: chora e chama.
- Sons: pasta `sons/`. Para usar os efeitos do Pixabay, abra cada link listado em `sons/pixabay.sh`, clique em "Free download" e rode `bash sons/pixabay.sh`; os que faltarem continuam com os da Kenney (CC0). No menu, o botão **som/mudo** liga e desliga. Das 22:00 às 8:00 (hora de verdade) ele fica mudo sozinho, para não acordar ninguém; o horário está em `SILENCIO_DE` e `SILENCIO_ATE`, no `main.py`.
- `previa/`: roda o firmware de verdade no MicroPython do computador e gera PNGs das telas (`brew install micropython`, depois `cd previa && micropython rodar.py && python3 montar.py`). O `novidades.py` da mesma pasta testa Wi-Fi, clima, amigos e presentes com um rádio de mentira.
- `design_handoff_capigoshi_1c/`: especificação visual (direção 1c Diorama) que o `desenho.py` segue.
- `simulador.html`: simulador do visual antigo (antes da 1c). Para o visual novo, use `previa/` ou abra `design_handoff_capigoshi_1c/Capigoshi 1c Diorama.dc.html`.
- Modo Pet: botões Comer (fome e um pouco de energia), Brincar (alegria, mas cansa), Banho (saúde e energia, e limpa os cocôs) e Remédio. Toda barra tem um botão que enche até o fim. Ela dorme sozinha das 22h às 6h e tira cochilos se ficar sem energia. Se ficar doente, aparece um termômetro e só o remédio cura.
- Modo Companion: sem botões. Com hora Simulada, um dia passa em 10 a 30 minutos; ela come, passeia, toma banho no lago, vê o pôr do sol, dorme, e recebe visitas (passarinho, tartaruga, borboleta, sapo e vaga-lumes à noite).
- Nos dois modos: sacudir a placa ou gritar perto. Acordada, ela adora. Dormindo, leva um susto.
- Tocar na Capi faz carinho.

## 4. Internet e amigos

- **Ligar no Wi-Fi (como lâmpada inteligente):** segure o BOOT por 3 segundos, ou aperte BOOT e PWR juntos (os dois botões da lateral), ou toque nas barrinhas de sinal no canto dos Ajustes. A placa vira uma rede aberta chamada **Capigoshi** e mostra um QR code. Aponte a câmera do celular: ele entra na rede e a página de configuração abre sozinha (se não abrir, digite `192.168.4.1` no navegador). Escolha a rede de casa, digite a senha e pronto: a placa grava e reinicia. BOOT de novo cancela.
- **Hora e tempo lá fora:** com Wi-Fi, de 30 em 30 minutos a placa acerta o relógio (o fuso vem junto) e pega a previsão no Open-Meteo, para a cidade do seu endereço de internet. O céu acompanha: nuvens, chuva, tempestade com raio, neve, neblina e vento. No Olhar a temperatura aparece ao lado da hora, e o bichinho comenta ("que chuva!", "que calor!"). Previsão com mais de 3 horas deixa de valer e o céu volta ao normal.
- **Amigos por perto:** duas placas bem encostadas (uns dois palmos) se reconhecem pelo rádio, sem precisar de internet. Os dois acordam, pulam de felicidade, o amigo espia pelo canto da tela e cada um manda um presente por minuto durante 5 minutos. Os presentes ficam no gramado e somem depois de 3 horas. Depois de uma rodada, eles descansam 10 minutos antes de trocar presentes de novo.
- **Modo offline:** três toques rápidos no BOOT desligam o rádio inteiro (sem internet e sem amigos por perto); mais três toques ligam de novo. A escolha fica guardada mesmo desligando a placa, e as barrinhas de sinal nos Ajustes ficam apagadas.
- Ajustes disso ficam no topo do `rede.py`: `RSSI_PERTO` (quão perto é "pertinho"; mais perto de zero = precisa encostar mais), `CLIMA_MS` e o número de presentes.

## 5. Ajustes (topo do main.py)

- A duração do dia agora é escolhida no menu (hora Simulada 1x/2x/3x).
- `PINO_BOTAO`: pino do botão físico (0 = BOOT).
- `TICK_PET_SEG`: a cada quantos segundos a fome/alegria/energia mudam no modo Pet.
- `LIMIAR_GRITO`: sensibilidade do microfone. Para calibrar, coloque `MOSTRAR_VOLUME = True`, rode pelo Thonny e veja os números enquanto fala e grita; escolha um valor entre os dois.
- `LIMIAR_SACUDIDA`: sensibilidade da sacudida.

## 6. Se algo não funcionar

- Imagem deslocada ou cortada: a placa usa a tela de 240x284 sem deslocamento; se aparecer uma faixa, ajuste a linha `self._cmd(0x2B, ...)` em `hw.py`.
- Imagem com falhas: baixe `baudrate=40_000_000` para `24_000_000` em `hw.py`.
- Sem som ou microfone: o jogo continua funcionando normalmente e mostra o motivo no terminal do Thonny. O áudio é a parte mais delicada (os chips de som são configurados registrador por registrador), então é a primeira coisa a conferir.
