#!/usr/bin/env python3
# Pergunta do sean: o erro da compressao se concentra na tinta?
# Compara |orig - vc| dentro da mascara de tinta contra fora, no proprio render
# (nao nas predicoes), na fatia do rotulo. Faz o mesmo para o ruido casado, que
# por construcao nao sabe onde ha tinta e serve de piso.
#
#   uv run --with zarr,numpy,tifffile,matplotlib python residuo_tinta.py w035
#   uv run --with zarr,numpy,tifffile,matplotlib python residuo_tinta.py w043

import os
import sys
import numpy as np
import zarr

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except ImportError:
    print('STOP: matplotlib missing')
    raise SystemExit(1)

SEG = sys.argv[1] if len(sys.argv) > 1 else 'w035'
H = os.path.expanduser('~/challenges/vesuvius')
ROOT = f'{H}/villa_ink/ink-detection'

if SEG == 'w035':
    D = f'{H}/ink-lens/metric/volcomp_w035'
    LAB = f'{ROOT}/labels_hf/native9-w035/w035_inklabels.zarr'
    SUP = None
    ORIG, VC = f'{D}/w043_orig.zarr', f'{D}/w043_vc.zarr'
    RUIDO = f'{D}/w043_ruido.zarr'          # pode nao existir
    FATIA = 14
else:
    D = f'{H}/ink-lens/metric/volcomp'
    C = f'{H}/ink-lens/metric/destila/segments_C/pherc0139-w043'
    LAB = f'{C}/pherc0139-w043_inklabels.zarr'
    SUP = f'{C}/pherc0139-w043_supervision_mask.zarr'
    ORIG, VC = f'{D}/w043_orig_novo.zarr', f'{D}/w043_vc_novo.zarr'
    RUIDO = f'{D}/w043_ruido_q8_novo.zarr'
    FATIA = 14

DY, DX = 39, 39
SAIDA = f'{D}/residuo_{SEG}.png'


def Z(p):
    z = zarr.open(p, 'r')
    try:
        k = list(z.array_keys())
    except Exception:
        return z
    return z['0'] if '0' in k else z


def carrega(p, k):
    if not os.path.exists(p):
        return None
    return np.asarray(Z(p)[k]).astype(np.float32)


ro = carrega(ORIG, FATIA)
rv = carrega(VC, FATIA)
if ro is None or rv is None:
    print(f'STOP: render ausente ({ORIG} / {VC})')
    raise SystemExit(1)
Hh, Ww = ro.shape
print(f'{SEG}: render {ro.shape}, fatia {FATIA}')

ink_full = np.asarray(Z(LAB)[FATIA]) > 0
ink = ink_full[DY:DY + Hh, DX:DX + Ww]
if SUP:
    sup = (np.asarray(Z(SUP)[FATIA]) > 0)[DY:DY + Hh, DX:DX + Ww]
else:
    sup = np.ones_like(ink)

valido = (ro > 0) & (rv > 0) & sup
dentro = ink & valido
fora = (~ink) & valido
print(f'  px validos {int(valido.sum())}, tinta {int(dentro.sum())}, '
      f'sem tinta {int(fora.sum())}')

if dentro.sum() < 1000 or fora.sum() < 1000:
    print('STOP: amostra pequena')
    raise SystemExit(1)


def resumo(err, rotulo):
    d, f = err[dentro], err[fora]
    print(f'  {rotulo:16} MAE tinta {d.mean():6.3f}   MAE fundo {f.mean():6.3f}'
          f'   razao {d.mean() / max(f.mean(), 1e-6):5.2f}'
          f'   P90 {np.percentile(d, 90):5.1f}/{np.percentile(f, 90):5.1f}')
    return d.mean(), f.mean()


print('\nerro absoluto no render, dentro vs fora da tinta:')
e_vc = np.abs(rv - ro)
mv = resumo(e_vc, 'volcomp q8')

rr = carrega(RUIDO, FATIA)
e_ru = None
if rr is not None:
    e_ru = np.abs(rr - ro)
    mr = resumo(e_ru, 'ruido casado')
    print(f'\n  concentracao relativa: volcomp {mv[0] / max(mv[1], 1e-6):.2f}x '
          f'contra {mr[0] / max(mr[1], 1e-6):.2f}x do ruido')
else:
    print(f'  (ruido casado ausente em {RUIDO}, pulando)')

# ---- painel ---------------------------------------------------------------
y0 = max(0, (Hh - 1800) // 2)
x0 = max(0, (Ww - 2200) // 2)
if SEG == 'w035':
    y0, x0 = 400, 300
jan = (slice(y0, y0 + 1800), slice(x0, x0 + 2200))

paineis = [(ro[jan], 'original render', 'gray', None),
           (rv[jan], 'volcomp q8 render', 'gray', None),
           (e_vc[jan], '|q8 - original|', 'inferno', None)]
if e_ru is not None:
    paineis.append((e_ru[jan], '|matched noise - original|', 'inferno', None))

vmin, vmax = np.percentile(ro[valido], [1, 99])
emax = float(np.percentile(e_vc[valido], 99))

fig, eixos = plt.subplots(1, len(paineis),
                          figsize=(4.2 * len(paineis), 4.2 * 1800 / 2200 + 1.4),
                          constrained_layout=True)
for ax, (img, titulo, cmap, _) in zip(np.atleast_1d(eixos), paineis):
    if cmap == 'gray':
        ax.imshow(img, cmap='gray', vmin=vmin, vmax=vmax, interpolation='nearest')
    else:
        ax.imshow(img, cmap='inferno', vmin=0, vmax=emax, interpolation='nearest')
    ax.set_title(titulo, fontsize=11, pad=8)
    ax.set_xticks([]); ax.set_yticks([])
    for b in ax.spines.values():
        b.set_visible(False)

fig.suptitle(f'PHerc0139 {SEG}, compression residual vs ink', fontsize=13)
fig.supxlabel('Error panels share a scale, 0 to the 99th percentile of the '
              'volcomp residual. Same slice, same crop.',
              fontsize=9, color='0.35')
fig.savefig(SAIDA, dpi=130, bbox_inches='tight', facecolor='white')
print(f'\nescrito {SAIDA}')
