#!/bin/bash
set -e

SO_ARQUIVOS=0
if [ "$1" = "--so-arquivos" ]; then SO_ARQUIVOS=1; shift; fi
PORT=${1:-/dev/cu.usbmodem101}
FIRMWARE=/tmp/micropython_s3_spiram_oct.bin
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Deploy Capi → ESP32-S3 ==="
echo ""

# Verifica porta
if [ ! -e "$PORT" ]; then
  echo "Porta $PORT não encontrada."
  echo ""
  echo "Coloque a placa em download mode:"
  echo "  Segure BOOT → aperte e solte RST → solte BOOT"
  echo ""
  echo "Depois rode novamente: bash deploy.sh"
  exit 1
fi

if [ "$SO_ARQUIVOS" = 0 ]; then
  # Baixa firmware se não existir
  if [ ! -f "$FIRMWARE" ]; then
    echo "Baixando MicroPython ESP32-S3 SPIRAM_OCT..."
    curl -L "https://micropython.org/resources/firmware/ESP32_GENERIC_S3-SPIRAM_OCT-20250415-v1.25.0.bin" \
         -o "$FIRMWARE" --progress-bar
    echo ""
  fi
  echo "Porta: $PORT"
  echo "Firmware: $FIRMWARE"
  echo ""
  echo "→ Apagando flash (isso zera os bichinhos salvos)..."
  esptool.py --chip esp32s3 --port "$PORT" erase_flash
  echo ""
  echo "→ Gravando MicroPython..."
  esptool.py --chip esp32s3 --port "$PORT" write_flash -z 0 "$FIRMWARE"
  echo ""
  echo "→ Aguardando placa reiniciar..."
  sleep 3
fi

echo ""
echo "→ Copiando arquivos e sons..."
mpremote connect "$PORT" \
  cp "$DIR/main.py" : \
  + cp "$DIR/hw.py" : \
  + cp "$DIR/desenho.py" : \
  + cp "$DIR/vida.py" : \
  + cp -r "$DIR/sons" :

# Acerta o relógio da placa com a hora deste computador (não precisa de internet)
AGORA=$(date "+%Y, %-m, %-d, %-H, %-M, %-S")
echo "→ Acertando o relógio da placa: $(date "+%d/%m/%Y %H:%M:%S")"
mpremote connect "$PORT" \
  exec "from machine import I2C, Pin; import hw; hw.Relogio(I2C(0, scl=Pin(14), sda=Pin(15), freq=400000)).acertar($AGORA)" \
  + reset

echo ""
echo "✓ Pronto! A Capi deve aparecer na tela em instantes."
