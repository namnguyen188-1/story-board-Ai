import importlib.util, json, os, sys, tempfile, time, unittest
from pathlib import Path
MODULE=Path(__file__).resolve().parents[2]/"studio"/"online_update.py"
class OnlineUpdateTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(),"Online updater must run silently and report its persistent status")
        spec=importlib.util.spec_from_file_location("online_update_tested",MODULE)
        self.mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(self.mod)
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.saved=os.environ.get("LOCALAPPDATA")
        os.environ["LOCALAPPDATA"]=str(self.root/"local")
        self.script=self.root/"worker.ps1"
        self.script.write_text('param($InstallDir,$StatusFile,[switch]$Yes)\nif(!$Yes){exit 9}\nStart-Sleep -Milliseconds 1500\n[IO.File]::WriteAllText($StatusFile,(@{state="completed";version="9.9.9";percent=100;pid=$PID}|ConvertTo-Json),(New-Object Text.UTF8Encoding($false)))\n',encoding="utf-8")
    def tearDown(self):
        if hasattr(self,"mod"):
            for proc in self.mod._processes.values():
                if proc.poll() is None: proc.terminate(); proc.wait(timeout=5)
        if hasattr(self,"saved"):
            if self.saved is None: os.environ.pop("LOCALAPPDATA",None)
            else: os.environ["LOCALAPPDATA"]=self.saved
        if hasattr(self,"tmp"): self.tmp.cleanup()
    def test_click_runs_without_dialog_and_reports_completion(self):
        result=self.mod.start_update(self.root,self.script)
        self.assertTrue(result["success"])
        deadline=time.monotonic()+12
        while time.monotonic()<deadline:
            status=self.mod.get_status(self.root)
            if status["state"] in ("completed","failed"): break
            time.sleep(.1)
        self.assertEqual(status["state"],"completed",status)
        self.assertEqual(status["version"],"9.9.9")
        spec=importlib.util.spec_from_file_location("online_update_restarted",MODULE)
        restarted=importlib.util.module_from_spec(spec); spec.loader.exec_module(restarted)
        self.assertEqual(restarted.get_status(self.root)["state"],"completed")
    def test_repeated_click_uses_existing_update(self):
        self.mod.start_update(self.root,self.script)
        first=self.mod.get_status(self.root)
        result=self.mod.start_update(self.root,self.script)
        second=self.mod.get_status(self.root)
        self.assertTrue(result["success"])
        self.assertEqual(first["pid"],second["pid"])
        self.assertEqual(len(self.mod._processes),1)
if __name__=="__main__": unittest.main(verbosity=2)
