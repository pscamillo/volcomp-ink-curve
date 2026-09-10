#!/usr/bin/env python3
# A) o nosso render esta invertido em profundidade em relacao ao w035.zarr oficial?
#    deslocamento-por-1 e inversao coincidem na fatia 14; divergem nas outras.
# B) qual fatia do rotulo native9 casa com o nosso render?
#    a fatia 14 tem que reproduzir 2,826 / 2,628, senao a minha metrica difere da do script.
# Nao escreve nada.

import os
import numpy as np
import zarr
import tifffile

D = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp_w035')
ROOT = os.path.expanduser('~/challenges/vesuvius/villa_ink/ink-detection')
OFF = f'{ROOT}/ink-dataset/pherc0139_9um/w035/w035.zarr'
LAB = f'{ROOT}/labels_hf/native9-w035/w035_inklabels.zarr'

DY, DX = 39, 39
WIN = 1200
SEED = 20260904
REF_RAZAO, REF_D = 2.826, 2.628   # o que mede_volcomp acabou de imprimir p/ orig _reverse, rotulo 14


def Z(p):
    z = zarr.open(p, 'r')
    try:
        keys = list(z.array_keys())
    except Exception:
        return z
    return z['0'] if '0' in keys else z


def corr(x, y):
    m = (x > 0) & (y > 0)
    n = int(m.sum())
    if n < 1000:
        return float('nan'), n
    return float(np.corrcoef(x[m], y[m])[0, 1]), n


def dprime(d, f):
    return float((d.mean() - f.mean()) / np.sqrt((d.var() + f.var()) / 2 + 1e-12))


ro = Z(f'{D}/w043_orig.zarr')
off = Z(OFF)
K = ro.shape[0]
H, W = ro.shape[1], ro.shape[2]
print(f'render {ro.shape}  oficial {off.shape}\n')

# ---------- A) inversao vs deslocamento ----------
print('=== A) pareamento de profundidade ===')
y0 = max(0, (H - WIN) // 2)
x0 = max(0, (W - WIN) // 2)
hw = min(WIN, H - y0)
ww = min(WIN, W - x0)

for j in (6, 10, 14, 18, 22):
    if j >= K:
        continue
    aw = np.asarray(ro[j, y0:y0 + hw, x0:x0 + ww]).astype(np.float32)
    k_desl = j - 1                 # hipotese: deslocado em 1
    k_inv = (K - 1) - j            # hipotese: invertido
    linha = f'  nossa {j:2d}: '
    for nome, kk in (('deslocado', k_desl), ('invertido', k_inv)):
        if kk < 0 or kk >= off.shape[0]:
            linha += f'{nome} {kk:>3}: fora   '
            continue
        b = np.asarray(off[kk, DY + y0:DY + y0 + hw, DX + x0:DX + x0 + ww]).astype(np.float32)
        r, _ = corr(aw, b)
        linha += f'{nome} {kk:>3}: r={r:6.3f}   '
    print(linha)
print('  (se as duas colunas coincidirem numa linha, e a fatia 14; olhe as outras)\n')

# ---------- B) varredura da fatia do rotulo ----------
print('=== B) fatia do rotulo native9 vs preds_orig_reverse ===')
lab = Z(LAB)
a = tifffile.imread(f'{D}/preds_orig_reverse.tif').astype(np.float32)
print(f'  preds {a.shape}  rotulo {lab.shape}')
rng = np.random.default_rng(SEED)

print(f"  {'fatia':>5} {'razao':>7} {'d prima':>8} {'n':>9}")
melhor = None
for s in range(max(0, 14 - 4), min(lab.shape[0], 14 + 5)):
    ink = np.asarray(lab[s]) > 0
    I0 = ink[DY:DY + a.shape[0], DX:DX + a.shape[1]]
    Hh, Ww = I0.shape
    av = a[:Hh, :Ww]
    mm = av > 0
    d = av[I0 & mm]
    f = av[~I0 & mm]
    if d.size < 1000 or f.size < 1000:
        print(f'  {s:5d}   amostra pequena')
        continue
    n = min(d.size, f.size)
    r2 = np.random.default_rng(SEED)
    de = r2.choice(d, n, replace=False)
    fe = r2.choice(f, n, replace=False)
    raz = float(np.median(de) / max(np.median(fe), 1))
    dp = dprime(de, fe)
    marca = ''
    if s == 14:
        ok = abs(raz - REF_RAZAO) < 0.02 and abs(dp - REF_D) < 0.05
        marca = '  <- controle: ' + ('bate com mede_volcomp' if ok else 'NAO BATE, metrica difere')
    print(f'  {s:5d} {raz:7.3f} {dp:8.3f} {n:9d}{marca}')
    if melhor is None or dp > melhor[1]:
        melhor = (s, dp, raz)

if melhor:
    print(f'\n  melhor fatia por d\': {melhor[0]}  (d\' {melhor[1]:.3f}, razao {melhor[2]:.3f})')
    print(f'  referencia oficial: 2,884 / 2,824')
