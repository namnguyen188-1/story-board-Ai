"""Prove current container-only QC accepts silent AAC, using synthetic local media.
No real APIs or production files are touched.
"""
import json
import math
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from series_studio import qc_clip


def make_clip(path: Path, tone: bool):
    source = ("sine=frequency=440:sample_rate=16000:duration=1.2" if tone
              else "anullsrc=channel_layout=mono:sample_rate=16000")
    cmd = ["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y",
           "-f","lavfi","-i","color=c=black:s=320x180:r=10:d=1.2",
           "-f","lavfi","-i",source,
           "-t","1.2","-c:v","libx264","-pix_fmt","yuv420p",
           "-c:a","aac","-shortest",str(path)]
    result = subprocess.run(cmd,capture_output=True,text=True,timeout=35)
    if result.returncode:
        raise RuntimeError("LOCAL_FFMPEG_FAILED:" + result.stderr[-500:])


def audio_peak_dbfs(path: Path) -> float:
    cmd = ["ffmpeg","-nostdin","-hide_banner","-i",str(path),
           "-vn","-af","volumedetect","-f","null","-"]
    proc = subprocess.run(cmd,capture_output=True,text=True,timeout=35)
    if proc.returncode:
        raise RuntimeError("LOCAL_VOLUMEDETECT_FAILED:" + proc.stderr[-500:])
    match = re.search(r"max_volume:\s*(-?inf|[-+]?\d+(?:\.\d+)?)\s*dB", proc.stderr, re.I)
    if not match:
        raise AssertionError("NO_AUDIO_PEAK_REPORTED")
    return float(match.group(1))


class MediaQCGaps(unittest.TestCase):
    def test_aac_stream_exists_but_can_be_inaudible(self):
        with tempfile.TemporaryDirectory(prefix="story_media_qa_") as directory:
            silent=Path(directory)/"silent.mp4"
            audible=Path(directory)/"tone.mp4"
            make_clip(silent,False)
            make_clip(audible,True)
            silent_qc=qc_clip(silent,need_audio=True,expected_wh=(320,180))
            audible_qc=qc_clip(audible,need_audio=True,expected_wh=(320,180))
            silent_peak=audio_peak_dbfs(silent)
            audible_peak=audio_peak_dbfs(audible)
            self.assertEqual(silent_qc["audio_codec"],"aac")
            self.assertEqual(audible_qc["audio_codec"],"aac")
            self.assertLess(silent_peak,-75.0)
            self.assertGreater(audible_peak,-50.0)
            print("CONTAINER_QC_ACCEPTS_SILENT_AAC",json.dumps({
                "silent_max_dbfs":silent_peak,"audible_max_dbfs":audible_peak,
                "silent_stream_qc":silent_qc["audio_codec"],
                "audible_stream_qc":audible_qc["audio_codec"]}))


if __name__=="__main__":
    unittest.main(verbosity=2)
