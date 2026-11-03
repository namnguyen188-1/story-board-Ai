"""Cross-scene continuity instructions for sequential Muse text-to-video.

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
