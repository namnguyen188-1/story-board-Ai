# -*- coding: utf-8 -*-
import sys
import json
import base64
from pathlib import Path
from muse_cli.cli import connect

cfg = json.load(open(r'studio/runtime/muse_profiles/account_09cffaca/.config/muse-cli/config.json'))
cfg['cookies_file'] = r'studio/runtime/muse_profiles/account_09cffaca/.config/muse-cli/cookies.txt'
gw = connect(cfg)

anchor_p = Path(r'studio/productions/kh-m-ph/episode_004/00_ASSET_PACK/characters/b_h_a_turnaround.jpg')
anc_bytes = anchor_p.read_bytes()
total_len = len(anc_bytes)
print(f"Total bytes to upload: {total_len}")

chunk_size = 24000  # 24KB binary -> ~32KB base64, comfortably below Noise limit (65535)
target_path = f"character_anchors/{anchor_p.name}"

for i in range(0, total_len, chunk_size):
    chunk = anc_bytes[i:i + chunk_size]
    is_first = (i == 0)
    b64_chunk = base64.b64encode(chunk).decode('ascii')
    res = gw.call_json('fs.write', body={
        'path': target_path,
        'data_base64': b64_chunk,
        'overwrite': is_first,
        'append': not is_first,
        'create_parent': is_first
    })
    print(f"Chunk {i // chunk_size}: {len(chunk)} bytes -> bytes_written: {res.get('bytes_written')}")

stat = gw.call_json('fs.stat', body={'path': target_path})
print("Final stat on Muse VM:", stat)
assert stat.get("size") == total_len, f"Size mismatch: {stat.get('size')} != {total_len}"
print("🏆 CHUNKED UPLOAD VERIFIED 100% SUCCESSFUL!")
