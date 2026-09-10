# PREREG — curva q do volcomp contra o `ink_9um`

Data: 2026-09-08. Selar antes de codificar. Encadeamento:
`REGISTRO_VOLCOMP_INK.md` (q = 8: razão 2,408 → 1,800, −25 %; d' −20 %).

## Pergunta

Qual quantizador q preserva a leitura do detector 2,5D? Curva razão × q e
d' × q, com a taxa de compressão de cada q, na mesma região e render do
registro anterior.

## Método

Mesmos 4 952 chunks originais em disco. Para cada q ∈ {2, 4, 16}: cada chunk
é codificado e decodificado com `volcomp_zarr._lib` (encoder e decoder do
autor, q em ponto flutuante), gravado em zarr v2 sem compressor, e a soma dos
bytes codificados dá a taxa. q = 8 vem do registro anterior (shards do
autor); q = 1 (original) idem. Render idêntico (28 fatias, malha oficial do
w043), inferência idêntica, medida idêntica (rótulo na grade nativa, offset
(40, 40), polaridade reverse, que é a que lê nestes renders).

Controle: um chunk codificado localmente em q = 8 tem de reproduzir o chunk
correspondente dos shards do autor (MAE ≤ 0,5): prova que encoder local e
shards publicados são o mesmo codec. Se falhar, a curva local não é
comparável ao publicado e o registro diz isso.

## Critérios, antes do número

- Para cada q, Δrazão e Δd' contra o original (2,408 / 1,596). Limiar de
  "não custa": |Δrazão| ≤ 0,05 e |Δd'| ≤ 0,10.
- **Recomendação** = maior q que satisfaz o limiar, com a taxa de compressão
  correspondente. Se nem q = 2 satisfizer, a recomendação é "volcomp não
  serve para 2,5D ink como está; teste q < 2 ou outro codec", e a curva
  mostra a inclinação.
- Monotonicidade esperada: razão não deve crescer com q. Se crescer em algum
  ponto, reportar como suspeito (suavização ajudando o detector) e não
  recomendar.

## Saídas

`metric/volcomp/vol_q{2,4,16}.zarr`, renders, predições, `curva_q.json`,
`curva_q.png`, registro. Texto para o Forrest a partir do registro.
