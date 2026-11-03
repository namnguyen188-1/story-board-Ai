import importlib.util, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
def load(name):
    spec=importlib.util.spec_from_file_location("portable_"+name,ROOT/"studio"/(name+".py"))
    obj=importlib.util.module_from_spec(spec); spec.loader.exec_module(obj); return obj
class MusePortableTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.home=Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def test_bundled_muse_python_is_used_on_a_new_machine(self):
        mod=load("muse_video_provider"); mod.HOME=self.home; mod.CONFIG_FILE=self.home/"provider.json"
        python=self.home/"runtime"/"muse"/"python"/"python.exe"
        python.parent.mkdir(parents=True); python.write_bytes(b"fixture")
        with patch.dict(os.environ,{"LOCALAPPDATA":str(self.home/"empty")}):
            cfg=mod.get_muse_config()
        self.assertTrue(cfg["configured"],cfg)
        self.assertEqual(Path(cfg["python_executable"]),python)
    def test_bundled_login_helper_does_not_require_global_npm_install(self):
        mod=load("muse_login")
        mod.__file__=str(self.home/"muse_login.py")
        helper=self.home/"runtime"/"muse"/"agent-browser.exe"
        helper.parent.mkdir(parents=True); helper.write_bytes(b"fixture")
        self.assertEqual(Path(mod._agent_browser_path()),helper)
if __name__=="__main__": unittest.main(verbosity=2)
