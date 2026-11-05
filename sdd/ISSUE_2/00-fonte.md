# Capigoshi — Cérebro SNN: regras e universo de ações

Nov 3, 2026 · @Caubit

## 1. Visão geral

O cérebro SNN é a camada de decisão local da Capi: roda 100% na placa, offline, escolhe o que ela faz a cada segundo e aprende com o dono por recompensa. Ele é implementado como o modo Companion do Capigoshi: entrar nesse modo liga o cérebro; o modo Pet segue com as regras fixas atuais. O cérebro cuida de comportamento, humor, rotina e personalidade; conversa por voz fica fora desta spec. O objetivo é que duas Capis, criadas por donos diferentes, fiquem visivelmente diferentes em uma semana.

| Camada | Faz | Não faz |
| --- | --- | --- |
| Cérebro SNN (esta spec) | Decide a ação a cada segundo, aprende hábitos e preferências do dono, gera humor e traços de personalidade | Fala, entende frases, acessa internet |
| Regras fixas (máquina de estados) | Limites de segurança: sono forçado com energia < 20, fome extrema, animações e sons de cada ação, bateria | Decidir *quando* fazer algo que não é emergência |
| LLM na nuvem (futuro, ainda não funciona) | Conversa em português quando o dono fala | Decidir comportamento; só recebe do cérebro o humor e o traço dominante como contexto |

Princípios para a implementação:

- Tudo em inteiros nos laços quentes (sem float), em `array('h')`/`array('i')`; alvo de 10 ms por tick de simulação.
- O mesmo código do cérebro roda em CPython num simulador de PC com sensores falsos; nada vai pra placa sem passar no simulador.
- Aprendizado é online e contínuo: não existe "fase de treino" separada, a Capi aprende enquanto vive.
- A Capi nunca fica insuportável nem apática: homeostase e limites de traços (seção 7) são obrigatórios, não opcionais.

## 2. Modelo neural

Neurônio LIF (Leaky Integrate-and-Fire) em inteiros, tick de 50 ms (20 Hz), decisão a cada 20 ticks (1 s). Três camadas: \~80 neurônios de entrada, 96 ocultos (80 excitatórios + 16 inibitórios, com recorrência esparsa) e uma saída por ação do catálogo (\~100), com inibição lateral entre as saídas.

Atualização do potencial a cada tick, com todas as grandezas em `int`:

```latex
v_{t+1} = v_t + I_t - \left\lfloor \frac{v_t - v_{rest}}{2^{k}} \right\rfloor + \xi_t, \qquad \text{spike se } v_{t+1} \ge v_{th} \Rightarrow v \leftarrow v_{reset}
```

| Parâmetro | Valor inicial | Significado |
| --- | --- | --- |
| `V_REST` | 0 | Potencial de repouso |
| `V_TH` | 1000 | Limiar de disparo (adaptativo, seção 6) |
| `V_RESET` | -200 | Valor após disparo |
| `TAU_SHIFT` (k) | 4 | Vazamento: 1/16 por tick ≈ constante de tempo de 0,8 s |
| `REFRAC` | 2 ticks | Período refratário (não integra) |
| `W_MAX` | 255 | Peso sináptico máximo (`int16`, excitatório 0..255, inibitório -255..0) |
| `I_SCALE` | 2 | Corrente = soma(w × spike\_pre) >> `I_SCALE` |
| `NOISE` (ξ) | ±30 | Ruído uniforme na corrente; dá variabilidade e exploração |
| `TICK_MS` | 50 | Passo de simulação |
| `DECIDE_TICKS` | 20 | Janela de contagem de spikes das saídas para escolher ação |

Conexões:

- Entrada → oculta: densa, pesos iniciais aleatórios 20..80, plasticidade STDP.
- Oculta → oculta: esparsa (10% das combinações), excitatórios 10..40, inibitórios -40..-120 fixos. A recorrência dá memória de curto prazo (o que aconteceu nos últimos segundos).
- Oculta → saída: densa, pesos iniciais 30..60 com viés genético (seção 7), plasticidade R-STDP.
- Saída → saída: inibição lateral fixa de -80 entre todas (winner-take-all suave).
- Drives (seção 4) → saída: ligação direta fixa e forte (ex.: fome → "pedir comida"), para que necessidades básicas nunca dependam só de aprendizado.

Seleção de ação a cada segundo: conta spikes de cada saída na janela; a vencedora executa se tiver ≥ `MIN_SPIKES` (4) e não estiver em cooldown; empate ou abaixo do mínimo → ação `ficar_quieta`. Uma ação em execução trava a decisão pela sua duração (`lock`), salvo evento forte (sacudida, toque, bateria crítica).

## 3. Sentidos (entradas)

