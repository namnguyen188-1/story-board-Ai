"""Guarded offline regression: IDEA / SCRIPT / LINK input modes.
No real network, external process, provider, media or production writes.
Operates only in a disposable temp folder in the current worktree test process.
"""
import builtins
import contextlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
STUDIO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STUDIO))
import series_studio as studio
from studio_input_modes import analyze_reference, parse_locked_screenplay, youtube_url


@contextlib.contextmanager
def isolated_runtime(temp_root):
    """Forbid network/spawning and any filesystem mutation outside temp_root."""
    allowed = Path(temp_root).resolve()
    def verify(path):
        if isinstance(path, int):
            return
        p = Path(path).resolve()
        if p != allowed and allowed not in p.parents:
            raise AssertionError("QA_WRITE_OUTSIDE_SANDBOX:" + str(p))
    def deny(*args, **kwargs):
        raise AssertionError("QA_EXTERNAL_ACTION_BLOCKED")
    original_open = builtins.open
    original_path_open = Path.open
    original_write_text = Path.write_text
    original_write_bytes = Path.write_bytes
    original_mkdir = Path.mkdir
    original_os_mkdir = os.mkdir
    original_replace = os.replace
    original_rename = os.rename
    original_unlink = os.unlink
    original_remove = os.remove
    original_copy2 = shutil.copy2
    original_copy = shutil.copy
    original_copytree = shutil.copytree
    original_rmtree = shutil.rmtree
    def open_guard(file, mode="r", *args, **kwargs):
        if any(c in mode for c in "wax+"):
            verify(file)
        return original_open(file, mode, *args, **kwargs)
    def path_open_guard(self, mode="r", *args, **kwargs):
        if any(c in mode for c in "wax+"):
            verify(self)
        return original_path_open(self, mode, *args, **kwargs)
    def write_text_guard(self, *args, **kwargs):
        verify(self)
        return original_write_text(self, *args, **kwargs)
    def write_bytes_guard(self, *args, **kwargs):
        verify(self)
        return original_write_bytes(self, *args, **kwargs)
    def path_mkdir_guard(self, *args, **kwargs):
        verify(self)
        return original_mkdir(self, *args, **kwargs)
    def os_mkdir_guard(path, *args, **kwargs):
        verify(path)
        return original_os_mkdir(path, *args, **kwargs)
    def op_guard(original):
        def wrapped(path, *args, **kwargs):
            verify(path)
            return original(path, *args, **kwargs)
        return wrapped
    def move_guard(original):
        def wrapped(src, dst, *args, **kwargs):
            verify(dst)
            return original(src, dst, *args, **kwargs)
        return wrapped
    with contextlib.ExitStack() as stack:
        for target, name, replacement in [
            (socket.socket, "connect", deny),
            (socket.socket, "connect_ex", deny),
            (urllib.request, "urlopen", deny),
            (subprocess, "Popen", deny),
            (os, "system", deny),
            (builtins, "open", open_guard),
            (Path, "open", path_open_guard),
            (Path, "write_text", write_text_guard),
            (Path, "write_bytes", write_bytes_guard),
            (Path, "mkdir", path_mkdir_guard),
            (os, "mkdir", os_mkdir_guard),
            (os, "replace", move_guard(original_replace)),
            (os, "rename", move_guard(original_rename)),
            (os, "remove", op_guard(original_remove)),
            (os, "unlink", op_guard(original_unlink)),
            (shutil, "copy2", move_guard(original_copy2)),
            (shutil, "copy", move_guard(original_copy)),
            (shutil, "copytree", move_guard(original_copytree)),
            (shutil, "rmtree", op_guard(original_rmtree)),
        ]:
            stack.enter_context(patch.object(target, name, replacement))
        yield


