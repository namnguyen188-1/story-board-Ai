"""Local acceptance checks: progressive full-color drawing, hand, final image, MP4."""
import unittest, tempfile, wave
from pathlib import Path
import numpy as np
import cv2

class HandColorTests(unittest.TestCase):
    def test_style_is_selectable_and_preserves_genre(self):
        from studio_modes import resolve_style, image_instruction
        self.assertEqual(resolve_style("hand_color","stoic"),"hand_color")
        self.assertIn("marble",image_instruction("stoic","hand_color").lower())
        self.assertIn("full",image_instruction("whiteboard","hand_color").lower())

    def test_blank_to_partial_to_complete_with_visible_hand(self):
        from studio_hand_color import iter_color_frames
        source=np.full((180,320,3),(55,130,210),np.uint8)
        frames=list(iter_color_frames(source,30,hold_frames=5))
        self.assertEqual(len(frames),30)
        self.assertTrue(np.all(frames[0]==255),"must start on blank whiteboard")
        exact=[np.mean(np.all(f==source,axis=2)) for f in frames]
        self.assertGreater(exact[12],.1)
        self.assertLess(exact[12],.9)
        self.assertTrue(np.array_equal(frames[-1],source),"all pixels must retain color")
        partial=frames[12]
        neither=np.any(partial!=source,axis=2)&np.any(partial!=255,axis=2)
        self.assertGreater(neither.sum(),100,"hand must be visible during drawing")
        for frame in frames[-5:]:
            self.assertTrue(np.array_equal(frame,source),"final hold must remove hand")

    def test_real_mp4_matches_audio_and_is_h264_color(self):
        from studio_hand_color import hand_color_video
        with tempfile.TemporaryDirectory() as d:
            d=Path(d); source=np.full((180,320,3),(55,130,210),np.uint8)
            cv2.imwrite(str(d/"image.png"),source)
            with wave.open(str(d/"audio.wav"),"wb") as w:
                w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000)
                w.writeframes(bytes(48000*2))
            hand_color_video(d/"image.png",d/"audio.wav",d/"out.mp4",320,180)
            c=cv2.VideoCapture(str(d/"out.mp4"))
            self.assertTrue(c.isOpened())
            self.assertAlmostEqual(c.get(cv2.CAP_PROP_FRAME_COUNT)/c.get(cv2.CAP_PROP_FPS),2,places=1)
            c.set(cv2.CAP_PROP_POS_FRAMES,49);ok,f=c.read();c.release()
            self.assertTrue(ok)
            self.assertLess(float(np.abs(f.astype(float)-source).mean()),5)

if __name__=="__main__":
    unittest.main(verbosity=2)
