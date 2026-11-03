"""Exactly one targeted retake for scene4 prop phantom on Minh waist.
Isolated folder, original Muse receipt/video preserved; single account with known
16:9 output, NOT auto failover. Staging only, review retake before selection.
"""
from pathlib import Path
import sys,json,shutil,copy,traceback
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_asset_first import bind_scene
from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.drama_schema import CharacterProfile
ep=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
sc=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))["scenes"][3]
bind_scene(ep,sc,verify_scene_image=True)
original=ep/"scenes"/"scene_0004"
retake=ep/"scenes"/"scene_0004_retake_no_phantom_key"
retake.mkdir(parents=True,exist_ok=True)
for name in ("scene_master.png","scene_master.json"):
 if not (retake/name).exists():shutil.copy2(original/name,retake/name)
scene=copy.deepcopy(sc)
scene["account_id"]="account_2a9520eb"
scene["visual_setup"]=(sc["visual_setup"]+
 " EXACT PHYSICAL PROP CONTINUITY: Start of 10 second shot, the brass key is COMPLETELY INSIDE MINH'S FRONT TROUSER POCKET. "
 "At seconds 3-4, Minh reaches into his right trouser pocket and withdraws ONE small brass key, shows it to Lan, then passes it into Lan's RIGHT HAND by seconds 7-8. "
 "There must NEVER be a visible key, dangling key chain, clipped key, golden ornament, or belt hook attached to his shirt, belt or apron. "
 "Absolutely ONLY ONE brass key exists in the scene. After the handoff Minh carries no duplicate key. "
 "Keep exact office/bookcase/window/door geometry, coats and faces identical to the approved opening Muse scene master. "
 "Keep cinematic native 16:9 widescreen framing, natural motion, Vietnamese spoken line 'Chìa khóa ở đây.'")
try:
 c={
  "Lan":CharacterProfile(name="Lan",gender="female",appearance_lock="Vietnamese woman, beige coat, burgundy sweater"),
  "Minh":CharacterProfile(name="Minh",gender="male",appearance_lock="Vietnamese man, short grey hair, blue vest, brown apron")
 }
 result=DramaVideoEngine(fps=24).render_scene(scene,retake,aspect_ratio="16:9",cast_map=c,
  reference_image_path=ep/"00_ASSET_PACK"/"characters"/"minh"/"front.png",
  image_provider="muse_video",bible={"language":"Vietnamese"},width=1280,height=720,
  subtitle_style="karaoke_viral",subtitle_size=58,no_subtitles=False)
 print("SCENE4_RETAKE_GENERATED",result["final_video_path"],flush=True)
except Exception as exc:
 print("SCENE4_RETAKE_FAILED_NO_RETRY",str(exc),flush=True)
