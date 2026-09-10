#!/usr/bin/env python
"""Curva q: roda encode->decode do volcomp (encoder do autor) nos chunks originais para q dados.
~/challenges/vesuvius/venv_volcomp/bin/python codifica_q.py 2 4 16
Também: controle q=8 local vs shards publicados.
"""
import sys, os, json, shutil, time, numpy as np, zarr
import volcomp_zarr
from volcomp_zarr import _lib

D = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp')
qs = [float(q) for q in sys.argv[1:]] or [2.0, 4.0, 16.0]
src = zarr.open(f'{D}/vol_orig.zarr/0', mode='r')
chunks = [tuple(map(int, l.split('/'))) for l in open(f'{D}/chunks_w043.txt') if l.strip()]
res = {}

def rt(blk, q):
    enc = _lib.encode(np.ascontiguousarray(blk, dtype=np.uint8).tobytes(), q)
    dec = np.frombuffer(bytes(_lib.decode(enc)), dtype=np.uint8).reshape(128, 128, 128)
    return dec, len(enc)

# controle: q=8 local vs shard publicado, num chunk do meio da lista
cz, cy, cx = chunks[len(chunks) // 2]
sl = (slice(cz * 128, (cz + 1) * 128), slice(cy * 128, (cy + 1) * 128), slice(cx * 128, (cx + 1) * 128))
pub = zarr.open(f'{D}/vol_vc_v3.zarr/0', mode='r')[sl]
loc, _ = rt(src[sl], 8.0)
mae_ctrl = float(np.abs(loc.astype(np.int16) - pub.astype(np.int16)).mean())
print(f'controle q=8 local vs publicado, chunk {cz}/{cy}/{cx}: MAE {mae_ctrl:.3f}  (exigido ≤ 0,5)')
res['controle_q8_mae'] = mae_ctrl

for q in qs:
    out = f'{D}/vol_q{int(q)}.zarr'
    if os.path.exists(out): shutil.rmtree(out)
    os.makedirs(out); shutil.copy(f'{D}/vol_orig.zarr/.zattrs', f'{out}/.zattrs'); shutil.copy(f'{D}/vol_orig.zarr/.zgroup', f'{out}/.zgroup')
    dst = zarr.create_array(store=f'{out}/0', shape=src.shape, chunks=(128, 128, 128), dtype='uint8', zarr_format=2, compressors=None, fill_value=0, dimension_names=None)
    t0 = time.time(); nbytes = 0; nvox = 0; err = []
    for i, (cz, cy, cx) in enumerate(chunks):
        sl = (slice(cz * 128, (cz + 1) * 128), slice(cy * 128, (cy + 1) * 128), slice(cx * 128, (cx + 1) * 128))
        blk = src[sl]
        if blk.max() == 0: continue
        dec, n = rt(blk, q); dst[sl] = dec; nbytes += n; nvox += blk.size
        if i % 500 == 0: err.append(float(np.abs(dec.astype(np.int16) - blk.astype(np.int16)).mean()))
    taxa = nvox / max(nbytes, 1)
    res[f'q{int(q)}'] = dict(bytes=nbytes, voxels=nvox, taxa=taxa, mae_amostra=float(np.mean(err)), segundos=time.time() - t0)
    print(f'q={q:g}: taxa {taxa:.1f}x  MAE amostral {np.mean(err):.2f}  {time.time()-t0:.0f}s')
json.dump(res, open(f'{D}/codifica_q.json', 'w'), indent=1)
