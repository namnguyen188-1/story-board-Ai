import json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from studio_mcp import production_tab as p
class Contract(unittest.TestCase):
 def test_preparation_forwards_account_id_for_portable_draft_archive(self):
  row={"id":"account_ee27d30a0c7f","name":"fixture","profile_directory":"Default","user_data_dir":str(Path.home()/".storyboard-studio-flow-accounts/account_b61dbd4f7ab7"),"state_dir":str(ROOT/"flow_accounts/account_ee27d30a0c7f_state"),"cdp_port":9461}
  with patch.object(p,"_pid_browser_for_account",return_value=1),patch.object(p.subprocess,"run",return_value=SimpleNamespace(returncode=0,stdout='{"ok":true,"target_id":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"}')) as call:
   p._call(row,"https://flow.google.com/project/11111111-1111-4111-8111-111111111111/tool/22222222-2222-4222-8222-222222222222","create")
  request=json.loads(call.call_args.kwargs["input"])
  self.assertEqual(request.get("account_id"),"account_ee27d30a0c7f")
if __name__=="__main__":unittest.main(verbosity=2)
