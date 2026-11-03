import sys,json
from pathlib import Path
sys.path.insert(0,"D:/STORYBOARD_AI/studio")
from cinematic_engine.drama_aspect_repair import normalize_3_2,video_info
from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.drama_schema import CharacterProfile
ep=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
folder=ep/"scenes"/"scene_0004_retake_no_phantom_key"
clip=folder/"muse_clip.mp4"
if not clip.is_file():raise RuntimeError("RETAKE_MEDIA_NOT_DOWNLOADED")
print("RETAKE_ORIGINAL_MEDIA",video_info(clip),flush=True)
qc=normalize_3_2(folder)
print("RETAKE_ASPECT_CORRECTED",qc["adapted_dimensions"],flush=True)
sc=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))["scenes"][3]
cast={
 "Lan":CharacterProfile(name="Lan",gender="female",appearance_lock="Vietnamese woman beige coat"),
 "Minh":CharacterProfile(name="Minh",gender="male",appearance_lock="Vietnamese man grey hair blue vest")}
try:
 r=DramaVideoEngine(fps=24).render_scene(sc,folder,aspect_ratio="16:9",
  cast_map=cast,reference_image_path=ep/"00_ASSET_PACK"/"characters"/"minh"/"front.png",
  image_provider="muse_video",bible={"language":"Vietnamese"},width=1280,height=720,
  subtitle_style="karaoke_viral",subtitle_size=58,no_subtitles=False)
 print("SCENE4_RETAKE_RECOVERED",r["final_video_path"],flush=True)
except Exception as e:print("RETAKE_MEDIA_RECOVERY_FAILED",type(e).__name__,str(e),flush=True)
