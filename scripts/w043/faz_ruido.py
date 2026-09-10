#!/usr/bin/env python3
# Controle plantado: perturbacao SEM estrutura com o mesmo MAE do volcomp q8.
# Se ruido de MAE 3,61 custar os mesmos ~26% de d' que o q8, a curva mede
# fragilidade do detector. Se custar bem menos, o volcomp remove algo especifico.
#
# Preserva os zeros (mascara identica), senao o --auto-crop muda e a comparacao morre.

import os
import sys
import numpy as np
import zarr

D = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp')
SRC = f'{D}/vol_orig.zarr'
DST = f'{D}/vol_ruido_{sys.argv[2]}.zarr'
LISTA = f'{D}/chunks_w043.txt'

MAE_ALVO = float(sys.argv[1])
SEED = 20260909
SIGMA = MAE_ALVO / np.sqrt(2 / np.pi)   # E|N(0,s)| = s*sqrt(2/pi)


def abre(p, modo='r'):
    z = zarr.open(p, modo)
    try:
        keys = list(z.array_keys())
    except Exception:
        return z, None
    if '0' in keys:
        return z['0'], '0'
    return z, None


src, chave = abre(SRC)
print(f'origem {src.shape}  dtype {src.dtype}  chunks {src.chunks}  '
      f'estrutura {"grupo com 0" if chave else "array"}')
print(f'sigma do ruido {SIGMA:.3f} para MAE alvo {MAE_ALVO}')

if os.path.exists(DST):
    print(f'PARE: {DST} ja existe. remova antes.')
    raise SystemExit(1)

cz, cy, cx = src.chunks
comp = getattr(src, 'compressor', None)

if chave:
    g = zarr.open(DST, mode='w')
    out = g.create_dataset('0', shape=src.shape, chunks=src.chunks,
                           dtype=src.dtype, compressor=comp)
else:
    out = zarr.open(DST, mode='w', shape=src.shape, chunks=src.chunks,
                    dtype=src.dtype, compressor=comp)

rng = np.random.default_rng(SEED)
linhas = [l.strip() for l in open(LISTA) if l.strip()]
print(f'{len(linhas)} chunks')

soma_abs = 0.0
soma_n = 0
p90s = []
p99s = []

for i, l in enumerate(linhas):
    z, y, x = map(int, l.split('/'))
    bloco = np.asarray(src[z * cz:(z + 1) * cz, y * cy:(y + 1) * cy, x * cx:(x + 1) * cx])
    if bloco.size == 0:
        continue
    m = bloco > 0
    if not m.any():
        out[z * cz:(z + 1) * cz, y * cy:(y + 1) * cy, x * cx:(x + 1) * cx] = bloco
        continue
    ruido = rng.normal(0.0, SIGMA, size=int(m.sum()))
    novo = bloco.astype(np.float32)
    novo[m] = np.clip(np.rint(novo[m] + ruido), 1, 255)
    novo = novo.astype(bloco.dtype)
    out[z * cz:(z + 1) * cz, y * cy:(y + 1) * cy, x * cx:(x + 1) * cx] = novo
    e = np.abs(novo[m].astype(np.float32) - bloco[m].astype(np.float32))
    soma_abs += float(e.sum())
    soma_n += int(e.size)
    if i % 200 == 0:
        p90s.append(float(np.percentile(e, 90)))
        p99s.append(float(np.percentile(e, 99)))
    if i % 100 == 0:
        print(f'  {i}/{len(linhas)}', end='\r')

print(f'\nescrito {DST}')
print(f'  MAE obtido {soma_abs / max(soma_n, 1):.3f}   (alvo {MAE_ALVO}, volcomp q8 3.61)')
print(f'  P90 ~{np.mean(p90s):.1f}  P99 ~{np.mean(p99s):.1f}   (volcomp q8: P90 8.0  P99 13.0)')
print(f'  voxels perturbados {soma_n}')
