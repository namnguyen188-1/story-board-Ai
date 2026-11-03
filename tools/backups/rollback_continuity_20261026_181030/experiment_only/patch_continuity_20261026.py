# -*- coding: utf-8 -*-
"""Non-destructive scene continuity patch for Muse Cinematic Drama."""
from pathlib import Path
from datetime import datetime
import shutil, py_compile
root = Path(r"D:\STORYBOARD_AI")
studio = root / "studio"
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = root / "tools" / "backups" / ("continuity_" + stamp)
targets = {
 "cinematic_engine/drama_orchestrator.py": studio / "cinematic_engine" / "drama_orchestrator.py",
 "cinematic_engine/drama_video_engine.py": studio / "cinematic_engine" / "drama_video_engine.py",
 "muse_video_provider.py": studio / "muse_video_provider.py",
}
src = {k:p.read_text(encoding="utf-8") for k,p in targets.items()}
if all("MUSE_CONTINUITY_V1" in v for v in src.values()):
 print("ALREADY_PATCHED_CONTINUITY_V1")
 raise SystemExit(0)

def replace_once(content, old, new, name):
 count = content.count(old)
 if count != 1:
  raise RuntimeError(f"UNSAFE_PATCH {name}: expected one anchor, found {count}")
 return content.replace(old, new, 1)

module = '''"""Cross-scene continuity instructions for sequential Muse text-to-video.

This improves scene intent but cannot guarantee frame-level matching because
the current Muse transport is text-to-video and does not accept a first frame.
"""
from __future__ import annotations

def continuity_instruction(previous: dict, current: dict) -> str:
    prev_setting = str(previous.get("setting") or "").strip()
    next_setting = str(current.get("setting") or "").strip()
    same_place = bool(prev_setting and next_setting and prev_setting.casefold() == next_setting.casefold())
    spoken = previous.get("dialogue_beats") or []
    last_spoken = ""
    last_action = ""
    if isinstance(spoken, list):
        for item in reversed(spoken):
            if isinstance(item, dict):
                if not last_spoken and item.get("text"):
                    last_spoken = f'{item.get("speaker", "")}: {item["text"]}'
                if not last_action and item.get("action"):
                    last_action = str(item["action"])
                if last_spoken and last_action:
                    break
    prev_summary = str(previous.get("summary") or "").strip()[:450]
    prior_cast = previous.get("characters_present") or []
    current_cast = current.get("characters_present") or []
    shared = [n for n in current_cast if n in prior_cast] if isinstance(prior_cast,list) and isinstance(current_cast,list) else []
    location_rule = (
        "SAME LOCATION: resume from the last action's resulting body positions, "
        "prop ownership, costume condition, weather, and movement direction; "
        "do not reset characters to their original poses."
        if same_place else
        "LOCATION CHANGE: establish a deliberate visible story transition to the new location; "
        "never imply instant teleportation or unexplained prop/costume changes."
    )
    details = [
        "THIS CLIP IS THE IMMEDIATE NEXT SHOT OF ONE FILM, NOT A NEW TRAILER OR REBOOT.",
        f"PREVIOUS SCENE EVENT: {prev_summary}.",
        f"PREVIOUS SCENE LAST ACTION: {last_action[:240]}.",
        f"PREVIOUS SCENE LAST SPOKEN LINE: {last_spoken[:200]}.",
        f"CONTINUING CHARACTERS: {', '.join(shared) if shared else 'as required by the screenplay'}.",
        location_rule,
        "Maintain character facial features, wardrobe, hairstyle, age, voice identity, "
        "set layout, screen direction and lighting continuity unless the screenplay explicitly changes them. "
        "Keep natural cause-and-effect acting and begin with the consequences of the prior shot."
    ]
    return " ".join(details)

def extract_last_frame(video, destination):
    """QA evidence only: current Muse transport does NOT use this as an I2V input."""
    import subprocess
    from pathlib import Path
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    run = subprocess.run(
      ["ffmpeg","-hide_banner","-loglevel","error","-y","-sseof","-0.15",
       "-i",str(video),"-frames:v","1",str(destination)],
      capture_output=True, timeout=30,
      creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
    return run.returncode == 0 and destination.is_file() and destination.stat().st_size > 1000
'''
orchestrator=src["cinematic_engine/drama_orchestrator.py"]
orchestrator=replace_once(orchestrator,
'        max_scene_retries = 3',
'''        # MUSE_CONTINUITY_V1: pass the previous real screenplay beat into the next render.
        if image_provider == "muse_video" and sc_idx > 1:
            from .scene_continuity import continuity_instruction
            sc_data = dict(sc_data)
            sc_data["continuity_context"] = continuity_instruction(scenes_data[sc_idx - 2], sc_data)

        max_scene_retries = 3''',"previous beat")
