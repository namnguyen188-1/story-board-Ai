import importlib.util,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("secure_release",ROOT/"make_secure_release.py")
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
class ReleasePackageTests(unittest.TestCase):
 def test_clean_package_keeps_nested_application_modules(self):
  with tempfile.TemporaryDirectory() as temp:
   base=Path(temp); source=base/"source"; target=base/"release"
   (source/"web").mkdir(parents=True)
   (source/"web/index.html").write_text("UI",encoding="utf-8")
   (source/"main.py").write_text("pass",encoding="utf-8")
   for package in ("cinematic_engine",):
    (source/package).mkdir()
    (source/package/"__init__.py").write_text("",encoding="utf-8")
    (source/package/"pipeline.py").write_text("READY=True",encoding="utf-8")
   with patch.multiple(builder,STUDIO_DIR=source,TARGET_DIR=target):
    builder.copy_core_studio()
   for package in ("cinematic_engine",):
    self.assertTrue((target/"studio"/package/"pipeline.py").is_file(),package+" missing from clean release")
if __name__=="__main__":unittest.main()
