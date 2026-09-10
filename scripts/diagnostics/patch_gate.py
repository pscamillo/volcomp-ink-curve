#!/usr/bin/env python3
# Corrige a quantizacao de 4 voxels na busca de offset do gate.
# Faz backup, verifica os alvos exatos antes de tocar, aborta se algo nao bater.

import os
import sys

D = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp_w035')
ALVO = f'{D}/mede_volcomp.py'

L_COARSE = "    dy, dx = iy * 4, ix * 4; ob = off[kk, dy:dy + H, dx:dx + W]\n"
L_NOVA = ("    dy, dx = _fino(off, kk, ro[k], iy * 4, ix * 4, H, W)"
          "; ob = off[kk, dy:dy + H, dx:dx + W]\n")

MARCA = "# gate: offset (nosso render está recortado do raster oficial) e fatia por correlação\n"

HELPER = '''def _fino(off, kk, ref, dy0, dx0, H, W, raio=4, win=1200):
    """Refina (dy0,dx0) em resolucao plena numa janela central. A busca grossa
    roda no arranjo decimado por 4 e so consegue devolver multiplos de 4."""
    y0 = max(0, (H - win) // 2); x0 = max(0, (W - win) // 2)
    hw = min(win, H - y0); ww = min(win, W - x0)
    aw = np.asarray(ref[y0:y0 + hw, x0:x0 + ww]).astype(np.float32)
    sl = np.asarray(off[kk]).astype(np.float32)
    melhor = (-2.0, dy0, dx0)
    for dy in range(dy0 - raio, dy0 + raio + 1):
        for dx in range(dx0 - raio, dx0 + raio + 1):
            ys, xs = dy + y0, dx + x0
            if ys < 0 or xs < 0 or ys + hw > sl.shape[0] or xs + ww > sl.shape[1]:
                continue
            b = sl[ys:ys + hw, xs:xs + ww]
            m = (aw > 0) & (b > 0)
            if m.sum() < 1000:
                continue
            r = float(np.corrcoef(aw[m], b[m])[0, 1])
            if np.isfinite(r) and r > melhor[0]:
                melhor = (r, dy, dx)
    return melhor[1], melhor[2]


'''

src = open(ALVO).read()

if '_fino(' in src:
    print('ja aplicado (achei _fino no arquivo). nada a fazer.')
    sys.exit(0)

falhas = []
if src.count(L_COARSE) != 1:
    falhas.append(f'linha do offset grosso aparece {src.count(L_COARSE)}x (esperado 1)')
if src.count(MARCA) != 1:
    falhas.append(f'comentario do gate aparece {src.count(MARCA)}x (esperado 1)')
if falhas:
    print('PARE, nao vou editar:')
    for f in falhas:
        print('  -', f)
    sys.exit(1)

open(ALVO + '.bak', 'w').write(src)

novo = src.replace(MARCA, HELPER + MARCA).replace(L_COARSE, L_NOVA)
novo = novo.replace('vs w043.zarr oficial fatia', 'vs w035.zarr oficial fatia')

open(ALVO, 'w').write(novo)

print('backup em mede_volcomp.py.bak')
print('helper _fino inserido; linha do offset trocada; string w043->w035 corrigida')
print('\ntrechos alterados:')
for i, ln in enumerate(novo.split('\n'), 1):
    if '_fino' in ln or 'w035.zarr oficial fatia' in ln:
        print(f'  {i}: {ln[:110]}')
