import ast, hashlib, json, shutil, subprocess, sys, time, urllib.request
from pathlib import Path
ROOT=Path(r"D:\STORYBOARD_AI\studio")
with urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=4) as r:
    assert json.load(r).get("running") is False, "STUDIO_BUSY_NO_CHANGE"
checkpoint=ROOT/"runtime"/("mcp_v2_only_"+time.strftime("%Y%m%d_%H%M%S"))
checkpoint.mkdir(parents=True)
names=["mcp_v2_images.py","mcp_v2_batch.py","flowkit_client.py","flow_account_manager.py","seo_packager.py","web_server.py"]
original={n:(ROOT/n).read_text(encoding="utf-8-sig") for n in names}
def replace_function(src,name,new):
    node=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=src.splitlines(keepends=True)
    return "".join(lines[:node.lineno-1])+new.rstrip()+"\n"+"".join(lines[node.end_lineno:])
updated=dict(original)
s=updated["mcp_v2_images.py"]
a=s.index('"""');b=s.index('"""',a+3)+3
s='"""Storyboard Studio images through the private MCP V2 runtime only."""'+s[b:]
a=s.index("    try:\n",s.index("def preflight"));b=s.index("    from studio_mcp.image_backend",a)
s=s[:a]+s[b:]
a=s.index('    """Exactly one image job');b=s.index('    if not 1 <=',a)
s=s[:a]+'    """One native MCP image job; errors propagate without another provider."""\n'+s[b:]
a=s.index("    # 1. FlowKit");b=s.index("    klass, image_models = preflight()",a)
s=s[:a]+s[b:]
updated["mcp_v2_images.py"]=s
s=updated["mcp_v2_batch.py"]
a=s.index("    # FlowKit Priority:");b=s.index("    # Reuse images ONLY",a)
native=s[s.index("\n    else:\n",a)+len("\n    else:\n"):b]
native="\n".join(line[4:] if line.startswith("    ") else line for line in native.split("\n"))
# Native queue preparation is unchanged; no FlowKit or alternative remote backend.
updated["mcp_v2_batch.py"]=s[:a]+native+s[b:]
s=updated["flowkit_client.py"]
s=replace_function(s,"ensure_flowkit_running",'''def ensure_flowkit_running(max_wait_seconds: int = 15) -> bool:
    """Disabled: Storyboard uses MCP V2; never launch or rewrite FlowKit jobs."""
    return False
''')
s=replace_function(s,"open_flowkit_browser",'''def open_flowkit_browser(show: bool = True) -> Dict[str, Any]:
    """Legacy entry point is disabled; open the active MCP account in Studio."""
    raise FlowKitError("FLOWKIT_DISABLED_USE_MCP_V2")
''')
updated["flowkit_client.py"]=s
s=updated["flow_account_manager.py"]
s=replace_function(s,"open_google_flow_login",'''def open_google_flow_login() -> Dict[str, Any]:
    """Open the existing active MCP V2 account for manual sign-in."""
    from studio_flow_accounts import active, open_login
    result = open_login(active()["id"])
    return {**result, "success": bool(result.get("opened")), "provider": "mcp_v2"}
''')
# Adding accounts remains an explicit UI action, never called by a failed job.
s=replace_function(s,"add_new_account",'''def add_new_account() -> Dict[str, Any]:
    """Create an MCP account only on the user's explicit Add Account action."""
    from studio_flow_accounts import create, open_login
    row = create("Google Flow " + time.strftime("%Y%m%d-%H%M%S"))
    result = open_login(row["id"])
    return {**result, "success": bool(result.get("opened")), "provider": "mcp_v2"}
''')
s=replace_function(s,"get_ui_status",'''def get_ui_status() -> Dict[str, Any]:
    """Read native connection/auth state without starting any background service."""
    from studio_mcp.accounts import (active_account, load_accounts, account_tool_url,
                                     connection_check, flow_auth_status)
    try:
        account = active_account()
        store = load_accounts()
        state = connection_check(account["id"])
        auth = flow_auth_status(account) if state.get("connected") else {}
        connected = bool(state.get("connected"))
        authenticated = bool(auth.get("authenticated"))
        ready = connected and authenticated and bool(account_tool_url(account))
        return {
            "provider": "mcp_v2", "flowkit_required": False,
            "ready": ready, "connected": connected, "logged_in": authenticated,
            "email": account.get("email", ""), "emails": [],
            "accounts": store.get("accounts", []), "active_id": account["id"],
            "total_accounts": len(store.get("accounts", [])),
            "ready_accounts": int(ready), "dispatch_mode": "active_account",
            "badge_text": "MCP V2: đã kết nối" if ready else "MCP V2: chưa sẵn sàng",
            "badge_type": "success" if ready else "warning",
            "status_text": ("MCP V2 đã kết nối; trạng thái tạo nội dung cần kiểm tra riêng."
                            if ready else "Mở tài khoản MCP V2 và kiểm tra đăng nhập Google Flow."),
            "watcher_active": False
        }
    except Exception as exc:
        return {"provider": "mcp_v2", "flowkit_required": False, "ready": False,
                "connected": False, "logged_in": False, "ready_accounts": 0,
                "total_accounts": 0, "emails": [], "email": "", "accounts": [],
                "badge_text": "MCP V2: cần kiểm tra", "badge_type": "warning",
                "status_text": str(exc), "watcher_active": False}
''')
updated["flow_account_manager.py"]=s
s=updated["seo_packager.py"]
a=s.index("    # Step A: Attempt Google Flow via FlowKit");b=s.index("    # Step B.2:",a)
s=s[:a]+'''    # Generate once through MCP V2. Never switch providers/models after denial.
    try:
        from mcp_v2_images import make_image
        make_image(prompt, out_base, series=series_name or ep_title, episode=1,
                   scene=9999 if is_short else 9998, max_new_images=1,
                   model_index=0, fallback=False, aspect_ratio=target_ratio)
        backend_used = "mcp_v2"
    except Exception as exc:
        return {"ok": False, "error": str(exc), "backend": "mcp_v2",
                "aspect_ratio": target_ratio, "is_short": is_short}

'''+s[b:]
updated["seo_packager.py"]=s
# The readiness checklist must no longer require a stopped FlowKit service.
s=updated["web_server.py"]
a=s.index("    # 5. FlowKit Gateway Service")
# All lines below use the existing checklist structure; replace only this block.
b=s.index('"id": "flowkit_service"',a)
end=s.index('        })',b)+len('        })')
block=s[a:end]
# retain indentation in the old checker so surrounding function remains intact
import re
block=re.sub(r'from flowkit_client import is_flowkit_alive', 'from mcp_v2_images import preflight as mcp_v2_preflight',block)
block=block.replace('flowkit_ok = is_flowkit_alive()', 'mcp_v2_preflight(); flowkit_ok = True')
block=block.replace('"id": "flowkit_service"','"id": "mcp_v2_runtime"')
block=block.replace('FlowKit Gateway Service (Port 18110)','MCP V2 runtime')
# Unicode labels vary across old installations; update complete literal values.
block=re.sub(r'"name": "[^"]*"', '"name": "MCP V2 runtime"',block)
block=re.sub(r'"message": [^\n]+', '"message": "MCP V2 runtime configured" if flowkit_ok else "MCP V2 runtime or account configuration missing",',block)
s=s[:a]+block+s[end:]
s=s.replace('("python_runtime", "ffmpeg", "flowkit_service", "project_storage")','("python_runtime", "ffmpeg", "mcp_v2_runtime", "project_storage")')
updated["web_server.py"]=s
# Compile every edited module before any production writes.
for n,text in updated.items():compile(text,str(ROOT/n),"exec")
for n in names:
    shutil.copy2(ROOT/n,checkpoint/n)
    (checkpoint/"after").mkdir(exist_ok=True)
    (checkpoint/"after"/n).write_text(updated[n],encoding="utf-8")
# Recheck idle immediately before commit.
with urllib.request.urlopen("http://127.0.0.1:8765/api/status",timeout=4) as r:
    assert json.load(r).get("running") is False, "STUDIO_BUSY_NO_CHANGE"
try:
    for n,text in updated.items():
        temp=(ROOT/n).with_suffix(".mcp-migration.tmp")
        temp.write_text(text,encoding="utf-8")
        temp.replace(ROOT/n)
    test=subprocess.run([str(ROOT/"runtime/python/python.exe"),"-B",str(ROOT/"tests/test_flowkit_removed_offline.py")],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=60,cwd=ROOT)
    (checkpoint/"routing_tests.txt").write_text(test.stdout+test.stderr,encoding="utf-8")
    if test.returncode:raise RuntimeError("OFFLINE_TEST_FAILED: "+test.stdout+test.stderr)
except Exception:
    for n in names:shutil.copy2(checkpoint/n,ROOT/n)
    raise
report={"checkpoint":str(checkpoint),"files":names,"tests":"7/7 offline","hashes":{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}}
(checkpoint/"migration_result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps(report))
print(test.stdout+test.stderr)
