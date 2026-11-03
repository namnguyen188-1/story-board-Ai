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


def writing_rules(genre: str, visual_style: str = "auto") -> str:
    """Feed the REAL installed skill to the multi-role drama screenwriter with strict genre branch locking."""
    _skill_files()
    def read(name, limit):
        return (SKILL / name).read_text(encoding="utf-8-sig")[:limit]

    genre_clean = str(genre or "").lower().strip()
    style_clean = str(visual_style or "").lower().strip()

    is_cinema_live_action = (
        genre_clean in ("drama", "family_drama", "action", "mafia_thriller", "romance_melodrama", "western", "history", "documentary") or
        style_clean in ("color_cinematic", "cinematic_drama", "cinematic", "live_action")
    )

    if is_cinema_live_action and not (genre_clean == "animation" and style_clean == "color_animation"):
        branch_name = "BRANCH 2: CINEMATIC LIVE-ACTION DRAMA PIPELINE (Real Actors)"
        branch_mandate = (
            "STRICT GENRE LOCK - PRESTIGE LIVE-ACTION CINEMA ONLY:\n"
            "- Characters MUST be photorealistic living human actors with believable skin textures, wardrobe weight, and naturalistic spatial lighting.\n"
            "- Visceral interpersonal drama, subtextual acting, credible body weight, turn-taking dialogue.\n"
            "- ZERO TOLERANCE: Strictly FORBID 3D cartoon animation, anime, or stone statues!"
        )
    elif any(k in genre_clean for k in ("animation", "hoạt hình")) or any(k in style_clean for k in ("animation", "anime", "cartoon")):
        branch_name = "BRANCH 1: ANIMATION PIPELINE (3D CGI or 2D Anime)"
        branch_mandate = (
            "STRICT GENRE LOCK - ANIMATION ONLY:\n"
            "- Characters MUST be stylized animated figures (Pixar/Disney 3D or Ghibli/Ufotable 2D Anime).\n"
            "- Movement MUST use animation principles (anticipation, squash and stretch, expressive exaggeration).\n"
            "- ZERO TOLERANCE: Strictly FORBID photorealistic human skin, live-action actors, or marble statues!"
        )
    elif any(k in genre_clean for k in ("stoic", "khắc kỷ")) or any(k in style_clean for k in ("stoic", "statue")):
        branch_name = "BRANCH 3: STOIC PHILOSOPHY PIPELINE (Classical Greco-Roman Statues)"
        branch_mandate = (
            "STRICT GENRE LOCK - STOIC PHILOSOPHY ONLY:\n"
            "- Visuals MUST depict magnificent FULL-LENGTH classical marble and bronze statues of ancient philosophers from head to toe.\n"
            "- Ancient Roman/Greek architecture, Pantheon, museum lighting, chiaroscuro golden hour rays.\n"
            "- Screenplay is profound philosophical contemplation and existential truth, spoken with slow, dignified authority.\n"
            "- ZERO TOLERANCE: Strictly FORBID half-body busts, modern cartoons, or petty domestic arguments!"
        )
    elif any(k in genre_clean for k in ("whiteboard", "marker")) or any(k in style_clean for k in ("whiteboard", "marker")):
        branch_name = "BRANCH 4: WHITEBOARD & HAND-DRAWN EXPLAINER PIPELINE"
        branch_mandate = (
            "STRICT GENRE LOCK - WHITEBOARD & HAND-DRAWN ONLY:\n"
            "- Visuals MUST depict dynamic hand-drawn marker sketching on pure white whiteboard background (#ffffff) in the signature After Skool style.\n"
            "- DRAWING & SPEECH SYNCHRONICITY MANDATE: The speed and progression of the marker drawing MUST synchronize 1:1 with the spoken explanation. As the narrator speaks each phrase, the hand/marker illustrates that specific visual metaphor in real-time. NEVER rush the drawing; maintain a calm, pedagogical pacing matching speech tempo so viewers can easily comprehend.\n"
            "- TIMED ACTION partitions: 0.0s to T_end must describe marker drawing strokes emerging concurrently with speech beats."
        )
    else:
        branch_name = "BRANCH 2: CINEMATIC LIVE-ACTION DRAMA PIPELINE (Real Actors)"
        branch_mandate = (
            "STRICT GENRE LOCK - PRESTIGE LIVE-ACTION CINEMA ONLY:\n"
            "- Characters MUST be photorealistic living human actors with believable skin textures, wardrobe weight, and naturalistic spatial lighting.\n"
            "- Visceral interpersonal drama, subtextual acting, credible body weight, turn-taking dialogue.\n"
            "- ZERO TOLERANCE: Strictly FORBID 3D cartoon animation, anime, or stone statues!"
        )

    return (
        f"\n\n[AUTHENTIC GENRE PIPELINE BRANCH ACTIVATED: {branch_name}]\n"
        f"{branch_mandate}\n\n"
        "SELECTED VISUAL STYLE: " + _visual_style(genre, visual_style) + "\n"
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
        "Each 10-second shot: one motivated major action, 1-2 caused reactions, "
        "concise speech fitting 10 seconds (12-18 words maximum per scene).\n"
        "CANONICAL SKILL:\n" + read("SKILL.md", 2600) +
        "\nFIELD CONTRACT:\n" + read("references/FORMAT_CONTRACT.md", 1050) +
        "\nACTING:\n" + read("references/REALISTIC_ACTING.md", 2000) +
        f"\nGENRE BRANCH SPECIFICATION ({genre}):\n" + read("references/GENRES.md", 4500) +
        "\nMANDATORY MULTI-ROLE ASSET-FIRST OVERRIDE (only for this drama branch):\n" +
        read("references/MULTI_ROLE_ASSET_FIRST.md", 3500)
    )


