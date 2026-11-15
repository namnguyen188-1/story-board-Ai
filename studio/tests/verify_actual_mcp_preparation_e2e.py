import hashlib,json,sys,time
from pathlib import Path
root=Path(r"D:\STORYBOARD_AI\studio");sys.path.insert(0,str(root))
from studio_mcp.accounts import active_account,account_tool_url
from studio_mcp.auto_flow_manager import ensure_ready
from studio_mcp.production_tab import prepare,abandon_fresh
from studio_mcp.transport import LocalFlowMcpTransport
from studio_mcp.image_backend import validate_image_tool_readiness
account=active_account();url=account_tool_url(account)
readiness=ensure_ready("auto",allow_open=False,account=account)
assert readiness.get("ready"),readiness
target=None
try:
 before=LocalFlowMcpTransport(timeout=75)("flow_storyboard_native_image",{"action":"health","tool_url":url},account=account)
 before=before.get("result",before)
 target=prepare(account,url)
 after=LocalFlowMcpTransport(timeout=75,target_id=target)("flow_storyboard_native_image",{"action":"health","tool_url":url},account=account)
 after=after.get("result",after)
 validate_image_tool_readiness(after,require_queue=True,scoped_production_target=target)
 assert before.get("queue_items")==after.get("queue_items"),"PREPARE_CHANGED_USER_QUEUE"
 release=abandon_fresh(account,url,target)
 assert release.get("kept") and release.get("closed") is False
 archives=sorted((Path(account["state_dir"])/"pinned_tab_drafts").glob("*.json"),key=lambda p:p.stat().st_mtime)
 assert archives,"DRAFT_ARCHIVE_MISSING"
 draft=json.loads(archives[-1].read_text(encoding="utf-8"))
 assert draft[0].get("id")=="shot_1" and draft[0].get("promptText")
 report={"account_id":account["id"],"preflight_ready":True,"session_prepared":True,
 "native_mcp_health":bool(after.get("native")),"queue_unchanged":True,"draft_archived":True,
 "original_tab_kept":True,"new_tabs":0,"generation_submitted":False}
 (root/"runtime/production_tab_e2e_20261108_111755/live_preflight_e2e.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print(json.dumps(report))
finally:
 if target:
  try:abandon_fresh(account,url,target)
  except Exception:pass
