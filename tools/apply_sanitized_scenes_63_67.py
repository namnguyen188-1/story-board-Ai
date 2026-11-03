import json
import shutil
import sys
from pathlib import Path

ROOT = Path(r"d:\STORYBOARD_AI\studio")
sys.path.insert(0, str(ROOT))
from cinematic_engine.drama_skill9 import export_episode

EP = ROOT / "productions" / "ho-t-h-nh-3d" / "episode_001"

# 1. Update drama_plan.json
drama_plan_path = EP / "drama_plan.json"
drama_plan = json.loads(drama_plan_path.read_text(encoding="utf-8"))

sc63 = drama_plan["scenes"][62]
assert sc63["scene_number"] == 63
sc63["summary"] = "Quốc sư Hắc Đạo trỗi dậy cuồng vọng, tiến bước dũng mãnh về phía luồng sáng với mưu đồ làm chủ sức mạnh không gian."
sc63["visual_setup"] = (
    "Dynamic over-the-shoulder tracking shot. Quốc sư Hắc Đạo, 50 years old with gaunt face, pale yellow eyes, "
    "long greasy grey hair, wearing black robes with silver eclipse motifs, holding a dark gnarled wooden staff. "
    "He strides purposefully over shattered roof tiles toward the towering neon violet light pillar. "
    "Luminous violet energy arcs flow smoothly around his robes. "
    "Background courtyard bathed in dramatic cyan rim light and deep midnight navy shadows."
)
sc63["visual_prompt"] = sc63["visual_setup"]
sc63["dialogue_beats"][0]["action"] = "Laughs sinisterly, raising his gnarled wooden staff toward the swirling column of cosmic light."
sc63["dialogue_beats"][1]["action"] = "Advances boldly toward the towering column of neon violet light, raising his gnarled wooden staff in triumph with a menacing smile."

sc67 = drama_plan["scenes"][66]
assert sc67["scene_number"] == 67
sc67["summary"] = "Quốc sư Hắc Đạo kinh ngạc trước dòng năng lượng thời gian cuộn trào, chật vật kiểm soát sức mạnh vô tận."
sc67["visual_setup"] = (
    "A surreal fragmented temporal domain glowing with electric cyan god-rays and shimmering violet gridlines "
    "across floating ancient temple debris. 8k master cinema shot. Quốc sư Hắc Đạo, 50 years old, gaunt, "
    "sinister pale yellow eyes wide in shock, wearing layered flowing black robes with silver eclipse motifs. "
    "Luminous rings of violet temporal energy swirl around his flowing robes as his long grey hair floats in the air. "
    "Volumetric cyan rim lighting illuminates his dark wooden staff glowing with cosmic runes. Deep midnight sapphire atmosphere."
)
sc67["visual_prompt"] = sc67["visual_setup"]
sc67["dialogue_beats"][0]["action"] = "Presses both hands to his temples in shock as glowing violet temporal glyphs shimmer gently in the air before him."
sc67["dialogue_beats"][1]["action"] = "Looks up at the swirling cosmic sky in disbelief, raising his arms as crystalline temporal light drifts around him."

drama_plan_path.write_text(json.dumps(drama_plan, ensure_ascii=False, indent=2), encoding="utf-8")
print("[OK] Updated drama_plan.json")

# 2. Update plan.json
plan_path = EP / "plan.json"
plan_data = json.loads(plan_path.read_text(encoding="utf-8-sig"))
plan_sc63 = plan_data["scenes"][62]
plan_sc63["summary"] = sc63["summary"]
plan_sc63["title"] = sc63["summary"]
plan_sc63["visual_setup"] = sc63["visual_setup"]
plan_sc63["description"] = sc63["visual_setup"]

plan_sc67 = plan_data["scenes"][66]
plan_sc67["summary"] = sc67["summary"]
plan_sc67["title"] = sc67["summary"]
plan_sc67["visual_setup"] = sc67["visual_setup"]
plan_sc67["description"] = sc67["visual_setup"]

plan_path.write_text(json.dumps(plan_data, ensure_ascii=False, indent=2), encoding="utf-8")
print("[OK] Updated plan.json")

# 3. Update scene_prompts_9_fields.txt & scene_prompts_9_fields_qc.json
report = export_episode(drama_plan, EP, genre="animation", visual_style="color_animation", language="Vietnamese", aspect="9:16", seconds=10)
print(f"[OK] Exported 9 fields: pass={report['pass']}, scenes={report['scene_count']}")

# 4. Update scene_0063
sc63_dir = EP / "scenes" / "scene_0063"
job63_path = sc63_dir / "job.json"
job63 = json.loads(job63_path.read_text(encoding="utf-8"))
job63["summary"] = sc63["summary"]
job63["title"] = sc63["summary"]
job63["text_overlay"] = sc63["summary"]
job63["visual_setup"] = sc63["visual_setup"]
job63["description"] = sc63["visual_setup"]
job63_path.write_text(json.dumps(job63, ensure_ascii=False, indent=2), encoding="utf-8")

for fname in ["muse_job.json", "muse_job_failed_before_repair.json", "muse_scene_repair.json", "muse_scene_repair_9_fields.txt"]:
    p = sc63_dir / fname
    if p.exists():
        archive_name = p.stem + ".failed_archive" + p.suffix
        p.replace(sc63_dir / archive_name)
        print(f"  Archived {fname} -> {archive_name}")

(sc63_dir / "result.json").write_text(json.dumps({"status": "PENDING", "qc": {"expected_duration_seconds": 10}}, ensure_ascii=False, indent=2), encoding="utf-8")
print("[OK] Prepared scene_0063")

# 5. Update scene_0067
sc67_dir = EP / "scenes" / "scene_0067"
job67_path = sc67_dir / "job.json"
job67 = json.loads(job67_path.read_text(encoding="utf-8"))
job67["summary"] = sc67["summary"]
job67["title"] = sc67["summary"]
job67["text_overlay"] = sc67["summary"]
job67["visual_setup"] = sc67["visual_setup"]
job67["description"] = sc67["visual_setup"]
job67_path.write_text(json.dumps(job67, ensure_ascii=False, indent=2), encoding="utf-8")

for fname in ["muse_job.json", "muse_job_failed_before_repair.json", "muse_scene_repair.json", "muse_scene_repair_9_fields.txt"]:
    p = sc67_dir / fname
    if p.exists():
        archive_name = p.stem + ".failed_archive" + p.suffix
        p.replace(sc67_dir / archive_name)
        print(f"  Archived {fname} -> {archive_name}")

(sc67_dir / "result.json").write_text(json.dumps({"status": "PENDING", "qc": {"expected_duration_seconds": 10}}, ensure_ascii=False, indent=2), encoding="utf-8")
print("[OK] Prepared scene_0067")
print("\nAll files successfully updated and armed for execution!")
