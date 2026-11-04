"""Offline regression of real local H.264/AAC cached Muse and procedural drama.

No Muse calls, no ASR/model inference, no production paths.
A synthetic tone proves signal-level transport only, not actual spoken dialogue.
"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

STUDIO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(STUDIO))
sys.path.insert(0,str(STUDIO/"engine"))
from cinematic_engine.drama_video_engine import DramaVideoEngine
from audio_signal_guard import expected_scene_speech
from test_media_signal_repro_qa import make_clip


def scene_setup(td, *, spoken=True, mode="muse", tone=True):
    scene_dir=Path(td)/"episode_001"/"scenes"/"scene_0001"
    scene_dir.mkdir(parents=True)
    Image.effect_noise((320,180),60).convert("RGB").save(scene_dir/"scene_base.png")
    scene={"scene_number":1,"summary":"Conversation in living room",
           "setting":"Living room","characters_present":[],
           "dialogue_beats":[{"speaker":"Lan","text":"Tôi cần biết sự thật."}] if spoken else []}
    if mode=="muse":
        source=scene_dir/"muse_clip.mp4"
        make_clip(source,tone)
    else:
        source=scene_dir/"scene_master_audio.wav"
        clip=scene_dir/"origin.mp4"
        make_clip(clip,tone)
        subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
                        "-i",str(clip),"-vn","-ac","1","-ar","16000",
                        "-c:a","pcm_s16le",str(source)],check=True,capture_output=True,timeout=30)
    return scene_dir,source,scene


class CachedDramaAudioQA(unittest.TestCase):
    def muse(self,tone,spoken=True,final_audio_drop=False):
        with tempfile.TemporaryDirectory(prefix="story_muse_audio_") as td:
            scene_dir,source,scene=scene_setup(td,spoken=spoken,tone=tone)
            original_sha=hashlib.sha256(source.read_bytes()).hexdigest()
            cleaner=types.ModuleType("clean_watermark")
            cleaner.remove_video_watermark=lambda *a,**k:None
            contexts=[patch.dict(sys.modules,{"clean_watermark":cleaner})]
            if final_audio_drop:
                muted=Path(td)/"silent_output.mp4"
                make_clip(muted,False)
                original_run=subprocess.run
                def local_final_drop(cmd,*args,**kwargs):
                    if isinstance(cmd,list) and cmd and str(cmd[0]).lower()=="ffmpeg" and Path(str(cmd[-1])).name=="scene_final.mp4":
                        shutil.copy2(muted,cmd[-1])
                        return subprocess.CompletedProcess(cmd,0,"","")
                    return original_run(cmd,*args,**kwargs)
                contexts.append(patch("subprocess.run",side_effect=local_final_drop))
            try:
                for context in contexts:
                    context.__enter__()
                if (spoken and not tone) or final_audio_drop:
                    with self.assertRaisesRegex(RuntimeError,"NARRATION_AUDIO_SILENT"):
                        DramaVideoEngine().render_scene(scene,scene_dir,
                            image_provider="muse_video",width=320,height=180,
                            no_subtitles=True,bible={"language":"Vietnamese"})
                    self.assertFalse((scene_dir/"render_style.json").exists(),
                                     "Rejected scene must not be marked finished")
                else:
                    result=DramaVideoEngine().render_scene(scene,scene_dir,
                        image_provider="muse_video",width=320,height=180,
                        no_subtitles=True,bible={"language":"Vietnamese"})
                    self.assertTrue(result["used_real_video"])
                    self.assertTrue((scene_dir/"scene_final.mp4").is_file())
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original_sha,
                                 "Native Muse cached original must remain unchanged")
            finally:
                for context in reversed(contexts):
                    context.__exit__(None,None,None)

    def test_cached_audible_muse_uses_native_audio(self):
        self.muse(True)

    def test_cached_silent_muse_with_dialogue_is_rejected(self):
        self.muse(False)

    def test_intentional_silent_muse_without_dialogue_allowed(self):
        self.muse(False,spoken=False)

    def test_muse_output_audio_loss_detected_after_mux(self):
        self.muse(True,final_audio_drop=True)

    def fallback(self,tone,final_audio_drop=False):
        with tempfile.TemporaryDirectory(prefix="story_procedural_audio_") as td:
            scene_dir,source,scene=scene_setup(td,mode="fallback",tone=tone)
            original_sha=hashlib.sha256(source.read_bytes()).hexdigest()
            content=Path(td)/"tone.mp4"
            make_clip(content,True)
            silent=Path(td)/"silence.mp4"
            make_clip(silent,False)
            calls=[]
            def fake_motion(*args,**kwargs):
                calls.append("motion")
                shutil.copy2(content,kwargs["output_video_path"])
            def fake_assemble(*args,**kwargs):
                calls.append("assemble")
                shutil.copy2(silent if final_audio_drop else content,kwargs["output_final_path"])
            with patch.object(DramaVideoEngine,"render_cinematic_motion_clip",side_effect=fake_motion),patch.object(DramaVideoEngine,"assemble_final_scene_video",side_effect=fake_assemble):
                if not tone or final_audio_drop:
                    with self.assertRaisesRegex(RuntimeError,"NARRATION_AUDIO_SILENT"):
                        DramaVideoEngine().render_scene(scene,scene_dir,
                            image_provider="gemini",width=320,height=180,no_subtitles=True)
                    self.assertFalse((scene_dir/"render_style.json").exists())
                    self.assertEqual(calls,["motion","assemble"] if final_audio_drop else [])
                else:
                    result=DramaVideoEngine().render_scene(scene,scene_dir,
                        image_provider="gemini",width=320,height=180,no_subtitles=True)
                    self.assertFalse(result["used_real_video"])
                    self.assertEqual(calls,["motion","assemble"])
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original_sha)

    def test_procedural_silent_master_wav_rejected_before_render(self):
        self.fallback(False)

    def test_procedural_voice_signal_passes_with_local_media(self):
        self.fallback(True)

    def test_procedural_final_audio_loss_rejected(self):
        self.fallback(True,final_audio_drop=True)

    def test_expected_scene_speech_collects_dialogue_not_action(self):
        scene={"narration":"","dialogue_beats":[
            {"speaker":"Lan","text":"Tôi cần biết sự thật.","action":"walk to door"},
            {"speaker":"Minh","text":"Tôi sẽ giải thích.","action":"sigh"}]}
        self.assertEqual(expected_scene_speech(scene),
                         "Tôi cần biết sự thật.\nTôi sẽ giải thích.")
        self.assertEqual(expected_scene_speech({"dialogue_beats":[]}),"")


if __name__=="__main__":
    unittest.main(verbosity=2)
