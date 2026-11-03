from pathlib import Path
import ast,re,unittest
ROOT=Path(__file__).resolve().parents[2]
class MuseErrorVisibilityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  tree=ast.parse((ROOT/"studio/web_server.py").read_text(encoding="utf-8-sig"))
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="format_user_log")
  ns={"re":re};exec(compile(ast.Module(body=[fn],type_ignores=[]),"<log formatter>","exec"),ns)
  cls.format=staticmethod(ns["format_user_log"])
 def test_actual_muse_failure_is_visible(self):
  message=self.format("[DRAMA_VIDEO_ERROR] Muse: MUSE_REMOTE_FAILED: Image generation failed; no video created.")
  self.assertIsNotNone(message)
  self.assertIn("MUSE_REMOTE_FAILED",message)
 def test_muse_error_does_not_expose_sensitive_values(self):
  message=self.format("RuntimeError: MUSE_CONNECTION_INTERRUPTED: cookie=private_session https://example.test/a?token=private_token")
  self.assertIsNotNone(message)
  self.assertNotIn("private_session",message);self.assertNotIn("private_token",message)
if __name__=="__main__":unittest.main()
