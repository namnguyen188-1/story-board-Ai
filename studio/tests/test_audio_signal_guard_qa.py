"""Regression tests for the non-integrated audio-signal preflight candidate."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audio_signal_guard import inspect_audio_signal, require_audible_if_spoken
from test_media_signal_repro_qa import make_clip


class AudioSignalGuardQA(unittest.TestCase):
    def test_silent_aac_rejected_if_narration_expected(self):
        with tempfile.TemporaryDirectory(prefix="story_voice_guard_") as td:
            path=Path(td)/"silent.mp4"
            make_clip(path,False)
            with self.assertRaisesRegex(RuntimeError,"NARRATION_AUDIO_SILENT"):
                require_audible_if_spoken(path,"Narrator should speak here.")

    def test_audible_signal_passes_without_claiming_speech_identity(self):
        with tempfile.TemporaryDirectory(prefix="story_voice_guard_") as td:
            path=Path(td)/"tone.mp4"
            make_clip(path,True)
            report=require_audible_if_spoken(path,"Expected spoken line")
            self.assertEqual(report["status"],"AUDIBLE_SIGNAL_PRESENT")
            self.assertFalse(report["speech_verified"])
            self.assertGreater(report["max_dbfs"],-50)

    def test_intentional_silence_allowed(self):
        with tempfile.TemporaryDirectory(prefix="story_voice_guard_") as td:
            missing=Path(td)/"no_audio_file.wav"
            report=require_audible_if_spoken(missing,"")
            self.assertEqual(report["status"],"SKIPPED_INTENTIONAL_SILENCE")

    def test_missing_speech_audio_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="story_voice_guard_") as td:
            with self.assertRaisesRegex(RuntimeError,"NARRATION_AUDIO_MISSING"):
                require_audible_if_spoken(Path(td)/"missing.wav","There should be a voice.")

    def test_cache_wav_with_silence_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="story_voice_guard_") as td:
            td=Path(td)
            silent=td/"silent.mp4"
            make_clip(silent,False)
            audio=td/"audio.wav"
            subprocess.run(["ffmpeg","-nostdin","-loglevel","error","-y","-i",str(silent),
                            "-vn","-ac","1","-ar","16000","-c:a","pcm_s16le",str(audio)],
                            check=True,capture_output=True,timeout=30)
            with self.assertRaisesRegex(RuntimeError,"NARRATION_AUDIO_SILENT"):
                require_audible_if_spoken(audio,"A retained narration line.")
            self.assertTrue(audio.is_file(),"preflight must not delete or overwrite the original cache")

    def test_threshold_can_fail_closed_for_quieter_signal(self):
        with tempfile.TemporaryDirectory(prefix="story_voice_guard_") as td:
            path=Path(td)/"tone.mp4"
            make_clip(path,True)
            with self.assertRaisesRegex(RuntimeError,"NARRATION_AUDIO_SILENT"):
                require_audible_if_spoken(path,"Expected line",min_peak_dbfs=-5,min_mean_dbfs=-5)


if __name__=="__main__":
    unittest.main(verbosity=2)
