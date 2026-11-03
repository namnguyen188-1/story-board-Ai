import sys, json, traceback
from pathlib import Path

sys.path.insert(0, r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_asset_first import bind_scene, validate_assets, atomic_write
from cinematic_engine.drama_video_engine import DramaVideoEngine
from cinematic_engine.drama_schema import CharacterProfile
from cinematic_engine.drama_orchestrator import export_legacy_compatibility_bridge

ep = Path(r"D:\STORYBOARD_AI\studio\productions\THI-N-S-HUY-N-PH-TR-N-QU\episode_001")
plan = json.loads((ep / "drama_plan.json").read_text(encoding="utf-8"))

cast = {}
for name, c in plan["cast"].items():
    if name == "Narrator":
        continue
    cast[name] = CharacterProfile(
        name=name,
        gender=c.get("gender", "female"),
        voice_id=c.get("voice_id", "Aoede"),
        voice_label=c.get("voice_label", ""),
        appearance_lock=c.get("appearance_lock") or c.get("appearance", ""),
        attire=c.get("attire", ""),
    )

n = 6
sc = plan["scenes"][n - 1]
folder = ep / "scenes" / f"scene_{n:04d}"
receipt = folder / "manual_live_i2v_production_20261031.json"

print(f"=== TESTING I2V RENDER FOR SCENE {n} ===", flush=True)
try:
    bind_scene(ep, sc, verify_scene_image=True)
    engine = DramaVideoEngine(fps=24)
    result = engine.render_scene(
        sc,
        folder,
        aspect_ratio="16:9",
        cast_map=cast,
        reference_image_path=ep / "00_ASSET_PACK" / "characters" / "luc_thanh_y" / "front.png",
        image_provider="muse_video",
        bible={"language": "Vietnamese", "cast": plan["cast"]},
        width=1280,
        height=720,
        subtitle_style="karaoke_viral",
        subtitle_size=58,
        no_subtitles=False,
    )
    output = Path(result["final_video_path"])
    print(f"SUCCESS: Scene {n} rendered to {output} (size: {output.stat().st_size} bytes)", flush=True)

    # Update bridge so UI sees scenes 1..6
    scene_videos = []
    for i in range(1, 67):
        vf = ep / "scenes" / f"scene_{i:04d}" / "scene_final.mp4"
        if vf.is_file() and vf.stat().st_size > 100000:
            scene_videos.append(vf)
    export_legacy_compatibility_bridge(ep, plan, scene_videos=scene_videos, image_provider="muse_video", subtitle_style="karaoke_viral", subtitle_size=58)
    print(f"BRIDGE_UPDATED: {len(scene_videos)} completed scenes", flush=True)

except Exception as e:
    print(f"ERROR on Scene {n}: {e}", flush=True)
    traceback.print_exc()
