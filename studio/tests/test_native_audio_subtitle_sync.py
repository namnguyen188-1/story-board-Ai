import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"engine"))
from cinematic_engine.native_audio_subtitles import validate_vad_anchor,validate_words
from tools.video_subtitle import generate_styled_ass
class NativeSubtitleSafety(unittest.TestCase):
    def test_silent_gap_alignment_rejected(self):
        vad=[{"start":0.034,"end":0.83},{"start":6.722,"end":8.702}]
        with self.assertRaisesRegex(RuntimeError,"WORD_IN_SILENCE"):
            validate_vad_anchor([{"word":"giếng.","start":6.1,"end":6.68}],vad)
        validate_vad_anchor([{"word":"giếng.","start":0.4,"end":0.7}],vad)
    def test_future_words_hidden_for_native_in_both_styles(self):
        words=[{"word":"Xin","start":1.00,"end":1.20},{"word":"chào","start":1.20,"end":1.43},{"word":"nhé","start":1.43,"end":1.70}]
        for style in ("karaoke_viral","yellow_black"):
            with self.subTest(style=style),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)
                (p/"subtitles.json").write_text(json.dumps({"timing_source":"native-audio-v1","subtitles":[{"start":1,"end":1.7,"text":"Xin chào nhé","words":words}]}),encoding="utf-8")
                generate_styled_ass(str(p/"subtitles.json"),str(p/"out.ass"),subtitle_style=style,enable_stickers=False)
                events=[s for s in (p/"out.ass").read_text(encoding="utf-8").splitlines() if s.startswith("Dialogue:")]
                self.assertEqual(len(events),3)
                self.assertIn("Xin",events[0])
                self.assertNotIn("chào",events[0])
                self.assertNotIn("nhé",events[0])
                self.assertIn("chào",events[1])
                self.assertNotIn("nhé",events[1])
                self.assertIn("nhé",events[2])
    def test_non_native_legacy_layout_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/"subtitles.json").write_text(json.dumps({"subtitles":[{"start":1,"end":1.7,"text":"Xin chào nhé","words":[{"word":"Xin","start":1,"end":1.2},{"word":"chào","start":1.2,"end":1.4},{"word":"nhé","start":1.4,"end":1.7}]}]}),encoding="utf-8")
            generate_styled_ass(str(p/"subtitles.json"),str(p/"out.ass"),enable_stickers=False)
            first=next(s for s in (p/"out.ass").read_text(encoding="utf-8").splitlines() if s.startswith("Dialogue:"))
            self.assertIn("nhé",first)
if __name__=="__main__":
    unittest.main(verbosity=2)
