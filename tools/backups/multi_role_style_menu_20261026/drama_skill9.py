"""Dedicated 9-field screenplay bridge for multi-role cinematic drama ONLY.

Do not import this module from narrative/voice-over paths.  Text preflight is
not video QC.  Muse / MCP transport is intentionally left unchanged.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2] / ".agents" / "skills" / "write-video-scene-prompts"
LABELS = ("FORMAT & STYLE", "CHARACTERS", "SETTING & START STATE",
          "LIGHTING & COLOR", "CAMERA", "TIMED ACTION", "END STATE",
          "AUDIO", "CONSTRAINTS")
_REQUIRED = ("SKILL.md", "references/FORMAT_CONTRACT.md",
             "references/REALISTIC_ACTING.md", "references/QC.md",
             "references/GENRES.md", "scripts/validate_prompts.py")


def _skill_files():
    missing = [name for name in _REQUIRED if not (SKILL / name).is_file()]
    if missing:
        raise RuntimeError("DRAMA_SKILL9_MISSING: " + ", ".join(missing))


def writing_rules(genre: str) -> str:
    """Feed the REAL installed skill to the multi-role drama screenwriter."""
    _skill_files()
    def read(name, limit):
        return (SKILL / name).read_text(encoding="utf-8-sig")[:limit]
    return (
        "\n\n[MULTI-ROLE DRAMA ONLY -- AUTHORITATIVE INSTALLED SKILL]\n"
        "Use write-video-scene-prompts to WRITE the screenplay, not just format it. "
        "This is spoken multi-character cinema, NOT a narrated slideshow. "
        "Keep character-specific dialogue beats, actions, voice and reaction. "
        "A silent listener does not lip-sync another speaker. "
        "For EVERY scene, generate explicit 'start_state' and 'end_state' as extra "
        "JSON scene fields: character locations, body pose, who holds which prop, "
        "gaze direction, light source. Next scene start must logically inherit "
        "previous end without teleporting or changing costume. "
        "Include 'characters_present' and 'dialogue_beats' exactly as the existing "
        "cinematic drama JSON contract demands. Do not output nine-field TXT "
        "instead of the expected JSON; it is validated/exported after planning. "
        "Do not invent missing source events for link/clone mode. "
        "For animations, retain 3D/2D style; do not turn into live action. "
        "Each 10-second shot: one motivated major action, 1-2 caused reactions, "
        "concise speech fitting 10 seconds.\n"
        "CANONICAL SKILL:\n" + read("SKILL.md", 2600) +
        "\nFIELD CONTRACT:\n" + read("references/FORMAT_CONTRACT.md", 1050) +
        "\nACTING:\n" + read("references/REALISTIC_ACTING.md", 2000) +
        "\nGENRE (" + str(genre) + "):\n" + read("references/GENRES.md", 1150)
    )


def _one_line(v, limit=2200):
    s = re.sub(r"\s+", " ", str(v or "")).strip()
    for label in LABELS:
        s = re.sub(r"(?i)\b" + re.escape(label) + r":", "", s)
    return s[:limit].strip()


def _clock(seconds):
    return f"{seconds//60:02d}:{seconds%60:02d}"


def _visual_style(genre, visual_style):
    v = (str(genre) + " " + str(visual_style)).lower()
    if any(k in v for k in ("animation", "hoạt hình", "3d_cgi", "color_animation", "cgi")):
        return "Feature-quality stylized 3D CGI animation, expressive consistent stylized actors; NEVER live-action"
    if any(k in v for k in ("anime", "2d", "manga")):
        return "Cinematic 2D hand-drawn animation, stable linework and character design; NEVER live-action"
    if any(k in v for k in ("stoic", "statue", "marble")):
        return "Cinematic documentary imagery of authentic stone/bronze sculptures, sculpture stays inanimate"
    if any(k in v for k in ("whiteboard", "marker")):
        return "Hand-drawn whiteboard illustration and marker animation on clean white backdrop"
    return "Cinematic naturalistic live-action drama, credible physical performances and natural skin texture"


def _cast_lock(scene, cast):
    names = list(scene.get("characters_present") or [])
    if not names:
        names = [b.get("speaker") for b in scene.get("dialogue_beats", []) if isinstance(b, dict)]
    result = []
    for name in dict.fromkeys(str(n) for n in names if n):
        if name.lower() in ("narrator", "người dẫn chuyện", "dẫn chuyện"):
            continue
        prof = (cast or {}).get(name, {}) if isinstance(cast, dict) else {}
        if not isinstance(prof, dict):
            prof = {}
        appearance = _one_line(prof.get("appearance_lock") or prof.get("appearance"), 550)
        result.append((name + (": " + appearance if appearance else "")).strip())
    return "; ".join(result) or "Retain exactly the named cast from the screenplay; no new characters"


def _dialogue_audio(beats, seconds, language, scene):
    beats = [b for b in (beats or []) if isinstance(b, dict) and str(b.get("text") or "").strip()]
    if not beats:
        return "0.0–{:.1f}s: Silent scene; source-based ambient sound and reactions only; no invented voiceover.".format(seconds)
    usable = max(0.4, seconds - 1.0)
    step = usable / len(beats)
    lines = []
    for i, beat in enumerate(beats):
        begin, end = 0.5 + i*step, min(seconds-0.3, 0.5+(i+1)*step)
        speaker = _one_line(beat.get("speaker"), 100) or "Speaker"
        spoken = _one_line(beat.get("text"), 1000)
        tone = _one_line(beat.get("tone"), 90)
        voice = _one_line(beat.get("voice_id"), 70)
        lines.append(f'{begin:.1f}–{end:.1f}s: {speaker} speaks in {language} ({tone}, voice {voice}): "{spoken}". Only {speaker} lip-syncs this turn; others listen/react silently.')
    cues = scene.get("sfx_cues") or []
    if cues:
        lines.append("Ambient SFX: " + _one_line(", ".join(map(str, cues)), 200) + ".")
    return " ".join(lines)


def build_scene(scene, cast, previous, *, genre, visual_style, language, aspect,
                seconds=10, index=1):
    """Produce exactly the nine canonical fields for one independent Muse T2V scene."""
    if seconds <= 0 or int(seconds) != seconds:
        raise ValueError("DRAMA_SKILL9_BAD_DURATION: whole-second scene duration required")
    seconds = int(seconds)
    summary = _one_line(scene.get("summary"), 800)
    visual = _one_line(scene.get("visual_setup") or scene.get("visual_prompt"), 1600)
    setting = _one_line(scene.get("setting"), 450)
    start = _one_line(scene.get("start_state"), 650)
    previous_end = _one_line(previous.get("end_state") or previous.get("summary"), 500) if previous else ""
    if not start:
        start = ("Continue directly from prior ending: " + previous_end) if previous else "Establish first shot with stable cast, props and positions as described"
    end = _one_line(scene.get("end_state"), 650) or ("Physical outcome of this shot: " + summary)
    movement = "; ".join(_one_line(b.get("action"), 270) for b in scene.get("dialogue_beats", [])
                         if isinstance(b, dict) and b.get("action"))
    action = movement or summary
    cast_text = _cast_lock(scene, cast)
    first = f"0.0–{min(2,seconds):.1f}s: A visible cause triggers attention and a purposeful reaction. "
    if seconds > 2:
        second = f"{min(2,seconds):.1f}–{max(2,seconds-2):.1f}s: {action}. Characters act within the established space with credible body weight and eye-lines. "
    else:
        second = ""
    third = f"{max(2,seconds-2):.1f}–{seconds:.1f}s: Complete the motivated action and settle naturally into the stated END STATE." if seconds > 2 else ""
    sections = [
        ("FORMAT & STYLE", f"{aspect}; {seconds}s motion-video scene; {_visual_style(genre, visual_style)}; same episode design and actor scale."),
        ("CHARACTERS", cast_text + ". Fix exact face, hairstyle, wardrobe, props, voice and character identity across cuts."),
        ("SETTING & START STATE", f"{setting}. {start}. Visual and spatial reference: {visual}."),
        ("LIGHTING & COLOR", "Keep light direction, palette, and exposure continuous with adjacent scenes; distinct faces clearly visible; no crushed-black frames."),
        ("CAMERA", _one_line(scene.get("camera_motion"), 150) + ". Motivated, physically possible cinema camera movement; maintain screen direction and spatial geography."),
        ("TIMED ACTION", first + second + third + " " + summary),
        ("END STATE", end + ". Hold actor positions, hand-held objects, eye lines and set dressing for the next shot; never spontaneously reset."),
        ("AUDIO", _dialogue_audio(scene.get("dialogue_beats"), seconds, language, scene)),
        ("CONSTRAINTS", "Only the listed characters and events. Stable face, outfit, voices, props and camera orientation. No teleportation, new characters, frozen actors, random gestures, mismatched lip-sync, unrequested narration, subtitles, text or logos."),
    ]
    start_secs = (index - 1) * seconds
    header = f"========== SCENE_{index:03d} | TIMELINE {_clock(start_secs)}–{_clock(start_secs+seconds)} | GENERATE {seconds} SECONDS =========="
    return header + "\n" + "\n".join(f"{k}: {v}" for k, v in sections)


def export_episode(raw_plan, folder: Path, *, genre, visual_style, language, aspect, seconds=10):
    """Fail closed BEFORE provider calls; do not touch narration engine or Muse CLI."""
    _skill_files()
    scenes = raw_plan.get("scenes") or []
    if not scenes:
        raise RuntimeError("DRAMA_SKILL9_EMPTY_PLAN")
    cast = raw_plan.get("cast") or {}
    blocks = []
    warnings = []
    for index, scene in enumerate(scenes, 1):
        if int(scene.get("scene_number", 0)) != index:
            raise RuntimeError(f"DRAMA_SKILL9_SCENE_SEQUENCE: scene {index}")
        previous = scenes[index-2] if index > 1 else None
        raw_existing = str(scene.get("raw_9_fields") or "").strip()
        block = raw_existing or build_scene(scene, cast, previous, genre=genre, visual_style=visual_style,
                                             language=language, aspect=aspect, seconds=seconds, index=index)
        scene["raw_9_fields"] = block
        words = sum(len(str(b.get("text", "")).split()) for b in scene.get("dialogue_beats", []) if isinstance(b, dict))
        if words > seconds*3.5:
            warnings.append(f"SCENE_{index:03d}: {words} dialogue words in {seconds}s; manual speech pacing review")
        blocks.append(block)
    text = "\n\n".join(blocks) + "\n"
    spec = importlib.util.spec_from_file_location("_drama_skill9_validator", SKILL / "scripts" / "validate_prompts.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.validate(text, target_seconds=len(scenes)*seconds, aspect=aspect)
    report["branch"] = "multi_role_cinematic_drama_only"
    report["skill"] = "write-video-scene-prompts"
    report["scope"] = "TXT preflight, NOT rendered-video E2E"
    report["warnings"] = list(report.get("warnings") or []) + warnings
    if not report["pass"]:
        raise RuntimeError("DRAMA_SKILL9_PREFLIGHT_FAILED: " + json.dumps(report["errors"], ensure_ascii=False))
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for filename, data in (("scene_prompts_9_fields.txt", text),
                           ("scene_prompts_9_fields_qc.json", json.dumps(report, ensure_ascii=False, indent=2))):
        dest = folder / filename
        temp = dest.with_suffix(dest.suffix + ".tmp")
        temp.write_text(data, encoding="utf-8")
        os.replace(temp, dest)
    return report
