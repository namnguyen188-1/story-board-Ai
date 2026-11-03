import os, json, subprocess, sys
from pathlib import Path

python_muse = r'D:\STORYBOARD_AI\studio\runtime\muse\python\python.exe'

with open(r'd:\STORYBOARD_AI\studio\runtime\muse_accounts.json', 'r', encoding='utf-8') as f:
    reg = json.load(f)

ep_dir = Path(r'd:\STORYBOARD_AI\studio\productions\DRAMA-2\episode_002\scenes')

for sc in [13, 41, 44, 56, 114, 163]:
    sdir = ep_dir / f'scene_{sc:04d}'
    jp = sdir / 'muse_job.json'
    muse_clip = sdir / 'muse_clip.mp4'
    scene_final = sdir / 'scene_final.mp4'
    
    if scene_final.is_file() and scene_final.stat().st_size > 100000:
        print(f"Scene {sc:04d}: COMPLETE (final={scene_final.stat().st_size // 1024}KB)")
        continue
    if muse_clip.is_file() and muse_clip.stat().st_size > 1000:
        print(f"Scene {sc:04d}: VIDEO DOWNLOADED, burning subs (clip={muse_clip.stat().st_size // 1024}KB)")
        continue
    if not jp.is_file():
        print(f"Scene {sc:04d}: PENDING (no receipt)")
        continue
        
    d = json.loads(jp.read_text(encoding='utf-8'))
    vm = d.get('account_vm_id')
    sid = d.get('session_id')
    state = d.get('state')
    
    acc = next((a for a in reg['accounts'] if a.get('vm_id') == vm), None)
    acc_name = acc['name'][:16] if acc else 'unknown'
    aid = acc['id'] if acc else 'default'
    profile_home = rf"D:\STORYBOARD_AI\studio\runtime\muse_profiles\{aid}"
    
    script = f'''
import sys
sys.path.insert(0, r"d:\\STORYBOARD_AI\\studio")
from muse_gateway_worker import GatewayAPI
api = GatewayAPI()
sessions = api.call("sessions.list").get("sessions", [])
sess = next((s for s in sessions if s.get("session_id", s.get("id")) == "{sid}"), {{}})
status = sess.get("status")

res = api.call("chat.history", {{"session_id": "{sid}", "limit": 10}})
events = res.get("chat_events", [])
last_msg = ""
for e in events:
    if e.get("event_name") == "message.assistant":
        pl = e.get("payload") or {{}}
        last_msg = (pl.get("display_text") or e.get("display_text") or "").replace("\\n", " ")[:100]
print(f"sess={{status}} | ev={{len(events)}} | {{last_msg}}")
'''
    env = os.environ.copy()
    env['USERPROFILE'] = profile_home
    env['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run([python_muse, '-c', script], env=env, capture_output=True, text=True, encoding='utf-8')
    out = r.stdout.strip()
    print(f"Scene {sc:04d} ({acc_name}): state={state} | {out}")