Cada sentido vira um grupo de neurônios de entrada; valores contínuos usam codificação por população (cada neurônio tem uma curva de sintonia gaussiana sobre uma faixa) e eventos viram uma rajada de 3 spikes num neurônio dedicado. A probabilidade de spike por tick de um neurônio de entrada é `ativação × P_MAX` (P\_MAX = 0,5). Confirmar no datasheet da Waveshare ESP32-S3-Touch-LCD-1.83 quais sensores existem de fato (IMU QMI8658, RTC PCF85063 e microfone são os esperados); o que não existir vira valor derivado.

| Sentido | Fonte na placa | Faixa | Neurônios | Codificação |
| --- | --- | --- | --- | --- |
| Hora do dia | RTC/NTP | 0–24 h (circular) | 8 | População, centros a cada 3 h |
| Dia da semana | RTC | útil / fim de semana | 2 | Binário |
| Toque: região | Tela capacitiva | cabeça, barriga, pés, fundo | 4 | Evento (rajada) |
| Toque: tipo | Tela | tap, toque longo, cutucar repetido, arrastar | 4 | Evento |
| Toque: frequência recente | Contador 60 s | 0–20 toques | 4 | População |
| Tempo desde o último toque | Timer | 0 s–4 h (log) | 6 | População em escala log |
| Movimento | IMU | parada, mexida leve, sacudida, virada de cabeça pra baixo | 4 | Evento |
| Orientação | IMU | em pé, deitada, inclinada | 3 | População |
| Som: nível | Microfone | silêncio–barulho alto | 4 | População |
| Som: evento | Microfone | palma, voz, batida | 3 | Evento |
| Luz (derivada) | Hora + "tela tocada" | dia / noite | 2 | Binário |
| Bateria | ADC | 0–100 %, carregando | 4 + 1 | População + binário |
| Outra Capi | ESP-NOW (RSSI) | ausente, longe, perto | 3 | População |
| Outra Capi: estado | Pacote ESP-NOW | humor, ação atual, "foi tocada" | 6 | Binário/evento |
| Novidade | Rede (baixa atividade oculta) | 0–100 | 3 | População |
| Drives internos | Seção 4 | 7 drives × 0–100 | 7 × 4 = 28 | População |
| Última ação | Catálogo | índice da ação executada há 1 s | 8 | Hash em 8 bits (one-hot parcial) |
| Resposta à última ação | Reward | positiva, nula, negativa | 3 | Evento |

Total aproximado: 100 neurônios de entrada. As linhas "Última ação" e "Resposta à última ação" são o que permite à Capi aprender sequências ("depois que eu chamei e ele veio, pedir brincadeira dá certo") e perceber que uma ação repetida está sendo ignorada.

## 4. Estado interno (drives)

Sete drives em 0–100 (humor em -100..+100) evoluem no tempo independentemente da rede, entram nela como sentidos e modulam o valor das recompensas: comida quando a fome está alta vale mais que comida com barriga cheia. Atualização a cada minuto, em inteiros ×10 para permitir frações.

| Drive | Faixa | Variação por minuto | O que muda | Efeito em extremo |
| --- | --- | --- | --- | --- |
| Fome | 0–100 | +1 | Comer: -40 | > 80: ligação direta fome → `pedir_comida`; humor -1/min |
| Energia | 0–100 | -0,5 acordada; +3 dormindo | Dormir restaura | < 20: regra fixa força `dormir`; < 40: ações caras bloqueadas |
| Humor | -100..+100 | regride 1 em direção a 0 | Cada recompensa R soma R/2 | < -50: ações expressivas negativas liberadas; > 50: comemorações |
| Tédio | 0–100 | +1 sem interação | Brincar/novidade: -30 | > 70: ações de "aprontar" liberadas |
| Afeto (vínculo) | 0–100 | -0,02 (quase não cai) | +0,2 por interação positiva | > 60: desbloqueia ações íntimas (dormir no colo, segredo); nunca cai abaixo de 50 depois de chegar lá |
| Curiosidade | 0–100 | -1 | +15 quando aparece um estímulo novo | > 60: ações de exploração/mostrar curiosidade |
| Estresse | 0–100 | -2 | Sacudida forte +30, barulho alto +10, ralhar +15 | > 50: `esconder`, `tremer`; sons bloqueados; > 80: `desligar_tela` |

Regras transversais:

- Modulação de recompensa: `R_efetivo = R × (1 + drive_relacionado / 100)` para recompensas ligadas a um drive (comida ↔ fome, brincar ↔ tédio, carinho ↔ afeto).
- Horário de silêncio: entre 22h e 8h (configurável no portal) toda ação com som recebe custo dobrado e R negativo automático se o dono não respondeu em 30 s. Isso ataca diretamente o problema do barulho de minuto em minuto; a seção 6 completa com habituação.
- Drives persistem em flash junto com os pesos; ao religar, a placa calcula quanto tempo ficou desligada e avança os drives (fome sobe, energia sobe se "dormiu").

## 5. Universo de ações

