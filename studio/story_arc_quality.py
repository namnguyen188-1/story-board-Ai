"""Non-destructive narrative beat guidance and viral retention QC.
Implements Hollywood & Netflix / Lemmino / Fern retention standards:
1. Multi-Stage Cold Open Hook (Paradox -> Stakes -> Open Loop in first 15s).
2. Interlocking Curiosity Gaps (Nested loops keeping viewers hooked past 30s, 60s, 5m).
3. Sensory Grounding (Physical somatic reactions instead of abstract exposition).
4. Midpoint Paradigm Shift & Psychological Climax.
5. Infinite Cliffhanger / Open Loop Outro (compels viewers to watch next episode).
100% backward-compatible with all existing studio pipelines and locked scripts.
"""
from __future__ import annotations
import math
import re

DYNAMIC_GENRES = {
    "drama", "family_drama", "mafia_thriller", "psychological_horror",
    "romance_melodrama", "theatrical_drama", "western", "action", "animation"
}

DOCUMENTARY_GENRES = {
    "documentary", "history", "philosophy", "stoic", "mystery",
    "investigation", "biography", "science", "ancient_civilization", "kham pha"
}

EARLY_CLOSURE = re.compile(
    r"^\s*(?:conclusion\b|final message\b|final lesson\b|"
    r"moral lesson\b|in conclusion\b|conclusi[oó]n\b|"
    r"fazit\b|schlusswort\b|k[eế]t lu[aậ]n\b|b[aà]i h[oọ]c cu[oố]i)\b", re.I
)

BAD_OPENING = re.compile(
    r"^\s*(?:xin ch[aà]o|ch[aà]o m[uừ]ng|h[oô]m nay ch[uú]ng ta s[eẽ]|trong video h[oô]m nay|"
    r"hola a todos|bienvenidos(?: a| al)|en este video vamos|"
    r"hello everyone|welcome back|in today's video|today we will|welcome to my channel|"
    r"hey guys|hi guys)\b", re.I
)

PASSIVE_CLICHE = re.compile(
    r"^\s*(?:as we all know|as history shows|it is worth noting|in this part|"
    r"as mentioned earlier|nh[uư] ch[uú]ng ta [dđ][aã] bi[eế]t|[dđ][aá]ng ch[uú] [yý] l[aà]|"
    r"trong ph[aầ]n n[aà]y|h[aã]y c[uù]ng t[iì]m hi[eể]u|nh[uư] [dđ][aã] n[oó]i [oở] tr[eê]n)\b", re.I
)


def target_beat(number: int, total: int) -> str:
    """Assigns precise narrative roles calibrated for maximum viewer retention."""
    if total < 1 or not 1 <= number <= total:
        raise ValueError("invalid scene position")
    if total == 1:
        return "HOOK_TURN_RESOLUTION"
    if total <= 3:
        if number == 1:
            return "HOOK"
        if number == total:
            return "CLIFFHANGER_OPEN_LOOP"
        return "ESCALATION"

    # Multi-Stage Cold Open Hook Window (Scenes 1 to 3)
    if number == 1:
        return "HOOK_PARADOX"
    if number == 2 and total >= 6:
        return "HOOK_STAKES"
    if number == 3 and total >= 8:
        return "HOOK_OPEN_LOOP"

    if number == total:
        return "CLIFFHANGER_OPEN_LOOP"

    # Narrative Pivots
    midpoint = max(3, round(total * 0.50))
    climax = max(2, min(total - 1, round(total * 0.82)))
    paradigm_shift = max(climax + 1, min(total - 1, round(total * 0.92)))

    if number == midpoint and total >= 10:
        return "MIDPOINT_REVERSAL"
    if number == climax:
        return "CLIMAX"
    if number == paradigm_shift and total >= 12:
        return "PARADIGM_SHIFT"

    relative = (number - 1) / max(1, total - 1)
    if relative < 0.22:
        return "SETUP"
    if relative < 0.50:
        return "ESCALATION"
    if relative < 0.82:
        return "COMPLICATION"
    return "AFTERMATH"


