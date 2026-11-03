"""Run the real worker finalizer with no child process or browser operations."""
import ast, io, os, sys, time, types, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio_mcp import accounts, production_tab
ROOT=Path(__file__).resolve().parents[1]
class FailedWorkerTests(unittest.TestCase):
    def run_worker(self, code, completed=False):
        source=ast.parse((ROOT/"web_server.py").read_text(encoding="utf-8"))
        worker=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=="worker_thread")
        logs=[]; closes=[]
        ns=dict(os=os,time=time,Path=Path,STUDIO_DIR=ROOT,PRODUCTIONS_DIR=ROOT/"scratch"/"nonexistent-fixture",
                job_status={},job_process=None,log_event=logs.append,
                subprocess=types.SimpleNamespace(Popen=lambda *a,**k:types.SimpleNamespace(stdout=[],wait=lambda:code)))
        exec(compile(ast.Module(body=[worker],type_ignores=[]),str(ROOT/"web_server.py"),"exec"),ns)
        def cdp_close(url,**kwargs):
            closes.append(str(url)); return io.BytesIO(b"true")
        error=production_tab.ProductionTabError("FLOW_JOB_SESSION_NOT_COMPLETED_PRESERVE_TAB")
        with patch("studio_flow_accounts.minimize_active_account_browser"), \
             patch.object(accounts,"find_account",return_value=accounts.active_account()), \
             patch.object(production_tab,"close_completed",side_effect=None if completed else error,return_value={"closed":True}) as close, \
             patch.object(production_tab,"abandon_fresh",side_effect=error) as abandon, \
             patch("urllib.request.urlopen",side_effect=cdp_close):
            ns["worker_thread"](["python","series_studio.py"],"test",1,"F"*32,"https://flow.google.com/","default")
        return closes,logs,close.call_count
    def test_failed_or_uncertain_job_never_forces_cdp_close(self):
        closes,logs,_=self.run_worker(1)
        self.assertEqual(closes,[], "A rejected safe close must preserve the tab")
    def test_completed_job_uses_verified_release(self):
        closes,logs,count=self.run_worker(0,completed=True)
        self.assertEqual(count,1)
        self.assertEqual(closes,[])
if __name__=="__main__":unittest.main()
