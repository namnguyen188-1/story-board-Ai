import os, json, subprocess, sys

python_muse = r'D:\STORYBOARD_AI\studio\runtime\muse\python\python.exe'
aid = 'account_2a9520eb'
sid = '77482459-ee12-4448-81ca-14a45ea7accb'
profile_home = rf'D:\STORYBOARD_AI\studio\runtime\muse_profiles\{aid}'

script = f'''
import sys
sys.path.insert(0, r"d:\\STORYBOARD_AI\\studio")
from muse_gateway_worker import GatewayAPI
api = GatewayAPI()
res = api.call("chat.history", {{"session_id": "{sid}", "limit": 5}})
events = res.get("chat_events", [])
for e in events:
    if e.get("event_name") == "message.user":
        pl = e.get("payload") or {{}}
        print("EVENT 0 FULL TEXT:")
        print(pl.get("display_text") or e.get("display_text"))
'''
env = os.environ.copy()
env['USERPROFILE'] = profile_home
env['PYTHONIOENCODING'] = 'utf-8'
r = subprocess.run([python_muse, '-c', script], env=env, capture_output=True, text=True, encoding='utf-8')
print(r.stdout)
if r.stderr:
    print('ERR:', r.stderr)
