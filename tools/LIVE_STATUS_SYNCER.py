"""Live UI Status Syncer for Storyboard AI Studio Pro.
Bridges background batch execution directly to the web interface via active_run_status.json.
"""
import time
import json
import re
from pathlib import Path

EPISODE_DIR = Path(r"D:\STORYBOARD_AI\studio\productions\THI-N-S-HUY-N-PH-TR-N-QU\episode_001")
TASK_LOG = Path(r"C:\Users\thean\.gemini\antigravity\brain\546909c0-dc2e-4f1c-bb37-21aa33365ca1\.system_generated\tasks\task-410.log")
TARGET_STATUS = Path(r"D:\STORYBOARD_AI\studio\web\active_run_status.json")

TOTAL_SCENES = 66
start_time = time.time()

print("[SYNCER] Starting Live UI Status Syncer daemon...")

while True:
    try:
        # 1. Count completed scene videos
        done_scenes = []
        for i in range(1, TOTAL_SCENES + 1):
            vf = EPISODE_DIR / "scenes" / f"scene_{i:04d}" / "scene_final.mp4"
            if vf.is_file() and vf.stat().st_size > 100000:
                done_scenes.append(i)
        
        comp_count = len(done_scenes)
        final_ep = EPISODE_DIR / "episode_final.mp4"
        is_fully_done = final_ep.is_file() and final_ep.stat().st_size > 500000

        # 2. Read latest task logs
        recent_logs = []
        current_scene = None
        if TASK_LOG.is_file():
            try:
                lines = TASK_LOG.read_text(encoding="utf-8", errors="replace").splitlines()
                recent_logs = lines[-50:]
                for line in reversed(lines[-40:]):
                    m = re.search(r"Cảnh\s+(\d+)", line)
                    if m:
                        current_scene = int(m.group(1))
                        break
            except Exception:
                pass

        if not current_scene:
            current_scene = min(comp_count + 1, TOTAL_SCENES)

        pct = 100 if is_fully_done else max(15, min(95, round((comp_count / TOTAL_SCENES) * 100)))

        msg = f"Đã hoàn thành toàn bộ tập 1 ({comp_count}/{TOTAL_SCENES} cảnh)!" if is_fully_done else f"Đang sản xuất Cảnh {current_scene}/{TOTAL_SCENES} bằng Muse AI Video (Đã xong: {comp_count}/{TOTAL_SCENES})..."

        status_obj = {
            "running": not is_fully_done,
            "series": "THI-N-S-HUY-N-PH-TR-N-QU",
            "episode": 1,
            "mode": "live",
            "stage": "COMPLETED" if is_fully_done else "RENDERING_VIDEO",
            "percent": pct,
            "current_scene": current_scene,
            "total_scenes": TOTAL_SCENES,
            "completed_scenes": comp_count,
            "message": msg,
            "exit_code": None,
            "final_video_url": "/media/productions/THI-N-S-HUY-N-PH-TR-N-QU/episode_001/episode_final.mp4" if is_fully_done else None,
            "start_time": start_time,
            "elapsed_seconds": int(time.time() - start_time),
            "awaiting_asset_review": False,
            "recent_logs": recent_logs,
            "timestamp": int(time.time() * 1000)
        }

        tmp_file = TARGET_STATUS.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(status_obj, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_file.replace(TARGET_STATUS)

        if is_fully_done:
            print("[SYNCER] Production complete! Final status published.")
            break

    except Exception as e:
        print(f"[SYNCER ERROR]: {e}")

    time.sleep(2)
