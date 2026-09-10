# REGISTRO — `ink_9um` sobre volume volcomp q = 8 [medido]. Custa 25 % da separação.

Data: 2026-09-08. Prereg `91d9e714…`, lista de chunks `0ef0b949…`.
Scripts `metric/volcomp/{transcreve_vc,mede_volcomp}.py`. Codec: `SuperOptimizer/
volume-compressor` compilado localmente (gcc 13, `-DCMAKE_C_COMPILER=gcc`);
`volcomp_zarr` instalado em venv próprio; primeira leitura Python do zarr v3
volcomp fora do ambiente do autor: funciona (bloco remoto em 1,1 s; 4 953
chunks locais decodificados em 40 s, sem erro).

## Material

PHerc0139 nativo 9,362 (`20250728140407`), malha oficial do w043 (frame nativo,
`volume_cache_0139_9um/w043`), 4 952 chunks 128³ ao redor da malha (±24 voxels).
Original: nível 0 do bucket S3 (7 chunks truncados no download, detectados por
leitura e rebaixados). Comprimido: 67 shards 1024³ do `volcomp` (1,9 GB),
decodificados e regravados em zarr v2 sem compressor. Render idêntico nos dois:
28 fatias, passo 1, nível 0, escala 1, auto-crop (39, 39), grade (28, 6041, 8041).

## Gate

Render do original vs `w043.zarr` oficial: r = 0,944 na fatia 13 do oficial
(nossa 14), offset (40, 40). Um fio abaixo do 0,95 exigido, com uma fatia de
defasagem e polaridade invertida (nosso reverse = oficial forward). Pelo prereg,
a comparação orig × vc entre renders idênticos vale por si.

## Erro pixel a pixel (comprimido − original, região válida)

MAE 3,47 · P90 7 · P99 13 · PSNR 35,1 dB. Por camada: 3,3 nas bordas, máximo
3,8 nas camadas 13–17 (superfície). Abaixo do P99 ≈ 20 previsto na spec.

## Detector (rótulo alinhado na grade nativa, offset (40, 40), n 204 960)

| braço | polaridade | razão | d' | nulo |
|---|---|---|---|---|
| original | fwd | 1,028 | 0,164 | 1,000 |
| **original** | **rev** | **2,408** | **1,596** | 1,000 |
| volcomp q=8 | fwd | 1,053 | 0,108 | 1,000 |
| **volcomp q=8** | **rev** | **1,800** | **1,274** | 1,000 |

Δ razão −0,608 (−25 %); Δ d' −0,322 (−20 %).

## Veredito pelo §Critérios

**Custa, quantificado.** Bem além de |Δrazão| ≤ 0,05 e |Δd'| ≤ 0,10.
R1: linhas de texto nítidas em `preds_orig_reverse`, apagadas em `preds_vc`.

## Leitura

- O detector 2,5D perde um quarto da separação com um erro de 3,5 níveis
  de cinza em média. PSNR não é proxy de leitura: o que a DCT-16 com zona
  morta remove (alta frequência de baixa amplitude) é parte do que o
  detector usa. Consistente com o resíduo de σ 16 que separa fino de nativo.
- O erro concentra-se nas camadas da superfície, onde o gradiente é maior.

## Consequência

Para 2,5D ink, volcomp q = 8 não é neutro. A pergunta seguinte, com comprador
(Forrest e quem usar os volumes comprimidos): qual q preserva a tinta.
Prereg próprio: mesma região, mesmo render, q ∈ {2, 4, 16} codificados
localmente com o encoder do autor, curva razão × q. Uma hora de máquina.


---

## ERRATA — 2026-09-10. Gate refeito, polaridade corrigida, medida repetida.

O registro original seguiu adiante com dois defeitos declarados mas não
resolvidos. Ambos foram corrigidos e a medida foi refeita do zero. A
conclusão não mudou; o método mudou. O que está acima permanece como
registro do que foi feito em 08/09; o que vale a partir daqui é esta seção.

