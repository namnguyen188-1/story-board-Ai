#!/usr/bin/env python3
"""Validate the legacy 9-field text-to-video format. No external dependencies.
Text preflight cannot certify cinematic quality of rendered clips.
"""
import argparse
import json
import re
from pathlib import Path

LABELS = (
    "FORMAT & STYLE", "CHARACTERS", "SETTING & START STATE",
    "LIGHTING & COLOR", "CAMERA", "TIMED ACTION", "END STATE",
    "AUDIO", "CONSTRAINTS",
)
HEADER = re.compile(r'^={10} SCENE_(\d{3}) \| TIMELINE (\d\d:\d\d)[–-](\d\d:\d\d) \| GENERATE (\d+(?:\.\d+)?) SECONDS ={10}$', re.M)
LABEL = re.compile(r'^([A-Z][A-Z &]+):', re.M)

def sec(tc):
    mm, ss = map(int, tc.split(':'))
    if ss >= 60:
        raise ValueError('Invalid timecode seconds: ' + tc)
    return mm * 60 + ss

def validate(text, target_seconds=None, aspect=None):
    errors, warnings = [], []
    found = list(HEADER.finditer(text))
    if not found:
        return {'pass': False, 'scene_count': 0, 'total_seconds': 0,
                'errors': ['No recognized legacy SCENE headers found'], 'warnings': []}
    if text[:found[0].start()].strip():
        errors.append('Non-scene text before SCENE_001')
    total = 0.0
    previous_end = None
    for i, h in enumerate(found):
        name = h.group(1)
        if int(name) != i + 1:
            errors.append(f'SCENE_{name}: expected SCENE_{i+1:03d}')
        b = text[h.end():(found[i+1].start() if i+1 < len(found) else len(text))]
        keys = [m.group(1) for m in LABEL.finditer(b)]
        if keys != list(LABELS):
            errors.append(f'SCENE_{name}: incorrect labels/order: {keys}')
        sections = {}
        matches = list(LABEL.finditer(b))
        for n, m in enumerate(matches):
            content = b[m.end():(matches[n+1].start() if n+1 < len(matches) else len(b))].strip()
            sections[m.group(1)] = content
        for key in LABELS:
            if not sections.get(key):
                errors.append(f'SCENE_{name}: missing/empty {key}')
        start, end, stated = sec(h.group(2)), sec(h.group(3)), float(h.group(4))
        if previous_end is not None and start != previous_end:
            errors.append(f'SCENE_{name}: timecode gap/overlap after {previous_end}s')
        if abs(end-start-stated) > 1e-6:
            errors.append(f'SCENE_{name}: header duration mismatch')
        previous_end = end
        total += end - start
        if aspect and aspect not in sections.get('FORMAT & STYLE',''):
            errors.append(f'SCENE_{name}: format does not specify {aspect}')
        audio = sections.get('AUDIO','')
        if not audio or not re.search(r'\b(speak|speaks|spoken|says|said|dialogue|narrat|voiceover|silent)\b',audio,re.I):
            warnings.append(f'SCENE_{name}: check speaker/voice audio explicitly')
        action = sections.get('TIMED ACTION','')
        if len(action) < 50:
            warnings.append(f'SCENE_{name}: TIMED ACTION unusually vague')
        # These are script-only warnings, never a visual quality pass.
        if re.search(r'\b(stands? still|stares? at camera|expressionless|motionless)\b', action, re.I) and not re.search(r'\b(statue|skeleton|mannequin|deliberately|intentionally|stillness)\b', sections.get('CHARACTERS','')+' '+action,re.I):
            warnings.append(f'SCENE_{name}: potential frozen actor; inspect artistic intent')
        chars = sections.get('CHARACTERS', '')
        if re.search(r'\b(transitioning|later changes|initially wears)\b', chars, re.I):
            warnings.append(f'SCENE_{name}: CHARACTERS uses vague transition words; lock wardrobe strictly per act')
        tokens = [t.strip() for t in chars.split(';') if t.strip()]
        for tok in tokens:
            if tok.startswith('Fix exact') or tok.startswith('Retain exactly'):
                continue
            if ':' not in tok and len(tok.split(',')) <= 2 and len(tok) < 80:
                clean_bare = tok.split('.')[0].strip()
                if clean_bare and clean_bare.lower() not in ('silent', 'unseen', 'heard only', 'no line', 'offscreen'):
                    warnings.append(f'SCENE_{name}: bare character without visual DNA: {clean_bare}')

        # Safety Moderation: detect forbidden words that trigger provider refusals
        scene_full_text = b
        mod_weapons = re.findall(r'\b(sidearms?(\s+holsters?)?|holsters?|guns?|pistols?|rifles?|firearms?|ammunition|knives|knif(?:e|ing)|daggers?|swords?|blades?|weapons?)\b', scene_full_text, re.I)
        if mod_weapons:
            matched_w = list(dict.fromkeys(m[0] if isinstance(m, tuple) else m for m in mod_weapons))
            errors.append(f'SCENE_{name}: FORBIDDEN WEAPON TERMS {matched_w} will trigger AI Safety Filter; replace with safe alternatives (see SAFETY_AND_MODERATION.md)')

        mod_violence = re.findall(r'\b(tackles?|tackling|pinned\s+(?:down|to|on)|kneels\s+over\s+him|shoved\s+onto|punches?|punching|kicks?|kicking|slaps?|strangles?|chokes?|(?:beating\s+(?:up|down|him|her|them|someone)|beats?\s+(?:up|down|him|her|them)|brutally\s+beat)|bloody|wound|stab|slash|kill|slay|corpse|flesh|mutilat)\b', scene_full_text, re.I)
        if mod_violence:
            matched_v = list(dict.fromkeys(m[0] if isinstance(m, tuple) else m for m in mod_violence))
            errors.append(f'SCENE_{name}: FORBIDDEN VIOLENCE TERMS {matched_v} will trigger AI Safety Filter; replace with dramatic cinema acting (see SAFETY_AND_MODERATION.md)')
    if target_seconds is not None and abs(total-target_seconds)>1e-6:
        errors.append(f'Total {total:g}s != requested {target_seconds:g}s')
    return {'pass': not errors, 'scene_count': len(found), 'total_seconds': total,
            'errors': errors, 'warnings': warnings,
            'note': 'TXT preflight only; rendered human motion/lip-sync requires video QC.'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('path', type=Path)
    p.add_argument('--seconds', type=float)
    p.add_argument('--aspect', choices=['9:16','16:9'])
    a = p.parse_args()
    result = validate(a.path.read_text(encoding='utf-8-sig'), a.seconds, a.aspect)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['pass'] else 1)

if __name__ == '__main__':
    main()
