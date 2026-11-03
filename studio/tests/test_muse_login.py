"""Multi-account login tests; every account/browser/session path is temporary."""
import importlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
class MuseLoginTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  import muse_accounts as a
  self.a=a
  for key,value in {'RUNTIME_DIR':self.root/'runtime','PROFILES_ROOT':self.root/'profiles','REGISTRY_PATH':self.root/'registry.json'}.items():
   p=patch.object(a,key,value);p.start();self.addCleanup(p.stop)
  p=patch.object(a,'_sync_active_to_system_default');self.sync=p.start();self.addCleanup(p.stop)
  a.save_registry({'active_id':'a','dispatch_mode':'round_robin','accounts':[{'id':'a','name':'A','status':'READY','vm_id':'old-a'},{'id':'b','name':'B','status':'READY','vm_id':'old-b'}]})
  for aid in ('a','b'):
   d=a.get_account_cli_dir(aid);d.mkdir(parents=True,exist_ok=True);(d/'cookies.txt').write_text('working-'+aid);(d/'config.json').write_text(json.dumps({'vm_id':'old-'+aid,'custom':'preserve'}))
  self.m=importlib.import_module('muse_login')
 def jar(self):return [{'name':'hatch_sess','value':'test-candidate','domain':'.muse.ai','path':'/','secure':True,'expires':2000000000}]
 def session(self,aid):return tuple((self.a.get_account_cli_dir(aid)/n).read_bytes() for n in ('cookies.txt','config.json'))
 def manager(self):return self.m.LoginManager(self.root/'studio',profile_root=self.root/'browsers')
 def state(self,manager,aid,**extra):
  _,_,p,_=manager._acc_paths(aid);p.parent.mkdir(parents=True,exist_ok=True)
  p.write_text(json.dumps({'pid':43210,'port':9001,'login_id':'current-'+aid,'account_id':aid,**extra}))
 def test_cookie_scope_is_exact_muse_domain(self):
  self.assertEqual(self.m.muse_cookies(self.jar()+[{'name':'x','value':'y','domain':'evilmuse.ai'}]),self.jar())
 def test_logged_out_profile_never_replaces_working_session(self):
  before=self.session('a')
  with patch.object(self.m,'_read_browser_cookies',return_value=[]):r=self.m.export_session(9001,self.root/'productions','a')
  self.assertFalse(r['ready']);self.assertEqual(before,self.session('a'))
 def test_invalid_candidate_preserves_both_session_files(self):
  before=self.session('a')
  with patch.object(self.m,'_read_browser_cookies',return_value=self.jar()),patch.object(self.m,'_verify_candidate',side_effect=RuntimeError('unauthorized')):
   r=self.m.export_session(9001,self.root/'productions','a')
  self.assertFalse(r['ready']);self.assertEqual(before,self.session('a'))
 def test_verified_non_active_account_does_not_replace_active_session(self):
  before=self.session('a')
  with patch.object(self.m,'_read_browser_cookies',return_value=self.jar()),patch.object(self.m,'_verify_candidate',return_value='new-b'):
   r=self.m.export_session(9001,self.root/'productions','b')
  self.assertTrue(r['ready']);self.assertEqual(before,self.session('a'));self.sync.assert_not_called()
  self.assertIn(b'test-candidate',self.session('b')[0]);self.assertNotIn('test-candidate',json.dumps(r))
 def test_pending_account_cannot_switch_remote_session(self):
  prod=self.root/'productions';p=prod/'show/episode_001/scenes/scene_0001/muse_job.json';p.parent.mkdir(parents=True);p.write_text(json.dumps({'state':'accepted','account_vm_id':'old-a'}))
  before=self.session('a')
  with patch.object(self.m,'_read_browser_cookies',return_value=self.jar()),patch.object(self.m,'_verify_candidate',return_value='new-a'):
   with self.assertRaisesRegex(RuntimeError,'MUSE_PENDING_ACCOUNT_LOCKED'):self.m.export_session(9001,prod,'a')
  self.assertEqual(before,self.session('a'))
 def test_pending_other_account_allows_independent_login(self):
  prod=self.root/'productions';p=prod/'scene/muse_job.json';p.parent.mkdir(parents=True);p.write_text(json.dumps({'state':'accepted','account_vm_id':'old-a'}))
  with patch.object(self.m,'_read_browser_cookies',return_value=self.jar()),patch.object(self.m,'_verify_candidate',return_value='new-b'):
   self.assertTrue(self.m.export_session(9001,prod,'b')['ready'])
 def test_missing_chrome_is_reported_without_success(self):
  with patch.object(self.m,'_chrome_path',return_value=None):
   with self.assertRaisesRegex(RuntimeError,'MUSE_CHROME_MISSING'):self.manager().start('a')
 def test_login_start_reuses_one_owned_browser(self):
  manager=self.manager();launches=[]
  with patch.object(self.m,'_chrome_path',return_value=Path(sys.executable)),patch.object(self.m,'_launch_browser',side_effect=lambda *args:launches.append(args) or 43210),patch.object(self.m,'_probe_browser',return_value=True),patch.object(self.m,'_owns_browser',return_value=True),patch.object(self.m,'_show_window',return_value=True):
   first=manager.start('a');second=manager.start('a')
  self.assertEqual(len(launches),1);self.assertEqual(first['login_id'],second['login_id']);self.assertTrue(second['reused'])
 def test_old_redirect_window_opens_email_entry_once(self):
  manager=self.manager();self.state(manager,'a');launches=[]
  with patch.object(self.m,'_chrome_path',return_value=Path(sys.executable)),patch.object(self.m,'_probe_browser',return_value=True),patch.object(self.m,'_owns_browser',return_value=True),patch.object(self.m,'_show_window',return_value=True),patch.object(self.m,'_launch_browser',side_effect=lambda *args:launches.append(args) or 777):
   manager.start('a');manager.start('a')
  self.assertEqual(len(launches),1);self.assertEqual(manager._state('a')['pid'],43210)
 def test_starting_owned_browser_never_launches_duplicate(self):
  manager=self.manager();self.state(manager,'a')
  with patch.object(self.m,'_chrome_path',return_value=Path(sys.executable)),patch.object(self.m,'_probe_browser',return_value=False),patch.object(self.m,'_owns_browser',return_value=True),patch.object(self.m,'_launch_browser',side_effect=AssertionError('duplicate')):
   with self.assertRaisesRegex(RuntimeError,'MUSE_LOGIN_BROWSER_STARTING'):manager.start('a')
 def test_completion_requires_current_login_identifier(self):
  manager=self.manager();self.state(manager,'a');calls=[]
  with patch.object(self.m,'_probe_browser',return_value=True),patch.object(self.m,'_owns_browser',return_value=True):
   with self.assertRaisesRegex(RuntimeError,'MUSE_LOGIN_STALE'):manager.complete('wrong',lambda *a,**k:calls.append(a),'a')
  self.assertEqual(calls,[])
 def test_completion_routes_correct_account_to_worker(self):
  manager=self.manager();self.state(manager,'b');calls=[]
  def worker(action,request,**kw):calls.append(request);return {'ready':True,'ok':True}
  with patch.object(self.m,'_probe_browser',return_value=True),patch.object(self.m,'_owns_browser',return_value=True):
   result=manager.complete('current-b',worker,'b')
  self.assertTrue(result['ready']);self.assertEqual(calls[0]['account_id'],'b');self.assertEqual(manager._state('b')['status'],'READY')
 def test_closed_browser_never_exports_session(self):
  manager=self.manager();calls=[]
  with self.assertRaisesRegex(RuntimeError,'MUSE_LOGIN_BROWSER_CLOSED'):manager.complete('current-a',lambda *a,**k:calls.append(a),'a')
  self.assertEqual(calls,[])
 def test_auth_timeout_stops_owned_worker(self):
  import muse_video_provider as provider,subprocess
  stopped=[]
  class Process:
   pid=99999991;calls=0
   def __enter__(self):return self
   def __exit__(self,*args):return False
   def kill(self):pass
   def poll(self):return 1
   def wait(self,*args,**kwargs):return 1
   def communicate(self,input=None,timeout=None):
    self.calls+=1
    if self.calls==1:raise subprocess.TimeoutExpired('worker',timeout)
    return '',''
  with patch.object(provider,'get_muse_config',return_value={'configured':True,'python_executable':sys.executable}),patch.object(provider.subprocess,'Popen',return_value=Process()),patch.object(provider,'_stop_worker',side_effect=lambda p:stopped.append(p.pid)):
   with self.assertRaisesRegex(RuntimeError,'MUSE_LOGIN_CHECK_TIMEOUT'):provider._worker('auth-export',{},timeout=.01)
  self.assertEqual(stopped,[99999991])
if __name__=='__main__':unittest.main(verbosity=2)
