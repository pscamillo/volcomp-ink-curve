# PREREG — o `ink_9um` sobrevive à compressão volcomp q = 8?

Data: 2026-09-08. Selar antes de baixar. Pergunta do Forrest (07/09, #general):
"Unsure on 2.5d ink". Compressor: `SuperOptimizer/volume-compressor`, DCT 3D
16³ com quantizador de zona morta, q = 8 (erro P99 ≈ 2,5q ≈ 20 níveis), 44×.
Referência: o resíduo que separa fino de nativo e derruba o detector tem
σ ≈ 16 (REGISTRO_DESLOCAMENTO). A perda é da ordem do que importa.

## Pergunta

Renderizando a mesma malha, com os mesmos parâmetros, do volume original e do
volume volcomp q = 8, o `ink_9um` lê igual?

## Material

PHerc0139 nativo 9,362 (`20250728140407`), malha oficial do w043
(`volume_cache_0139_9um/w043`, frame nativo). Original: chunks 128³ de nível 0
do bucket ao redor da malha (±24 voxels na normal). Comprimido: mesmos chunks
lidos do zarr v3 volcomp (`dl.ash2txt.org/community-uploads/forrest/volcomp`)
com `volcomp_zarr` (codec construído localmente, gcc 13; leitura remota
validada num bloco: média 75,5, σ 44,4) e regravados em zarr v2 local, sem
outra transformação.

## Método

1. Render idêntico dos dois volumes: `vc_render_tifxyz` do `main`, 28 fatias,
   passo 1, nível 0, `--scale 1.0`, mesma malha. Gate: o render do original
   contra o `w043.zarr` oficial de 28 fatias com r ≥ 0,95 na fatia 14 (prova
   que os parâmetros são os oficiais; se falhar, ajusta-se `--flip-normals`
   e reporta-se; se ainda falhar, compara-se só original vs comprimido nossos).
2. Erro pixel a pixel do render comprimido contra o original, na região válida:
   MAE, P90, P99, PSNR; e por camada.
3. Inferência do `ink_9um` (hybrid_3d2d seed43 step-060000, overlap 0,75,
   gaussian, both) nos dois renders.
4. Medida no w043: rótulo alinhado já na grade nativa (`segments_C`), razão de
   medianas tinta/papiro, n equalizado, d', nulo por permutação, polaridade
   forward (a que lê nos volumes oficiais). Referência oficial: 2,310 / 1,481.
5. R1: predições lado a lado em resolução plena numa região com letras.

## Critérios, antes do número

Seja Δrazão = razão(comprimido) − razão(original), idem d'.
- **Não custa tinta:** |Δrazão| ≤ 0,05 e |Δd'| ≤ 0,10, nulo 1,00 ± 0,02,
  letras iguais no R1. Consequência: 2,5D ink pode rodar direto no volcomp q=8.
- **Custa, quantificado:** perda maior, reportar quanto e em que camadas o
  erro se concentra (perfil por camada), e sugerir q menor. Sem varrer q aqui.
- **Suspeito:** comprimido melhor que o original em > 0,10. Investigar antes
  de qualquer leitura (efeito de suavização sobre o detector).

## Saídas

`metric/volcomp/` — listas de chunks, `vol_orig.zarr`, `vol_vc.zarr`, renders,
predições, `volcomp_resumo.json`, `R1.png`, registro.