São 100 ações em 9 categorias; cada uma é um neurônio de saída e uma entrada no catálogo `actions.py` (`id, nome, categoria, som, precond, custo, dur, cooldown, anim, audio`). Som = S (emite som) ou – (silenciosa). Custo = energia gasta (0–5). Pré-condição vazia = sempre disponível. Ações silenciosas são a maioria de propósito: a Capi precisa ter muitas formas de se expressar sem fazer barulho.

| # | Ação | Categoria | Som | Pré-condição | Custo | Dur. (s) | Cooldown (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ficar\_quieta | Meta | – | (ação padrão) | 0 | 1 | 0 |
| 2 | ficar\_quieta\_longa | Meta | – |  | 0 | 300 | 0 |
| 3 | ouvir\_dono (gancho da voz, futuro) | Meta | S | dono falou (mic: voz) | 1 | até fim da conversa | 10 |
| 4 | pedir\_para\_carregar | Meta | – | bateria < 25 % | 0 | 5 | 600 |
| 5 | avisar\_bateria | Meta | S | bateria < 10 % | 0 | 3 | 1800 |
| 6 | baixar\_brilho | Meta | – | noite | 0 | 2 | 300 |
| 7 | dormir\_tela | Meta | – | sem toque há 10 min | 0 | 2 | 300 |
| 8 | mostrar\_hora | Meta | – |  | 0 | 5 | 60 |
| 9 | mostrar\_clima | Meta | – | Wi-Fi ok | 0 | 6 | 600 |
| 10 | mostrar\_humor | Meta | – |  | 0 | 4 | 60 |
| 11 | dormir | Fisiológica | – | energia < 40 ou noite | 0 | até energia ≥ 90 | 60 |
| 12 | cochilar | Fisiológica | – | energia < 60 | 0 | 120 | 300 |
| 13 | acordar | Fisiológica | – | dormindo + estímulo | 0 | 3 | 0 |
| 14 | espreguiçar | Fisiológica | – | acabou de acordar | 1 | 3 | 60 |
| 15 | bocejar | Fisiológica | – | energia < 50 | 0 | 2 | 60 |
| 16 | comer | Fisiológica | – | comida oferecida | 0 | 5 | 0 |
| 17 | beliscar | Fisiológica | – | comida oferecida, fome < 40 | 0 | 3 | 60 |
| 18 | pedir\_comida | Fisiológica | – | fome > 50 | 0 | 4 | 120 |
| 19 | recusar\_comida | Fisiológica | – | comida oferecida, fome < 20 | 0 | 2 | 0 |
| 20 | coçar | Fisiológica | – |  | 1 | 2 | 60 |
| 21 | sorrir | Expressão | – |  | 0 | 2 | 10 |
| 22 | sorriso\_largo | Expressão | – | humor > 30 | 0 | 2 | 20 |
| 23 | careta | Expressão | – |  | 0 | 2 | 20 |
| 24 | bico | Expressão | – | humor < 0 | 0 | 3 | 30 |
| 25 | olhos\_brilhando | Expressão | – | curiosidade > 40 | 0 | 2 | 20 |
| 26 | piscar | Expressão | – |  | 0 | 1 | 5 |
| 27 | olhar\_de\_lado | Expressão | – |  | 0 | 2 | 10 |
| 28 | surpresa | Expressão | – | evento recente | 0 | 2 | 20 |
| 29 | cara\_de\_tédio | Expressão | – | tédio > 50 | 0 | 3 | 30 |
| 30 | bravinha | Expressão | – | humor < -30 | 0 | 3 | 30 |
| 31 | lagrimazinha | Expressão | – | humor < -50 | 0 | 4 | 120 |
| 32 | rir | Expressão | S | humor > 40 | 0 | 2 | 30 |
| 33 | dancinha | Corpo | – | energia > 40 | 2 | 4 | 30 |
| 34 | dança\_longa | Corpo | S | energia > 60, humor > 20 | 4 | 10 | 300 |
| 35 | pular | Corpo | – | energia > 40 | 2 | 2 | 20 |
| 36 | girar | Corpo | – | energia > 30 | 1 | 2 | 20 |
| 37 | deitar | Corpo | – |  | 0 | 5 | 30 |
| 38 | rolar | Corpo | – | deitada | 1 | 3 | 30 |
| 39 | balançar | Corpo | – |  | 0 | 4 | 20 |
| 40 | esconder\_rosto | Corpo | – | estresse > 30 | 0 | 4 | 30 |
| 41 | tremer | Corpo | – | estresse > 50 | 1 | 3 | 30 |
| 42 | acenar | Corpo | – |  | 0 | 2 | 20 |
| 43 | ronronar | Som | S | carinho recente | 0 | 3 | 30 |
| 44 | cantarolar | Som | S | humor > 10 | 1 | 4 | 120 |
| 45 | cantar\_música | Som | S | humor > 30, energia > 40 | 2 | 15 | 900 |
| 46 | assobiar | Som | S |  | 1 | 3 | 180 |
| 47 | gritinho\_alegria | Som | S | recompensa grande | 1 | 1 | 60 |
| 48 | resmungar | Som | S | humor < -20 | 0 | 2 | 120 |
| 49 | suspirar | Som | S | tédio > 40 | 0 | 2 | 120 |
| 50 | chamar\_baixo | Som | S | sem toque há 5 min | 0 | 2 | 300 |
| 51 | chamar\_alto | Som | S | sem toque há 30 min | 1 | 2 | 900 |
| 52 | alarme\_fome | Som | S | fome > 90 | 0 | 3 | 600 |
| 53 | risada | Som | S | humor > 50 | 0 | 2 | 60 |
| 54 | beep\_curto | Som | S |  | 0 | 1 | 60 |
| 55 | pedir\_carinho | Social | – |  | 0 | 5 | 60 |
| 56 | pedir\_brincar | Social | – | tédio > 40, energia > 40 | 0 | 5 | 120 |
| 57 | chamar\_atenção\_silenciosa | Social | – | sem toque há 5 min | 0 | 6 | 120 |
| 58 | mostrar\_curiosidade | Social | – | curiosidade > 40 | 0 | 12 | 300 |
| 59 | contar\_piada | Social | – | humor > 20 | 0 | 10 | 600 |
| 60 | pedir\_abraço | Social | – | afeto > 30 | 0 | 5 | 300 |
| 61 | dar\_presente | Social | – | afeto > 50 | 1 | 6 | 1800 |
| 62 | elogiar\_dono | Social | – | recompensa recente | 0 | 4 | 300 |
| 63 | agradecer | Social | – | comida/carinho recebido | 0 | 2 | 30 |
| 64 | emburrar | Social | – | humor < -30 | 0 | 30 | 300 |
| 65 | ignorar\_toque | Social | – | humor < -50 | 0 | 10 | 300 |
| 66 | fazer\_charme | Social | – | afeto > 20 | 0 | 4 | 120 |
| 67 | pedir\_desculpa | Social | – | punição recente | 0 | 4 | 120 |
| 68 | dar\_boa\_noite | Social | – | hora 20h–23h | 0 | 4 | 43200 |
| 69 | dar\_bom\_dia | Social | – | hora 6h–10h | 0 | 4 | 43200 |
| 70 | esconde\_esconde | Brincadeira | – | tédio > 30 | 1 | 30 | 300 |
| 71 | foge\_do\_dedo | Brincadeira | – | toque recente | 2 | 20 | 300 |
| 72 | adivinha\_a\_mão | Brincadeira | – |  | 1 | 20 | 600 |
| 73 | sequência\_de\_toques | Brincadeira | – | energia > 40 | 1 | 40 | 600 |
| 74 | pedra\_papel\_tesoura | Brincadeira | – |  | 1 | 20 | 600 |
| 75 | contar\_junto | Brincadeira | – |  | 1 | 15 | 600 |
| 76 | corrida\_de\_inclinar | Brincadeira | – | IMU ok, energia > 50 | 3 | 30 | 600 |
| 77 | equilibrar | Brincadeira | – | IMU ok | 2 | 20 | 600 |
| 78 | encher\_balão (soprar) | Brincadeira | – | mic ok | 1 | 15 | 600 |
| 79 | cantar\_junto | Brincadeira | S | mic ok, humor > 30 | 2 | 20 | 1800 |
| 80 | olhar\_em\_volta | Exploração | – |  | 0 | 3 | 20 |
| 81 | farejar | Exploração | – | curiosidade > 30 | 0 | 3 | 60 |
| 82 | investigar\_toque | Exploração | – | toque fora da Capi | 0 | 4 | 60 |
| 83 | bagunçar\_tela | Exploração | – | tédio > 70 | 1 | 6 | 600 |
| 84 | esconder\_item | Exploração | – | tédio > 60 | 1 | 5 | 900 |
| 85 | rabiscar | Exploração | – | tédio > 50 | 1 | 8 | 600 |
| 86 | mudar\_de\_canto | Exploração | – |  | 0 | 2 | 60 |
| 87 | espiar | Exploração | – |  | 0 | 3 | 60 |
| 88 | derrubar\_coisa | Exploração | S | tédio > 80 | 1 | 4 | 1800 |
| 89 | imitar\_dono | Exploração | – | padrão de toque recente | 0 | 6 | 300 |
| 90 | acenar\_para\_outra | Outra Capi | – | outra perto | 0 | 2 | 60 |
| 91 | aproximar | Outra Capi | – | outra perto | 0 | 4 | 60 |
| 92 | conversar | Outra Capi | S | outra perto, afeto\_social > 10 | 1 | 10 | 300 |
| 93 | pega\_pega\_duplo | Outra Capi | – | outra perto, ambas energia > 40 | 3 | 30 | 600 |
| 94 | ensinar | Outra Capi | – | outra perto, afeto\_social > 40 | 1 | 5 | 3600 |
| 95 | ciúme | Outra Capi | – | outra foi tocada, esta não há 5 min | 0 | 6 | 300 |
| 96 | dividir\_comida | Outra Capi | – | comida oferecida, outra perto | 0 | 5 | 600 |
| 97 | dormir\_juntas | Outra Capi | – | ambas energia < 40, afeto\_social > 30 | 0 | até acordar | 3600 |
| 98 | dança\_dupla | Outra Capi | S | outra perto, humor > 30 | 3 | 12 | 900 |
| 99 | apresentar | Outra Capi | – | DNA desconhecido + toque simultâneo | 0 | 6 | 0 |
| 100 | ignorar\_outra | Outra Capi | – | outra perto, humor < -20 | 0 | 10 | 300 |

