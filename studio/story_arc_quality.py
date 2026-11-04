"""Non-destructive narrative beat guidance and QC. Keeps user-owned locked scripts untouched."""
from __future__ import annotations
import re

DYNAMIC_GENRES = {
    "drama", "family_drama", "mafia_thriller", "psychological_horror",
    "romance_melodrama", "theatrical_drama", "western", "action", "animation"
}
EARLY_CLOSURE = re.compile(
    r"^\s*(?:conclusion\b|final message\b|final lesson\b|"
    r"moral lesson\b|in conclusion\b|conclusi[oó]n\b|"
    r"fazit\b|schlusswort\b|k[eế]t lu[aậ]n\b|b[aà]i h[oọ]c cu[oố]i)\b",re.I)
BAD_OPENING = re.compile(
    r"^\s*(?:xin chào|chào mừng|hôm nay chúng ta sẽ|trong video hôm nay|"
    r"hola a todos|bienvenidos(?: a| al)|en este video vamos|"
    r"hello everyone|welcome back|in today's video|today we will)\b",re.I)

def target_beat(number:int,total:int)->str:
    if total < 1 or not 1<=number<=total:raise ValueError("invalid scene position")
    if total==1:return "HOOK_TURN_RESOLUTION"
    if number==1:return "HOOK"
    if number==total:return "CLIFFHANGER_OPEN_LOOP"
    climax=max(2,min(total-1,round(total*.82)))
    if number==climax:return "CLIMAX"
    relative=(number-1)/max(1,total-1)
    if relative<.22:return "SETUP"
    if relative<.55:return "ESCALATION"
    if relative<.82:return "COMPLICATION"
    return "AFTERMATH"

def beat_guidance(first:int,count:int,total:int,genre:str,premise:str="")->str:
    hint=str(premise or "").lower()
    plot_driven=genre=="documentary" and any(k in hint for k in
         ("hoa","neighbor","neighbour","ranch","confrontation","dispute","court","injustice","landowner"))
    dynamic=genre in DYNAMIC_GENRES or plot_driven
    theme=(
        "Drama: observable obstacles, characters make choices with consequences, "
        "pressure escalates, climax reveals a specific outcome. Keep realistic stakes, no filler."
        if dynamic else
        "Educational/philosophical film: use a compelling dilemma, conflicting choices, "
        "clear discovery or conceptual reversal, practical payoff. Never invent violent drama."
    )
    roles=", ".join(f"scene {i}={target_beat(i,total)}" for i in range(first,first+count))
    return (
      "STORY ARC CONTRACT: " + roles + ". "
      +theme+
      " HOOK begins with a high-stakes curiosity gap or paradoxical dilemma in the first 3 seconds without greetings. "
      "ESCALATION/COMPLICATION should add new information, obstacles or meaningful choices, not repeat the same shot. "
      "CLIMAX must be a distinct turning point near the final fifth of the FULL film. "
      "FINAL BEAT (CLIFFHANGER & OPEN LOOP) must deliver an emotional peak and abruptly unveil a sudden secret, mystery, or cliffhanger twist that leaves viewers desperate to watch the next episode, never an early farewell or closed moral lesson. "
      "Vary scene composition: wide establishing, environment, full-body, objects and close-ups according to meaning. "
      "Do not force the same protagonist or half-body statue into every scene."
    )

def audit_plan(scenes:list[dict],genre:str,locked:bool=False)->dict:
    if not scenes:return {"quality":"NEEDS_REVIEW","warnings":["no_scenes"]}
    descriptions=[re.sub(r"\s+"," ",str(s.get("description","")).strip().lower())[:180] for s in scenes]
    opening=str(scenes[0].get("narration","") or "").strip()
    warnings=[]
    if not locked and BAD_OPENING.search(opening):warnings.append("generic_greeting_hook")
    if not locked and len(opening.split())<10:warnings.append("short_opening_narration")
    if len(scenes)>=5:
        bad_early=[i+1 for i,scene in enumerate(scenes)
                   if (i+1)<len(scenes)*.75 and
                   EARLY_CLOSURE.search(str(scene.get("summary","")).strip())]
        if bad_early:warnings.append("premature_conclusion_scenes:"+",".join(map(str,bad_early)))
    if len(descriptions)>1 and len(set(descriptions))<len(descriptions):
        warnings.append("repeated_visual_descriptions")
    roles=[target_beat(i,len(scenes)) for i in range(1,len(scenes)+1)]
    return {
      "quality":"REVIEW" if warnings else "STRUCTURE_READY",
      "content_quality_human_verified":False,
      "script_preserved":bool(locked),
      "genre":genre,"scene_count":len(scenes),
      "expected_beats":{role:roles.count(role) for role in sorted(set(roles))},
      "warnings":warnings,
      "note":"Structure-ready indicates guidance/checks, not independently verified dramatic quality or audience retention."
    }
