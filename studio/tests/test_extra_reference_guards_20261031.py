import sys, tempfile, unittest, json, wave, types
from pathlib import Path
from unittest.mock import patch
from PIL import Image
ROOT=Path(r"D:\STORYBOARD_AI\studio")
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"engine"))
from cinematic_engine.drama_video_engine import DramaVideoEngine
import muse_video_provider
import muse_accounts

class AdditionalReferenceGuards(unittest.TestCase):
  def test_two_people_image_generator_receives_both_images_and_cache_invalidates(self):
    with tempfile.TemporaryDirectory() as temp:
      root=Path(temp)/"episode_001"
      asset=root/"00_ASSET_PACK"/"characters";asset.mkdir(parents=True)
      sc=root/"scenes"/"scene_0001";sc.mkdir(parents=True)
      lan=asset/"lan_turnaround.jpg";minh=asset/"minh_turnaround.jpg"
      Image.effect_noise((260,260),60).convert("RGB").save(lan)
      Image.effect_noise((260,260),80).convert("RGB").save(minh)
      produced=Path(temp)/"generated.png";Image.effect_noise((260,260),30).convert("RGB").save(produced)
      calls=[]
      def fake_gen(**kw):
        calls.append(kw)
        return str(produced)
      fake=types.ModuleType("comfyui_image_provider");fake.make_image=fake_gen
      scene={"characters_present":["Lan","Minh"],"visual_setup":"Lan and Minh in studio"}
      with patch.dict(sys.modules,{"comfyui_image_provider":fake}):
        e=DramaVideoEngine()
        e.ensure_scene_base_visual(scene,sc,reference_image_path=lan)
        self.assertEqual(calls[0]["character_reference_paths"],[str(minh)])
        proof=json.loads((sc/"scene_base_reference.json").read_text(encoding="utf-8"))
        self.assertEqual(len(proof["secondary_reference_sha256"]),1)
        e.ensure_scene_base_visual(scene,sc,reference_image_path=lan)
        self.assertEqual(len(calls),1)
        Image.effect_noise((260,260),90).convert("RGB").save(minh)
        e.ensure_scene_base_visual(scene,sc,reference_image_path=lan)
        self.assertEqual(len(calls),2)
  def test_quota_portrait_fallback_is_not_publishable(self):
    with tempfile.TemporaryDirectory() as temp:
      ep=Path(temp)/"episode_001";sc=ep/"scenes"/"scene_0001"
      char=ep/"00_ASSET_PACK"/"characters";char.mkdir(parents=True);sc.mkdir(parents=True)
      portrait=char/"lan_turnaround.jpg"
      Image.effect_noise((260,260),55).convert("RGB").save(portrait)
      wav=sc/"dialogue_master.wav"
      with wave.open(str(wav),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(24000);w.writeframes(b"\0"*48000*2)
      fake=types.ModuleType("comfyui_image_provider")
      fake.make_image=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("COMFY_REMOTE_FAILURE"))
      with patch.dict(sys.modules,{"comfyui_image_provider":fake}):
        with self.assertRaisesRegex(RuntimeError,"SCENE_COMPOSITION_MISSING"):
          DramaVideoEngine().render_scene({"characters_present":["Lan"],"dialogue_beats":[],"visual_setup":"Lan talks in room"},
             sc,reference_image_path=portrait,image_provider="comfyui",no_subtitles=True)
  def test_muse_no_video_does_not_failover_to_other_accounts(self):
    with tempfile.TemporaryDirectory() as tmp:
      account={"id":"testing_account","name":"E2E_OFFLINE"}
      with patch.object(muse_accounts,"get_account_for_scene",return_value=account) as chooser, \
           patch.object(muse_video_provider,"_worker",side_effect=RuntimeError("MUSE_REMOTE_FAILED: Job kết thúc nhưng chưa có video gắn đúng mã cảnh.")) as worker:
        with self.assertRaisesRegex(RuntimeError,"MUSE_SCENE_REVIEW_REQUIRED"):
          muse_video_provider.make_scene_media(
            {"scene_number":1,"raw_9_fields":"9-field test scene","scene_dir":tmp},
            {"world":"test"},Path(tmp)/"scene_base.png",width=1280,height=720,duration=10)
        self.assertEqual(worker.call_count,1)
        self.assertEqual(chooser.call_count,1)
if __name__=="__main__": unittest.main(verbosity=2)
