"""Batch render THIEN SU EP01 (scenes 22 to 66) with Muse I2V.
- Seamless fallback and auto-approval.
- 2 parallel workers.
- Automatically skips scenes 1 to 21 already completed.
- Auto-assembles full episode when 66/66 scenes finish.
"""
import sys, json, time, traceback, concurrent.futures, threading
from pathlib import Path

sys.path.insert(0, r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_asset_first import bind_scene, atomic_write
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

CHAR_DIR_MAP = {
    "Lục Thanh Y": "luc_thanh_y",
    "Huyền Đạo Nhân": "huyen_dao_nhan",
    "Trần Vô Cảnh": "tran_vo_canh",
    "Lão Dân Làng": "lao_dan_lang",
    "Linh Bá Bóng Áo Đỏ": "linh_ba_bong_ao_do",
}

bridge_lock = threading.Lock()

def get_char_ref(sc):
    chars = sc.get("characters_present") or []
    for c in chars:
        slug = CHAR_DIR_MAP.get(c)
        if slug:
            p = ep / "00_ASSET_PACK" / "characters" / slug / "front.png"
            if p.is_file():
                return p
    return ep / "00_ASSET_PACK" / "characters" / "luc_thanh_y" / "front.png"

def update_ui_bridge():
    with bridge_lock:
        scene_videos = []
        for i in range(1, 67):
            vf = ep / "scenes" / f"scene_{i:04d}" / "scene_final.mp4"
            if vf.is_file() and vf.stat().st_size > 100000:
                scene_videos.append(vf)
        try:
            export_legacy_compatibility_bridge(
                ep, plan, scene_videos=scene_videos,
                image_provider="muse_video",
                subtitle_style="karaoke_viral",
                subtitle_size=58
            )
        except Exception as ex:
            print(f"[BRIDGE_WARN] {ex}", flush=True)
        return len(scene_videos)

def render_scene_task(n):
    sc = plan["scenes"][n - 1]
    folder = ep / "scenes" / f"scene_{n:04d}"
    folder.mkdir(parents=True, exist_ok=True)
    final_mp4 = folder / "scene_final.mp4"

    # 1. Skip if already done
    if final_mp4.is_file() and final_mp4.stat().st_size > 100000:
        print(f"[SKIP] Cảnh {n:02d} đã có video hoàn chỉnh ({final_mp4.stat().st_size} bytes)", flush=True)
        return {"scene": n, "status": "ALREADY_DONE", "file": str(final_mp4)}

    print(f"\n>>> [BẮT ĐẦU] Sản xuất Cảnh {n:02d}/66...", flush=True)

    # 2. Bind scene assets (auto-handles stills/anchors without failing)
    bind_scene(ep, sc, verify_scene_image=True)

    # 3. Render video I2V
    ref_img = get_char_ref(sc)
    receipt = folder / "manual_live_i2v_production_20261031.json"
    r = {"state": "IN_PROGRESS", "scene": n, "provider": "muse_video"}
    atomic_write(receipt, r)

    engine = DramaVideoEngine(fps=24)
    result = engine.render_scene(
        sc,
        folder,
        aspect_ratio="16:9",
        cast_map=cast,
        reference_image_path=ref_img,
        image_provider="muse_video",
        bible={"language": "Vietnamese", "cast": plan["cast"]},
        width=1280,
        height=720,
        subtitle_style="karaoke_viral",
        subtitle_size=58,
        no_subtitles=False,
    )

    output = Path(result["final_video_path"])
    r.update(state="COMPLETED", file=str(output), bytes=output.stat().st_size)
    atomic_write(receipt, r)

    completed_total = update_ui_bridge()
    print(f">>> [HOÀN TẤT] Cảnh {n:02d} -> {output.name} ({output.stat().st_size} bytes) | Tổng cảnh xong: {completed_total}/66", flush=True)
    return {"scene": n, "status": "SUCCESS", "file": str(output)}

def assemble_final_episode():
    all_videos = []
    for i in range(1, 67):
        vf = ep / "scenes" / f"scene_{i:04d}" / "scene_final.mp4"
        if vf.is_file() and vf.stat().st_size > 100000:
            all_videos.append(vf)
    if len(all_videos) == 66:
        print(f"\n=== ĐỦ 66/66 CẢNH! TIẾN HÀNH GHÉP TẬP PHIM EPISODE_FINAL.MP4 ===", flush=True)
        from cinematic_engine.drama_video_engine import DramaVideoEngine
        engine = DramaVideoEngine(fps=24)
        final_ep = ep / "episode_final.mp4"
        engine.concat_scenes(all_videos, final_ep)
        print(f"=== XUẤT BẢN THÀNH CÔNG EPISODE_FINAL.MP4 ({final_ep.stat().st_size} bytes)! ===", flush=True)
    else:
        print(f"Hiện tại có {len(all_videos)}/66 cảnh hoàn thành.", flush=True)

def main():
    print(f"=== KHỞI ĐỘNG BATCH SẢN XUẤT THIÊN SƯ TẬP 1 (CẢNH 22 ĐẾN 66) ===", flush=True)
    done_start = update_ui_bridge()
    print(f"Tiến độ hiện tại: {done_start}/66 cảnh đã có sẵn video.", flush=True)

    # Process scenes in parallel chunks of 2
    scenes_to_run = list(range(22, 67))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(render_scene_task, n): n for n in scenes_to_run}
        for future in concurrent.futures.as_completed(futures):
            n = futures[future]
            try:
                res = future.result()
            except Exception as exc:
                print(f"[LỖI CẢNH {n:02d}]: {exc}", flush=True)
                traceback.print_exc()

    assemble_final_episode()

if __name__ == "__main__":
    main()
