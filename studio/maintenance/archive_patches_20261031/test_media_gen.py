import os, json, subprocess, sys

python_muse = r'D:\STORYBOARD_AI\studio\runtime\muse\python\python.exe'
aid = 'account_3d53a67c'
profile_home = rf'D:\STORYBOARD_AI\studio\runtime\muse_profiles\{aid}'

script = '''
import sys
sys.path.insert(0, r"d:\\STORYBOARD_AI\\studio")
from muse_gateway_worker import GatewayAPI
api = GatewayAPI()
# start session
res = api.call("session.start", {"method": "/api/session/start", "params": {"origin": "fresh", "lifecycle": "persistent", "title": "Test Generation"}})
sid = res.get("session_id") or res.get("id")
print("Started test session:", sid)

# send prompt
import subprocess
env = {"MUSE_NO_UPDATE_CHECK": "1", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
p = subprocess.run([sys.executable, "-m", "muse_cli", "send", 
    "Please test media.generate_video by creating a 5-second 16:9 test video of an ocean wave.", 
    "--thread", sid, "--wait", "1"], capture_output=True, text=True, encoding="utf-8")
print("Send result:", p.stdout)
'''
env = os.environ.copy()
env['USERPROFILE'] = profile_home
env['PYTHONIOENCODING'] = 'utf-8'
r = subprocess.run([python_muse, '-c', script], env=env, capture_output=True, text=True, encoding='utf-8')
print(r.stdout)
if r.stderr:
    print('ERR:', r.stderr)
