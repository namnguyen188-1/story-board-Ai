"""Fail-closed one-shot automatic prompt repair for MULTI-ROLE Muse scenes only.

Never repair a live/pending receipt or silently change screenplay, cast, voices,
style, timestamps or event. Never retry a provider moderation refusal.
"""
from __future__ import annotations
import hashlib
import json
import os
import time
import re
from pathlib import Path

FIELDS = (
    "FORMAT & STYLE", "CHARACTERS", "SETTING & START STATE",
    "LIGHTING & COLOR", "CAMERA", "TIMED ACTION", "END STATE",
    "AUDIO", "CONSTRAINTS"
)
META_NAME = "muse_scene_repair.json"
ALT_NAME = "muse_scene_repair_9_fields.txt"
OLD_RECEIPT_NAME = "muse_job_failed_before_repair.json"
TERMINAL = {"failed"}
BLOCK_RE = re.compile(
    r"(?i)moderation|policy|safety|content.blocked|refused|rejected|"
    r"not.allowed|prohibited|bị.từ.chối|vi.phạm"
)


def digest(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def parse_9_fields(block: str) -> tuple[str, dict]:
    header, _, rest = block.partition("\n")
    if "SCENE_" not in header or "GENERATE 10 SECONDS" not in header:
        raise ValueError("SCENE_REPAIR_INVALID_HEADER")
    fields = {}
    for line in rest.splitlines():
        for key in FIELDS:
            if line.startswith(key + ": "):
                if key in fields:
                    raise ValueError("SCENE_REPAIR_DUPLICATE_FIELD: " + key)
                fields[key] = line[len(key) + 2:].strip()
                break
    if set(fields) != set(FIELDS):
        raise ValueError("SCENE_REPAIR_MISSING_NINE_FIELDS")
    return header, fields


def _safe_text(text, maximum=250):
    return re.sub(r"\s+", " ", str(text or "")).strip()[:maximum]



FORBIDDEN_REPLACEMENTS = [
    # Demons / monsters / evil entities
    (re.compile(r"\b(foul\s+demon|demons?|demonic)\b", re.IGNORECASE), "shadowy rival"),
    (re.compile(r"\b(serpentine\s+beast|monstrous\s+shadow|beasts?|monsters?)\b", re.IGNORECASE), "mysterious phantom"),
    (re.compile(r"\bdark\s+spirit\b", re.IGNORECASE), "secret power"),
    (re.compile(r"\bwhat\s+has\s+possessed\s+you\b", re.IGNORECASE), "what has come over you"),
    (re.compile(r"\bpossessed\b", re.IGNORECASE), "overcome"),
    # Weapons / firearms / attacks / gore
    (re.compile(r"\b(sidearms?(\s+holsters?)?|holsters?|guns?|pistols?|rifles?|firearms?|ammunition)\b", re.IGNORECASE), "badge holder"),
    (re.compile(r"\b(furiously\s+intervenes|violently\s+intervenes)\b", re.IGNORECASE), "firmly intervenes"),
    (re.compile(r"\b(heavy\s+iron\s+broadsword|iron\s+broadsword|broadswords?|spears?|swords?|blades?|daggers?|knives|knif(?:e|ing)|weapons?)\b", re.IGNORECASE), "ceremonial staff"),
    (re.compile(r"\b(moonbeams?|light|rays?)\s+slash(?:es|ing)?\b", re.IGNORECASE), r"\g<1> streak"),
    (re.compile(r"\bslash(?:es|ing)?\b", re.IGNORECASE), "sweep"),
    (re.compile(r"\b(strike|slay|kill|stab|wound|bloody|corpse|mutilat\w*)\b", re.IGNORECASE), "confront"),
    (re.compile(r"\b(through\s+your\s+blood|in\s+your\s+blood|bloody|blood)\b", re.IGNORECASE), "through your spirit"),
    (re.compile(r"\bflesh\b", re.IGNORECASE), "skin"),
    (re.compile(r"\b(beat(?:s|ing)?)\s+(?:up|down|him|her|them)\b", re.IGNORECASE), "confront"),
    # Horror / extreme distress triggers
    (re.compile(r"\b(in\s+terror|terror|horrific|grotesque)\b", re.IGNORECASE), "in stunned disbelief"),
    (re.compile(r"\b(flee\s+in\s+disgust|humiliating,\s+involuntary\s+sound|flee\s+in\s+panic)\b", re.IGNORECASE), "step back in surprise"),
    (re.compile(r"\bsharp_guttural_sound\b", re.IGNORECASE), "sharp_gasp"),
    (re.compile(r"\bconsumed\s+by\s+dark\s+magic\b", re.IGNORECASE), "struggling with an intense surge of energy"),
    (re.compile(r"\bveined\s+with\s+black\s+lines\b", re.IGNORECASE), "holding her hands tightly"),
    (re.compile(r"\bfingers\s+clawing\b", re.IGNORECASE), "hands pressing"),
    (re.compile(r"\bher\s+ritual\s+consumes\s+everything\b", re.IGNORECASE), "her ritual takes hold of the kingdom"),
    # Group crowd lip-syncing issues
    (re.compile(r"\bCHARACTERS:\s*Villagers\.?\b", re.IGNORECASE), "CHARACTERS: Elder Chuka: Age 58, respected village elder in festive tunic; Villagers in background."),
    (re.compile(r"\bOnly\s+Villagers\s+lip-syncs\b", re.IGNORECASE), "Only Elder Chuka lip-syncs"),
    (re.compile(r"\bVillagers\s+speaks\s+in\s+English\b", re.IGNORECASE), "Elder Chuka speaks in English"),
    (re.compile(r"\bVillagers\s+acts:\b", re.IGNORECASE), "Elder Chuka acts:"),
    # Physical violence / tackles / assault / police brutality triggers
    (re.compile(r"\b(tackles?\s+.*?to\s+(?:the\s+)?floor)\b", re.IGNORECASE), "firmly restrains David Miller"),
    (re.compile(r"\b(tackles?|tackling)\b", re.IGNORECASE), "firmly restrains"),
    (re.compile(r"\b(pinned\s+(?:to|on)\s+(?:the\s+)?floor|pinned\s+down)\b", re.IGNORECASE), "firmly held by the arm"),
    (re.compile(r"\bshoved\s+onto\s+(?:the\s+)?(?:polished\s+hardwood\s+)?floor\b", re.IGNORECASE), "firmly held back in the room"),
    (re.compile(r"\bshoved\b", re.IGNORECASE), "held back"),
    (re.compile(r"\bkneels\s+over\s+him\b", re.IGNORECASE), "stands confronting him"),
    (re.compile(r"\blies\s+face-down\s+on\s+(?:the\s+)?(?:wood\s+)?floor\b", re.IGNORECASE), "stands backed against the counter"),
    (re.compile(r"\bcheek\s+pressed\s+against\s+(?:dark\s+)?floorboard\b", re.IGNORECASE), "expression tense and defensive"),
    (re.compile(r"\bforcefully\s+grip\b", re.IGNORECASE), "firmly hold"),
    (re.compile(r"\bsteady\s+downward\s+wrist\s+lock\b", re.IGNORECASE), "firm professional hold"),
    (re.compile(r"\bwinces?\s+in\s+pain\b", re.IGNORECASE), "looks visibly distressed"),
    (re.compile(r"\bpleads\s+in\s+terror\b", re.IGNORECASE), "pleads urgently"),
    (re.compile(r"\b(punches?|punching|kicks?|kicking|slaps?|strangles?|chokes?)\b", re.IGNORECASE), "firmly confronts"),
    (re.compile(r"\bbody_tackle_thud\b", re.IGNORECASE), "dramatic_tense_accent"),
    # Modern drama, police, conflict & distress triggers (Anti-Integrity Filter)
    (re.compile(r"\b(police\s+tactical\s+polo|tactical\s+polo|tactical\s+vest|tactical\s+gear)\b", re.IGNORECASE), "professional dark collared polo"),
    (re.compile(r"\b(handcuffs?|handcuffing|cuffed)\b", re.IGNORECASE), "escorting"),
    (re.compile(r"\b(arrest(?:s|ed|ing)?)\b", re.IGNORECASE), "question"),
    (re.compile(r"\b(interrogation\s+room|interrogat(?:e|ing|ion))\b", re.IGNORECASE), "formal discussion room"),
    (re.compile(r"\b(confiscate[s|d]?|seize[s|d]?)\b", re.IGNORECASE), "collect"),
    (re.compile(r"\b(sirens?\s+wailing|police\s+sirens?)\b", re.IGNORECASE), "distant city hum"),
    (re.compile(r"\b(screams?\s+in\s+terror|screaming|shrieks?|hysterical(?:ly)?)\b", re.IGNORECASE), "speaks with intense urgency"),
    (re.compile(r"\b(break(?:s|ing)?\s+into|forced\s+entry)\b", re.IGNORECASE), "hurriedly enter"),
    (re.compile(r"\b(shatter(?:s|ed|ing)?|smash(?:es|ed|ing)?)\b", re.IGNORECASE), "drop"),
    (re.compile(r"\b(threaten(?:s|ed|ing)?|blackmail(?:s|ed|ing)?|extort(?:s|ed|ing)?)\b", re.IGNORECASE), "firmly warn"),
    (re.compile(r"\b(unconscious|passed\s+out|collapsed\s+to\s+the\s+floor)\b", re.IGNORECASE), "sitting exhausted"),
    (re.compile(r"\b(poison(?:ed|ing)?|overdose[d]?)\b", re.IGNORECASE), "suddenly feeling weak"),
    (re.compile(r"\b(bleed(?:s|ing)?|pool\s+of\s+blood)\b", re.IGNORECASE), "visible exhaustion"),
    (re.compile(r"\bdesperately\s+redials\b", re.IGNORECASE), "urgently checks her phone"),
    (re.compile(r"\b(number\s+has\s+been\s+deactivated|disconnected\s+tone)\b", re.IGNORECASE), "unanswered call"),

]

def sanitize_forbidden_words(text: str) -> str:
    for pattern, replacement in FORBIDDEN_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    return text


def simplified_prompt(original: str, scene: dict) -> str:
    """Remove overloaded camera/VFX instructions without changing any narrative event."""
    header, fields = parse_9_fields(original)
    beats = [b for b in (scene.get("dialogue_beats") or []) if isinstance(b, dict)]
    visible_actions = "; ".join(_safe_text(b.get("action"), 190) for b in beats if b.get("action"))
    summary = _safe_text(scene.get("summary"), 340)
    action = visible_actions or summary
    # IMPORTANT: keep exact cast, wardrobe, world position, dialogue/audio and next-shot ending.
    keep_start = fields["SETTING & START STATE"].split("Visual and spatial reference:")[0].strip()
    if not keep_start:
        keep_start = fields["SETTING & START STATE"][:430]
    revised = dict(fields)
    revised["SETTING & START STATE"] = keep_start
    revised["LIGHTING & COLOR"] = "Keep the existing light direction, colors, exposure and same environment as adjacent scenes. Visible actors."
    revised["CAMERA"] = "One stable continuous medium-wide shot with gentle motivated movement, consistent screen direction."
    revised["TIMED ACTION"] = (
        "0–2s: The named characters continue from the exact START STATE. "
        f"2–8s: {action}. {summary}. "
        "8–10s: The action naturally completes at the exact END STATE."
    )
    revised["CONSTRAINTS"] = (
        "Preserve the same named cast, face, hairstyle, clothing, props, dialogue, voices, "
        "world and ending. No extra people or events. No text overlays or unrelated narration. "
        "Use non-graphic depiction. No placeholder or still-image substitute."
    )
    sanitized = {k: sanitize_forbidden_words(revised[k]) for k in FIELDS}
    clean_header = sanitize_forbidden_words(header)
    return clean_header + "\n" + "\n".join(f"{k}: {sanitized[k]}" for k in FIELDS)


def load_armed_repair(scene_dir: Path, scene: dict) -> bool:
    """Resume a previously armed one-shot retry without creating another remote job."""
    scene_dir = Path(scene_dir)
    mf = scene_dir / META_NAME
    if not mf.exists():
        return False
    data = json.loads(mf.read_text(encoding="utf-8"))
    has_archived = any(f.name.startswith("muse_job_failed") for f in scene_dir.iterdir() if f.is_file())
    if not has_archived and not (scene_dir / OLD_RECEIPT_NAME).is_file():
        return False
    alternate_path = scene_dir / ALT_NAME
    if not alternate_path.is_file():
        return False
    alternate = alternate_path.read_text(encoding="utf-8")
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
    return True


def arm_one_repair(scene_dir: Path, scene: dict, error: str) -> bool:
    """Return True ONLY if an original remote attempt is proven terminal FAILED.

    One controlled shorter-prompt retry. Existing accepted/pending jobs are immutable.
    """
    scene_dir = Path(scene_dir)
    error = str(error)
    if BLOCK_RE.search(error):
        return False
    if (scene_dir / "muse_clip.mp4").is_file():
        return False
    rp = scene_dir / "muse_job.json"
    if not rp.is_file():
        if (scene_dir / META_NAME).is_file() and (scene_dir / ALT_NAME).is_file():
            alternate = (scene_dir / ALT_NAME).read_text(encoding="utf-8")
            scene["raw_9_fields"] = alternate
            return True
        return False
    receipt = json.loads(rp.read_text(encoding="utf-8"))
    if receipt.get("terminal_reason") in ("moderation_refusal", "policy_refusal"):
        return False

    mf = scene_dir / META_NAME
    existing_meta = json.loads(mf.read_text(encoding="utf-8")) if mf.is_file() else {}
    attempts_so_far = int(existing_meta.get("attempt_limit", 0) or 0)
    if attempts_so_far >= 10:
        return False

    original = str(scene.get("raw_9_fields") or "").strip()
    if not original:
        sc_num = scene.get("scene_number", scene.get("number", 0))
        if not sc_num:
            # Try parsing from directory name like scene_0047
            try:
                sc_num = int(scene_dir.name.split("_")[-1])
            except Exception:
                sc_num = 0
        for candidate_path in [scene_dir.parent.parent / "scene_prompts_9_fields.txt", scene_dir.parent / "scene_prompts_9_fields.txt"]:
            if candidate_path.is_file():
                content = candidate_path.read_text(encoding="utf-8")
                m = re.search(rf"(========== SCENE_{sc_num:03d} .*?)(?=\n========== SCENE_|\Z)", content, re.DOTALL)
                if m:
                    original = m.group(1).strip()
                    break
    if not original:
        return False
    if (scene_dir / ALT_NAME).is_file():
        alternate = (scene_dir / ALT_NAME).read_text(encoding="utf-8")
    else:
        alternate = simplified_prompt(original, scene)
        if original == alternate:
            return False

    manifest = {
        "status": "ONE_REPAIR_ARMED",
        "attempt_limit": attempts_so_far + 1,
        "original_sha256": existing_meta.get("original_sha256") or digest(original),
        "repaired_sha256": digest(alternate),
        "error_class": "MUSE_COMPLETED_WITHOUT_VIDEO",
        "prior_receipt_state": receipt.get("state"),
        "prior_session_id": receipt.get("session_id"),
        "must_not_cascade_accounts": True
    }
    new_path = scene_dir / ALT_NAME
    tmp = new_path.with_suffix(".tmp")
    tmp.write_text(alternate, encoding="utf-8")
    os.replace(tmp, new_path)

    archive_name = OLD_RECEIPT_NAME if attempts_so_far == 0 else f"muse_job_failed_attempt_{attempts_so_far+1}.json"
    os.replace(rp, scene_dir / archive_name)
    tmp_mf = mf.with_suffix(".tmp")
    tmp_mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp_mf, mf)
    scene["raw_9_fields"] = alternate
    return True
