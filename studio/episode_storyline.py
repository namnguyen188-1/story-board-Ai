"""Read-only, fail-safe continuity context for original multi-episode scripts.

This module never edits completed episodes. Script and link/clone modes are
intentionally excluded by the caller.
"""
from __future__ import annotations

import json
from pathlib import Path


def _plan(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def build_episode_context(series_dir: str | Path, episode: int, genre: str) -> str:
    """Ground episode N in the actual scripts for episodes 1..N-1.

    Returns an empty string when there is no compatible original screenplay.
    Never infer content from folder names or reuse unrelated cloned videos.
    """
    if int(episode) <= 1:
        return ""
    base = Path(series_dir)
    previous = _plan(base / f"episode_{int(episode)-1:03d}" / "plan.json")
    previous_cfg = previous.get("config") or {}
    previous_scenes = previous.get("scenes") or []
    if not isinstance(previous_cfg, dict) or not isinstance(previous_scenes, list):
        return ""
    if previous_cfg.get("input_mode") != "idea":
        return ""
    if str(previous_cfg.get("genre") or "") != str(genre):
        return ""
    if not previous_scenes:
        return ""

    root = _plan(base / "episode_001" / "plan.json")
    root_cfg = root.get("config") or {}
    if not isinstance(root_cfg, dict) or root_cfg.get("input_mode") != "idea":
        root_cfg = previous_cfg
    root_premise = str(root_cfg.get("prompt") or previous_cfg.get("prompt") or "").strip()[:1700]
    if not root_premise:
        return ""

    previous_outline = [
        str(s.get("summary") or "").strip()[:240]
        for s in previous_scenes if isinstance(s, dict) and s.get("summary")
    ]
    previous_finish = previous_outline[-7:]
    previous_start = previous_outline[:2]
    prev_last = previous_scenes[-1] if isinstance(previous_scenes[-1], dict) else {}
    prior_spoken = str(prev_last.get("narration") or "")[:450]
    bible = previous.get("bible") or {}
    theme = str(bible.get("core_moral_theme") or "")[:380] if isinstance(bible, dict) else ""

    parts = [
        "SERIES EPISODE CONTINUITY CONTRACT (priority over generic viral hooks):",
        f"This is episode {int(episode)} of ONE ongoing series, not a standalone random topic.",
        "LOCKED ORIGINAL SERIES PREMISE: " + root_premise,
        "PREVIOUS EPISODE OPENING TOPICS: " + " | ".join(previous_start),
        "PREVIOUS EPISODE FINAL DEVELOPMENTS: " + " | ".join(previous_finish),
        "PREVIOUS EPISODE LAST SPOKEN LINE: " + prior_spoken,
        "CONTINUATION: Advance the same thesis, themes, learning journey, and unresolved question. "
        "Episode N must explore the NEXT consequential step; never retell episode N-1 or switch "
        "to an unrelated topic. Keep narrator identity, established facts, visual identity, "
        "audience promise, and language consistent. A distinct chapter title is allowed ONLY "
        "when directly connected to the overall premise.",
        "BEGINNING: briefly bridge the unresolved conclusion of the prior episode in the "
        "first minute, then develop new material. ENDING: deliver meaningful value and "
        "set up a concrete question naturally answered in episode N+1.",
    ]
    if theme:
        parts.append("SERIES CORE THEME: " + theme)
    if genre == "stoic":
        parts.append(
            "STOIC SERIES RULES: Calm, grounded, thoughtful philosophical education with "
            "practical exercises and accurate attribution. No fabricated Marcus Aurelius "
            "quotes, no weapons/life-or-death drama, no random shocking secrets, no fictional "
            "cliffhangers or manipulative sensationalism. The next lesson must build upon "
            "the previous episode's insight."
        )
    return "\n".join(parts) + "\n"