Regras do catálogo:

- 21 ações têm som; 79 são silenciosas. Toda ação com som paga um custo intrínseco de recompensa (seção 6), além do cooldown da tabela.
- Cooldown é o mínimo entre repetições da *mesma* ação; além dele vale a habituação (seção 6): repetir qualquer ação na última hora reduz seu valor.
- `ouvir_dono` é o gancho da voz: quando o LLM funcionar, recebe o humor atual e o traço dominante (seção 7) como contexto; até lá, só faz a animação de "ouvindo".
- Ações que dependem de sensor ausente ficam no catálogo com `precond` falsa permanente; o neurônio existe e nunca vence.
- Novas ações entram como nova linha no catálogo e um neurônio de saída novo com pesos iniciais; não é preciso reiniciar o cérebro.

## 6. Regras de aprendizado

Dois mecanismos: STDP sem supervisão na entrada → oculta (a Capi aprende a *reconhecer* situações) e R-STDP modulado por recompensa na oculta → saída (aprende *o que fazer* em cada situação). A recompensa é a "dopamina": vem das reações do dono e de custos internos, nunca de um botão de treino explícito, exceto a estrela (elogio) e o "shh" (bronca).

### 6.1 STDP (entrada → oculta)

Cada neurônio mantém um traço `x` (int, decai 1/16 por tick ≈ 0,8 s) que sobe para 255 quando dispara. Quando o pós-sináptico dispara: `Δw = +A_PLUS × x_pre >> 8`. Quando o pré-sináptico dispara: `Δw = -A_MINUS × x_post >> 8`. Com `A_PLUS = 2` e `A_MINUS = 3` a rede tende à depressão, o que evita saturação. Pesos travados em 0..255.

