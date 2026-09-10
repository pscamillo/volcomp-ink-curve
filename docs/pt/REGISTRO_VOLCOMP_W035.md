# REGISTRO — volcomp × `ink_9um` no w035, segunda volta [medido]

Data: 2026-09-10. **Sem prereg próprio.** O protocolo foi herdado de
`metric/volcomp/PREREG_VOLCOMP_CURVA_Q.md` (`93ab53cb…`): mesma métrica,
mesmo n equalizado, mesmo nulo por permutação, mesmo limiar de gate, mesma
semente (20260904). Os scripts são cópia adaptada dos da volta 1. Três
correções de instrumento foram feitas **durante** a execução, depois de ver
dados (seção "Correções de instrumento"), e o controle plantado de ruído é
**post hoc** — foi desenhado depois de observar a instabilidade de moldura.
Nada disso estava previsto. Scripts e artefatos selados em `SELOS.txt` na
mesma data.

Objetivo: replicar em segundo segmento a curva medida no w043, com o
detector `ink_9um` sobre volumes comprimidos pelo `volcomp` do Forrest.

## Material

PHerc0139 nativo 9,362 (`20250728140407`), malha oficial do w035
(`volume_cache_0139_9um/w035`), 3 031 chunks 128³ ao redor da malha.
Original: nível 0 do bucket S3, validado por leitura (0 truncados).
Comprimido: 58 shards do `volcomp`, decodificados e regravados em zarr v2
sem compressor. Controle do codec: chunk 43/32/17 codificado localmente em
q = 8 contra o shard publicado, **MAE 0,000** — encoder local e shards
publicados são o mesmo codec.

Os shards do `volcomp` não estão no bucket oficial. Estão em
`dl.ash2txt.org/community-uploads/forrest/volcomp/`, publicados em
01/09/2026, cobrindo 41 rolos, entre eles elegíveis (0125, 0211, 0800,
0813, 1667) e Paris3/Paris4.

Os shards publicados usam **q = 8**, conforme o metadata do array
(`codecs[0].configuration.codecs[0] = {"name": "volcomp", "q": 8.0}`,
verificado em 10/09/2026 no zarr do PHercParis4). Existe pipeline público que
os consome como fonte primária de treino: o `train_config_reference.json` do
checkpoint `tsm_paris4_rvfw_30k` (mesma pasta de community-uploads) lista o
volume comprimido em `volume.url` e o volume oficial do S3 apenas em
`volume.alt_url`. Esse pipeline opera a 2,4 µm, não a 9,4 µm; a medida deste
registro não se transfere diretamente para ele.

Render idêntico nos cinco volumes: 28 fatias, passo 1, nível 0, escala 1,
`--flip-normals`, auto-crop (39, 39), grade (28, 5741, 5161).

Rótulo `labels_hf/native9-w035/w035_inklabels.zarr`, fatia 14, 285 960 px de
tinta. **Não há `supervision_mask` para este segmento**; a supervisão foi
tomada como toda a região com dado (`sup = ones`). A volta 1 (w043) usa
máscara de supervisão. Os valores absolutos de d' das duas voltas não são
diretamente comparáveis por essa razão; as perdas relativas são.

## Gate

Render do original vs `w035.zarr` oficial: **r = 1,0000** na fatia oficial
14 (nossa 14), offset (39, 39), n 24 978 427. O nosso render do volume
original reproduz o render publicado.

Codificação: q2 taxa 10,5× (MAE amostral 1,99), q4 16,9× (3,06), q8 44,0×,
q16 50,8× (6,68). As taxas replicam as da volta 1 (11,0 / 17,8 / 44,0 /
53,5) dentro de 5 %.

## Erro pixel a pixel (comprimido q = 8 − original, região válida)

MAE 3,61 · P90 8 · P99 13 · PSNR 34,7 dB. Por camada: 3,5 nas bordas,
máximo 3,9 nas camadas 12–15 (superfície). Sem degradação dependente de
profundidade.

## Detector (offset (39, 39), n 285 960 equalizado, semente 20260904)

| braço | polaridade | razão | d' | nulo |
|---|---|---|---|---|
| **original** | **fwd** | **2,826** | **2,587** | 1,000 |
| original | rev | 0,986 | 0,094 | 1,000 |
| **volcomp q = 8** | **fwd** | **2,507** | **1,923** | 1,000 |
| volcomp q = 8 | rev | 1,041 | 0,170 | 1,000 |

Referência publicada para o `w035.zarr` oficial na área inteira:
2,884 / 2,824. A inferência sobre o volume oficial reproduziu exatamente
esse par com a nossa métrica, o que valida a implementação. A diferença
para o nosso 2,826 / 2,587 é de moldura de inferência, não de render nem de
métrica (ver "Instabilidade de moldura").

## Curva q

| q | taxa | razão | d' | Δ d' |
|---|---|---|---|---|
| 1 | 1,0 | 2,826 | 2,587 | — |
| 2 | 10,5 | 2,826 | 2,561 | −1,0 % |
| 4 | 16,9 | 2,729 | 2,395 | −7,4 % |
| 8 | 44,0 | 2,507 | 1,923 | −25,7 % |
| 16 | 50,8 | 2,110 | 1,445 | −44,1 % |

Réplica contra a volta 1 (w043, medida refeita em 10/09):

| q | Δ d' w043 | Δ d' w035 |
|---|---|---|
| 2 | −2,1 % | −1,0 % |
| 4 | −7,2 % | −7,4 % |
| 8 | −21,9 % | −25,7 % |
| 16 | −44,3 % | −44,1 % |

Os extremos replicam dentro de um ponto percentual; o q = 8 diverge em
3,8 pontos. Joelho entre q = 4 e q = 8 nas duas voltas.

