import ast, io, json, os, re, shutil, sys, tempfile, types, unittest, urllib.parse
from pathlib import Path
from unittest.mock import patch
SOURCE=Path(sys.argv[1]) if __name__=="__main__" and len(sys.argv)>1 else Path(__file__).resolve().parents[2]/"studio"/"web_server.py"
if __name__=="__main__": sys.argv=sys.argv[:1]
sys.path.insert(0,str(SOURCE.parent))
tree=ast.parse(SOURCE.read_bytes())
method=next(n for c in tree.body if isinstance(c,ast.ClassDef) for n in c.body if isinstance(n,ast.FunctionDef) and n.name=="do_POST")
ns={"json":json,"urllib":urllib,"re":re,"Path":Path,"shutil":shutil}
exec(compile(ast.Module(body=[method],type_ignores=[]),str(SOURCE),"exec"),ns)
class Request:
    path="/api/update/start"
    def __init__(self,origin="http://127.0.0.1:8765"):
        self.headers={"Host":"127.0.0.1:8765","Origin":origin,"Content-Length":"2","Sec-Fetch-Site":"same-origin"}
        self.rfile=io.BytesIO(b"{}")
    def end_json(self,body,status=200):
        self.result=(status,body)
        return self.result
class UpdateStartTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        updater=self.root/"StoryboardAI"/"Updater"/"Update-StoryboardAI.ps1"
        updater.parent.mkdir(parents=True)
        updater.write_text("param($InstallDir,$StatusFile,[switch]$Yes)\nif(!$Yes){exit 9}\n[IO.File]::WriteAllText($StatusFile,'{\"state\":\"completed\"}')\n",encoding="utf-8")
        ns.update(os=types.SimpleNamespace(name="nt",environ={"LOCALAPPDATA":str(self.root)}),ROOT_DIR=self.root)
    def tearDown(self): self.temp.cleanup()
    def test_local_button_request_starts_updater(self):
        req=Request()
        # Exercise the real request handler and an isolated worker, with no app changes.
        with patch.dict(os.environ,{"LOCALAPPDATA":str(self.root)}):
            ns["do_POST"](req)
            import online_update
            for process in online_update._processes.values(): process.wait(timeout=8)
        self.assertEqual(req.result,(200,{"success":True,"message":"Updater started"}))
    def test_cross_origin_request_is_rejected(self):
        req=Request("https://untrusted.example")
        ns["do_POST"](req)
        self.assertEqual(req.result[0],403)
if __name__=="__main__": unittest.main(verbosity=2)