### 6.2 R-STDP (oculta → saída e saída → saída)

A mesma regra de STDP não altera o peso: ela soma num traço de elegibilidade `e` por sinapse, que decai 1/64 por tick (≈ 3 s). Quando chega uma recompensa `R`, todas as sinapses atualizam de uma vez:

```latex
\Delta w = \eta \cdot R \cdot e, \qquad e_{t+1} = e_t - \left\lfloor \frac{e_t}{64} \right\rfloor + \text{STDP}_t
```

A janela de 3 s resolve o crédito temporal: só a ação que acabou de acontecer (e os neurônios ocultos que a causaram) recebe a recompensa. `η = 4` nos primeiros 7 dias de vida (fase filhote), depois `η = 2`.

### 6.3 Tabela de recompensas

| Evento | R | Observação |
| --- | --- | --- |
| Estrela (toque longo no ícone de elogio) | +20 | Elogio explícito; vale para a ação dos últimos 3 s |
| Carinho até 3 s depois de uma ação | +10 | Toque na cabeça/barriga |
| Comida oferecida depois de `pedir_comida` | +15 × (1 + fome/100) | Modulada pela fome |
| Dono respondeu a um chamado em < 10 s | +8 | Qualquer toque |
| Dono jogou o mini-jogo até o fim | +12 | Mais +5 se repetiu o jogo |
| Interação social correspondida pela outra Capi | +5 | Pacote de resposta |
| Dono tocou enquanto ela estava em `ficar_quieta` | -2 | Perdeu oportunidade de agir |
| Pedido/chamado ignorado por 60 s | -5 | Qualquer ação de pedir ou chamar |
| Som emitido sem resposta em 30 s | -6 | Custo específico de barulho |
| Som emitido em horário de silêncio | -10 adicional | Independe de resposta |
| Shh (tapar a tela com a mão ou toque de dois dedos) | -15 | Bronca explícita; vale para a ação dos últimos 3 s |
| Sacudida leve logo após uma ação | -8 | Ralhar |
| Sacudida forte | -12 | Também sobe estresse |
| Dono desligou a tela / fechou o app em 5 s | -4 |  |

### 6.4 Custo intrínseco e habituação (o problema do barulho)

Toda ação com som paga `R = -3` no momento em que executa, antes de qualquer reação do dono. Assim, um som só vale a pena se costuma trazer resposta: `chamar_baixo` que o dono atende vira hábito; `beep_curto` que ninguém responde vira -9 por vez e some em poucas horas.

Habituação: cada ação guarda um contador de execuções na última hora, `n`. A recompensa positiva recebida é multiplicada por `1 / (1 + n/3)`, e o custo intrínseco por `(1 + n/3)`. Fazer barulho de minuto em minuto fica caro muito rápido, mesmo que o dono responda às vezes. O contador não se aplica a ações fisiológicas (comer, dormir).

