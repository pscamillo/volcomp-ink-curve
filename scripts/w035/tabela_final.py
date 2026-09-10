#!/usr/bin/env python3
# Tabela final da volta 2 (w035): volcomp x ruido casado por MAE, mesmo braco (fwd),
# mesma moldura de render (39,39), mesmo rotulo, mesmo n equalizado.

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

# q -> (arquivo volcomp, arquivo ruido casado, MAE do volcomp, taxa)
NIVEIS = [
    (2,  'preds_q2.tif',  'preds_ruido_q2.tif',  1.99, 10.5),
    (4,  'preds_q4.tif',  'preds_ruido_q4.tif',  3.06, 16.9),
    (8,  'preds_vc.tif',  'preds_ruido.tif',     3.61, 44.0),
    (16, 'preds_q16.tif', 'preds_ruido_q16.tif', 6.68, 50.8),
]


def Z(p):
    z = zarr.open(p, 'r')
    try:
        keys = list(z.array_keys())
    except Exception:
        return z
    return z['0'] if '0' in keys else z


def medida(caminho, ink):
    if not os.path.exists(caminho):
        return None
    a = tifffile.imread(caminho).astype(np.float32)
    I = ink[DY:DY + a.shape[0], DX:DX + a.shape[1]]
    a = a[:I.shape[0], :I.shape[1]]
    mm = a > 0
    d = a[I & mm]
    f = a[~I & mm]
    if d.size < 1000 or f.size < 1000:
        return None
    n = min(d.size, f.size)
    rng = np.random.default_rng(SEED)
    de = rng.choice(d, n, replace=False)
    fe = rng.choice(f, n, replace=False)
    raz = float(np.median(de) / max(np.median(fe), 1))
    dp = float((de.mean() - fe.mean()) / np.sqrt((de.var() + fe.var()) / 2))
    return raz, dp, n


ink = np.asarray(Z(LAB)[FATIA]) > 0

base = medida(f'{D}/preds_orig.tif', ink)
if base is None:
    print('PARE: preds_orig.tif ausente')
    raise SystemExit(1)
raz0, dp0, n0 = base
print(f'w035, braco fwd, moldura (39,39), rotulo fatia {FATIA}, n {n0}')
print(f'original: razao {raz0:.3f}  d prima {dp0:.3f}')
print(f'referencia publicada (area inteira): 2.884 / 2.824\n')

print(f"{'q':>3} {'taxa':>6} {'MAE':>5} | {'volcomp d':>9} {'perda':>7} | "
      f"{'ruido d':>8} {'perda':>7} | {'fator':>6}")
print('-' * 74)

linhas = []
for q, fq, fr, mae, taxa in NIVEIS:
    mv = medida(f'{D}/{fq}', ink)
    mr = medida(f'{D}/{fr}', ink)
    if mv is None:
        print(f'{q:3d} {taxa:6.1f} {mae:5.2f} | volcomp ausente')
        continue
    pv = (mv[1] - dp0) / dp0 * 100
    if mr is None:
        print(f'{q:3d} {taxa:6.1f} {mae:5.2f} | {mv[1]:9.3f} {pv:6.1f}% | '
              f'{"ausente":>8} {"":>7} | {"":>6}')
        continue
    pr = (mr[1] - dp0) / dp0 * 100
    fator = pv / pr if abs(pr) > 1e-6 else float('inf')
    print(f'{q:3d} {taxa:6.1f} {mae:5.2f} | {mv[1]:9.3f} {pv:6.1f}% | '
          f'{mr[1]:8.3f} {pr:6.1f}% | {fator:5.1f}x')
    linhas.append((q, mae, mv[1], pv, mr[1], pr, fator))

if linhas:
    print('\nrazoes (controle de que o ruido nao desloca a mediana):')
    for q, fq, fr, mae, taxa in NIVEIS:
        mv = medida(f'{D}/{fq}', ink)
        mr = medida(f'{D}/{fr}', ink)
        if mv and mr:
            print(f'  q{q:<3} volcomp {mv[0]:.3f}   ruido {mr[0]:.3f}   original {raz0:.3f}')
    print('\nleitura: se o fator for >> 1, a perda do volcomp nao e reacao generica')
    print('a perturbacao; e remocao de estrutura que o detector usa.')
