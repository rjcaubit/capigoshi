# Calibração do cérebro SNN

Toda constante de `companion/config.py` que mudou em relação à fonte (`sdd/ISSUE_2/00-fonte.md`), com o motivo e o
número medido. Antes de gravar na placa, rodar `python3 -m companion.sim.aceite todos`.

## Fase 0 (issue #2, 2026-11)

| Constante | Fonte | Agora | Motivo (medido no simulador) |
|---|---|---|---|
| STDP entrada→oculta | aditivo, A+=2, A-=3, pesos 0..255 | limite suave, pesos x16 (`W_FRAC=4`, `STDP_SHIFT=14`) | Passos inteiros 0/1/2: a depressão venceu, a normalização levou o peso para entradas mudas e em 10 min os ocultos calaram (limiar a 49) |
| Normalização | `SUM_TARGET` fixo | soma inicial de cada oculto | Entrada esparsa tem soma inicial diferente por neurônio |
| Pesos iniciais entrada→oculta | densos 20..80 | 25 % em 20..80, resto 0..5 (`IH_FORTES`, `W_IH_FRACO`) | Uniformes, nenhum oculto ficava seletivo |
| Corrente de saída | `soma(w) >> 2` | `soma(w) * 6` (`I_OUT_MUL`) | Com `>> 2` a contagem máxima na janela era 0 a 1 |
| Empate na decisão | `ficar_quieta` | maior potencial no fim da janela | Saídas sincronizadas empatavam: 100 % `ficar_quieta` |
| Limiar adaptativo | sem limite, todas as camadas | só ocultos, 500..4000 (`TH_MIN`, `TH_MAX`) | Na saída desfaria a punição; sem limite colapsava |
| Elegibilidade | decai 1/64 por tick | x25/32 a cada 16 ticks, só colunas ativas | Mesmo valor, custo de CPU muito menor |
| Habituação | execuções na última hora | contador x10, perde 1/6 a cada 10 min | Inteiro, sem lista |
| Meta de velocidade | 7 dias < 1 min | 7 dias <= 180 s | 63 s medidos na execução (CPython 3.14, Mac); a meta fica com folga |
| Teste do silêncio | Capi normal | Capi falante (som x6) | A normal já nasce com < 1 som/h |
| Teste do hábito | "vencem na janela" | taxa na janela >= 2x a taxa fora, 5 de 7 dias | Do jeito da fonte passa por acaso |
| R-STDP | todas as sinapses elegíveis | só a coluna da ação que recebe o crédito | As saídas perdedoras também disparam e levariam crédito |
| Chamado atendido | "+8, qualquer toque" | +8 vai para o chamado que armou o prazo, mesmo que a ação atual já seja outra; afeto não modula o +8 | Antes ia para a ação corrente: `chamar_baixo` (2 s) tinha janela real de 2 s, não 10 s |
| Horário de silêncio | custo dobrado | custo normal + R -10 na hora (`R_SOM_SILENCIO`) | É a linha da tabela 6.3; o "dobro" da seção 4 ficaria contado duas vezes |
| Ligação direta do estresse | estresse > 80 → `desligar_tela` (seção 4) | estresse > 80 → `esconder_rosto` | `desligar_tela` não está no catálogo da seção 5 |
| `ciume` | "outra foi tocada, esta não há 5 min" | só "outra foi tocada" (campo `tocada`, que o `social.py` da fase 5 calcula já com os 5 min) | A gramática da pré-condição não tem tempo desde o último toque por outra Capi |
| Esquecimento | 1 %/dia | 1 %/dia arredondado para longe de zero (anda ao menos 1) | Com divisão inteira, desvio < 100 nunca andava: a camada oculta→saída nunca esquecia |

Ainda não implementado (fase 3): "estresse > 50 bloqueia sons" (seção 4).

## Erros da fonte

- Seção 2: ~80 entradas; a tabela da seção 3 soma 100.
- Seção 5: 21 ações com som; a tabela tem 20.
- Seção 6.2: R-STDP em saída→saída; a seção 2 diz que é fixa.
- Seção 6.3: "shh" com dois dedos; o CST816D só lê um toque (gesto decidido na fase 2).