Parte do diagnóstico abaixo veio da segunda volta (w035,
`REGISTRO_VOLCOMP_W035.md`, a escrever), onde os mesmos defeitos
apareceram e foram caracterizados com mais controles. Onde for o caso,
está dito de qual segmento vem a evidência.

### Defeito 1 — busca de offset quantizada em 4 voxels

A busca de offset do gate roda no arranjo decimado por 4 e devolve
`dy, dx = iy * 4, ix * 4`. Só consegue expressar múltiplos de 4. O offset
verdadeiro é (39, 39); a busca devolveu (40, 40), a um voxel de distância,
e o gate saiu em r = 0,944 — abaixo do 0,95 exigido pelo prereg.

O mesmo `dy, dx` recorta o rótulo (linha 41). O desalinhamento de um voxel
contaminou também a comparação com o rótulo, não só o gate.

Corrigido com um refinamento em resolução plena (`_fino`, ±4 voxels numa
janela central de 1200²) aplicado após a busca grossa. Com offset (39, 39),
**r = 1,0000**: o render do volume original reproduz o `w043.zarr` oficial.
O gate passa a cumprir o prereg em vez de ser dispensado por argumento.

Em w035 o mesmo defeito produziu r = 0,944 com offset (40, 40); o offset
verdadeiro também era (39, 39) e o r também subiu para 1,0000.

### Defeito 2 — polaridade invertida

O registro original observou que o braço reverso do nosso render
correspondia ao forward do oficial, e mediu no reverso.

A causa foi caracterizada em w035: a malha renderiza a folha invertida em
profundidade, de modo que a fatia *j* nossa corresponde à fatia (27 − *j*)
oficial, e não a (*j* − 1). Confirmado por correlação em cinco pares de
fatias (r = 1,000 em todos os pares invertidos, ruído em todos os
deslocados). Em w043 a inversão foi confirmada visualmente: no render sem
`--flip-normals`, o sinal de tinta está no braço reverso e o forward é
ruído.

Medir no braço reverso recupera a maior parte do sinal. Não há evidência de
que isso enviese a comparação orig × q, já que todos os volumes de uma
mesma volta são renderizados igual. A correção foi feita por outra razão:
sem ela, a volta 1 estaria medida no braço reverso e a volta 2 no forward,
e duas voltas em braços diferentes não constituem réplica metodológica.
Corrigido re-renderizando os cinco volumes com `--flip-normals`. O gate
passa a apontar a fatia oficial 14 (não 13) e o sinal passa a estar no
braço forward, como no volume oficial.

Registre-se o que **não** justifica essa correção, para não repetir o
raciocínio: em w035, os mapas de predição do nosso render e do volume
oficial correlacionam r = 0,76 antes do flip e r = 0,79 depois — o flip
quase não muda. Essa discordância entre mapas não é efeito de braço; é
efeito da moldura de inferência (ver "Instabilidade de grade" abaixo).

### Defeito 3 — braço fixo no script de curva

`mede_curva_q.py` lia `preds_q{q}_reverse.tif` por sufixo fixo. Com a
orientação corrigida, isso passa a ler o braço sem sinal. Em w035, onde a
correção foi aplicada primeiro, o script produziu uma tabela completa,
plausível e inteiramente falsa, com recomendação e tudo. O que a denunciou
foi o q = 1 valer razão 0,986 — valor que só existe quando não há sinal.

Corrigido nas duas voltas: o braço passa a ser escolhido pelo maior d'.
Recomenda-se abortar quando o braço escolhido para q = 1 tiver d' abaixo
de 1.

### Medida refeita (2026-09-10)

