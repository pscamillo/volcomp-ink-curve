#!/usr/bin/env python3
# O controle foi casado por MAE no VOLUME. O render interpola, o que atenua
# ruido descorrelacionado e nao atenua erro de quantizacao (correlacionado por
# bloco DCT). Este script mede o MAE de cada braco no proprio render, contra o
# render original, para descobrir qual nivel de ruido casa de fato na entrada
# do detector.
#
#   uv run --with zarr,numpy python mede_mae_render.py w035

import os
import sys
import numpy as np
import zarr

SEG = sys.argv[1] if len(sys.argv) > 1 else 'w035'
H = os.path.expanduser('~/challenges/vesuvius')
FATIA = 14

if SEG == 'w035':
    D = f'{H}/ink-lens/metric/volcomp_w035'
    ORIG = f'{D}/w043_orig.zarr'
    BRACOS = [
        ('volcomp q2',  f'{D}/w043_q2.zarr',        1.99),
        ('volcomp q4',  f'{D}/w043_q4.zarr',        3.06),
        ('volcomp q8',  f'{D}/w043_vc.zarr',        3.61),
        ('volcomp q16', f'{D}/w043_q16.zarr',       6.68),
        ('ruido q2',    f'{D}/w043_ruido_q2.zarr',  1.99),
        ('ruido q4',    f'{D}/w043_ruido_q4.zarr',  3.06),
        ('ruido q8',    f'{D}/w043_ruido.zarr',     3.61),
        ('ruido q16',   f'{D}/w043_ruido_q16.zarr', 6.68),
    ]
else:
    D = f'{H}/ink-lens/metric/volcomp'
    ORIG = f'{D}/w043_orig_novo.zarr'
    BRACOS = [
        ('volcomp q2',  f'{D}/w043_q2_novo.zarr',       1.92),
        ('volcomp q4',  f'{D}/w043_q4_novo.zarr',       2.93),
        ('volcomp q8',  f'{D}/w043_vc_novo.zarr',       3.47),
        ('volcomp q16', f'{D}/w043_q16_novo.zarr',      6.29),
        ('ruido q8',    f'{D}/w043_ruido_q8_novo.zarr', 3.47),
    ]


def Z(p):
    z = zarr.open(p, 'r')
    try:
        k = list(z.array_keys())
    except Exception:
        return z
    return z['0'] if '0' in k else z


if not os.path.exists(ORIG):
    print(f'STOP: {ORIG} nao existe')
    raise SystemExit(1)

ro = np.asarray(Z(ORIG)[FATIA]).astype(np.float32)
print(f'{SEG}: render original {ro.shape}, fatia {FATIA}\n')
print(f"{'braco':14} {'MAE volume':>11} {'MAE render':>11} {'atenuacao':>10}"
      f" {'P90':>6} {'P99':>6}")
print('-' * 64)

for nome, caminho, mae_vol in BRACOS:
    if not os.path.exists(caminho):
        print(f'{nome:14}   ausente ({os.path.basename(caminho)})')
        continue
    a = np.asarray(Z(caminho)[FATIA]).astype(np.float32)
    if a.shape != ro.shape:
        print(f'{nome:14}   shape {a.shape} != {ro.shape}')
        continue
    m = (ro > 0) & (a > 0)
    e = np.abs(a[m] - ro[m])
    mae_r = float(e.mean())
    print(f'{nome:14} {mae_vol:11.2f} {mae_r:11.3f} {mae_r / mae_vol:9.2f}x'
          f' {np.percentile(e, 90):6.1f} {np.percentile(e, 99):6.1f}')

print('\nleitura: o controle honesto e o nivel de ruido cujo MAE no RENDER')
print('bate com o do volcomp q8, nao aquele casado no volume.')
