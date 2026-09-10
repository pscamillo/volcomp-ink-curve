#!/usr/bin/env python3
# 1) razao / d' do preds_oficial (fwd e reverse) na grade nativa, offset (0,0)
#    -> reproduz a referencia 2,884 / 2,824?
# 2) o nosso mapa (preds_orig_reverse, render recortado e invertido) contra o
#    oficial (preds_oficial, fwd) no mesmo recorte -> quanto vale o resto?
# Nao escreve nada.

import os
import numpy as np
import zarr
import tifffile

D = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp_w035')
ROOT = os.path.expanduser('~/challenges/vesuvius/villa_ink/ink-detection')
LAB = f'{ROOT}/labels_hf/native9-w035/w035_inklabels.zarr'

DY, DX = 39, 39
SEED = 20260904
FATIA = 14


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
        print(f'  {rotulo:22} amostra pequena ({d.size}/{f.size})')
        return
    n = min(d.size, f.size)
    rng = np.random.default_rng(SEED)
    de = rng.choice(d, n, replace=False)
    fe = rng.choice(f, n, replace=False)
    raz = float(np.median(de) / max(np.median(fe), 1))
    print(f'  {rotulo:22} razao {raz:6.3f}   d prima {dprime(de, fe):6.3f}   n {n}')


lab = Z(LAB)
ink = np.asarray(lab[FATIA]) > 0
print(f'rotulo {lab.shape}, fatia {FATIA}, tinta {int(ink.sum())} px\n')

# ---------- 1) metrica no volume oficial, grade nativa ----------
print('=== 1) preds do w035.zarr oficial, offset (0,0) ===')
for nome, arq in (('oficial fwd', 'preds_oficial.tif'),
                  ('oficial _reverse', 'preds_oficial_reverse.tif')):
    a = tifffile.imread(f'{D}/{arq}').astype(np.float32)
    if a.ndim != 2:
        print(f'  {nome}: shape inesperado {a.shape}')
        continue
    mede(a, ink, 0, 0, nome)
print('  referencia oficial:    razao  2.884   d prima  2.824\n')

# ---------- 2) nosso mapa vs oficial, mesmo recorte ----------
print('=== 2) nosso render recortado vs oficial, mapa a mapa ===')
of = tifffile.imread(f'{D}/preds_oficial.tif').astype(np.float32)
nos = tifffile.imread(f'{D}/preds_orig_reverse.tif').astype(np.float32)
print(f'  oficial {of.shape}   nosso {nos.shape}')

H, W = nos.shape
oc = of[DY:DY + H, DX:DX + W]
if oc.shape != nos.shape:
    print(f'  recorte {oc.shape} != {nos.shape}; abortando comparacao')
else:
    m = (oc > 0) & (nos > 0)
    n = int(m.sum())
    x, y = oc[m], nos[m]
    r = float(np.corrcoef(x, y)[0, 1])
    e = y - x
    print(f'  n {n}')
    print(f'  r        {r:.4f}')
    print(f'  MAE      {np.abs(e).mean():.3f}')
    print(f'  P99      {np.percentile(np.abs(e), 99):.1f}')
    print(f'  faixa    oficial [{x.min():.0f},{x.max():.0f}]  nosso [{y.min():.0f},{y.max():.0f}]')
    print(f'  medianas oficial {np.median(x):.1f}   nosso {np.median(y):.1f}')
    print('\n  e a mesma metrica nos dois, no mesmo recorte:')
    mede(oc, ink, DY, DX, 'oficial (recortado)')
    mede(nos, ink, DY, DX, 'nosso _reverse')