Renders com `--flip-normals`, crop (39, 39) idêntico nos cinco volumes,
grade (28, 6041, 8041). Gate r = 1,0000, fatia oficial 14, offset (39, 39).
Rótulo `destila/segments_C/pherc0139-w043`, fatia 14, com máscara de
supervisão. n = 204 960 equalizado, semente 20260904.

| braço | razão | d' |
|---|---|---|
| original (fwd) | 2,380 | 1,605 |
| volcomp q = 8 (fwd) | 1,790 | 1,253 |

Δ razão −0,590 (−24,8 %); Δ d' −0,352 (−21,9 %).

Curva completa (`mede_curva_q.py`):

| q | taxa | razão | d' | Δ d' |
|---|---|---|---|---|
| 1 | 1,0 | 2,380 | 1,605 | — |
| 2 | 11,0 | 2,219 | 1,571 | −2,1 % |
| 4 | 17,8 | 2,153 | 1,490 | −7,2 % |
| 8 | 44,0 | 1,790 | 1,253 | −21,9 % |
| 16 | 53,5 | 1,451 | 0,894 | −44,3 % |

Comparação com os valores de 08/09: razão do original 2,408 → 2,380;
q = 8 1,800 → 1,790; perda de d' 20,2 % → 21,9 %. Os três defeitos
deslocavam a perda medida em 1,7 ponto percentual. **A conclusão publicada
não dependia deles** — mas isso só é afirmável depois de ter refeito, não
antes.

### Controle plantado (novo, não existia em 08/09)

Ruído gaussiano de média zero, MAE casado ao do volcomp q = 8 (3,461
obtido contra 3,47 do volcomp; P90 7 contra 7; P99 11 contra 13), zeros
preservados para manter a máscara e o auto-crop idênticos, mesma moldura de
render, mesmo checkpoint, mesmo rótulo e mesma semente.

| perturbação | MAE | razão | d' | perda de d' |
|---|---|---|---|---|
| nenhuma (original) | — | 2,380 | 1,605 | — |
| ruído sem estrutura | 3,46 | 2,274 | 1,454 | −9,4 % |
| volcomp q = 8 | 3,47 | 1,790 | 1,251 | −22,1 % |

Fator **2,3×**. A perda do volcomp não é reação genérica a perturbação de
mesma magnitude; parte dela é remoção de estrutura que o detector usa.
No w035 o mesmo controle dá fator 11,3× (volcomp −25,8 %, ruído −2,3 %).
A magnitude depende do segmento; a direção não. Hipótese não testada para
a diferença: w043 tem sinal de tinta difuso e linha de base bem mais baixa
(1,605 contra 2,587), de modo que qualquer perturbação morde
proporcionalmente mais.

Nota sobre os dois valores de d' do volcomp q = 8 nesta errata: 1,253 vem
do `mede_volcomp.py`, 1,251 do script avulso que mediu o ruído. A
diferença é de implementação do d' (variância com e sem termo de
estabilização), não de dados. As perdas correspondentes são −21,9 % e
−22,1 %.

### Instabilidade de grade de inferência (achado colateral, w035)

Recortar o volume oficial em (20, 20) em vez de (39, 39), sem render nem
compressão no meio, muda o d' de 2,824 para 2,085 — perda de 26 %, da
mesma ordem que o q = 8 custa. Dois recortes do mesmo volume produzem
mapas com r = 0,72 entre si. A inferência é determinística (r = 1,000000,
MAE 0,0 em execução repetida com a mesma entrada), então o efeito é da
moldura de tiles com overlap 0,75 e blend gaussiano.

Isso não afeta as curvas acima, que rodam com moldura idêntica em todos os
volumes de cada volta, mas afeta qualquer comparação de d' entre segmentos
ou entre rodadas com molduras diferentes. Registro próprio a fazer.

### Limites desta errata

Um checkpoint, 2,5D, um rolo. Não foi testado treinar ou afinar em volume
comprimido — a medida vale para quem aplica um detector pronto sobre
volume comprimido, não para quem treinaria nele.
