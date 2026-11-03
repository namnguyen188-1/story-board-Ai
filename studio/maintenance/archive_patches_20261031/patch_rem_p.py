# -*- coding: utf-8 -*-
with open(r'studio/muse_gateway_worker.py', 'r', encoding='utf-8') as f:
    txt = f.read()
target = 'rem_p = f"workspace/character_anchors/{lp.name}"'
repl = 'rem_p = f"character_anchors/{lp.name}"'
assert target in txt, "target not found!"
txt = txt.replace(target, repl, 1)
with open(r'studio/muse_gateway_worker.py', 'w', encoding='utf-8') as f:
    f.write(txt)
print("Updated rem_p successfully!")
