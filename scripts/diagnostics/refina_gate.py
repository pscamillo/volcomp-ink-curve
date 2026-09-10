#!/usr/bin/env python3
# Diagnostico do gate do volcomp_w035.
# 1) reproduz o r atual (fatia 13, offset 40,40) como validacao do proprio script
# 2) varre fatia x offset em resolucao plena numa janela central
# 3) confirma o melhor candidato no arranjo inteiro
# Nao escreve nada. Nao altera mede_volcomp.py.

import os
import numpy as np
import zarr

D = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp_w035')
ROOT = os.path.expanduser('~/challenges/vesuvius/villa_ink/ink-detection')
OFF = f'{ROOT}/ink-dataset/pherc0139_9um/w035/w035.zarr'

BASE_K, BASE_DY, BASE_DX = 13, 40, 40   # o que o gate atual gravou
R_ESPERADO = 0.9444                      # o que ele imprimiu
RAIO = 6                                 # varredura +- RAIO voxels em cada eixo
WIN = 1200                               # janela central para a varredura


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


ro = Z(f'{D}/w043_orig.zarr')
off = Z(OFF)
K = ro.shape[0]
k = K // 2
print(f'render nosso {ro.shape}  oficial {off.shape}  fatia nossa {k}')

a_full = np.asarray(ro[k]).astype(np.float32)
H, W = a_full.shape

# ---- 1) validacao contra o numero ja medido -------------------------------
ob = np.asarray(off[BASE_K, BASE_DY:BASE_DY + H, BASE_DX:BASE_DX + W]).astype(np.float32)
r0, n0 = corr(a_full, ob)
print(f'baseline fatia {BASE_K} offset ({BASE_DY},{BASE_DX}): r = {r0:.4f}  n = {n0}')
if not np.isfinite(r0) or abs(r0 - R_ESPERADO) > 0.002:
    print(f'PARE: nao reproduz o gate atual ({R_ESPERADO}). O script esta lendo algo diferente.')
    raise SystemExit(1)
print('ok, reproduz o gate atual. seguindo para a varredura.\n')
del ob

# ---- 2) varredura em resolucao plena, janela central -----------------------
y0 = max(0, (H - WIN) // 2)
x0 = max(0, (W - WIN) // 2)
hw = min(WIN, H - y0)
ww = min(WIN, W - x0)
aw = a_full[y0:y0 + hw, x0:x0 + ww]
print(f'janela de busca: {hw}x{ww} a partir de ({y0},{x0}); '
      f'nao-zeros na janela: {int((aw > 0).sum())}')

cands = []
for kk in range(max(0, k - 2), min(off.shape[0], k + 3)):
    sl = np.asarray(off[kk]).astype(np.float32)
    achou = 0
    for dy in range(BASE_DY - RAIO, BASE_DY + RAIO + 1):
        for dx in range(BASE_DX - RAIO, BASE_DX + RAIO + 1):
            ys, xs = dy + y0, dx + x0
            if ys < 0 or xs < 0 or ys + hw > sl.shape[0] or xs + ww > sl.shape[1]:
                continue
            r, n = corr(aw, sl[ys:ys + hw, xs:xs + ww])
            if np.isfinite(r):
                cands.append((r, kk, dy, dx, n))
                achou += 1
    print(f'  fatia {kk}: {achou} offsets avaliados')
    del sl

if not cands:
    print('PARE: nenhum candidato valido.')
    raise SystemExit(1)

cands.sort(reverse=True)
print('\ntop 8 na janela (r, fatia, dy, dx, n):')
for c in cands[:8]:
    print(f'  r={c[0]:.4f}  fatia {c[1]}  offset ({c[2]},{c[3]})  n={c[4]}')

# onde o (13,40,40) caiu no ranking da janela
for i, c in enumerate(cands):
    if (c[1], c[2], c[3]) == (BASE_K, BASE_DY, BASE_DX):
        print(f'  [atual (13,40,40) esta em {i + 1}o lugar, r janela = {c[0]:.4f}]')
        break

# ---- 3) confirmacao do melhor no arranjo inteiro ---------------------------
_, kb, dyb, dxb = cands[0][:4]
print(f'\nconfirmando ({kb},{dyb},{dxb}) no arranjo inteiro...')
ob = np.asarray(off[kb, dyb:dyb + H, dxb:dxb + W]).astype(np.float32)
if ob.shape != a_full.shape:
    print(f'PARE: shape {ob.shape} != {a_full.shape}; offset cai fora do raster oficial.')
    raise SystemExit(1)
rb, nb = corr(a_full, ob)
print(f'r inteiro = {rb:.4f}  n = {nb}   (gate exige >= 0,95; atual {r0:.4f})')
print(f'delta r = {rb - r0:+.4f}')
print(f'\ngate: {"PASSA" if rb >= 0.95 else "AINDA REPROVA"}')
print(f'offset a usar: [{dyb}, {dxb}]  fatia oficial: {kb}')