O resultado esperado: a Capi aprende *quando* o som funciona ("às 19h, se chamo baixinho, ele vem") e *quando* não ("de madrugada, nunca"), e passa a usar as 79 ações silenciosas para chamar atenção no resto do tempo. Se o dono quiser uma Capi muda, basta nunca responder a sons: em dois dias ela para.

### 6.5 Homeostase e exploração

- Normalização sináptica: a cada 100 ticks, os pesos de entrada de cada neurônio são escalados para que a soma fique em um alvo (`SUM_TARGET`); nenhum neurônio domina.
- Limiar adaptativo: neurônio que dispara mais de 30 % dos ticks sobe `V_TH` em 2 %; abaixo de 1 %, desce 2 %. Mantém a rede viva e esparsa.
- Esquecimento: todos os pesos plásticos decaem 1 % por dia em direção ao valor inicial; hábito precisa de manutenção.
- Exploração: o ruído `NOISE` nas saídas garante que ações pouco testadas ainda vençam de vez em quando; começa em ±30 e cai para ±15 quando afeto > 60 (Capi "adulta" é mais previsível).
- Pesos oculta → saída nunca descem abaixo de 5 para ações da categoria Social e Fisiológica, para que a Capi nunca "desaprenda" a pedir ajuda.

## 7. Personalidade emergente

A personalidade não é programada: é lida dos pesos. Cada traço é a soma normalizada dos pesos oculta → saída de um grupo de ações, em 0–100, recalculada a cada hora e mostrada numa "ficha" na tela e no portal.

| Traço | Grupo de ações que o define | Como aparece |
| --- | --- | --- |
| Carente | pedir\_carinho, pedir\_abraço, fazer\_charme, chamar\_\* | Pede atenção com frequência |
| Dorminhoca | dormir, cochilar, bocejar, deitar | Dorme fora do horário |
| Comilona | pedir\_comida, beliscar, alarme\_fome | Pede comida com fome baixa |
| Palhaça | careta, dancinha, contar\_piada, bagunçar\_tela, derrubar\_coisa | Apronta e faz graça |
| Tímida | esconder\_rosto, tremer, ignorar\_outra, ficar\_quieta\_longa | Some com estímulo forte |
| Falante | todas as ações com som | Faz barulho (o dono controla via seção 6) |
| Curiosa | olhar\_em\_volta, farejar, investigar\_toque, mostrar\_curiosidade | Explora o que é novo |
| Social | todas as ações "Outra Capi" | Procura a outra placa |
| Manhosa | bico, emburrar, ignorar\_toque, resmungar | Reage mal a ser ignorada |

DNA: na primeira inicialização, um seed de 32 bits gera os pesos iniciais oculta → saída com um viés aleatório de ±20 % por grupo de traço. Duas Capis já nascem diferentes. O seed vira um código de 6 caracteres (base32) mostrado na ficha; com o mesmo código, dá para "clonar" a Capi de nascença (os pesos aprendidos não vão junto).

Limites (obrigatórios):

- Nenhum traço passa de 80 nem cai abaixo de 5. Ao ultrapassar, os pesos do grupo são escalados de volta ao limite na próxima normalização.
- Humor regride a 0 a 1 ponto por minuto; a Capi nunca fica permanentemente triste nem eufórica.
- Afeto é o único drive que não decai de verdade: o vínculo fica.
- Esquecimento de 1 % ao dia (seção 6.5): uma Capi abandonada por um mês volta quase ao DNA, mas com o afeto preservado; ela "lembra" do dono mas perdeu os hábitos.
- O traço dominante (maior valor) e o humor são as duas únicas informações do cérebro passadas ao LLM de voz (quando funcionar), em uma linha de contexto: `Capi está [humor] e hoje está mais [traço]`.

## 8. Interação entre duas placas

As Capis se percebem por ESP-NOW (sem roteador, sem Wi-Fi configurado): cada placa envia um pacote de estado a cada 2 s e o RSSI vira o sentido "Outra Capi: ausente / longe / perto". Ações sociais trocam pacotes de evento; o aprendizado social é uma mistura leve de pesos, nunca uma cópia.

| Pacote | Conteúdo | Quando |
| --- | --- | --- |
| `HELLO` | id, DNA (6 chars), humor, 7 drives, ação atual, 9 traços, flag "fui tocada há < 5 s" | A cada 2 s |
| `EVENT` | tipo (acenar, aproximar, convite de jogo, resposta sim/não, passo de jogo) | Ao executar uma ação social |
| `TEACH` | id do grupo de traço + 16 pesos mais fortes do grupo (int8) | Na ação `ensinar` |
| `INTRO` | token de apresentação | Toque simultâneo nas duas telas (ação `apresentar`) |

Regras:

