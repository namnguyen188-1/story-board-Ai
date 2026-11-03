# -*- coding: utf-8 -*-
with open(r'studio/muse_gateway_worker.py', 'r', encoding='utf-8') as f:
    txt = f.read()

target = '''            for loc_anc in anchor_list:
                lp = Path(loc_anc)
                if lp.is_file():
                    try:
                        anc_bytes = lp.read_bytes()
                        rem_p = f"character_anchors/{lp.name}"
                        api.call("fs.write", {
                            "path": rem_p,
                            "data_base64": base64.b64encode(anc_bytes).decode("ascii"),
                            "overwrite": True,
                            "append": False,
                            "create_parent": True
                        })
                        remote_anchors.append(rem_p)
                        print(f"[MUSE_ANCHOR_SYNC] Uploaded {lp.name} ({len(anc_bytes)} bytes) to {rem_p} on Muse VM.", flush=True)
                    except Exception as anc_up_err:
                        print(f"[MUSE_ANCHOR_WARN] Could not upload anchor {lp.name}: {anc_up_err}", flush=True)'''

replacement = '''            for loc_anc in anchor_list:
                lp = Path(loc_anc)
                if lp.is_file():
                    try:
                        anc_bytes = lp.read_bytes()
                        rem_p = f"character_anchors/{lp.name}"
                        chunk_size = 24000  # 24KB binary stays well under Noise 65535-byte frame limit
                        for i in range(0, len(anc_bytes), chunk_size):
                            chunk = anc_bytes[i:i + chunk_size]
                            is_first = (i == 0)
                            api.call("fs.write", {
                                "path": rem_p,
                                "data_base64": base64.b64encode(chunk).decode("ascii"),
                                "overwrite": is_first,
                                "append": not is_first,
                                "create_parent": is_first
                            })
                        remote_anchors.append(rem_p)
                        print(f"[MUSE_ANCHOR_SYNC] Uploaded {lp.name} ({len(anc_bytes)} bytes) to {rem_p} on Muse VM.", flush=True)
                    except Exception as anc_up_err:
                        print(f"[MUSE_ANCHOR_WARN] Could not upload anchor {lp.name}: {anc_up_err}", flush=True)'''

assert target in txt, "target not found in muse_gateway_worker.py"
txt = txt.replace(target, replacement, 1)
with open(r'studio/muse_gateway_worker.py', 'w', encoding='utf-8') as f:
    f.write(txt)
print("Updated muse_gateway_worker.py with chunked Noise upload!")
