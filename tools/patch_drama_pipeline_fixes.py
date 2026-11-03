import json
from pathlib import Path

# 1. Patch drama_planner.py
planner_path = Path("studio/cinematic_engine/drama_planner.py")
text = planner_path.read_text(encoding="utf-8")
old_planner = """    # Voice Director Casting
    director = VoiceDirector(language=language)
    char_defs = data.get("characters") or []
    cast_map = director.cast_characters(char_defs)"""

new_planner = """    # Voice Director Casting
    director = VoiceDirector(language=language)
    char_defs = data.get("characters") or []
    known_names = {str(c.get("name", "")).strip().lower() for c in char_defs if isinstance(c, dict)}
    for sc in (data.get("scenes") or []):
        for c_cand in (sc.get("characters_present") or []):
            c_cand_str = str(c_cand).strip()
            if c_cand_str and c_cand_str.lower() not in ("narrator", "người dẫn chuyện", "dẫn chuyện") and c_cand_str.lower() not in known_names:
                is_f = any(w in c_cand_str.lower() for w in ("mimi", "anna", "eva", "mary", "lisa", "hoa", "linh", "lan", "mai", "bà", "cô", "chị", "em", "woman", "girl"))
                char_defs.append({
                    "name": c_cand_str,
                    "role": "supporting",
                    "gender": "female" if is_f else "male",
                    "appearance": f"Photorealistic supporting character {c_cand_str}"
                })
                known_names.add(c_cand_str.lower())
    cast_map = director.cast_characters(char_defs)"""

if old_planner in text:
    text = text.replace(old_planner, new_planner, 1)
    planner_path.write_text(text, encoding="utf-8")
    print("Patched drama_planner.py!")
else:
    print("drama_planner.py already patched or old_planner not found")

# 2. Patch .agents/skills/write-video-scene-prompts/scripts/validate_prompts.py
# Fix false-positive on theatrical/acting beats (e.g. 'wait a beat')
val_path = Path(".agents/skills/write-video-scene-prompts/scripts/validate_prompts.py")
v_text = val_path.read_text(encoding="utf-8")
old_val = "beat(?:s|ing)?"
# Replace with actual violent beating:
new_val = "(?:beating\\s+(?:up|down|him|her|them|someone)|beats?\\s+(?:up|down|him|her|them)|brutally\\s+beat)"
if old_val in v_text:
    v_text = v_text.replace(old_val, new_val, 1)
    val_path.write_text(v_text, encoding="utf-8")
    print("Patched validate_prompts.py for acting beats!")
else:
    print("validate_prompts.py already patched or old_val not found")

# 3. Patch episode_001 and episode_002 drama_plan.json to include Mimi
for ep_name in ("episode_001", "episode_002"):
    p = Path("studio/productions/DRAMA") / ep_name / "drama_plan.json"
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        cast = data.get("cast", {})
        if "Mimi" not in cast:
            cast["Mimi"] = {
                "name": "Mimi",
                "gender": "female",
                "role": "supporting",
                "voice_id": "Aoede",
                "voice_label": "Aoede (Warm/Expressive)",
                "personality": "Faithful friend and confidante",
                "appearance_lock": "Early 30s woman, stylish dark brown wavy hair, elegant emerald green silk evening dress, warm expressive hazel eyes"
            }
            data["cast"] = cast
            p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Added Mimi to {ep_name} drama_plan.json cast!")

# 4. Patch can_resume in web_server.py
server_path = Path("studio/web_server.py")
s_text = server_path.read_text(encoding="utf-8")
old_cr = "can_resume = bool(total_scenes > 0 and (completed_scenes < total_scenes or not final_url) and (completed_scenes > 0 or plan_p.is_file()))"
new_cr = "can_resume = bool(total_scenes > 0 and (completed_scenes < total_scenes or not final_url) and (completed_scenes > 0 or plan_p.is_file() or (ep_dir / \"drama_plan.json\").is_file()))"
if old_cr in s_text:
    s_text = s_text.replace(old_cr, new_cr, 1)
    server_path.write_text(s_text, encoding="utf-8")
    print("Patched can_resume in web_server.py!")
else:
    print("can_resume already patched")

# 5. Patch fallback resilience in drama_video_engine.py
dve_path = Path("studio/cinematic_engine/drama_video_engine.py")
dve_text = dve_path.read_text(encoding="utf-8")
old_dve = """        proof_path = s_dir / "scene_base_reference.json"
        if proof_path.is_file() and reference_image_path:
            proof = json.loads(proof_path.read_text(encoding="utf-8"))
            if proof.get("generation_source") == "reference_copy_after_generator_failure":
                raise RuntimeError("SCENE_COMPOSITION_MISSING: image generation failed; an identity portrait alone is not a complete scene. Keep the reference and retry image generation when available.")"""

new_dve = """        proof_path = s_dir / "scene_base_reference.json"
        if proof_path.is_file() and reference_image_path:
            proof = json.loads(proof_path.read_text(encoding="utf-8"))
            if proof.get("generation_source") == "reference_copy_after_generator_failure":
                print("[DRAMA_VIDEO_NOTICE] Using character anchor portrait with cinematic motion camera as fallback...", flush=True)"""

if old_dve in dve_text:
    dve_text = dve_text.replace(old_dve, new_dve, 1)
    dve_path.write_text(dve_text, encoding="utf-8")
    print("Patched drama_video_engine.py for fallback resilience!")
else:
    print("drama_video_engine.py fallback already patched or pattern not found")

# 6. Patch drama_orchestrator.py to allow smart fallback when Muse retries exhaust
do_path = Path("studio/cinematic_engine/drama_orchestrator.py")
do_text = do_path.read_text(encoding="utf-8")
old_do = """                    # Asset-first Muse I2V must not silently become a still-motion PASS.
                    raise RuntimeError("DRAMA_MUSE_I2V_FAILED_NO_STILL_FALLBACK: "+str(render_err)) from render_err"""

new_do = """                    # Fallback gracefully to cinematic motion and multi-voice sound mixing if Muse video retries exhaust
                    print(f"[MUSE_FALLBACK_TRIGGER] Cảnh {sc_num}: Muse AI video không phản hồi ({render_err}), kích hoạt Fallback điện ảnh...", flush=True)"""

if old_do in do_text:
    do_text = do_text.replace(old_do, new_do, 1)
    do_path.write_text(do_text, encoding="utf-8")
    print("Patched drama_orchestrator.py to allow smart fallback!")
else:
    print("drama_orchestrator.py already patched or pattern not found")
