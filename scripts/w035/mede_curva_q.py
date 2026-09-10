#!/usr/bin/env python
"""Curva q: mede razão/d' (reverse) das predições preds_q{Q}.tif contra o original. uv run --with tifffile,numpy,zarr,matplotlib python mede_curva_q.py"""
import os, json, numpy as np, zarr, tifffile
D = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp_w035'); C = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/destila/segments_C/pherc0139-w043')
DY, DX = json.load(open(f'{D}/volcomp_resumo.json'))['gate']['offset']
def Z(p):
    z = zarr.open(p, 'r'); a = z['0'] if hasattr(z, 'array_keys') and '0' in list(z.array_keys()) else z; return np.asarray(a[:], np.float32)
import os as _o; ROOT=_o.path.expanduser('~/challenges/vesuvius/villa_ink/ink-detection'); ink = Z(f'{ROOT}/labels_hf/native9-w035/w035_inklabels.zarr')[14] > 0; sup = np.ones_like(ink)  # native9 sem supervision_mask: toda a região com dado
cod = json.load(open(f'{D}/codifica_q.json')); prev = json.load(open(f'{D}/volcomp_resumo.json'))
def medida(p):
    rng = np.random.default_rng(20260904); a = tifffile.imread(p).astype(np.float32)
    I = ink[DY:DY + a.shape[0], DX:DX + a.shape[1]]; S = sup[DY:DY + a.shape[0], DX:DX + a.shape[1]]; a = a[:I.shape[0], :I.shape[1]]; m = a > 0
    d = a[I & S & m]; f = a[~I & S & m]; n = min(d.size, f.size); de = rng.choice(d, n, replace=False); fe = rng.choice(f, n, replace=False)
    return float(np.median(de) / max(np.median(fe), 1)), float((de.mean() - fe.mean()) / np.sqrt((de.var() + fe.var()) / 2))
pts = {1: ((prev['orig'] if prev['orig']['d'] >= prev['orig_reverse']['d'] else prev['orig_reverse'])['razao'], (prev['orig'] if prev['orig']['d'] >= prev['orig_reverse']['d'] else prev['orig_reverse'])['d'], 1.0), 8: ((prev['vc'] if prev['vc']['d'] >= prev['vc_reverse']['d'] else prev['vc_reverse'])['razao'], (prev['vc'] if prev['vc']['d'] >= prev['vc_reverse']['d'] else prev['vc_reverse'])['d'], 44.0)}
for q in (2, 4, 16):
    if os.path.exists(f'{D}/preds_q{q}.tif'):
        r, d = medida(f'{D}/preds_q{q}.tif'); pts[q] = (r, d, cod[f'q{q}']['taxa'])
r0, d0, _ = pts[1]
print(f"{'q':>3} {'taxa':>6} {'razao':>7} {'d prima':>8} {'d razao':>8} {'d d':>7} {'passa':>6}")
rec = None
for q in sorted(pts):
    r, d, t = pts[q]; ok = abs(r - r0) <= 0.05 and abs(d - d0) <= 0.10
    print(f'{q:3d} {t:6.1f} {r:7.3f} {d:8.3f} {r-r0:+8.3f} {d-d0:+7.3f} {"sim" if ok else "nao":>6}')
    if ok and q > 1: rec = q
print(f'\nrecomendacao (maior q que nao custa): {rec if rec else "nenhum >= 2; volcomp nao serve para 2,5D ink como esta"}')
json.dump({str(k): dict(razao=v[0], d=v[1], taxa=v[2]) for k, v in pts.items()}, open(f'{D}/curva_q.json', 'w'), indent=1)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
qs = sorted(pts); fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].plot(qs, [pts[q][0] for q in qs], 'o-'); ax[0].axhline(r0 - 0.05, ls='--', c='gray'); ax[0].set_xscale('log', base=2); ax[0].set_xlabel('q'); ax[0].set_ylabel('razao tinta/papiro'); ax[0].set_title('ink_9um, w035')
ax[1].plot([pts[q][2] for q in qs], [pts[q][1] for q in qs], 'o-'); [ax[1].annotate(f'q={q}', (pts[q][2], pts[q][1])) for q in qs]; ax[1].set_xscale('log'); ax[1].set_xlabel('taxa de compressao'); ax[1].set_ylabel("d'")
fig.tight_layout(); fig.savefig(f'{D}/curva_q.png', dpi=110)
