import json,sys,traceback
from pathlib import Path
from unittest.mock import patch
root=Path(r"D:\STORYBOARD_AI\studio");sys.path.insert(0,str(root))
from studio_mcp import accounts,auto_flow_manager as auto,projects
account=accounts.active_account()
print("ACCOUNT_META",json.dumps({k:account.get(k) for k in ["id","cdp_port","state_dir"]}))
for name,fn in [
 ("baseline",auto.verify_v2_baseline),
 ("registry",lambda:projects.load(account)),
 ("connection",lambda:accounts.connection_check(account["id"])),
 ("pid",lambda:accounts._pid_browser_for_account(account)),
 ("auth",lambda:accounts.flow_auth_status(account)),
 ("tab_count",lambda:[(p["id"],projects.exact_tool_tab_count(account,projects.project_url(p["project_id"],p["tool_id"]))) for p in projects.load(account)["projects"]]),
]:
 try:
  val=fn()
  if name=="registry":val={"active":val["active"],"projects":val["projects"],"genres":val["genres"]}
  print(name,json.dumps(val,ensure_ascii=True))
 except Exception:
  print(name,"EXCEPTION");traceback.print_exc()
with patch.object(auto,"_set",side_effect=lambda *a,**kw:{"args":a[1:],"kwargs":kw}),patch.object(auto,"choose"),patch.object(auto,"register"):
 try:print("ATTEMPT",auto._attempt(account,allow_open=False))
 except Exception:traceback.print_exc()
