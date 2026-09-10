#!/usr/bin/env python
"""Compara render original vs volcomp e as predições do ink_9um. uv run --with zarr,numpy,scipy,tifffile python mede_volcomp.py"""
import os, json, numpy as np, zarr, tifffile
ROOT = os.path.expanduser('~/challenges/vesuvius/villa_ink/ink-detection'); D = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp')
C = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/destila/segments_C/pherc0139-w043')


def Z(p):
    z = zarr.open(p, 'r'); a = z['0'] if hasattr(z, 'array_keys') and '0' in list(z.array_keys()) else z
    return np.asarray(a[:], np.float32)


def dprime(a, b): return float((a.mean() - b.mean()) / np.sqrt((a.var() + b.var()) / 2 + 1e-12))


R = {}
from scipy.signal import fftconvolve
ro = Z(f'{D}/w043_orig_novo.zarr'); rv = Z(f'{D}/w043_vc_novo.zarr'); off = Z(f'{ROOT}/ink-dataset/pherc0139_9um/w043/w043.zarr')
K = ro.shape[0]; H = min(ro.shape[1], rv.shape[1]); W = min(ro.shape[2], rv.shape[2]); ro, rv = ro[:, :H, :W], rv[:, :H, :W]
k = K // 2
def _fino(off, kk, ref, dy0, dx0, H, W, raio=4, win=1200):
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


# gate: offset (nosso render está recortado do raster oficial) e fatia por correlação
a = ro[k][::4, ::4].copy(); a[a > 0] -= a[a > 0].mean()
best = None
for kk in range(max(0, k - 2), min(off.shape[0], k + 3)):
    b = off[kk][::4, ::4].copy(); b[b > 0] -= b[b > 0].mean()
    c = fftconvolve(b, a[::-1, ::-1], mode='valid'); iy, ix = np.unravel_index(np.argmax(c), c.shape)
    dy, dx = _fino(off, kk, ro[k], iy * 4, ix * 4, H, W); ob = off[kk, dy:dy + H, dx:dx + W]
    if ob.shape != ro[k].shape: continue
    m = (ro[k] > 0) & (ob > 0); r = float(np.corrcoef(ro[k][m], ob[m])[0, 1])
    if best is None or r > best[0]: best = (r, kk, dy, dx)
r_off, kk, dy, dx = best
print(f'gate: render original nosso (fatia {k}) vs w043.zarr oficial fatia {kk}, offset ({dy},{dx}): r = {r_off:.4f} (exigido ≥ 0,95)')
R['gate'] = dict(r=r_off, fatia_oficial=kk, offset=[int(dy), int(dx)])
# erro pixel a pixel
mv = (ro > 0) & (rv > 0); e = (rv - ro)[mv]
R['erro'] = dict(MAE=float(np.abs(e).mean()), P90=float(np.percentile(np.abs(e), 90)), P99=float(np.percentile(np.abs(e), 99)),
                 PSNR=float(20 * np.log10(255 / max(np.sqrt((e ** 2).mean()), 1e-6))), por_camada=[float(np.abs((rv[j] - ro[j])[(ro[j] > 0) & (rv[j] > 0)]).mean()) for j in range(K)])
print(f"erro volcomp vs original: MAE {R['erro']['MAE']:.2f}  P90 {R['erro']['P90']:.1f}  P99 {R['erro']['P99']:.1f}  PSNR {R['erro']['PSNR']:.1f} dB")
print('  MAE por camada:', np.round(R['erro']['por_camada'], 1).tolist())
# predições
ink = Z(f'{C}/pherc0139-w043_inklabels.zarr')[14] > 0; sup = Z(f'{C}/pherc0139-w043_supervision_mask.zarr')[14] > 0
rng = np.random.default_rng(20260904)
print(f"{'braco':6} {'sent':4} {'razao':>7} {'d prima':>8} {'nulo':>6} {'n':>8}")
for b in ('orig', 'vc'):
    for s in ('', '_reverse'):
        a = tifffile.imread(f'{D}/preds_{b}_novo{s}.tif').astype(np.float32)
        I0 = ink[dy:dy + a.shape[0], dx:dx + a.shape[1]]; S0 = sup[dy:dy + a.shape[0], dx:dx + a.shape[1]]; Hh, Ww = I0.shape; a = a[:Hh, :Ww]; I = I0; S = S0; mm = a > 0
        d = a[I & S & mm]; f = a[~I & S & mm]; n = min(d.size, f.size)
        de = rng.choice(d, n, replace=False); fe = rng.choice(f, n, replace=False)
        idx = rng.permutation(np.flatnonzero((S & mm).ravel())); kk = int((I & S & mm).sum()); cv = a.ravel()
        raz = float(np.median(de) / max(np.median(fe), 1)); dp = dprime(de, fe); nul = float(np.median(cv[idx[:kk]]) / max(np.median(cv[idx[kk:2 * kk]]), 1))
        print(f'{b:6} {s or "fwd":4} {raz:7.3f} {dp:8.3f} {nul:6.3f} {n:8d}'); R[f'{b}{s}'] = dict(razao=raz, d=dp, nulo=nul, n=n)
print('  ref oficial (w043.zarr, fwd): 2,310 / 1,481.  criterio: |delta razao| <= 0,05 e |delta d| <= 0,10')
json.dump(R, open(f'{D}/volcomp_resumo.json', 'w'), indent=1)
