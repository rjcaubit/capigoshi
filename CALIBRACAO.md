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

## Hábito — não resolvido

Critério: em 5 de 7 dias, taxa de `pedir_carinho` + `chamar_baixo` entre 18h50 e 19h10 >= 2x a taxa das 8h às 22h
fora da janela. Dono do teste: ausente o dia todo, atende pedidos de carinho das 19h00 às 19h15.

Em todos os ajustes a Capi ou aprende a pedir carinho em todas as horas, ou para de pedir. A representação de hora
na camada oculta não separa 19h de 10h o bastante para a recompensa ficar presa ao horário.

| Ajuste (`python3 -m companion.sim.aceite habito ...`) | Dias ok |
|---|---|
| configuração base (execução, D1) | 2 |
| `P_MAX_HORA=255` | 0 |
| `HH_DENS_INIB=40` | 1 |
| `P_MAX_HORA=255 HH_DENS_INIB=40` | 0 |
| `R_IGNORADO=-10` | 1 |
| `IH_FORTES=10` | 0 |
| `IH_FORTES=10 R_IGNORADO=-10` | 1 |
| `OCULTOS_TEMPO=16` / `32` (índice de luz errado, já corrigido) | 1 / 1 |
| `OCULTOS_TEMPO=16 ETA_FILHOTE=8` | 0 (pede a toda hora: dia 7 com 12/h na janela e 10/h fora) |
| `OCULTOS_TEMPO=16 ETA_FILHOTE=8 R_IGNORADO=-10` | 0 (para de pedir) |
| `OCULTOS_TEMPO=16 HH_DENS_INIB=40 ETA_FILHOTE=8` (D2) | 1 |
| `OCULTOS_TEMPO=16 HH_DENS_INIB=40 ETA_FILHOTE=8 P_MAX_HORA=255` (D3) | 0 (dia 7: 12/h na janela, 9,8/h fora) |

Linha de base da execução, dia a dia:

```
habito dia 1: 3.0/h na janela 18h50-19h10, 0.2/h fora ok
habito dia 2: 0.0/h na janela 18h50-19h10, 0.2/h fora -
habito dia 3: 3.0/h na janela 18h50-19h10, 0.9/h fora ok
habito dia 4: 0.0/h na janela 18h50-19h10, 4.2/h fora -
habito dia 5: 0.0/h na janela 18h50-19h10, 5.2/h fora -
habito dia 6: 6.0/h na janela 18h50-19h10, 4.0/h fora -
habito dia 7: 3.0/h na janela 18h50-19h10, 7.2/h fora -
habito: 2 de 7 dias (meta 5)
```

Depois da revisão de código (crédito do chamado atendido corrigido, modulação pela fome de antes de comer, e
refeições do cenário do hábito movidas de 8h/12h/19h para 8h/12h/21h, porque a das 19h00 tocava a Capi bem no
início da janela), a linha de base ficou em **0 de 7**: a Capi quase não pede carinho em hora nenhuma
(0,1 a 0,4/h fora, 0/h na janela). Parte dos "ok" de antes vinha da refeição das 19h, não de aprendizado.

Opções levadas para `/sdd-refine 2`: (a) contar só os dias 3 a 7; (b) o dono do teste atender das 18h50 às 19h20,
para dar mais recompensas por dia; (c) uma via plástica direta "hora → saída" ao lado da rede.
