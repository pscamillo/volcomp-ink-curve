#!/usr/bin/env python3
# Criterio de sucesso do --flip-normals:
#   preds_orig.tif (fwd, render invertido pela flag) vs preds_oficial.tif (fwd)
#   antes: r 0.7641, MAE 14.7, nosso d' 2.622 contra 2.812 do oficial recortado
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
ANTES_R, ANTES_MAE, ANTES_D = 0.7641, 14.727, 2.622


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
        print(f'  {rotulo:24} amostra pequena')
        return None
    n = min(d.size, f.size)
    rng = np.random.default_rng(SEED)
    de = rng.choice(d, n, replace=False)
    fe = rng.choice(f, n, replace=False)
    raz = float(np.median(de) / max(np.median(fe), 1))
    dp = dprime(de, fe)
    print(f'  {rotulo:24} razao {raz:6.3f}   d prima {dp:6.3f}   n {n}')
    return raz, dp


ink = np.asarray(Z(LAB)[FATIA]) > 0

of = tifffile.imread(f'{D}/preds_oficial.tif').astype(np.float32)
nos = tifffile.imread(f'{D}/preds_orig.tif').astype(np.float32)
nos_r = tifffile.imread(f'{D}/preds_orig_reverse.tif').astype(np.float32)
print(f'oficial {of.shape}   nosso fwd {nos.shape}\n')

print('=== mapa a mapa, mesmo recorte ===')
H, W = nos.shape
oc = of[DY:DY + H, DX:DX + W]
if oc.shape != nos.shape:
    print(f'  recorte {oc.shape} != {nos.shape}; abortando')
    raise SystemExit(1)
m = (oc > 0) & (nos > 0)
x, y = oc[m], nos[m]
r = float(np.corrcoef(x, y)[0, 1])
e = y - x
mae = float(np.abs(e).mean())
print(f'  n {int(m.sum())}')
print(f'  r     {r:.4f}   (antes do flip: {ANTES_R:.4f})')
print(f'  MAE   {mae:.3f}   (antes: {ANTES_MAE:.3f})')
print(f'  P99   {np.percentile(np.abs(e), 99):.1f}')

print('\n=== metrica no mesmo recorte ===')
mede(oc, ink, DY, DX, 'oficial (recortado)')
res = mede(nos, ink, DY, DX, 'nosso fwd (flip)')
mede(nos_r, ink, DY, DX, 'nosso _reverse (ruido)')
print(f'  referencia oficial na area inteira: 2.884 / 2.824')

print('\n=== veredito ===')
if res is None:
    print('  sem numero para o braco fwd')
else:
    print(f"  d' era {ANTES_D:.3f} sem flip, agora {res[1]:.3f}, oficial recortado 2.812")
    if r > 0.95 and abs(res[1] - 2.812) < 0.05:
        print('  flip resolveu: rodar os outros quatro volumes')
    elif r > ANTES_R + 0.1:
        print('  melhorou mas nao fechou: olhar o residuo antes de rodar o resto')
    else:
        print('  flip nao resolveu: parar e reabrir a hipotese')