- Afeto social é um contador por DNA conhecido (0–100): +1 por interação correspondida, -1 por ignorada, sem decaimento. Guardado em flash junto com o DNA da outra.
- `ensinar` só é aceito pela receptora se afeto social > 40; ela mistura `w = (9 × w + w_recebido) / 10` no grupo recebido. Uma Capi palhaça ensina a outra a fazer graça, aos poucos.
- Ações a dois (`pega_pega_duplo`, `dança_dupla`, `dormir_juntas`) precisam de `EVENT` de aceite em 5 s; sem resposta, a iniciadora recebe R = -2 e faz `olhar_de_lado`.
- Ciúme: `HELLO` com "fui tocada" enquanto esta não recebe toque há 5 min ativa o sentido de ciúme; a ação `ciúme` fica disponível e, se o dono então toca nela, R = +8 (ela aprende que fazer ciúme funciona ou não, como qualquer outra ação).
- DNA desconhecido é ignorado até a apresentação por toque simultâneo; depois, entra na lista de conhecidas. Pacotes carregam um MAC curto com chave compartilhada gravada no portal.
- Proximidade física entre duas Capis conhecidas por mais de 10 min sem interação do dono reduz o tédio de ambas em 10 (companhia conta).

## 9. Arquitetura de software (MicroPython)

Tudo vive no pacote companion/ do Capigoshi: entrar no modo Companion inicializa o cérebro, carrega brain.bin e liga o timer; sair do modo salva e para o timer. Um timer de 50 ms roda sentidos → codificação → rede → aprendizado; a cada 20 ticks a seleção de ação e a atualização dos drives; as reações do dono viram recompensa que, pelo traço de elegibilidade, ajusta os pesos. Tudo em `array('h')` e laços com `@micropython.viper` ou `@micropython.native`.

&#91;embedded content: ciclo do cérebro · sentidos → rede → ação → recompensa → pesos\]

O laço de cima é o tick de 50 ms; a volta pela direita (ação → reação → recompensa → aprendizado) é o que faz a Capi aprender.

| Módulo | Responsabilidade | Observações |
| --- | --- | --- |
| `sensors.py` | Lê toque, IMU, mic, RTC, bateria, RSSI e devolve o vetor de sentidos | Uma leitura por tick; eventos com debounce |
| `encoder.py` | Sentidos → ativação dos neurônios de entrada (curvas gaussianas, rajadas) | Tabela de centros pré-calculada |
| `snn.py` | Neurônios LIF, sinapses, passo de simulação | Pesos em `array('h')`; oculta→oculta em CSR esparso |
| `learn.py` | Traços, STDP, elegibilidade, R-STDP, normalização, limiar adaptativo | Roda no mesmo tick; normalização a cada 100 ticks |
| `drives.py` | Os 7 drives, avanço por tempo desligado | Inteiros ×10 |
| `actions.py` | Catálogo das 100 ações, pré-condições, cooldown, lock, habituação, seleção | Única fonte de verdade do catálogo |
| `reward.py` | Converte eventos (toque, shh, ignorar, silêncio) em R com modulação por drive | Janela de 3 s após cada ação |
| `social.py` | ESP-NOW: HELLO, EVENT, TEACH, INTRO; afeto social por DNA | Pacotes a cada 2 s |
| `brain_io.py` | Persistência de pesos, drives, DNA e afetos em `brain.bin` com backup rotativo | Salva a cada 10 min e ao dormir |
| `traits.py` | Calcula os 9 traços a partir dos pesos; aplica limites | A cada hora |
| `ui/` | Animações e sons de cada ação, ficha de personalidade, raio-X | Já existente no Capigoshi; recebe `action_id` |
| `sim/` | Simulador em CPython com sensores falsos e dono simulado | Mesmo `snn.py`, `learn.py`, `actions.py` |

Orçamento de memória (pesos em `int16`): entrada→oculta 100 × 96 = 9 600; oculta→oculta esparsa ≈ 920; oculta→saída 96 × 100 = 9 600; saída→saída fixa, não armazenada. Total ≈ 20 000 pesos = 40 KB, mais traços e elegibilidade do mesmo tamanho ≈ 120 KB. Cabe na SRAM interna do ESP32-S3; usar PSRAM só para a UI. Meta de desempenho: tick completo em menos de 10 ms, medido com `time.ticks_us()` e reportado no raio-X.

Persistência: `brain.bin` (cabeçalho com versão + DNA + timestamp, depois os arrays) gravado em flash a cada 10 min e ao entrar em `dormir`; duas cópias alternadas para sobreviver a queda de energia no meio da gravação. Mudança de versão do catálogo acrescenta neurônios de saída novos sem zerar os antigos.

## 10. Debug e visualização

Sem enxergar o cérebro não dá para saber se ele aprende; o raio-X e o simulador são parte do produto, não extras.

