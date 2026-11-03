import os, json, subprocess, sys, time

python_muse = r'D:\STORYBOARD_AI\studio\runtime\muse\python\python.exe'
aid = 'account_3d53a67c'
sid = 'f748acb4-4cd9-4478-ac72-ebe1c455acb6'
profile_home = rf'D:\STORYBOARD_AI\studio\runtime\muse_profiles\{aid}'

for i in range(12):
    script = f'''
import sys
sys.path.insert(0, r"d:\\STORYBOARD_AI\\studio")
from muse_gateway_worker import GatewayAPI
api = GatewayAPI()
res = api.call("chat.history", {{"session_id": "{sid}", "limit": 10}})
events = res.get("chat_events", [])
for e in events:
    if e.get("event_name") == "message.assistant":
        pl = e.get("payload") or {{}}
        print("ASSISTANT:", pl.get("display_text") or e.get("display_text"))
'''
    env = os.environ.copy()
    env['USERPROFILE'] = profile_home
    env['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run([python_muse, '-c', script], env=env, capture_output=True, text=True, encoding='utf-8')
    if "ASSISTANT:" in r.stdout:
        print(r.stdout)
        break
    print(f"Check {i+1}/12: still waiting...")
    time.sleep(10)