orchestrator=replace_once(orchestrator,
'                print(f"SCENE_PASS {sc_num}", flush=True)\n                return sc_num, scene_video',
'''                if image_provider == "muse_video":
                    try:
                        from .scene_continuity import extract_last_frame
                        extract_last_frame(scene_video, sc_dir / "continuity_last_frame.jpg")
                    except Exception as frame_exc:
                        print(f"[CONTINUITY_QA_WARN] Cannot save tail frame: {frame_exc}", flush=True)
                print(f"SCENE_PASS {sc_num}", flush=True)
                return sc_num, scene_video''',"extract frame")
orchestrator=replace_once(orchestrator,
'    # 1. SCENE 1: Always rendered first to establish visual actor anchor',
'''    # MUSE_CONTINUITY_V1: require preceding clip to finish before next starts.
    if image_provider == "muse_video":
        configured_workers = 1
        print("[CONTINUITY] Muse sequential continuity enabled (workers=1).", flush=True)

    # 1. SCENE 1: Always rendered first to establish visual actor anchor''',"force sequential")
orchestrator=replace_once(orchestrator,
'    if missing_nums:\n        print(f"\\n[BẢO VỆ TIẾN ĐỘ]',
'''    # MUSE_CONTINUITY_V1: blank three-second filler is not a valid film scene.
    if missing_nums and image_provider == "muse_video":
        raise RuntimeError(f"MUSE_CONTINUITY_MISSING_SCENES: {missing_nums}. Preserve all existing clips and retry failed scenes; do not insert black fillers.")

    if missing_nums:
        print(f"\\n[BẢO VỆ TIẾN ĐỘ]''',"disable filler")
video=src["cinematic_engine/drama_video_engine.py"]
video=replace_once(video,
'                        "raw_9_fields": scene.get("raw_9_fields", "") if isinstance(scene, dict) else getattr(scene, "raw_9_fields", ""),',
'''                        "raw_9_fields": scene.get("raw_9_fields", "") if isinstance(scene, dict) else getattr(scene, "raw_9_fields", ""),
                        "continuity_context": scene.get("continuity_context", "") if isinstance(scene, dict) else "",  # MUSE_CONTINUITY_V1''',"pass context")
provider=src["muse_video_provider.py"]
provider=replace_once(provider,
'    # 1. If the scene was provided using the 9-field skill contract, pass it directly to Muse!',
'''    # MUSE_CONTINUITY_V1: plain-text constraints, not a frame reference. Keep nine field labels unchanged.
    prior_context = str(scene.get("continuity_context") or "").strip()[:1750]
    # 1. If the scene was provided using the 9-field skill contract, pass it directly to Muse!''',"context variable")
provider=replace_once(provider,
'        return str(scene["raw_9_fields"]).strip()',
'''        raw = str(scene["raw_9_fields"]).strip()
        if prior_context and "SETTING & START STATE:" in raw:
            raw = raw.replace("SETTING & START STATE:", "SETTING & START STATE: " + prior_context + " ", 1)
        return raw''',"9 field")
provider=replace_once(provider,
'    return "\\n".join(parts)',
'''    if prior_context:
        parts.insert(0, "SCENE-TO-SCENE CONTINUITY: " + prior_context)
    return "\\n".join(parts)''',"text prompt")
patches={
 "cinematic_engine/drama_orchestrator.py":orchestrator,
 "cinematic_engine/drama_video_engine.py":video,
 "muse_video_provider.py":provider,
}
backup.mkdir(parents=True,exist_ok=False)
for k,p in targets.items():
 dest=backup/k
 dest.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(p,dest)
for k,content in patches.items():
 compile(content,str(targets[k]),"exec")
compile(module,str(studio / "cinematic_engine" / "scene_continuity.py"),"exec")
for k,content in patches.items():
 tmp=targets[k].with_suffix(".continuity_tmp")
 tmp.write_text(content,encoding="utf-8")
 tmp.replace(targets[k])
(studio/"cinematic_engine"/"scene_continuity.py").write_text(module,encoding="utf-8")
for p in list(targets.values())+[studio/"cinematic_engine"/"scene_continuity.py"]:
 py_compile.compile(str(p),doraise=True)
print("CONTINUITY_PATCH_PASS")
print("BACKUP:",backup)
print("PATCHED:",",".join(patches))