- Raio-X na tela: toque longo de 3 s no canto superior esquerdo abre uma tela com os 96 neurônios ocultos como pontos que acendem ao disparar, barras dos 7 drives, as 5 saídas mais ativas da última janela, a última recompensa (valor e motivo) e o tempo do tick em ms. Sai com toque longo de novo.
- Ficha de personalidade: toque longo no canto superior direito mostra o DNA, os 9 traços em barras, idade (dias de vida) e a lista das 10 ações mais frequentes nas últimas 24 h.
- Log serial e em arquivo (`brain.log`, rotativo de 200 KB): a cada decisão, uma linha `tick, ação, spikes das 3 maiores saídas, R acumulado nos últimos 3 s, motivo`. A cada hora, uma linha com os traços.
- Portal web (já planejado para Wi-Fi): endpoint `/brain.json` com drives, traços, histórico das últimas 200 recompensas e resumo dos pesos; botões "resetar cérebro" (mantém DNA e afeto), "exportar DNA", "baixar brain.bin"; controles de `η`, `NOISE`, horário de silêncio e um interruptor "modo muda" (custo de som ×3).
- Simulador em CPython (`sim/`): roda o mesmo cérebro em velocidade acelerada com um dono simulado configurável (responde a sons com probabilidade p, faz carinho às 19h, ignora de madrugada). Gera gráficos de traços e de frequência de sons ao longo de 7 dias simulados. Teste obrigatório: com um dono que nunca responde a sons, a frequência de ações com som deve cair abaixo de 2 por hora em 48 h simuladas.

## 11. Roteiro de implementação para o Claude Code

Sete fases, cada uma com critério de aceite verificável. A fase 0 (simulador) vem antes de qualquer código na placa, e cada fase seguinte só começa com a anterior aceita.

1. **Fase 0 — Simulador em CPython.** `snn.py`, `learn.py`, `actions.py`, `drives.py`, `reward.py` rodando em PC com sensores falsos e dono simulado; testes unitários do LIF (spike no tick certo), do STDP (potencia pré-antes-de-pós, deprime o contrário) e do R-STDP (peso sobe só quando R chega dentro da janela de elegibilidade).
   - [ ] 7 dias simulados em menos de 1 min de execução.
   - [ ] Teste do silêncio: dono que nunca responde a sons → menos de 2 sons/h após 48 h simuladas.
   - [ ] Teste do hábito: dono que faz carinho sempre às 19h → `chamar_baixo` ou `pedir_carinho` vencem entre 18h50 e 19h10 em 5 dos 7 dias.
2. **Fase 1 — Núcleo na placa, sem aprendizado.** Portar `snn.py` e `encoder.py` para MicroPython; sentidos reais; seleção de ação com pesos iniciais e ruído; as 100 ações ligadas às animações existentes (as que ainda não têm animação usam um placeholder).
   - [ ] Tick completo abaixo de 10 ms, medido no raio-X.
   - [ ] 24 h ligada sem reset nem vazamento de memória (`gc.mem_free()` estável).
3. **Fase 2 — Aprendizado e recompensa.** `learn.py` e `reward.py` na placa; estrela e shh funcionando; custo de som e habituação; persistência em `brain.bin`.
   - [ ] Pesos sobrevivem a desligar e ligar.
   - [ ] Em 2 dias reais ignorando sons, ela para de fazer barulho de minuto em minuto.
4. **Fase 3 — Drives completos e horário de silêncio.** Os 7 drives com avanço por tempo desligado; modulação de R; configuração de silêncio no portal.
   - [ ] Fome a 90 gera `pedir_comida` mesmo com pesos ruins (ligação direta).
   - [ ] Nenhum som entre 22h e 8h após 3 noites.
5. **Fase 4 — Raio-X, ficha e portal.** Telas de debug, `brain.log`, `/brain.json`, botões de reset/export.
   - [ ] Reset mantém DNA e afeto.
6. **Fase 5 — Social entre duas placas.** ESP-NOW, HELLO/EVENT/TEACH/INTRO, afeto social, ações a dois.
   - [ ] Apresentação por toque simultâneo funciona e persiste.
   - [ ] `ensinar` altera visivelmente o traço da receptora em uma semana.
7. **Fase 6 — Personalidade.** DNA, 9 traços, limites, esquecimento diário, contexto para o LLM de voz (futuro).
   - [ ] Duas placas com DNAs diferentes e donos diferentes têm traço dominante diferente após 7 dias.
   - [ ] Nenhum traço fora de 5–80 em nenhum momento do log.

Regras para o Claude Code durante todo o projeto:

- Nenhum float nos laços de tick; qualquer constante decimal desta spec vira inteiro ×10 ou deslocamento de bits.
- O catálogo de ações (seção 5) é a única fonte de verdade; animações, sons e neurônios de saída são gerados a partir dele.
- Toda regra numérica desta spec entra em `config.py` como constante nomeada, com o número da seção em comentário, para calibrar sem reescrever código.
- Quando um valor da spec se mostrar errado na prática (aprende devagar demais, satura), ajustar a constante, anotar o motivo em `CALIBRACAO.md` e rodar de novo o simulador antes de gravar na placa.
