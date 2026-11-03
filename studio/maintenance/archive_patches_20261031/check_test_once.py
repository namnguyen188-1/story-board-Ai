import os, json, subprocess, sys

python_muse = r'D:\STORYBOARD_AI\studio\runtime\muse\python\python.exe'
aid = 'account_3d53a67c'
sid = 'f748acb4-4cd9-4478-ac72-ebe1c455acb6'
profile_home = rf'D:\STORYBOARD_AI\studio\runtime\muse_profiles\{aid}'

script = f'''
import sys
sys.path.insert(0, r"d:\\STORYBOARD_AI\\studio")
from muse_gateway_worker import GatewayAPI
api = GatewayAPI()
sessions = api.call("sessions.list").get("sessions", [])
sess = next((s for s in sessions if s.get("session_id", s.get("id")) == "{sid}"), {{}})
print("SESSION STATUS:", sess.get("status"))

res = api.call("chat.history", {{"session_id": "{sid}", "limit": 10}})
events = res.get("chat_events", [])
print("TOTAL EVENTS:", len(events))
for e in events:
    if e.get("event_name") == "message.assistant":
        pl = e.get("payload") or {{}}
        print("ASSISTANT:", pl.get("display_text") or e.get("display_text"))
'''
env = os.environ.copy()
env['USERPROFILE'] = profile_home
env['PYTHONIOENCODING'] = 'utf-8'
r = subprocess.run([python_muse, '-c', script], env=env, capture_output=True, text=True, encoding='utf-8')
print(r.stdout)