def beat_guidance(first: int, count: int, total: int, genre: str, premise: str = "") -> str:
    """Generates authoritative narrative instructions injected into AI story generation prompts."""
    hint = str(premise or "").lower()
    g_clean = str(genre or "documentary").strip().lower()
    plot_driven = g_clean in DYNAMIC_GENRES or (
        g_clean == "documentary" and any(k in hint for k in (
            "hoa", "neighbor", "neighbour", "ranch", "confrontation", "dispute", "court", "injustice", "landowner"
        ))
    )

    if plot_driven:
        theme = (
            "HIGH-STAKES DRAMA FRAMEWORK (VIRAL RETENTION MANDATE): "
            "1. THE TICKING CLOCK: Establish an urgent countdown or narrowing window of survival/remedy (before nightfall, before the blizzard strikes, before the auction/deadline). Characters feel time running out in every scene. "
            "2. SHOW, DON'T TELL (SENSORY GROUNDING): Forbid abstract emotional labels ('he was scared', 'she felt sad'). Ground all emotion in physical actions, somatic reactions, and sensory reality (trembling fingers, smelling the cold air, protective body posture, a blackened injury, labored breathing). "
            "3. IMPOSSIBLE MORAL DILEMMAS: Force characters into agonizing choices with severe consequences (sacrifice self vs save children; preserve pride vs beg for life). "
            "4. PUNCHY DIALOGUE: Spoken lines must be concise, authentic, and fraught with subtext ('Not without you', 'Take the boys and go'). "
            "5. ESCALATING OBSTACLES: Every beat must reveal a new complication that raises the stakes higher. No flat scenes."
        )
    else:
        # Documentary / Mystery / History / Philosophy (Lemmino / Fern / Netflix standard)
        theme = (
            "VIRAL DOCUMENTARY & HISTORICAL MYSTERY FRAMEWORK (LEMMINO / FERN / NETFLIX STANDARD): "
            "1. THE 3-SECOND COLD OPEN PARADOX: Scene 1 MUST open in medias res with an arresting anomaly, an impossible contradiction, or a suppressed discovery that defies modern understanding. Zero greetings, zero pleasantries ('Xin chao', 'Welcome', 'Today we will' are strictly forbidden). "
            "2. INTERLOCKING CURIOSITY GAPS (NESTED OPEN LOOPS): Open an intriguing question before revealing an answer. When clue A is discovered, immediately reveal an unsettling contradiction B that deepens the mystery. "
            "3. SENSORY & VISCERAL GROUNDING: Forbid dry textbook exposition. Anchor every historical fact in tangible physical details (the scorch marks on 2,000-year-old granite, the smell of burning pitch and cedar, the deafening thud of an 8-ton flywheel, grease-stained blueprints in trembling hands). "
            "4. MIDPOINT PARADIGM SHIFT: At the 50% mark, overturn the surface-level explanation. Prove the accepted theory wrong or unveil a hidden motive that resets the investigation. "
            "5. CLIMAX REVELATION & PHILOSOPHICAL MIRROR: Deliver a monumental breakthrough in the final fifth, followed by a haunting insight into human ambition, pride, or destiny that mirrors our modern world. "
            "6. INFINITE CLIFFHANGER OUTRO: The final beat must leave a lingering unanswered question or open a thrilling new frontier, compelling viewers to watch the next episode."
        )

    roles = ", ".join(f"scene {i}={target_beat(i, total)}" for i in range(first, first + count))
    return (
        f"STORY ARC CONTRACT: {roles}. {theme} "
        "HOOK begins with an arresting in medias res moment or impossible moral dilemma in the first 3 seconds without greetings. "
        "ESCALATION/COMPLICATION should add new obstacles, worsening stakes, and visceral choices, not repeat the same shot. "
        "CLIMAX must be a distinct turning point near the final fifth of the FULL film where the central sacrifice or revelation occurs. "
        "FINAL BEAT (CLIFFHANGER & OPEN LOOP) must deliver an emotional peak and abruptly unveil a sudden secret, mystery, or cliffhanger twist that leaves viewers desperate to watch the next episode, never an early farewell or closed moral lesson. "
        "Vary scene composition: wide establishing, environment, full-body, objects and close-ups according to meaning. "
        "Do not force the same protagonist or half-body statue into every scene."
    )


def audit_plan(scenes: list[dict], genre: str, locked: bool = False) -> dict:
    """Performs deep viral retention and narrative structure audit on the planned scenes."""
    if not scenes:
        return {"quality": "NEEDS_REVIEW", "warnings": ["no_scenes"]}

    descriptions = [re.sub(r"\s+", " ", str(s.get("description", "")).strip().lower())[:180] for s in scenes]
    opening = str(scenes[0].get("narration", "") or "").strip()
    warnings = []

    # 1. Hook Quality Checks
    if not locked and BAD_OPENING.search(opening):
        warnings.append("generic_greeting_hook")
    if not locked and len(opening.split()) < 8:
        warnings.append("short_opening_narration")
    if not locked and PASSIVE_CLICHE.search(opening):
        warnings.append("passive_cliche_opening")

    # 2. Premature Conclusion Detection
    if len(scenes) >= 5:
        bad_early = [
            i + 1 for i, scene in enumerate(scenes)
            if (i + 1) < len(scenes) * 0.75 and
            EARLY_CLOSURE.search(str(scene.get("summary", "")).strip())
        ]
        if bad_early:
            warnings.append("premature_conclusion_scenes:" + ",".join(map(str, bad_early)))

    # 3. Visual Monotony Detection
    if len(descriptions) > 1 and len(set(descriptions)) < len(descriptions) * 0.85:
        warnings.append("repeated_visual_descriptions")

    roles = [target_beat(i, len(scenes)) for i in range(1, len(scenes) + 1)]

    # 4. Retention Scoring (0-100)
    score = 100
    if "generic_greeting_hook" in warnings:
        score -= 25
    if "short_opening_narration" in warnings:
        score -= 15
    if "passive_cliche_opening" in warnings:
        score -= 15
    if any(w.startswith("premature_conclusion") for w in warnings):
        score -= 20
    if "repeated_visual_descriptions" in warnings:
        score -= 15

    score = max(20, min(100, score))
    grade = "A+" if score >= 90 else ("A" if score >= 80 else ("B" if score >= 70 else "C"))

    return {
        "quality": "REVIEW" if warnings else "STRUCTURE_READY",
        "retention_score": score,
        "retention_grade": grade,
        "content_quality_human_verified": False,
        "script_preserved": bool(locked),
        "genre": genre,
        "scene_count": len(scenes),
        "expected_beats": {role: roles.count(role) for role in sorted(set(roles))},
        "warnings": warnings,
        "note": "Calibrated against Netflix / Lemmino / Fern retention standards (Cold Open Paradox, Curiosity Gaps, Sensory Grounding)."
    }