def _one_line(v, limit=2200):
    s = re.sub(r"\s+", " ", str(v or "")).strip()
    for label in LABELS:
        s = re.sub(r"(?i)\b" + re.escape(label) + r":", "", s)
    return s[:limit].strip()


def _clock(seconds):
    return f"{seconds//60:02d}:{seconds%60:02d}"


def _visual_style(genre, visual_style):
    """Explicit Phong cách selection wins over broad Thể loại (incl. animation)."""
    selected = str(visual_style or "").lower().strip()
    genre_str = str(genre or "").lower().strip()

    if selected == "colored_marker":
        return ("Hand-drawn COLOR FELT-TIP MARKER illustration, bold multicolor marker strokes "
                "on a bright whiteboard, sequential ink drawing motion, 2D only; NO 3D CGI, NO live action")
    if selected == "hand_color":
        return ("Hand-drawn AND hand-colored 2D illustration animation: visible pencil/ink outlines, "
                "pigment/colored-pencil fills, charming drawn characters; NO 3D CGI, NO live action")
    if selected == "whiteboard":
        return ("Classic monochrome whiteboard hand-drawn animation: crisp black marker outlines "
                "on pure white board; limited black-and-white palette, NO 3D CGI, NO live action")
    if selected == "color_animation":
        return ("Premium stylized 3D CGI character animation with consistent sculpted models, "
                "costumes, expressive motion, Pixar and Disney 3D standard; NO live-action humans, NO statues")
    if selected in ("anime", "animation_2d", "2d_animation"):
        return ("Cinematic 2D illustrated anime animation with cel-shaded coloring, bold ink contours, "
                "Studio Ghibli aesthetic; NO 3D CGI, NO live action, NO statues")
    if selected == "color_cinematic":
        if any(k in genre_str for k in ("stoic", "statue", "marble", "khắc kỷ")):
            return ("Cinematic Greco-Roman classical world of monumental classical statues (16:9 widescreen). "
                    "Depicts magnificent full-length classical marble and bronze sculptures of ancient philosophers "
                    "standing and seated from head to toe with complete anatomical figures, weathered Carrara marble textures, "
                    "flowing classical draped togas extending to the feet, and grand ground-level ancient Roman architecture backdrop. "
                    "Deep atmospheric chiaroscuro lighting, volumetric rim light. Strictly full statues only, never half-body busts; sculpture remains inanimate.")
        return ("Full-color cinematic film aesthetics, naturalistic spatial lighting, "
                "credible live-action actors and physical performances; NO 3D cartoon rendering, NO statues")

    # Routing based on genre if visual_style is auto
    if any(k in genre_str for k in ("whiteboard",)):
        return _visual_style(genre, "whiteboard")
    if any(k in genre_str for k in ("marker",)):
        return _visual_style(genre, "colored_marker")
    if any(k in genre_str for k in ("anime", "2d", "manga")):
        return _visual_style(genre, "animation_2d")
    if any(k in genre_str for k in ("animation", "hoạt hình", "cgi")):
        return _visual_style(genre, "color_animation")
    if any(k in genre_str for k in ("stoic", "statue", "marble", "khắc kỷ")):
        return _visual_style(genre, "color_cinematic")
    return _visual_style(genre, "color_cinematic")


