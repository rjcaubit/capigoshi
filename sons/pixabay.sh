#!/bin/bash
# Converte os efeitos baixados do Pixabay (Pixabay Content License: uso livre, sem atribuicao)
# para o formato da placa: 16 kHz, 16 bits, estereo, sem cabecalho, curtinhos e no mesmo volume.
# Uso: baixe cada som clicando em "Free download" (vai para ~/Downloads) e rode: bash sons/pixabay.sh
set -e
cd "$(dirname "$0")"
mkdir -p extra
# Os arquivos vao para sons/extra/ (fora do git: a licenca do Pixabay nao permite redistribuir o som solto).
ORIGEM=${1:-$HOME/Downloads}

# nome  id-no-pixabay  duracao-max(s)   pagina
LISTA="
clique  467466 0.4  https://pixabay.com/sound-effects/clean-minimal-pop-467466/
feliz   6346   1.8  https://pixabay.com/sound-effects/film-special-effects-short-success-sound-glockenspiel-treasure-video-game-6346/
amor    115095 1.2  https://pixabay.com/sound-effects/film-special-effects-sound-effect-twinklesparkle-115095/
comer   39234  0.8  https://pixabay.com/sound-effects/film-special-effects-cartoon-bite-39234/
banho   229138 0.8  https://pixabay.com/sound-effects/film-special-effects-bubble-popping-229138/
remedio 546563 1.6  https://pixabay.com/sound-effects/film-special-effects-fantasy-healing-spell-soft-magic-chime-1-546563/
susto   99300  1.0  https://pixabay.com/sound-effects/film-special-effects-surprise-sound-effect-99300/
bocejo  42499  1.5  https://pixabay.com/sound-effects/people-yawn-42499/
piu     535477 0.8  https://pixabay.com/sound-effects/film-special-effects-sweet-bird-chirping-1-535477/
triste  383962 1.4  https://pixabay.com/sound-effects/film-special-effects-fail-trumpet-02-383962/
moeda   230517 0.8  https://pixabay.com/sound-effects/film-special-effects-coin-recieved-230517/
pulo    6462   0.8  https://pixabay.com/sound-effects/film-special-effects-cartoon-jump-6462/
"

faltam=0
while read -r nome id dur pagina; do
  [ -z "$nome" ] && continue
  arq=$(ls -t "$ORIGEM"/*"$id"*.mp3 2>/dev/null | head -1 || true)
  if [ -z "$arq" ]; then
    echo "FALTA  $nome  -> abra $pagina e clique em Free download"
    faltam=$((faltam + 1))
    continue
  fi
  # corta o silencio do comeco, limita a duracao, fade-out curto e volume parecido entre todos
  ffmpeg -v error -y -i "$arq" \
    -af "silenceremove=start_periods=1:start_threshold=-45dB,atrim=0:$dur,afade=t=out:st=$(echo "$dur - 0.12" | bc):d=0.12,loudnorm=I=-20:TP=-6:LRA=7,volume=0.8" \
    -ar 16000 -ac 2 -f s16le "extra/$nome.raw"
  printf "ok     %-8s <- %s (%d bytes)\n" "$nome" "$(basename "$arq")" "$(stat -f%z "extra/$nome.raw")"
done <<< "$LISTA"

if [ "$faltam" -gt 0 ]; then
  echo ""
  echo "$faltam som(ns) ainda nao baixado(s). Os que faltam continuam com o som antigo (Kenney)."
fi

# ---- voz quando ele fala: https://pixabay.com/sound-effects/film-special-effects-alien-voice-102709/
# O original tem 9 s com 4 frases. Corta um pedaco de cada frase (comecos medidos: 0,2 / 3,5 / 5,4 / 8,1 s),
# deixa mais agudo e um pouco mais rapido (estilo minion) e limita a ~1,3 s. Cada fala sorteia um.
voz=$(ls -t "$ORIGEM"/*102709*.mp3 2>/dev/null | head -1 || true)
if [ -z "$voz" ]; then
  echo "FALTA  voz      -> abra https://pixabay.com/sound-effects/film-special-effects-alien-voice-102709/ e clique em Free download"
else
  i=0
  for ini in 0.2 3.5 5.4 8.1; do
    i=$((i + 1))
    ffmpeg -v error -y -ss "$ini" -t 1.9 -i "$voz" \
      -af "aresample=44100,asetrate=44100*1.45,aresample=44100,atrim=0:1.3,afade=t=in:d=0.03,afade=t=out:st=1.15:d=0.15,loudnorm=I=-20:TP=-6:LRA=7,volume=0.8" \
      -ar 16000 -ac 2 -f s16le "extra/fala$i.raw"
    echo "ok     fala$i    <- $(basename "$voz") a partir de $ini s ($(stat -f%z "extra/fala$i.raw") bytes)"
  done
fi
