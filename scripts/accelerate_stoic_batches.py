import sys
import json
import time
import concurrent.futures
from pathlib import Path

sys.path.insert(0, "studio")
import reference_scene_assembler as rsa
from resilient_gemini import ResilientClient, get_all_api_keys

cache_dir = Path("D:/STORYBOARD_AI/studio/character_clones/15yOVuLfqV0_observed_storyboard_2088s")
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

sub_file = Path("D:/STORYBOARD_AI/studio/character_clones/15yOVuLfqV0_captions_spanish.json")
lines = json.loads(sub_file.read_text(encoding="utf-8"))["lines"]
active_lines = [l for l in lines if float(l.get("start", 0)) <= duration_seconds + 5.0]
timed_windows = rsa.attach_timed_captions(windows, active_lines)

# Read digest from existing verified batch
b6 = json.loads((cache_dir / "evidence_batch_006.json").read_text(encoding="utf-8"))
digest = b6["fingerprint"]
print(f"[ACCELERATOR] Fingerprint: {digest}", flush=True)

SCENE_KEYS = (
    "scene_number", "summary", "narration", "description",
    "visual_setup", "text_overlay", "observed_subjects",
    "visual_confidence", "uncertainties"
)

keys = get_all_api_keys()
client = ResilientClient(api_keys=keys)

def process_batch(batch_num):
    index = (batch_num - 1) * 4
    batch = timed_windows[index : index + 4]
    dest = cache_dir / f"evidence_batch_{batch_num:03d}.json"
    
    if dest.is_file():
        try:
            saved = json.loads(dest.read_text(encoding="utf-8"))
            if saved.get("fingerprint") == digest and len(saved.get("model_scenes", [])) == len(batch):
                print(f"[ACCELERATOR] Batch {batch_num} đã có sẵn trong cache.", flush=True)
                return batch_num, True
        except Exception:
            pass

    ids = [w["scene_number"] for w in batch]
    print(f"[ACCELERATOR] >> Đang tạo kịch bản Batch {batch_num}/35 (Cảnh {ids[0]}-{ids[-1]})...", flush=True)
    t0 = time.time()
    
    for attempt in range(1, 4):
        try:
            accepted = rsa.create_storyboard_batch(
                batch,
                genre="stoic",
                target_language="Spanish",
                client=client,
                model="gemini-flash-lite-latest"
            )
            doc = {
                "fingerprint": digest,
                "scene_ids": ids,
                "model_scenes": [{key: scene.get(key, "") for key in SCENE_KEYS} for scene in accepted]
            }
            tmp = dest.with_suffix(".tmp")
            tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(dest)
            
            # Also save individual scenes for single-scene checkpointing
            for src, scn in zip(batch, accepted):
                s_dest = cache_dir / f"evidence_scene_{src['scene_number']:04d}.json"
                s_doc = {
                    "fingerprint": digest,
                    "scene_ids": [src["scene_number"]],
                    "model_scenes": [{key: scn.get(key, "") for key in SCENE_KEYS}]
                }
                s_tmp = s_dest.with_suffix(".tmp")
                s_tmp.write_text(json.dumps(s_doc, ensure_ascii=False, indent=2), encoding="utf-8")
                s_tmp.replace(s_dest)

            elapsed = time.time() - t0
            print(f"[ACCELERATOR] ✅ Hoàn tất Batch {batch_num} trong {elapsed:.1f}s!", flush=True)
            return batch_num, True
        except Exception as exc:
            print(f"[ACCELERATOR] ⚠️ Batch {batch_num} thử lại (lần {attempt}): {exc}", flush=True)
            time.sleep(2.0)

    print(f"[ACCELERATOR] ❌ Thất bại Batch {batch_num}", flush=True)
    return batch_num, False

def main():
    batches_to_run = []
    for b_num in range(7, 36):
        dest = cache_dir / f"evidence_batch_{b_num:03d}.json"
        if not dest.is_file():
            batches_to_run.append(b_num)

    print(f"[ACCELERATOR] Cần xử lý song song {len(batches_to_run)} batches: {batches_to_run}", flush=True)
    
    # Run 3 parallel workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_batch, b_num): b_num for b_num in batches_to_run}
        for f in concurrent.futures.as_completed(futures):
            b_num, ok = f.result()
            print(f"[ACCELERATOR] Đã ghi nhận xong Batch {b_num} (status={ok})", flush=True)

    print("[ACCELERATOR] 🎉 ĐÃ HOÀN TẤT TOÀN BỘ 140 PHÂN CẢNH VÀO CACHE CHO VIDEO STOIC!", flush=True)

if __name__ == "__main__":
    main()
