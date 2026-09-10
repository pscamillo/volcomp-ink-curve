#!/usr/bin/env python
"""Decodifica os chunks listados do zarr v3 volcomp local e grava um zarr v2 (sem compressor) com a mesma
geometria do volume original, para o vc_render_tifxyz ler.
~/challenges/vesuvius/venv_volcomp/bin/python transcreve_vc.py
"""
import os, json, shutil, time, numpy as np, zarr, volcomp_zarr  # noqa: F401 (registra o codec)
D = os.path.expanduser('~/challenges/vesuvius/ink-lens/metric/volcomp_w035')
src = zarr.open(f'{D}/vol_vc_v3.zarr/0', mode='r')
dst_path = f'{D}/vol_vc.zarr'
if os.path.exists(dst_path): shutil.rmtree(dst_path)
os.makedirs(dst_path)
shutil.copy(f'{D}/vol_orig.zarr/.zattrs', f'{dst_path}/.zattrs'); shutil.copy(f'{D}/vol_orig.zarr/.zgroup', f'{dst_path}/.zgroup')
dst = zarr.create_array(store=f'{dst_path}/0', shape=src.shape, chunks=(128, 128, 128), dtype='uint8', zarr_format=2,
                        compressors=None, fill_value=0, dimension_names=None) if hasattr(zarr, 'create_array') else \
      zarr.create(shape=src.shape, chunks=(128, 128, 128), dtype='uint8', store=f'{dst_path}/0', zarr_format=2, compressor=None, fill_value=0)
chunks = [tuple(map(int, l.split('/'))) for l in open(f'{D}/chunks_w043.txt') if l.strip()]
t0 = time.time(); n_ok = 0; n_zero = 0; soma = 0.0; nvox = 0
for i, (cz, cy, cx) in enumerate(chunks):
    sl = (slice(cz * 128, (cz + 1) * 128), slice(cy * 128, (cy + 1) * 128), slice(cx * 128, (cx + 1) * 128))
    try:
        blk = src[sl]
    except Exception as e:
        print(f'  chunk {cz}/{cy}/{cx}: ERRO {e}'); continue
    if blk.max() == 0: n_zero += 1; continue
    dst[sl] = blk; n_ok += 1; soma += float(blk.sum()); nvox += blk.size
    if (i + 1) % 500 == 0: print(f'  {i+1}/{len(chunks)}  {time.time()-t0:.0f}s')
print(f'transcritos {n_ok}, vazios {n_zero}, de {len(chunks)} em {time.time()-t0:.0f}s; media dos voxels {soma/max(nvox,1):.1f}')
json.dump(dict(transcritos=n_ok, vazios=n_zero, pedidos=len(chunks)), open(f'{D}/transcricao.json', 'w'))