class InputModeGuardedQA(unittest.TestCase):
    def test_guard_rejects_network_process_and_main_write(self):
        with tempfile.TemporaryDirectory(prefix="story_three_modes_") as tmp:
            with isolated_runtime(tmp):
                with self.assertRaisesRegex(AssertionError, "QA_EXTERNAL_ACTION_BLOCKED"):
                    with socket.socket() as s:
                        s.connect(("127.0.0.1", 9))
                with self.assertRaisesRegex(AssertionError, "QA_EXTERNAL_ACTION_BLOCKED"):
                    subprocess.Popen(["echo", "must-not-execute"])
                with self.assertRaisesRegex(AssertionError, "QA_WRITE_OUTSIDE_SANDBOX"):
                    Path(r"D:\STORYBOARD_AI\studio\qa_should_never_exist.txt").write_text("deny")
                self.assertFalse(Path(r"D:\STORYBOARD_AI\studio\qa_should_never_exist.txt").exists())

    def test_script_plan_preserves_locked_narration_without_ai(self):
        raw = 'CẢNH 1:\nGóc máy ngang trong nhà.\n"Đừng mở cửa."\nCẢNH 2:\nKhông có lời thoại.'
        with tempfile.TemporaryDirectory(prefix="story_three_modes_") as tmp:
            args = studio.parser().parse_args([
                "run", "--input-mode", "script", "--mode", "live", "--series", "OfflineScriptQA",
                "--episode", "1", "--minutes", "1", "--scene-seconds", "8",
                "--genre", "family_drama", "--visual-style", "color_cinematic", "--region", "VN",
                "--language", "Vietnamese", "--voice-name", "Kore", "--prompt", raw
            ])
            folder = Path(tmp)
            with isolated_runtime(tmp), patch.object(studio, "own_api_key", side_effect=AssertionError("LLM_FOR_SCRIPT")), patch.object(studio, "ResilientClient", side_effect=AssertionError("LLM_FOR_SCRIPT")):
                plan = studio.produce_plan(args, folder, folder / "episode_001", raw)
            self.assertEqual(plan["config"]["prompt"], raw)
            self.assertEqual([s["narration"] for s in plan["scenes"]], ["Đừng mở cửa.", ""])
            self.assertEqual(len(plan["scenes"]), 2)

    def test_idea_plan_uses_correct_installed_skill_via_fake_model(self):
        body = {
            "scenes": [{"scene_number":1,"summary":"A traveler reaches an old harbor",
                        "narration":"The harbor comes alive as morning light reaches the stone pier.",
                        "description":"Quiet coastal village, one traveler approaches old harbor in dawn light",
                        "visual_setup":"Wide cinematic establishing shot","text_overlay":""}]
        }
        class FakeModel:
            requests = []
            def generate_content(self, **kwargs):
                self.requests.append(str(kwargs.get("contents", "")))
                return SimpleNamespace(text=json.dumps(body))
        fake = FakeModel()
        args = studio.parser().parse_args([
            "run", "--input-mode", "idea", "--mode", "live", "--series", "OfflineIdeaQA",
            "--episode", "1", "--minutes", "0.1", "--scene-seconds", "8",
            "--size", "1280x720", "--aspect-ratio", "16:9",
            "--genre", "documentary", "--visual-style", "auto", "--region", "US",
            "--language", "English", "--voice-name", "Kore", "--prompt", "The old harbor"
        ])
        bible = {"world":"an old harbor","visual_style":"documentary","characters":[],"continuity_rules":"steady location"}
        with tempfile.TemporaryDirectory(prefix="story_three_modes_") as tmp:
            folder = Path(tmp)
            with isolated_runtime(tmp), patch.object(studio,"own_api_key",return_value="FAKE"), patch.object(studio,"get_api_keys",return_value=[]), patch.object(studio,"make_bible",return_value=bible), patch.object(studio,"ResilientClient",return_value=SimpleNamespace(models=fake)):
                plan = studio.produce_plan(args,folder,folder/"episode_001",args.prompt)
            self.assertEqual(len(plan["scenes"]), 1)
            self.assertTrue(any("INSTALLED SKILL: write-narrative-scene-prompts" in q for q in fake.requests))
            self.assertEqual(plan["skill_pipeline"]["name"],"write-narrative-scene-prompts")

    def test_link_analysis_is_mocked_without_network(self):
        class FakeModels:
            def generate_content(self, **kwargs):
                return SimpleNamespace(text=json.dumps({
                    "genre":"documentary","primary_language":"Vietnamese",
                    "hook_technique":"mystery","new_original_story_seed":"An original fictional adventure",
                    "visual_style":"cinematic"
                }))
        url = "https://youtu.be/9hE5-98ZeCg"
        with tempfile.TemporaryDirectory(prefix="story_three_modes_") as tmp:
            with isolated_runtime(tmp):
                result = analyze_reference(SimpleNamespace(models=FakeModels()),"fake-model",url)
                self.assertEqual(result["source_url"],youtube_url(url))
                self.assertEqual(result["genre"],"documentary")

    def test_link_invalid_host_rejected_without_network(self):
        for candidate in ["https://youtube.com.example.test/watch?v=9hE5-98ZeCg",
                          "http://youtu.be/9hE5-98ZeCg", "https://127.0.0.1/"]:
            with self.assertRaises(ValueError):
                youtube_url(candidate)

    def test_link_invalid_model_response_rejected_without_retry(self):
        class BadModels:
            def generate_content(self,**kwargs):
                return SimpleNamespace(text='{"genre":"documentary"}')
        with tempfile.TemporaryDirectory(prefix="story_three_modes_") as tmp:
            with isolated_runtime(tmp), self.assertRaisesRegex(RuntimeError,"missing required details"):
                analyze_reference(SimpleNamespace(models=BadModels()),"fake-model","https://youtu.be/9hE5-98ZeCg")


if __name__ == "__main__":
    unittest.main(verbosity=2)
