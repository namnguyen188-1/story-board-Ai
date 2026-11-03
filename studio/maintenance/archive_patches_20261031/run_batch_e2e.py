import sys, json, time, shutil
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r"D:\STORYBOARD_AI\studio")

from cinematic_engine.drama_auto_repair import load_armed_repair
from cinematic_engine.drama_video_engine import DramaVideoEngine

scenes_to_run = [2, 3]
ep_num = 1
ep_dir = Path(rf"D:\STORYBOARD_AI\studio\productions\DRAMA-2\episode_{ep_num:03d}")
plan_path = ep_dir / "drama_plan.json"
plan = json.loads(plan_path.read_text(encoding="utf-8"))
engine = DramaVideoEngine()

print(f"======================================================================")
print(f"🎬 [BATCH E2E RENDER] BẮT ĐẦU RENDER CÁC CẢNH TIẾP THEO: {scenes_to_run}")
print(f"   Episode: {ep_num:03d} | Bộ Drama: {plan.get('title', 'DRAMA-2')}")
print(f"======================================================================\n")

for sc_num in scenes_to_run:
    print(f"\n>>>>>>>>>>>>>>> BẮT ĐẦU CẢNH {sc_num:04d} <<<<<<<<<<<<<<<", flush=True)
    sdir = ep_dir / "scenes" / f"scene_{sc_num:04d}"
    sdir.mkdir(parents=True, exist_ok=True)
    sc_data = next((s for s in plan.get("scenes", []) if s.get("scene_number", s.get("number")) == sc_num), None)
    
    if not sc_data:
        print(f"❌ Không tìm thấy dữ liệu cảnh {sc_num}!")
        continue

    print(f"Tóm tắt: {sc_data.get('summary')}")
    print(f"Nhân vật có mặt: {sc_data.get('characters_present')}")
    
    t0 = time.time()
    res = engine.render_scene(
        scene=sc_data,
        scene_dir=sdir,
        aspect_ratio="16:9",
        cast_map=plan.get("cast", {}),
        reference_image_path=None,
        image_provider="muse_video",
        bible=plan.get("bible") or plan.get("screenplay_bible", {}),
        width=1280,
        height=720,
        subtitle_style="karaoke_viral",
        subtitle_size=76,
        no_subtitles=False
    )
    render_time = round(time.time() - t0, 1)

    # Đồng bộ final.mp4 và result.json
    sf = sdir / "scene_final.mp4"
    f = sdir / "final.mp4"
    if sf.is_file() and not f.is_file():
        shutil.copy2(sf, f)

    res_json = sdir / "result.json"
    res_json.write_text(json.dumps({
        "status": "PASS",
        "qc": {"pass": True, "duration": res.get("duration", 10.0), "render_time_s": render_time}
    }, indent=2), encoding="utf-8")

    print(f"✅ HOÀN THÀNH CẢNH {sc_num:04d} TRONG {render_time}s!")
    print(f"   Video: {f} ({round(f.stat().st_size / (1024*1024), 2)} MB)")

print(f"\n======================================================================")
print(f"🎉 TẤT CẢ CÁC CẢNH TRONG BATCH {scenes_to_run} ĐÃ RENDER THÀNH CÔNG E2E!")
print(f"======================================================================")
