#!/usr/bin/env python3
# Escreve um segundo recorte do w035.zarr oficial, deslocado de (39,39),
# com o mesmo tamanho do nosso render. Serve de controle: se dois recortes
# do MESMO volume discordarem tanto quanto o nosso discorda do oficial,
# o residuo e da grade de tiles da inferencia, nao do render.

import os
import numpy as np
import zarr

ROOT = os.path.expanduser('~/challenges/vesuvius/villa_ink/ink-detection')
D = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp_w035')
SRC = f'{ROOT}/ink-dataset/pherc0139_9um/w035/w035.zarr'
DST = f'{D}/vol_recorte2.zarr'

CY, CX = 20, 20          # recorte deslocado; o nosso e (39,39)
H, W = 5741, 5161        # mesmo tamanho do nosso render


def abre(p):
    z = zarr.open(p, 'r')
    try:
        keys = list(z.array_keys())
    except Exception:
        return z, None
    if '0' in keys:
        return z['0'], '0'
    return z, None


src, chave = abre(SRC)
print(f'origem {SRC}')
print(f'  shape {src.shape}  dtype {src.dtype}  chunks {src.chunks}  '
      f'estrutura {"grupo com 0" if chave else "array"}')

if CY + H > src.shape[1] or CX + W > src.shape[2]:
    print('PARE: recorte cai fora do volume')
    raise SystemExit(1)

if os.path.exists(DST):
    print(f'PARE: {DST} ja existe. remova antes.')
    raise SystemExit(1)

comp = getattr(src, 'compressor', None)

if chave:
    g = zarr.open(DST, mode='w')
    out = g.create_dataset('0', shape=(src.shape[0], H, W), chunks=src.chunks,
                           dtype=src.dtype, compressor=comp)
else:
    out = zarr.open(DST, mode='w', shape=(src.shape[0], H, W), chunks=src.chunks,
                    dtype=src.dtype, compressor=comp)

for k in range(src.shape[0]):
    out[k] = np.asarray(src[k, CY:CY + H, CX:CX + W])
    print(f'  fatia {k + 1}/{src.shape[0]}', end='\r')

print(f'\nescrito {DST}  shape {out.shape}')

# validacao: o recorte tem que ser identico a origem naquela janela
k = src.shape[0] // 2
a = np.asarray(out[k]).astype(np.float32)
b = np.asarray(src[k, CY:CY + H, CX:CX + W]).astype(np.float32)
print(f'  validacao fatia {k}: MAE {np.abs(a - b).mean():.6f}  (tem que ser 0)')
