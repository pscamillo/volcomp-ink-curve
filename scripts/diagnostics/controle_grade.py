#!/usr/bin/env python3
# Controle da grade de tiles.
#   recorte2 = w035.zarr oficial recortado em (20,20), 5741x5161
#   nosso    = render do vol_orig (flip), recorte (39,39), 5741x5161
#   oficial  = w035.zarr inteiro, 5820x5240
# Se recorte2 discordar do oficial tanto quanto o nosso discorda,
# o residuo e da grade de tiles e nao do nosso render.

import os
import numpy as np
import zarr
import tifffile

D = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp_w035')
ROOT = os.path.expanduser('~/challenges/vesuvius/villa_ink/ink-detection')
LAB = f'{ROOT}/labels_hf/native9-w035/w035_inklabels.zarr'

SEED = 20260904
FATIA = 14
NOSSO = (39, 39)
REC2 = (20, 20)


def Z(p):
    z = zarr.open(p, 'r')
    try:
        keys = list(z.array_keys())
    except Exception:
        return z
    return z['0'] if '0' in keys else z


def dprime(d, f):
    return float((d.mean() - f.mean()) / np.sqrt((d.var() + f.var()) / 2 + 1e-12))


def mede(a, ink, dy, dx, rotulo):
    I0 = ink[dy:dy + a.shape[0], dx:dx + a.shape[1]]
    Hh, Ww = I0.shape
    av = a[:Hh, :Ww]
    mm = av > 0
    d = av[I0 & mm]
    f = av[~I0 & mm]
    if d.size < 1000 or f.size < 1000:
        print(f'  {rotulo:26} amostra pequena')
        return
    n = min(d.size, f.size)
    rng = np.random.default_rng(SEED)
    de = rng.choice(d, n, replace=False)
    fe = rng.choice(f, n, replace=False)
    print(f'  {rotulo:26} razao {float(np.median(de) / max(np.median(fe), 1)):6.3f}'
          f'   d prima {dprime(de, fe):6.3f}   n {n}')


def par(x, y, rotulo):
    m = (x > 0) & (y > 0)
    a, b = x[m], y[m]
    r = float(np.corrcoef(a, b)[0, 1])
    print(f'  {rotulo:34} r {r:.4f}   MAE {float(np.abs(a - b).mean()):6.2f}   n {int(m.sum())}')
    return r


ink = np.asarray(Z(LAB)[FATIA]) > 0

of = tifffile.imread(f'{D}/preds_oficial.tif').astype(np.float32)
nos = tifffile.imread(f'{D}/preds_orig.tif').astype(np.float32)
r2 = tifffile.imread(f'{D}/preds_recorte2.tif').astype(np.float32)
H, W = nos.shape
print(f'oficial {of.shape}   nosso {nos.shape}   recorte2 {r2.shape}\n')

print('=== metrica de tinta ===')
mede(of, ink, 0, 0, 'oficial (inteiro)')
mede(of[NOSSO[0]:NOSSO[0] + H, NOSSO[1]:NOSSO[1] + W], ink, *NOSSO, 'oficial recortado (39,39)')
mede(nos, ink, *NOSSO, 'nosso render (39,39)')
mede(r2, ink, *REC2, 'recorte2 do oficial (20,20)')
print('  referencia publicada: 2.884 / 2.824\n')

print('=== mapa a mapa ===')
ra = par(of[REC2[0]:REC2[0] + H, REC2[1]:REC2[1] + W], r2,
         'recorte2 vs oficial (mesmo conteudo)')
rb = par(of[NOSSO[0]:NOSSO[0] + H, NOSSO[1]:NOSSO[1] + W], nos,
         'nosso vs oficial (mesmo conteudo)')
# nosso(y,x) == recorte2(y+19, x+19)
d = NOSSO[0] - REC2[0]
rc = par(r2[d:, d:], nos[:H - d, :W - d],
         'nosso vs recorte2 (mesmo conteudo)')

print('\n=== veredito ===')
print(f'  recorte2 x oficial: {ra:.4f}    nosso x oficial: {rb:.4f}')
if ra < 0.90:
    print('  dois recortes do MESMO volume ja discordam nessa magnitude.')
    print('  o residuo e instabilidade da grade de tiles, nao do nosso render.')
    print('  a curva orig x q roda toda na mesma grade: o efeito cancela.')
elif ra > 0.97:
    print('  recortes do mesmo volume concordam. o residuo e do nosso render.')
    print('  PARE: hipotese da grade morre, procurar outra coisa.')
else:
    print('  resultado intermediario: a grade explica parte, sobra residuo.')
