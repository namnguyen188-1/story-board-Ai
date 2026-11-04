"""Static wiring guard: both pre-render WAV and post-render MP4 signals are checked.
Read-only AST inspection, no rendering, provider calls or user-data mutation.
"""
import ast
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "series_studio.py"


class AudioGateWiring(unittest.TestCase):
    def test_guards_exist_inside_render_one_before_success(self):
        tree=ast.parse(SOURCE.read_text(encoding="utf-8-sig"))
        render=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=="render_one")
        checks=[]
        reports=[]
        for node in ast.walk(render):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                if node.func.id=="require_audible_if_spoken":
                    checks.append(node)
                if node.func.id=="write_json":
                    if any(isinstance(arg,ast.Constant) and arg.value=="result.json" for arg in node.args):
                        reports.append(node.lineno)
        self.assertEqual(len(checks),2,"Expected precisely 2 signal checks")
        self.assertEqual(sorted(n.args[0].id for n in checks),["audio","final"])
        self.assertTrue(all(len(n.args)>1 for n in checks))
        success_lines=[n.lineno for n in ast.walk(render)
                       if isinstance(n,ast.Constant) and n.value=="SCENE_PASS"]
        self.assertTrue(success_lines)
        self.assertTrue(all(n.lineno<min(success_lines) for n in checks),
                        "Audio checks must run before scene PASS")
        gate_ifs=[node for node in ast.walk(render)
                  if isinstance(node,ast.If)
                  and "scene.get('narration')" in ast.unparse(node.test)]
        self.assertGreaterEqual(len(gate_ifs),2,"Expected explicit narration guards")
        print("RENDER_AUDIO_GATE_WIRING_PASS",[(n.args[0].id,n.lineno) for n in checks])


if __name__=="__main__":
    unittest.main(verbosity=2)
