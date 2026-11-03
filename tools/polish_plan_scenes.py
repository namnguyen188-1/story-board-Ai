# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

plan_path = Path("studio/productions/Stoic-Philosophy-Full-Guides/episode_001/plan.json")
data = json.loads(plan_path.read_text(encoding="utf-8"))

def polish_text(t: str) -> str:
    if not t:
        return ""
    t = re.sub(r'(?i)\bfrom\s+head\s+to\s+toe\b', '', t)
    t = re.sub(r'(?i)\bcomplete\s+anatomical\s+figure\s+of\s+the\s+standing[^\,]*\,', 'the imposing chest-up figure of the hyper-muscular philosopher emperor,', t)
    t = re.sub(r'(?i)\bthe\s+entire\s+figure\s+from\s+head\s+to\s+toe\b', 'the muscular torso and chiseled shoulders', t)
    t = re.sub(r'(?i)\bstone\s+feet\s+and\s+draped\s+toga\s+base\b', 'the colonnade floor and draped crimson toga', t)
    t = re.sub(r'(?i)\bstone\s+surface\s+of\s+the\s+complete\s+full[- ]length\s+hyper[- ]muscular\s+philosopher\s+emperor\b', 'chiseled chest muscles and weathered bronze skin of the emperor', t)
    t = re.sub(r'(?i)\bstands\s+complete\s+from\s+head\s+to\s+toe\b', 'commands the hall in heroic chest-up composition', t)
    t = re.sub(r'(?i)\bhead[- ]to[- ]toe\s+full[- ]length\s+hyper[- ]muscular\s+Stoic\s+philosopher\s+emperor\b', 'hyper-muscular Stoic philosopher emperor in heroic chest-up framing', t)
    t = re.sub(r'(?i)\bstanding\s+resolute\s+on\s+its\s+weathered\s+ancient\s+marble\s+colonnade\b', 'commanding the space with broad muscular shoulders and sculpted chest pecs', t)
    t = re.sub(r'(?i)\bcomplete\s+full[- ]length\s+hyper[- ]muscular\s+philosopher\s+emperor\b', 'hyper-muscular Stoic philosopher emperor', t)
    t = re.sub(r'(?i)\bphilosopher\s+hyper[- ]muscular\s+philosopher\s+emperor\b', 'hyper-muscular Stoic philosopher emperor', t)
    t = re.sub(r'(?i)\bhyper[- ]muscular\s+philosopher\s+emperor\b', 'hyper-muscular Stoic emperor', t)
    t = re.sub(r'(?i)\bstone\s+hyper[- ]muscular\b', 'hyper-muscular', t)
    t = re.sub(r'(?i)\bcarved\s+stone\s+fissures\b', 'weathered sun-kissed skin pores and veins', t)
    t = re.sub(r'(?i)\bmotionless\s+stone\s+statue\b', 'stoic, unyielding philosopher emperor', t)
    t = re.sub(r'(?i)\bmotionless\s+stability\b', 'unshakable inner tranquility', t)
    t = re.sub(r'\s{2,}', ' ', t).strip()
    return t

count = 0
for sc in data.get("scenes", []):
    d = sc.get("description", "")
    vs = sc.get("visual_setup", "")
    nd = polish_text(d)
    nvs = polish_text(vs)
    if nd != d or nvs != vs:
        sc["description"] = nd
        sc["visual_setup"] = nvs
        count += 1

plan_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Polished {count} scenes to remove stone/pedestal/head-to-toe relics.")
