#!/usr/bin/env python3
# Aplica na volta 1 (w043) as mesmas tres correcoes da volta 2:
#   1) refinamento fino do offset do gate (a busca grossa so devolve multiplos de 4)
#   2) leitura dos preds_*_novo.tif (renders com --flip-normals)
#   3) escolha do braco pelo maior d', em vez de sufixo fixo
# Faz backup e aborta se qualquer alvo nao bater exatamente.

import os
import sys

S = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp')
MV = f'{S}/mede_volcomp.py'
MC = f'{S}/mede_curva_q.py'

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

MARCA = "# gate: offset (nosso render está recortado do raster oficial) e fatia por correlação\n"
L_COARSE = "    dy, dx = iy * 4, ix * 4; ob = off[kk, dy:dy + H, dx:dx + W]\n"
L_NOVA = ("    dy, dx = _fino(off, kk, ro[k], iy * 4, ix * 4, H, W)"
          "; ob = off[kk, dy:dy + H, dx:dx + W]\n")

VOLS_ANT = "ro = Z(f'{D}/w043_orig.zarr'); rv = Z(f'{D}/w043_vc.zarr')"
VOLS_NOV = "ro = Z(f'{D}/w043_orig_novo.zarr'); rv = Z(f'{D}/w043_vc_novo.zarr')"

PREDS_ANT = "a = tifffile.imread(f'{D}/preds_{b}{s}.tif')"
PREDS_NOV = "a = tifffile.imread(f'{D}/preds_{b}_novo{s}.tif')"


def carrega(p):
    if not os.path.exists(p):
        print(f'PARE: {p} nao existe')
        sys.exit(1)
    return open(p).read()


# ---------------- mede_volcomp.py ----------------
src = carrega(MV)
if '_fino(' in src:
    print('mede_volcomp.py: ja aplicado')
else:
    falhas = []
    for nome, alvo in (('comentario do gate', MARCA), ('offset grosso', L_COARSE),
                       ('abertura dos volumes', VOLS_ANT), ('leitura dos preds', PREDS_ANT)):
        if src.count(alvo) != 1:
            falhas.append(f'{nome}: {src.count(alvo)} ocorrencias (esperado 1)')
    if falhas:
        print('PARE, mede_volcomp.py nao editado:')
        for f in falhas:
            print('  -', f)
        sys.exit(1)
    open(MV + '.bak', 'w').write(src)
    novo = (src.replace(MARCA, HELPER + MARCA)
               .replace(L_COARSE, L_NOVA)
               .replace(VOLS_ANT, VOLS_NOV)
               .replace(PREDS_ANT, PREDS_NOV))
    open(MV, 'w').write(novo)
    print('mede_volcomp.py: backup .bak, gate refinado, volumes e preds _novo')

# ---------------- mede_curva_q.py ----------------
src = carrega(MC)
if "prev['orig']['d'] >=" in src:
    print('mede_curva_q.py: ja aplicado')
    raise SystemExit(0)

open(MC + '.bak', 'w').write(src)
novo = src

# braco por maior d' no JSON
for b in ('orig', 'vc'):
    ant = f"prev['{b}_reverse']['razao'], prev['{b}_reverse']['d']"
    esc = (f"(prev['{b}'] if prev['{b}']['d'] >= prev['{b}_reverse']['d'] "
           f"else prev['{b}_reverse'])")
    if ant in novo:
        novo = novo.replace(ant, f"{esc}['razao'], {esc}['d']")
        print(f"mede_curva_q.py: braco de {b} agora escolhido pelo maior d'")
    else:
        print(f"AVISO: padrao de {b} nao encontrado; conferir a mao")

# arquivos dos q
if 'preds_q{q}_reverse.tif' in novo:
    novo = novo.replace('preds_q{q}_reverse.tif', 'preds_q{q}_novo.tif')
    print('mede_curva_q.py: preds dos q apontam para _novo (braco fwd)')
elif 'preds_q{q}.tif' in novo:
    novo = novo.replace('preds_q{q}.tif', 'preds_q{q}_novo.tif')
    print('mede_curva_q.py: preds dos q apontam para _novo')
else:
    print('AVISO: padrao dos preds q nao encontrado; conferir a mao')

# offset pelo gate em vez de fixo
if 'DY, DX = 40, 40' in novo:
    novo = novo.replace(
        'DY, DX = 40, 40',
        "DY, DX = json.load(open(f'{D}/volcomp_resumo.json'))['gate']['offset']")
    if 'import json' not in novo:
        novo = novo.replace('import os', 'import os\nimport json', 1)
    print('mede_curva_q.py: offset lido do gate')
else:
    print('AVISO: DY, DX = 40, 40 nao encontrado; conferir a mao')

open(MC, 'w').write(novo)
print('\npronto. conferir com: grep -n "_fino\\|_novo\\|prev\\[" nos dois arquivos')
