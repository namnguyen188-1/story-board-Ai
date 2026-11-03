import json
from pathlib import Path

p = Path("studio/productions/Stoic-Philosophy-Full-Guides/episode_001/plan.json")
d = json.loads(p.read_text(encoding="utf-8"))
scenes = d.get("scenes", [])
print(f"Total scenes: {len(scenes)}")

matches = []
for s in scenes:
    text = (s.get("description", "") + " " + s.get("visual_setup", "")).lower()
    if any(k in text for k in ["statue", "pedestal", "sculpture", "marble"]):
        matches.append((s.get("scene_number"), s.get("description", "")[:100]))

print(f"Scenes with statue/pedestal/marble: {len(matches)}")
for num, desc in matches[:10]:
    print(f"Scene {num}: {desc}")
