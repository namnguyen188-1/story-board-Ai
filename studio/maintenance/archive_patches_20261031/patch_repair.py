from pathlib import Path
import time

p = Path(r"d:\STORYBOARD_AI\studio\cinematic_engine\drama_auto_repair.py")
text = p.read_text(encoding="utf-8")

if "import time" not in text:
    text = text.replace("import os\n", "import os\nimport time\n")

target = """    alternate = alternate_path.read_text(encoding="utf-8")
    alternate = sanitize_forbidden_words(alternate)
    parse_9_fields(alternate)
    scene["raw_9_fields"] = alternate
    return True"""

replacement = """    alternate = alternate_path.read_text(encoding="utf-8")
    alternate = sanitize_forbidden_words(alternate)
    parse_9_fields(alternate)
    scene["raw_9_fields"] = alternate
    rp = scene_dir / "muse_job.json"
    if rp.is_file():
        archive_path = scene_dir / f"muse_job_failed_armed_{int(time.time())}.json"
        try:
            os.replace(rp, archive_path)
        except Exception:
            pass
    return True"""

if target in text:
    text = text.replace(target, replacement)
    p.write_text(text, encoding="utf-8")
    print("Successfully patched drama_auto_repair.py")
else:
    print("Target not found, checking with normalized newlines...")
    norm_text = text.replace("\r\n", "\n")
    norm_target = target.replace("\r\n", "\n")
    norm_replacement = replacement.replace("\r\n", "\n")
    if norm_target in norm_text:
        norm_text = norm_text.replace(norm_target, norm_replacement)
        p.write_text(norm_text, encoding="utf-8")
        print("Successfully patched drama_auto_repair.py (normalized)")
    else:
        print("Could not match target!")
