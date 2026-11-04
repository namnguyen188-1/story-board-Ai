"""Bridge installed skills into Storyboard AI idea-mode.

Routes dynamically by genre and format:
- Shorts (9:16, <=58s): write-viral-shorts-prompts
- Stoic: Proven benchmark configuration with write-video-scene-prompts / Stoic Cold Open (100% stable)
- Cinematic Drama: write-video-scene-prompts (9-field acting contract)
- Narrative / Documentary / History: write-narrative-scene-prompts (1 voiceover, pure 40-80w image prompt)

No edits to locked-script/clone source. No external API calls.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / ".agents" / "skills"
SKILL_ROOT = SKILLS_DIR / "write-video-scene-prompts"
FIELDS = ("FORMAT & STYLE", "CHARACTERS", "SETTING & START STATE",
          "LIGHTING & COLOR", "CAMERA", "TIMED ACTION",
          "END STATE", "AUDIO", "CONSTRAINTS")


def resolve_skill_name(genre: str = "documentary", production_mode: str = "auto",
                       aspect_ratio: str = "16:9", is_short: bool = False) -> str:
    """Resolve the canonical skill for a given genre, mode, and aspect ratio."""
    g = str(genre or "documentary").strip().lower()
    pm = str(production_mode or "auto").strip().lower()

    # 1. Short-form (strictly 9:16, explicit shorts genre, or explicit is_short)
    if is_short or aspect_ratio == "9:16" or g.endswith("_shorts"):
        return "write-viral-shorts-prompts"

    # 2. Stoic benchmark branch (long-form 16:9 benchmark stable branch, keep 100% intact)
    if g == "stoic":
        return "write-video-scene-prompts"

    # 3. Cinematic Drama (multi-role drama)
    if pm == "cinematic_drama" or g in ("drama", "family_drama", "theatrical_drama", "mafia_thriller",
                                        "romance_melodrama", "psychological_horror", "western", "action"):
        return "write-video-scene-prompts"

    # 4. Narrative Storytelling / Documentary / History (1-voice narrative)
    return "write-narrative-scene-prompts"


def installed_skill(skill_name: str = "write-video-scene-prompts") -> dict:
    """Load installed skill contents and digest.

    Defaults to write-video-scene-prompts to ensure 100% backward compatibility.
    """
    target_root = SKILLS_DIR / skill_name
    if not target_root.is_dir():
        raise RuntimeError(f"SKILL_MISSING: {skill_name}")

    if skill_name == "write-video-scene-prompts" or target_root == SKILL_ROOT:
        required = ("SKILL.md", "references/FORMAT_CONTRACT.md",
                    "references/REALISTIC_ACTING.md", "references/QC.md",
                    "references/GENRES.md", "scripts/validate_prompts.py")
        missing = [p for p in required if not (target_root / p).is_file()]
        if missing:
            raise RuntimeError("FILM_SKILL_MISSING: " + ", ".join(missing))
        contents = {p: (target_root / p).read_text(encoding="utf-8-sig") for p in required[:-1]}
        digest = hashlib.sha256("".join(contents.values()).encode("utf-8")).hexdigest()
        return {"contents": contents, "sha256": digest, "root": str(target_root), "name": "write-video-scene-prompts"}

    # Other skills (write-narrative-scene-prompts, write-viral-shorts-prompts, etc.)
    skill_md = target_root / "SKILL.md"
    if not skill_md.is_file():
        raise RuntimeError(f"SKILL_MISSING: {skill_name}/SKILL.md")
    contents = {"SKILL.md": skill_md.read_text(encoding="utf-8-sig")}
    ref_dir = target_root / "references"
    if ref_dir.is_dir():
        for f in ref_dir.glob("*.md"):
            contents[f"references/{f.name}"] = f.read_text(encoding="utf-8-sig")
    digest = hashlib.sha256("".join(contents.values()).encode("utf-8")).hexdigest()
    return {"contents": contents, "sha256": digest, "root": str(target_root), "name": skill_name}


def skill_prompt(genre: str = "documentary", production_mode: str = "auto",
                 aspect_ratio: str = "16:9", is_short: bool = False) -> str:
    """Generate the authoritative skill prompt based on the resolved genre branch."""
    skill_name = resolve_skill_name(genre, production_mode, aspect_ratio, is_short)
    pack = installed_skill(skill_name)
    contents = pack["contents"]

    if skill_name == "write-viral-shorts-prompts":
        return (
            f"\nINSTALLED SKILL: write-viral-shorts-prompts. Skill SHA256: {pack['sha256']}\n"
            f"AUTHORITATIVE SHORTS WRITING RULES (9:16 VERTICAL, DURATION < 59 SECONDS):\n"
            f"{contents['SKILL.md'][:6500]}\n"
            "\nSTRICT COMPATIBILITY:\n"
            "- Output MUST remain valid JSON with 'scenes' array matching existing schema: "
            "(scene_number, summary, narration, description, visual_setup, text_overlay).\n"
            "- Pacing: 2.0s to 3.5s per scene.\n"
            "- Spoken narration: Concise, punchy (~2.5 words/second).\n"
            "- Scene 1: Must be Act 1 Super Hook (curiosity-gap audio hook + striking visual hook).\n"
            "- Final Scene: Must be Act 3 Climax & Seamless Infinite Loop connecting to Scene 1.\n"
            "- Visual framing: 9:16 vertical safe zone framing; keep subject centered.\n"
        )
    elif skill_name == "write-narrative-scene-prompts":
        return (
            f"\nINSTALLED SKILL: write-narrative-scene-prompts. Skill SHA256: {pack['sha256']}\n"
            f"AUTHORITATIVE NARRATIVE RULES (1-VOICE STORYTELLING & PURE IMAGE PROMPTS):\n"
            f"{contents['SKILL.md'][:6500]}\n"
            "\nSTRICT COMPATIBILITY:\n"
            "- Output MUST remain valid JSON with 'scenes' array matching existing schema: "
            "(scene_number, summary, narration, description, visual_setup, text_overlay).\n"
            "- Spoken line ('narration'): Single voiceover narrator (thuyết minh), eloquent and immersive.\n"
            "- Visual description ('description' & 'visual_setup'): PURE VISUAL PROMPT in English (40-80 words). "
            "Describe the subject, camera angle, atmospheric lighting, and details consistent with the selected visual style. "
            "DO NOT include dialogue lines, acting cues, or 9-field labels inside the visual prompt!\n"
            "- Dynamic visual variety: Alternate between wide establishing landscapes, aerial views, and detailed close-ups.\n"
            "- Visual continuity: Align faithfully with the topic and Series Bible.\n"
        )
    else:
        # write-video-scene-prompts (used for drama and stoic benchmark)
        return (
            "\nINSTALLED SKILL: write-video-scene-prompts. Skill SHA256: " + pack["sha256"] +
            "\nAUTHORITATIVE WRITING RULES (for ORIGINAL IDEA mode only):\n" +
            contents["SKILL.md"][:7500] +
            "\nREAL ACTING:\n" + contents.get("references/REALISTIC_ACTING.md", "")[:3500] +
            "\nGENRE RULES (" + str(genre) + "):\n" + contents.get("references/GENRES.md", "")[:2400] +
            "\nSTRICT COMPATIBILITY: The external scene export keeps the exact nine labels "
            "and continuous scene numbering. The application LLM reply MUST REMAIN its existing "
            "JSON schema with scenes, scene_number, summary, narration, description, visual_setup, "
            "text_overlay, so downstream images/TTS/subtitles remain compatible. "
            "Write purposeful scene actions and keep the story and characters continuous. "
            "Don't introduce a reference-image dependency. Don't fabricate source-video details.\n"
        )


def _clean(value, fallback="", limit=1200) -> str:
    result = str(value or fallback).replace("\r", " ").replace("\n", " ").strip()
    result = re.sub(r"\s+", " ", result)
    # Embedded label-looking prefixes must not create an extra field.
    result = re.sub(r"(?i)\b(?:FORMAT & STYLE|CHARACTERS|SETTING & START STATE|LIGHTING & COLOR|CAMERA|TIMED ACTION|END STATE|AUDIO|CONSTRAINTS):", "", result)
    result = re.sub(r'(?i)\bweapons?\b', 'equipment', result)
    result = re.sub(r'(?i)\b(?:guns?|pistols?|rifles?|firearms?|sidearms?|ammunition)\b', 'flashlights', result)
    result = re.sub(r'(?i)\b(?:knives|knife|knifing|daggers?|swords?|blades?)\b', 'tools', result)
    return result[:limit].strip()


def _clock(seconds: int) -> str:
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _validate_narrative_export(scenes: list, length: int, is_short: bool) -> list:
    """Check only measurable text requirements; do not claim content or render QC."""
    errors = []
    if is_short and len(scenes) * length > 58:
        errors.append("shorts_total_duration_exceeds_58_seconds")
    for i, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            errors.append(f"scene_{i}:invalid_scene")
            continue
        if not str(scene.get("narration") or "").strip():
            errors.append(f"scene_{i}:missing_narration")
        description = str(scene.get("description") or scene.get("visual_setup") or scene.get("summary") or "").strip()
        if not description:
            errors.append(f"scene_{i}:missing_visual_description")
    return errors


def export_idea_scenes(scenes: list, bible: dict, scene_seconds: int,
                       width: int, height: int,
                       genre: str = "documentary",
                       production_mode: str = "auto",
                       title: str = "") -> tuple[str, dict]:
    """Export scene contract artifact and produce QC report matching the active skill."""
    length = int(scene_seconds)
    if length < 1 or length > 60:
        raise ValueError("Unsupported skill scene duration")
    aspect = "9:16" if height > width else "16:9"
    is_short = (aspect == "9:16")
    if not scenes:
        raise ValueError("No generated scenes to export")

    skill_name = resolve_skill_name(genre, production_mode, aspect, is_short)
    pack = installed_skill(skill_name)

    if skill_name == "write-narrative-scene-prompts":
        blocks = [
            "# KỊCH BẢN PHÂN CẢNH KỂ CHUYỆN & THUYẾT MINH (16:9)",
            f"- **Tác phẩm**: {title or 'Series Kể Chuyện'}",
            f"- **Thể loại**: {genre}",
            f"- **Tỷ lệ**: 16:9 Ngang",
            f"- **Thời lượng mỗi cảnh**: {length}s (Tổng: {_clock(len(scenes)*length)})",
            "- **Định dạng**: 1 giọng đọc thuyết minh + Prompt ảnh thuần túy (40–80 từ tiếng Anh)",
            "\n" + "=" * 70 + "\n"
        ]
        for idx, scene in enumerate(scenes, 1):
            beginning, ending = (idx - 1) * length, idx * length
            narration = _clean(scene.get("narration"), "", 1400)
            desc = _clean(scene.get("description") or scene.get("visual_setup") or scene.get("summary"), "", 650)
            camera = _clean(scene.get("camera"), "Ken Burns smooth zoom in with subtle drift")

            scene_block = (
                f"### SCENE {idx:03d} ({_clock(beginning)} – {_clock(ending)})\n"
                f"- **IMAGE PROMPT** (Tiếng Anh, 40–80 từ cho AI tạo ảnh):\n"
                f"  {desc}\n"
                f"- **THUYẾT MINH / VOICEOVER** (Dành cho TTS & Phụ đề):\n"
                f"  {narration}\n"
                f"- **CAMERA MOTION**: {camera}\n"
                f"- **DURATION**: {length}s"
            )
            blocks.append(scene_block)

        text = "\n\n".join(blocks) + "\n"
        errors = _validate_narrative_export(scenes, length, is_short=False)
        report = {
            "pass": not errors,
            "errors": errors,
            "warnings": ["structural checks only; content and rendered media not verified"],
            "scene_count": len(scenes),
            "total_seconds": len(scenes) * length,
            "skill_name": "write-narrative-scene-prompts",
            "skill_sha256": pack["sha256"],
            "validation_scope": "structural_text_checks_only"
        }
        return text, report

    elif skill_name == "write-viral-shorts-prompts":
        blocks = [
            "# THÔNG TIN DỰ ÁN YOUTUBE SHORTS (9:16)",
            f"- **Tên Short**: {title or 'Viral Short'}",
            f"- **Thể loại**: {genre}",
            f"- **Tỷ lệ**: 9:16 Dọc",
            f"- **Thời lượng mỗi cảnh**: {length}s (Tổng: {_clock(len(scenes)*length)})",
            "- **Cấu trúc**: 3 Hồi Chuẩn (Siêu Hook 3s - Thân bài leo thang - Cao trào & Infinite Loop)",
            "\n" + "=" * 70 + "\n"
        ]
        for idx, scene in enumerate(scenes, 1):
            beginning, ending = (idx - 1) * length, idx * length
            narration = _clean(scene.get("narration"), "", 1400)
            desc = _clean(scene.get("description") or scene.get("visual_setup") or scene.get("summary"), "", 650)
            text_overlay = _clean(scene.get("text_overlay"), "")
            act = "ACT 1: SIÊU HOOK" if idx == 1 else ("ACT 3: CAO TRÀO & INFINITE LOOP" if idx == len(scenes) else "ACT 2: THÂN BÀI / LEO THANG")

            scene_block = (
                f"### SCENE {idx:03d} ({_clock(beginning)} – {_clock(ending)}) [{act}]\n"
                f"- **IMAGE PROMPT** (9:16 Safe Zone, Tiếng Anh 40–60 từ):\n"
                f"  {desc}\n"
                f"- **THUYẾT MINH / VOICEOVER** (Súc tích, nhịp nhanh):\n"
                f"  {narration}\n"
                f"- **TEXT OVERLAY (VÙNG AN TOÀN)**: {text_overlay}\n"
                f"- **DURATION**: {length}s"
            )
            blocks.append(scene_block)

        text = "\n\n".join(blocks) + "\n"
        errors = _validate_narrative_export(scenes, length, is_short=True)
        report = {
            "pass": not errors,
            "errors": errors,
            "warnings": ["structural checks only; content and rendered media not verified"],
            "scene_count": len(scenes),
            "total_seconds": len(scenes) * length,
            "skill_name": "write-viral-shorts-prompts",
            "skill_sha256": pack["sha256"],
            "validation_scope": "structural_text_checks_only"
        }
        return text, report

    else:
        # write-video-scene-prompts (used for drama and stoic benchmark)
        source = SKILL_ROOT / "scripts" / "validate_prompts.py"
        spec = importlib.util.spec_from_file_location("_studio_skill_validator", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        chars = bible.get("characters") if isinstance(bible, dict) else []
        profiles = []
        for c in (chars or [])[:5]:
            if isinstance(c, dict):
                profiles.append(_clean(" ".join(str(c.get(k, "")) for k in
                                      ("name", "stable_appearance", "appearance",
                                       "attire", "personality", "immutable_rules")), limit=650))
        stable_cast = "; ".join(p for p in profiles if p) or "Characters as established in the series bible"
        atmosphere = _clean(bible.get("visual_style") or bible.get("world") if isinstance(bible, dict) else "", "Consistent cinematic lighting and color", 350)
        blocks = []
        for idx, scene in enumerate(scenes, 1):
            if not isinstance(scene, dict) or int(scene.get("scene_number", -1)) != idx:
                raise ValueError("Non-continuous scene number in skill export")
            beginning, ending = (idx - 1) * length, idx * length
            summary = _clean(scene.get("summary"), "Continue the scene's meaningful action", 430)
            desc = _clean(scene.get("description"), summary, 650)
            visual = _clean(scene.get("visual_setup"), desc, 400)
            narration = _clean(scene.get("narration"), "", 1400)
            fields = (
                ("FORMAT & STYLE", f"{aspect} cinematic sequence; preserve series art style, framing and subject proportions."),
                ("CHARACTERS", stable_cast),
                ("SETTING & START STATE", visual + "; the characters and props start where the prior scene left them."),
                ("LIGHTING & COLOR", atmosphere),
                ("CAMERA", _clean(scene.get("camera"), "Motivated stable cinematic shot with natural framing")),
                ("TIMED ACTION", f"0.0–{length:.1f}s: {summary}. Visual behavior: {desc}. Characters respond naturally to events; no random gestures."),
                ("END STATE", f"The visible action ends naturally; preserve eye-lines, prop ownership and relative positioning for the next scene. {summary}"),
                ("AUDIO", f'Narrator voiceover, 0.0–{length:.1f}s: "{narration}"' if narration else f"Silent ambient sound for {length} seconds; no spoken dialogue."),
                ("CONSTRAINTS", "Keep identity, age, attire and voice stable. No face morphing, frozen acting, accidental subtitles, overlays or logos. Do not invent a new story."),
            )
            header = f"========== SCENE_{idx:03d} | TIMELINE {_clock(beginning)}–{_clock(ending)} | GENERATE {length} SECONDS =========="
            blocks.append(header + "\n" + "\n".join(f"{key}: {value}" for key, value in fields))
        text = "\n\n".join(blocks) + "\n"
        report = module.validate(text, target_seconds=len(scenes)*length, aspect=aspect)
        report["skill_sha256"] = pack["sha256"]
        report["skill_name"] = "write-video-scene-prompts"
        report["validation_scope"] = "text_only_not_render_qc"
        if not report["pass"]:
            print(f"[FILM_SKILL_QC_WARNING] {report['errors'][:4]}", flush=True)
        return text, report
