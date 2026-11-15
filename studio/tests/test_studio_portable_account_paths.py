"""Offline regression for Storyboard-owned portable account state paths."""
import json,sys,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from studio_mcp import accounts,transport,auto_flow_manager as auto
import flow_account_manager as manager
class AccountPathTests(unittest.TestCase):
 def setUp(self):
  self.row={"id":"account_ee27d30a0c7f","name":"Offline fixture","profile_directory":"Default",
   "user_data_dir":str(Path.home()/".storyboard-studio-flow-accounts/account_b61dbd4f7ab7"),
   "state_dir":str(ROOT/"flow_accounts/account_ee27d30a0c7f_state"),"cdp_port":9461}
 def test_existing_studio_state_is_accepted(self):transport._isolated(self.row)
 def test_portable_profile_from_studio_account_creator_is_accepted(self):
  row={**self.row,"user_data_dir":str(ROOT/"flow_accounts"/self.row["id"])}
  transport._isolated(row)
 def test_foreign_v2_state_stays_rejected(self):
  for state in [r"D:\FLOW_MCP_SERVER\runtime",str(ROOT/"flow_accounts/account_aaaaaaaaaaaa_state"),str(ROOT/"flow_accounts")]:
   with self.subTest(state=state),self.assertRaises(accounts.AccountError):
    transport._isolated({**self.row,"state_dir":state})
 def test_legacy_v2_port_stays_rejected(self):
  with self.assertRaises(accounts.AccountError):transport._isolated({**self.row,"cdp_port":9333})
 def test_python_transport_forwards_account_identity_to_node_guard(self):
  url="https://flow.google.com/project/11111111-1111-4111-8111-111111111111/tool/22222222-2222-4222-8222-222222222222"
  with patch.object(accounts,"connection_check",return_value={"connected":True}),patch.object(accounts,"account_tool_url",return_value=url),patch("studio_mcp.projects.is_registered",return_value=True),patch.object(transport.subprocess,"run",return_value=SimpleNamespace(returncode=0,stdout='{"ok":true,"result":{"offline":true}}')) as call:
   result=transport.LocalFlowMcpTransport()("flow_storyboard_native_image",{"action":"health","tool_url":url},account=self.row)
  self.assertTrue(result["offline"])
  env=call.call_args.kwargs["env"]
  self.assertEqual(env["STORYBOARD_MCP_ACCOUNT_ID"],"account_ee27d30a0c7f")
  self.assertEqual(env["STORYBOARD_MCP_APPROVED"],"0")
 def test_preflight_keeps_specific_account_error_code(self):
  with patch.object(auto,"_attempt",side_effect=accounts.AccountError("STORYBOARD_PRIVATE_PROFILE_MUST_NOT_USE_V2")),patch.object(auto,"_set",side_effect=lambda a,c,**kw:{"code":c,**kw}),patch.dict(auto._CURRENT,{"ready":False},clear=True):
   result=auto.ensure_ready(allow_open=False,account=self.row)
  self.assertEqual(result["code"],"AUTO_FLOW_SAFETY_BLOCKED")
  self.assertEqual(result["detail"],"STORYBOARD_PRIVATE_PROFILE_MUST_NOT_USE_V2")
 def test_ui_cannot_report_ready_for_rejected_account_paths(self):
  bad={**self.row,"state_dir":r"D:\FLOW_MCP_SERVER\runtime"}
  with patch.object(accounts,"active_account",return_value=bad),patch.object(accounts,"load_accounts",return_value={"accounts":[bad]}),patch.object(accounts,"connection_check",return_value={"connected":True}),patch.object(accounts,"flow_auth_status",return_value={"authenticated":True}),patch.object(accounts,"account_tool_url",return_value="url"):
   result=manager.get_ui_status()
  self.assertFalse(result["ready"]);self.assertIn("STORYBOARD_PRIVATE_PROFILE",result["status_text"])
if __name__=="__main__":unittest.main(verbosity=2)
