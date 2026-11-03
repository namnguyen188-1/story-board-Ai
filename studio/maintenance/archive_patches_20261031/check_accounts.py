# -*- coding: utf-8 -*-
import sys
import urllib.request
import json

sys.stdout.reconfigure(encoding="utf-8")

with urllib.request.urlopen("http://127.0.0.1:8765/api/muse/status", timeout=5) as res:
    data = json.loads(res.read().decode("utf-8"))
    accounts = data.get("accounts", [])
    print(f"Tổng số tài khoản: {len(accounts)}")
    for a in accounts:
        proxy_info = a.get("proxy") or "IP gốc (Direct)"
        ready_icon = "🟢" if a.get("ready") else "🟡"
        print(f"  {ready_icon} [{a.get('id')}] {a.get('name')}: {proxy_info}")