O critério pré-registrado (|Δ razão| ≤ 0,05 e |Δ d'| ≤ 0,10, absolutos)
recomenda q = 2 neste segmento e q = 1 no w043. O limiar absoluto não
transfere entre segmentos com linhas de base diferentes (2,587 contra
1,605). A comparação por perda relativa acima é **post hoc** e está
declarada como tal.

## Controle plantado — ruído sem estrutura, MAE casado (post hoc)

Ruído gaussiano de média zero, MAE casado ao de cada nível de q, zeros
preservados para manter máscara e auto-crop idênticos, mesma moldura,
mesmo checkpoint, mesmo rótulo, mesma semente. Desenhado para falsificar a
curva: se perturbação sem estrutura custasse o mesmo, a curva estaria
medindo fragilidade do detector, não remoção de informação.

| q | MAE | volcomp d' | perda | ruído d' | perda | fator |
|---|---|---|---|---|---|---|
| 2 | 1,99 | 2,561 | −1,0 % | 2,572 | −0,6 % | 1,7× |
| 4 | 3,06 | 2,395 | −7,4 % | 2,555 | −1,2 % | 6,0× |
| 8 | 3,61 | 1,923 | −25,8 % | 2,528 | −2,3 % | 11,3× |
| 16 | 6,68 | 1,445 | −44,1 % | 2,371 | −8,4 % | 5,3× |

A razão do ruído fica em 2,826 (idêntica à do original) até q = 8, e 2,771
em q = 16; a do volcomp cai monotonicamente (2,826 → 2,110). O ruído não
desloca a mediana; a quantização desloca.

Ressalvas: o fator em q = 2 (1,7×) é empate dentro do ruído da medida — q = 2
não custa nada por nenhum dos dois caminhos. O fator em q = 16 cai para
5,3× porque o ruído casado nesse nível tem cauda mais pesada que qualquer
nível do volcomp (P90 14 / P99 22 contra P90 8 / P99 13 do q = 8); o
controle é mais agressivo que o necessário e ainda assim perde por 5×.

No w043 o mesmo controle em q = 8 dá fator 2,3× (volcomp −22,1 %, ruído
−9,4 %). A direção replica nos dois segmentos; a magnitude não. Hipótese
não testada: w043 tem tinta difusa e linha de base mais baixa, de modo que
qualquer perturbação morde proporcionalmente mais.

## Veto visual (R1)

`panel_w035_full.png` e `panel_w035_detail.png`: original, ruído MAE 3,6,
volcomp q8 (mesmo MAE) e q16, mesma moldura, escala de cinza comum tirada
dos percentis 1–99 do original, sem normalização por painel. Original e
ruído são indistinguíveis a olho; q8 borra as letras visivelmente; q16
apaga. Painéis equivalentes para o w043 em `metric/volcomp/`.

## Correções de instrumento (feitas durante a execução)

1. **Busca de offset quantizada em 4 voxels.** A busca grossa roda no
   arranjo decimado por 4 e só devolve múltiplos de 4; devolveu (40, 40)
   com r = 0,944, reprovando o gate. O offset verdadeiro é (39, 39), com
   r = 1,0000. Corrigido com refinamento em resolução plena (`_fino`).
   O mesmo offset recorta o rótulo, então o desalinhamento contaminava
   também a medida contra o rótulo (efeito pequeno: d' 2,616 → 2,628).

2. **Polaridade invertida.** A malha do w035 renderiza a folha invertida em
   profundidade: fatia *j* nossa ↔ fatia (27 − *j*) oficial. Confirmado por
   correlação em cinco pares (r = 1,000 nos invertidos, ruído nos
   deslocados). Corrigido com `--flip-normals`; o gate passou a apontar a
   fatia oficial 14 e o sinal passou ao braço forward.

3. **Braço fixo no script de curva.** `mede_curva_q.py` lia
   `preds_q{q}_reverse.tif` por sufixo fixo; com a orientação corrigida
   passou a ler o braço sem sinal e produziu uma tabela completa, plausível
   e inteiramente falsa, com recomendação. O que a denunciou foi q = 1
   valer razão 0,986. Corrigido: braço escolhido pelo maior d'. Sugestão
   para os próximos: abortar quando o braço de q = 1 tiver d' abaixo de 1.

As três correções deslocaram a perda medida em q = 8 de −27,8 % para
−25,7 %. O resultado é robusto a elas; isso só é afirmável porque foi
refeito.

## Instabilidade de moldura de inferência (achado colateral)

Recortar o volume oficial em (20, 20) em vez de (39, 39), sem render nem
compressão no meio, muda o d' de 2,824 para 2,085 — perda de 26 %, mesma
ordem do custo de q = 8. Dois recortes do mesmo volume produzem mapas com
r = 0,72 entre si; o nosso render contra o oficial dá r = 0,79. A
inferência é determinística (r = 1,000000, MAE 0,0 em repetição), então o
efeito é da grade de tiles com overlap 0,75 e blend gaussiano.

Não afeta as curvas acima, medidas com moldura idêntica em todos os volumes
de cada volta. Afeta qualquer comparação de d' entre segmentos ou entre
rodadas com molduras diferentes. Registro próprio a fazer; a caracterizar:
curva de d' contra deslocamento (0, 5, 10, 20, 40, 80 px) e efeito de
overlap 0,5 / 0,75 / 0,9.

## Limites

Um checkpoint (`ink_9um` hybrid_3d2d-seed43 step-060000), 2,5D, um rolo,
dois segmentos. Não foi testado treinar ou afinar em volume comprimido: a
medida vale para quem aplica um detector pronto sobre volume comprimido,
não para quem treinaria nele. Sem prereg próprio, com três correções de
instrumento em execução e controle plantado post hoc, conforme declarado na
abertura.
