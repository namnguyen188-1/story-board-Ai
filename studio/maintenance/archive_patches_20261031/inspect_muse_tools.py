# -*- coding: utf-8 -*-
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
from muse_cli.cli import load_config, connect

gw = connect(load_config())
sess = gw.call_json("sessions.list")
sessions = sess.get("sessions", [])
print(f"Total sessions: {len(sessions)}")
if sessions:
    last_s = sessions[0]
    sid = last_s.get("session_id") or last_s.get("id")
    print(f"Inspecting session {sid} (title: {last_s.get('title')})...")
    hist = gw.call_json("chat.history", body={"session_id": sid, "limit": 25})
    for ev in hist.get("chat_events", []):
        ename = ev.get("event_name")
        pl = ev.get("payload") or {}
        if ename == "call.tool":
            print(f"TOOL CALL: {pl.get('name')} | args: {json.dumps(pl.get('arguments', {}), ensure_ascii=False)}")
        elif ename == "message.assistant":
            print(f"ASSISTANT: {pl.get('display_text')}")