def _cast_lock(scene, cast):
    names = list(scene.get("characters_present") or [])
    if not names:
        names = [b.get("speaker") for b in scene.get("dialogue_beats", []) if isinstance(b, dict)]
    result = []
    sc_num = scene.get("scene_number", 1) if isinstance(scene, dict) else 1
    for name in dict.fromkeys(str(n) for n in names if n):
        if name.lower() in ("narrator", "người dẫn chuyện", "dẫn chuyện"):
            continue
        prof = (cast or {}).get(name, {}) if isinstance(cast, dict) else {}
        if not isinstance(prof, dict):
            prof = {}
        
        # Check for act-specific wardrobe
        wardrobe_by_act = prof.get("wardrobe_by_act") or {}
        act_wardrobe = ""
        if wardrobe_by_act and isinstance(wardrobe_by_act, dict):
            if sc_num <= 24:
                act_wardrobe = wardrobe_by_act.get("act_1", "")
            elif sc_num <= 150:
                act_wardrobe = wardrobe_by_act.get("act_2", "")
            else:
                act_wardrobe = wardrobe_by_act.get("act_3", "")

        appearance = prof.get("appearance_lock") or prof.get("appearance") or ""
        try:
            from studio.cinematic_engine.character_isolator import extract_single_character_description
        except ImportError:
            try:
                from cinematic_engine.character_isolator import extract_single_character_description
            except ImportError:
                def extract_single_character_description(txt, n): return txt
        clean_app = extract_single_character_description(appearance, name).strip()
        
        # Avoid duplicate "Name: Name:"
        prefix = f"{name}:"
        if clean_app.lower().startswith(prefix.lower()):
            clean_app = clean_app[len(prefix):].strip()
            
        if act_wardrobe and "wardrobe strictly locked by act" in clean_app.lower():
            clean_app = re.sub(r'Wardrobe strictly locked by act:.*', act_wardrobe, clean_app, flags=re.I).strip()
        elif act_wardrobe:
            clean_app = f"{clean_app} {act_wardrobe}".strip()

        # Fallback for secondary characters to ensure zero bare names
        if not clean_app:
            clean_app = f"Authentic living human actor portraying {name}, distinct naturalistic facial features, locked wardrobe and cinematic lighting."

        # Generous limit to preserve full DNA and wardrobe without truncating mid-sentence
        clean_app_oneline = _one_line(clean_app, 1200)
        primary_char = str(scene.get("primary_focus_character") or "").strip()
        # Fallback to speaker if not explicitly defined
        if not primary_char:
            speakers = [b.get("speaker") for b in scene.get("dialogue_beats", []) if isinstance(b, dict)]
            if speakers:
                primary_char = str(speakers[0]).strip()
        
        if primary_char and name.lower() == primary_char.lower():
            role_tag = "[PRIMARY FOCUS ACTOR] "
        elif len(names) > 1:
            role_tag = "[SUPPORTING/REACTION ACTOR] "
        else:
            role_tag = ""
        result.append(f"{role_tag}{name}: {clean_app_oneline}".strip())
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
    """Produce exactly nine fields; I2V image assets travel in a separate binding JSON."""
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

    # Strictly synchronize TIMED ACTION with dialogue beats and character turns
    beats_list = [b for b in (scene.get("dialogue_beats") or []) if isinstance(b, dict) and str(b.get("text") or "").strip()]
    if beats_list:
        usable = max(0.4, seconds - 1.0)
        step = usable / len(beats_list)
        timed_action_parts = []
        timed_action_parts.append(f"0.0–0.5s: Camera establishes shot and characters locked in spatial positions.")
        for i, beat in enumerate(beats_list):
            b_begin, b_end = 0.5 + i * step, min(seconds - 0.3, 0.5 + (i + 1) * step)
            speaker = _one_line(beat.get("speaker"), 100) or "Speaker"
            b_act = _one_line(beat.get("action"), 250) or f"{speaker} delivers dialogue with cinematic gravity"
            other_chars = [c for c in scene.get("characters_present", []) if c != speaker]
            react_note = f" Other characters ({', '.join(other_chars)}) maintain credible listening eye-lines without speaking." if other_chars else ""
            timed_action_parts.append(f"{b_begin:.1f}–{b_end:.1f}s: {speaker} acts: {b_act}.{react_note}")
        last_end = min(seconds - 0.3, 0.5 + len(beats_list) * step)
        if last_end < seconds:
            timed_action_parts.append(f"{last_end:.1f}–{seconds:.1f}s: Complete motivated action and settle into END STATE. {summary}")
        timed_action_text = " ".join(timed_action_parts)
    else:
        first = f"0.0–{min(2,seconds):.1f}s: A visible cause triggers attention and a purposeful reaction. "
        second = f"{min(2,seconds):.1f}–{max(2,seconds-2):.1f}s: {action}. Characters act within the established space with credible body weight and eye-lines. " if seconds > 2 else ""
        third = f"{max(2,seconds-2):.1f}–{seconds:.1f}s: Complete the motivated action and settle naturally into the stated END STATE." if seconds > 2 else ""
        timed_action_text = first + second + third + " " + summary

    # Enrich camera motion with Hollywood master shot grammar if primitive
    cam_raw = _one_line(scene.get("camera_motion"), 350)
    if not cam_raw or len(cam_raw) < 45 or any(k in cam_raw.lower() for k in ["slow_zoom", "tight_macro", "wide_establishing", "dutch_angle", "camera"]):
        try:
            from cinematic_engine.drama_cinematography import enrich_scene_camera_direction
            shot_meta = enrich_scene_camera_direction(
                scene=scene,
                scene_number=index,
                total_scenes=scene.get("total_scenes") or 25,
                genre=genre
            )
            cam_raw = shot_meta["camera_motion"]
        except Exception:
            pass

    sections = [
        ("FORMAT & STYLE", f"{aspect}; {seconds}s motion-video scene; {_visual_style(genre, visual_style)}; same episode design and actor scale."),
        ("CHARACTERS", cast_text + ". Fix exact face, hairstyle, wardrobe, props, voice and character identity across cuts."),
        ("SETTING & START STATE", f"{setting}. {start}. Visual and spatial reference: {visual}."),
        ("LIGHTING & COLOR", "Keep light direction, palette, and exposure continuous with adjacent scenes; distinct faces clearly visible; no crushed-black frames."),
        ("CAMERA", cam_raw + ". Motivated, physically possible cinema camera movement; maintain screen direction and spatial geography."),
        ("TIMED ACTION", timed_action_text),
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
        from .drama_auto_repair import sanitize_forbidden_words
        block = sanitize_forbidden_words(block)
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
