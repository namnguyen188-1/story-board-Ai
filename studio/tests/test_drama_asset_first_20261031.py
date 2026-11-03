import json,sys,tempfile,unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_asset_first import (
    build_manifest,validate_assets,bind_scene,gate_episode,AssetGateError,sha,VIEW_SPEC,atomic_write
)
def example_plan():
    sc=[]
    for i in range(1,7):
        sc.append({"scene_number":i,"setting":"Family living room" if i<=3 else "Company office",
         "summary":"Lan hands her black phone to Minh in a dispute about the documents" if i<=3 else "Minh places dossier on the desk",
         "characters_present":["Lan","Minh"],"props_required":["phone","document"] if i<=3 else ["document"],
         "start_state":"Lan holds black phone, Minh waits" if i==1 else "Continue preceding end",
         "end_state":"Lan holds phone; Minh waits" if i==1 else "Minh places document on table",
         "dialogue_beats":[{"speaker":"Lan","text":"Anh đã giấu em điều gì?","action":"Lan holds a black phone"}]})
    return {"title":"Asset-first test episode","cast":{
        "Lan":{"appearance_lock":"Vietnamese woman 34, shoulder-length black hair","attire":"beige coat"},
        "Minh":{"appearance_lock":"Vietnamese man 38, short dark hair","attire":"navy vest"}},
        "scenes":sc}

class AssetFirstTests(unittest.TestCase):
 def test_three_categories_and_six_scene_bindings(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)
   plan=example_plan()
   m=build_manifest(root,plan)
   self.assertEqual(len(m["characters"]),2)
   self.assertEqual(len(m["locations"]),2)
   self.assertGreaterEqual(len(m["props"]),2)
   self.assertEqual(len(m["scenes"]),6)
   self.assertEqual(m["scenes"]["scene_0001"]["location_id"],m["scenes"]["scene_0003"]["location_id"])
   self.assertNotEqual(m["scenes"]["scene_0001"]["location_id"],m["scenes"]["scene_0004"]["location_id"])
   self.assertEqual(set(VIEW_SPEC["characters"]),set(m["characters"]["lan"]["views"]))
   r=validate_assets(root,m)
   self.assertEqual(r["status"],"BLOCKED_PREPRODUCTION")
   self.assertEqual(len(r["blocked"]),len(m["characters"])+len(m["locations"])+len(m["props"]))
   with self.assertRaisesRegex(AssetGateError,"DRAMA_ASSET_UNAPPROVED"):
    bind_scene(root,plan["scenes"][0])

 def test_fake_duplicate_angles_stay_blocked(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);m=build_manifest(root,example_plan())
   asset=m["characters"]["lan"]
   common=Image.effect_noise((400,400),52).convert("RGB")
   for v in asset["views"].values():
    p=Path(v["path"])
    common.save(p)
   self.assertTrue((root/"00_ASSET_PACK"/"characters"/"lan"/"front.png").is_file())
   r=validate_assets(root,m)
   self.assertIn("DUPLICATE_VIEW_IMAGE",[x["reason"] for x in r["blocked"]])

 def test_real_files_still_need_visual_approval_and_sha(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);p=example_plan();m=build_manifest(root,p)
   item=m["characters"]["minh"]; hashes={}
   for i,(view,v) in enumerate(item["views"].items()):
    target=Path(v["path"])
    Image.effect_noise((420,360),40+i*8).convert("RGB").save(target)
    hashes[view]=sha(target)
   r=validate_assets(root,m)
   self.assertIn("AWAITING_VISUAL_APPROVAL",[x["reason"] for x in r["blocked"]])
   atomic_write(root/"00_ASSET_PACK"/item["folder"]/"approval.json",
       {"approved":True,"reviewer":"test_only_fake_images_not_production","spec_sha256":item["spec_sha256"],
        "view_sha256":hashes})
   r2=validate_assets(root,m)
   self.assertNotIn("minh",[x["id"] for x in r2["blocked"]])
   Image.effect_noise((420,360),89).convert("RGB").save(Path(item["views"]["front"]["path"]))
   r3=validate_assets(root,m)
   self.assertIn("APPROVAL_REFERENCE_CHANGED",[x["reason"] for x in r3["blocked"]])

 def test_fail_closed_before_muse_or_missing_scene(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaisesRegex(AssetGateError,"DRAMA_PREPRODUCTION_BLOCKED"):
    gate_episode(Path(t),example_plan())
   with self.assertRaisesRegex(AssetGateError,"DRAMA_SCENE_SEQUENCE_INVALID"):
    p=example_plan();p["scenes"][0]["scene_number"]=3
    build_manifest(Path(t),p)

if __name__=="__main__":unittest.main(verbosity=2)
