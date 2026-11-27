import sys
import json
import time
from pathlib import Path

sys.path.insert(0, "studio")
import reference_scene_assembler as rsa
from resilient_gemini import ResilientClient, get_all_api_keys

cache_dir = Path("D:/STORYBOARD_AI/studio/character_clones/H2R6ugBeILU_observed_storyboard_2088s")
frames_dir = cache_dir / "frames"
existing_frames = sorted(f for f in frames_dir.glob("source_*.jpg") if f.is_file() and f.stat().st_size > 800)
duration_seconds = 2088.0
scene_seconds = 15

windows = []
n = len(existing_frames)
for i, file in enumerate(existing_frames):
    start = i * scene_seconds
    end = duration_seconds if i == n - 1 else min(duration_seconds, (i + 1) * scene_seconds)
    windows.append({
        "scene_number": i + 1,
        "source_start_seconds": round(start, 3),
        "source_end_seconds": round(end, 3),
        "frame_path": str(file)
    })

sub_file = Path("D:/STORYBOARD_AI/studio/character_clones/H2R6ugBeILU_captions_english.json")
lines = json.loads(sub_file.read_text(encoding="utf-8"))["lines"]
active_lines = [l for l in lines if float(l.get("start", 0)) <= duration_seconds + 5.0]
timed_windows = rsa.attach_timed_captions(windows, active_lines)

# Read digest from existing verified batch
b25 = json.loads((cache_dir / "evidence_batch_025.json").read_text(encoding="utf-8"))
digest = b25["fingerprint"]
print(f"[ACCELERATOR] Fingerprint: {digest}")

SCENE_KEYS = (
    "scene_number", "summary", "narration", "description",
    "visual_setup", "text_overlay", "observed_subjects",
    "visual_confidence", "uncertainties"
)

def save_verified(file, part, result):
    doc = {
        "fingerprint": digest,
        "scene_ids": [w["scene_number"] for w in part],
        "model_scenes": [{key: scene[key] for key in SCENE_KEYS} for scene in result]
    }
    tmp = file.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(file)

keys = get_all_api_keys()
client = ResilientClient(api_keys=keys)

batch_size = 4
tot_batches = len(timed_windows) // batch_size
print(f"[ACCELERATOR] Bắt đầu tăng tốc xử lý các đợt cảnh còn lại từ batch 26 đến {tot_batches}...")

for b_idx in range(25, tot_batches):
    s_start = b_idx * batch_size
    batch = timed_windows[s_start:s_start + batch_size]
    batch_num = b_idx + 1
    dest = cache_dir / f"evidence_batch_{batch_num:03d}.json"
    ids = [w["scene_number"] for w in batch]

    if dest.is_file():
        try:
            chk = json.loads(dest.read_text(encoding="utf-8"))
            if chk.get("fingerprint") == digest and chk.get("scene_ids") == ids:
                print(f"[ACCELERATOR] Batch {batch_num} (cảnh {ids}) đã có sẵn, bỏ qua.")
                continue
        except Exception:
            pass

    print(f"\n[ACCELERATOR] >> Đang tạo kịch bản Batch {batch_num}/{tot_batches} (Cảnh {ids[0]}-{ids[-1]})...", flush=True)
    t0 = time.time()
    try:
        accepted = rsa.create_storyboard_batch(
            batch,
            genre="western",
            target_language="English",
            client=client,
            model="gemini-flash-lite-latest"
        )
        for source, scene in zip(batch, accepted):
            single = cache_dir / f"evidence_scene_{source['scene_number']:04d}.json"
            save_verified(single, [source], [scene])
        save_verified(dest, batch, accepted)
        dt = round(time.time() - t0, 1)
        print(f"[ACCELERATOR] ✅ Hoàn tất Batch {batch_num} trong {dt}s! Đã lưu cache an toàn.", flush=True)
    except Exception as e:
        print(f"[ACCELERATOR] ❌ Lỗi tại Batch {batch_num}: {e}", flush=True)
        time.sleep(3)

print("\n[ACCELERATOR] 🎉 ĐÃ HOÀN TẤT TOÀN BỘ 140 PHÂN CẢNH VÀO CACHE!", flush=True)
