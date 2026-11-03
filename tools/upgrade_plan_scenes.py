# -*- coding: utf-8 -*-
"""
Deeply transform all 137 scenes in Stoic-Philosophy-Full-Guides/episode_001/plan.json:
Replaces scrawny distant full-length stone statues on pedestals with
Hyper-Muscular Chiseled Warrior-Philosopher Emperor (Marcus Aurelius demigod build)
in dynamic Chest-Up / Medium 3/4 framing with one-shoulder draped crimson toga.
"""
import json
import re
from pathlib import Path

plan_path = Path("studio/productions/Stoic-Philosophy-Full-Guides/episode_001/plan.json")
data = json.loads(plan_path.read_text(encoding="utf-8"))

scenes = data.get("scenes", [])
print(f"Total scenes to process: {len(scenes)}")

def transform_stoic_scene(desc: str, setup: str, scene_idx: int) -> tuple[str, str]:
    # Combine or treat individually
    def clean_text(t: str) -> str:
        if not t:
            return ""
        # 1. Transform wide / full shot camera framing to chest-up / medium heroic
        t = re.sub(r'(?i)\bwide\s+shot\s+inside\s+a\s+monumental\s+ancient\s+Greco-Roman\s+temple\s+inner\s+sanctuary\.\s*A\s+full-length\s+standing\s+marble\s+philosopher\s+statue\b',
                   'Cinematic medium shot inside a monumental ancient Greco-Roman temple sanctuary, focusing on the hyper-muscular chiseled Stoic philosopher emperor with massive broad shoulders, sculpted chest pecs, and royal crimson toga draped over one shoulder', t)
        
        t = re.sub(r'(?i)\b(dramatic\s+)?(low[- ]angle\s+)?full[- ]length\s+shot\s+of\s+the\s+standing\s+classical\s+marble\s+philosopher\s+statue\s+from\s+head\s+to\s+toe\b',
                   'Heroic low-angle chest-up shot of the hyper-muscular chiseled Stoic philosopher emperor, showcasing his massive broad shoulders, thick muscular neck, and sculpted chest pecs', t)

        t = re.sub(r'(?i)\beye[- ]level\s+full[- ]shot\s+of\s+the\s+heroic\s+full[- ]length\s+standing\s+classical\s+marble\s+statue\s+of\s+a\s+stoic\s+philosopher\b',
                   'Cinematic eye-level medium close-up (bust) of the hyper-muscular chiseled Stoic philosopher emperor with intense piercing eyes, thick beard, and sculpted chest', t)

        t = re.sub(r'(?i)\bwide\s+panoramic\s+view\s+of\s+a\s+grand\s+ancient\s+Roman\s+plaza[^\.]*\.\s*In\s+the\s+center\s+stands\s+a\s+heroic\s+full[- ]length\s+classical\s+marble\s+statue[^\.]*\b',
                   'Cinematic chest-up shot of the hyper-muscular chiseled Stoic philosopher emperor with massive broad shoulders, thick neck, and sculpted chest pecs, royal crimson toga draped over one shoulder leaving muscular chest and arm exposed, against a grand ancient Roman forum at dawn', t)

        t = re.sub(r'(?i)\b(heroic\s+)?full[- ]length\s+standing\s+classical\s+marble\s+statue\s+(of\s+an?\s+ancient\s+bearded\s+stoic\s+philosopher\s+)?from\s+head\s+to\s+toe,\s+legs\s+grounded\s+on\s+ancient\s+temple\s+base\b',
                   'hyper-muscular chiseled Stoic philosopher emperor with massive broad shoulders, thick neck, and sculpted chest pecs', t)

        t = re.sub(r'(?i)\bheroic\s+full[- ]length\s+standing\s+classical\s+marble\s+statue\s+of\s+an?\s+ancient\s+bearded\s+stoic\s+philosopher\b',
                   'hyper-muscular chiseled Stoic philosopher emperor with massive broad shoulders, thick neck, sculpted chest pecs, and striated deltoids', t)

        t = re.sub(r'(?i)\bfull[- ]length\s+standing\s+(classical\s+)?marble\s+statue(\s+of\s+a\s+bearded\s+stoic\s+philosopher)?\b',
                   'hyper-muscular chiseled Stoic philosopher emperor with massive broad shoulders, thick neck, and sculpted chest', t)

        t = re.sub(r'(?i)\bstanding\s+classical\s+marble\s+philosopher\s+statue\b',
                   'hyper-muscular Stoic philosopher emperor in heroic chest-up framing', t)

        t = re.sub(r'(?i)\bclassical\s+marble\s+philosopher\s+statue\b',
                   'hyper-muscular chiseled Stoic philosopher emperor with sculpted pecs', t)

        t = re.sub(r'(?i)\bstanding\s+classical\s+statue\b',
                   'hyper-muscular Stoic emperor', t)

        t = re.sub(r'(?i)\bclassical\s+marble\s+statue\b',
                   'hyper-muscular chiseled Roman philosopher emperor with weathered bronze skin', t)

        t = re.sub(r'(?i)\bmarble\s+statue\b',
                   'hyper-muscular Stoic philosopher emperor', t)

        t = re.sub(r'(?i)\bstatue\b',
                   'hyper-muscular philosopher emperor', t)

        # 2. Transform attire and pedestal
        t = re.sub(r'(?i)\bdraped\s+stone\s+toga(\s+flowing\s+down\s+past\s+knees\s+to\s+stone\s+base)?\b',
                   'royal crimson red toga draped across one shoulder, leaving the sculpted muscular chest and powerful shoulder/arm bare', t)

        t = re.sub(r'(?i)\bweathered\s+carrara\s+marble\s+textures,\s+draped\s+toga\s+flowing\s+to\s+stone\s+base\b',
                   'weathered sun-kissed bronze skin, sculpted muscular pecs and shoulder, royal crimson red toga draped over one shoulder', t)

        t = re.sub(r'(?i)\bstanding\s+resolute\s+on\s+its\s+weathered\s+stone\s+pedestal\b',
                   'commanding presence in heroic medium close-up against illuminated ancient colonnades', t)

        t = re.sub(r'(?i)\b(stone\s+)?pedestals?\b', 'ancient marble colonnade', t)
        t = re.sub(r'(?i)\bpedestal\b', 'ancient colonnade', t)

        # 3. Framing enhancement
        if not re.search(r'(?i)\b(chest[- ]up|medium|close[- ]up|portrait)\b', t):
            t = "Cinematic chest-up composition: " + t

        t = re.sub(r'\s{2,}', ' ', t).strip()
        return t

    new_desc = clean_text(desc)
    new_setup = clean_text(setup)
    return new_desc, new_setup

modified_count = 0
for idx, sc in enumerate(scenes):
    d = sc.get("description", "")
    vs = sc.get("visual_setup", "")
    nd, nvs = transform_stoic_scene(d, vs, idx + 1)
    if nd != d or nvs != vs:
        sc["description"] = nd
        sc["visual_setup"] = nvs
        modified_count += 1

data["scenes"] = scenes
plan_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Transformed {modified_count}/{len(scenes)} scenes to hyper-muscular warrior-philosopher demigod framing!")