## Hábito (issue #3, 2026-11)

Resolvido com três acréscimos à fonte. Planejamento e execução: `sdd/ISSUE_3/`.

| Acréscimo | Constante | Por quê (medido) |
|---|---|---|
| Via hora → saída: 72 células de 20 min ligadas às 100 saídas, crédito no minuto em que a ação começou | `RELOGIO_BINS=72`, `RELOGIO_K_POS=24`, `RELOGIO_K=8`, `RELOGIO_MAX=1500` | A camada oculta não separa 19h de 17h ou 21h (8 neurônios de 3 h); 13 configurações na #2 deram 0 a 2 dias |
| Marca: ocultos ativos quando um pedido começa recebem o castigo atrasado | `MARCA_K=1` | O "ignorado" chega em 60 s e a elegibilidade zera em ~16 s: a rede nunca aprendia a parar de pedir (9 pedidos/h às 3h) |
| Solidão: afeto < 20 soma corrente em `pedir_carinho` | `SOLIDAO=(D_AFETO, 200, 'pedir_carinho', 1000)` | Sem exploração a Capi não pede às 19h e não descobre o hábito |

Resultado: hábito 5 de 7 dias (semente 1); sementes 1 a 4: [5, 5, 5, 6], média 5,25. Silêncio (12,0 → 0,1 sons/h) e
velocidade (66 s) continuam passando.
Na semana normal (3 dias) a Capi pede menos: `pedir_carinho` 498 → 246, `pedir_comida` 544 → 70.

A ligação direta (`DIRETO`) continua sobrescrevendo a corrente do relógio: somar deu 4 dias na semente 1.
O CT03 da #2 tinha a tabela das 13 tentativas sem o relógio; ela continua no histórico do git (commit `01932af`).

Limites conhecidos do relógio: todo R passa por ele, inclusive o custo de som (R < 0 no início de cada ação sonora,
creditado com K=8 na célula de início), o que reduz o prêmio líquido; isso já está dentro da calibração medida. Se a
mesma ação recomeça antes do R atrasado (pedido a cada menos de 60 s), o "ignorado" do primeiro credita o minuto
e a marca do segundo.

## Clima (issue #4, 2026-11)

O clima entra como sentido (grupo `clima`, 4 binários, e `temperatura`, 3 em população; `N_IN` 100 → 107) e como
alvo do humor. Planejamento e execução: `sdd/ISSUE_4/`.

| Mudança | Constante | Por quê (medido) |
|---|---|---|
| Com previsão, o humor regride para o alvo do clima, `1 + 5 % da distância` por minuto | `CLIMA_HUMOR=(200, -100, -350, -500)`, `CLIMA_PUXA_PCT=5` | Só o alvo, a 1/min, não aparece: as recompensas mantêm o humor abaixo dos dois alvos (tristes/h 0,62 na chuva × 0,64 no sol) |
| Chuva e tempestade cansam; frio também | `CLIMA_ENERGIA=(0, 0, -3, -3)`, `FRIO=15`, `FRIO_ENERGIA=-3` | Pedido na issue; sem regra fixa de sono |
| Sol dá curiosidade | `CLIMA_CURIOSIDADE=(10, 0, 0, 0)` | Pedido na issue |

Resultado (sementes 1 a 4, chuva 18 °C × sol 25 °C, das 8h às 22h): humor −37 na chuva e +18 no sol; ações tristes
0,5 a 1,45/h na chuva e 0 a 0,02/h no sol.

As 7 linhas novas de `w_ih` são sorteadas no fim do `Rede.__init__`, e a rede da fonte nasce igual. Mesmo sem clima,
os aceites antigos mudam de número: hábito 5 → 6 dias e sementes [5, 5, 5, 6] → [6, 6, 5, 5]; silêncio 12,0 → 10,8
sons/h no começo. O motivo é a sequência aleatória deslocada e a normalização da entrada, que soma as linhas do clima.
