#!/usr/bin/env python3
# Figure for the README / R1 visual check.
# Same render footprint, same grayscale window across all panels.
#
#   uv run --with numpy,tifffile,matplotlib python faz_painel.py            # full sheet
#   uv run --with numpy,tifffile,matplotlib python faz_painel.py detail     # zoomed crop

import os
import sys
import numpy as np
import tifffile

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except ImportError:
    print('STOP: matplotlib missing')
    raise SystemExit(1)

D = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp_w035')

MODO = sys.argv[1] if len(sys.argv) > 1 else 'full'
if MODO == 'detail':
    Y0, X0, ALT, LARG = 400, 300, 1800, 2200
    SAIDA = f'{D}/panel_w035_detail.png'
    SUB = 'detail crop'
else:
    Y0, X0, ALT, LARG = 0, 0, 5741, 5161
    SAIDA = f'{D}/panel_w035_full.png'
    SUB = 'full segment'

PAINEIS = [
    ('preds_orig.tif',  'original',               "d' 2.587"),
    ('preds_ruido.tif', 'matched noise, MAE 3.6', "d' 2.528   (-2.3%)"),
    ('preds_vc.tif',    'volcomp q8, MAE 3.6',    "d' 1.921   (-25.8%)"),
    ('preds_q16.tif',   'volcomp q16, MAE 6.7',   "d' 1.445   (-44.1%)"),
]

imgs = []
for arq, titulo, sub in PAINEIS:
    p = f'{D}/{arq}'
    if not os.path.exists(p):
        print(f'STOP: {arq} missing')
        raise SystemExit(1)
    a = tifffile.imread(p).astype(np.float32)
    rec = a[Y0:Y0 + ALT, X0:X0 + LARG]
    if rec.size == 0:
        print(f'STOP: empty window for {arq} (shape {a.shape})')
        raise SystemExit(1)
    imgs.append((rec, titulo, sub))
    print(f'{arq:20} window {rec.shape}')

ref = imgs[0][0]
vmin, vmax = np.percentile(ref[ref > 0], [1, 99])
print(f'shared grayscale window: [{vmin:.0f}, {vmax:.0f}]')

alt, larg = imgs[0][0].shape
aspecto = alt / larg
lado = 4.2

fig, eixos = plt.subplots(
    1, len(imgs),
    figsize=(lado * len(imgs), lado * aspecto + 1.6),
    constrained_layout=True,
)

for ax, (rec, titulo, sub) in zip(np.atleast_1d(eixos), imgs):
    ax.imshow(rec, cmap='gray', vmin=vmin, vmax=vmax, interpolation='nearest')
    ax.set_title(f'{titulo}\n{sub}', fontsize=11, linespacing=1.5, pad=10)
    ax.set_xticks([])
    ax.set_yticks([])
    for borda in ax.spines.values():
        borda.set_visible(False)

fig.suptitle(f'PHerc0139 w035, ink_9um detector - {SUB}', fontsize=13)

legenda = (
    'Identical render footprint and inference settings across panels. '
    f'Shared grayscale window [{vmin:.0f}, {vmax:.0f}] from the 1st-99th percentiles '
    "of the original; no per-panel normalisation. d' measured against the same "
    'label slice with equalised n.'
)
fig.supxlabel(legenda, fontsize=9, color='0.35', wrap=True)

fig.savefig(SAIDA, dpi=130, bbox_inches='tight', facecolor='white')
print(f'written {SAIDA}')
