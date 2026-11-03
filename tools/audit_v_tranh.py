import json
from pathlib import Path

# 1. Audit v-tranh/episode_001
v_plan_path = Path(r"d:\STORYBOARD_AI\studio\productions\v-tranh\episode_001\plan.json")
if v_plan_path.exists():
    v_data = json.loads(v_plan_path.read_text(encoding="utf-8"))
    scenes = v_data.get("scenes", [])
    print("=== AUDIT: v-tranh / episode_001 ===")
    print(f"Title: {v_data.get('title')}")
    print(f"Total scenes: {len(scenes)}")
    print(f"Character locks in bible/config: {v_data.get('bible', {}).get('characters') or v_data.get('characters')}")
    
    # Check Scene 1 (Hook)
    if len(scenes) > 0:
        s1 = scenes[0]
        print("\n--- SCENE 1 (HOOK) ---")
        print(f"Summary: {s1.get('summary')}")
        print(f"Visual setup: {s1.get('visual_setup') or s1.get('description')}")
        print(f"Narration: {s1.get('narration')}")

    # Check Scene 2
    if len(scenes) > 1:
        s2 = scenes[1]
        print("\n--- SCENE 2 ---")
        print(f"Summary: {s2.get('summary')}")
        print(f"Visual setup: {s2.get('visual_setup') or s2.get('description')}")

    # Check Middle Scene (Body)
    mid_idx = len(scenes) // 2
    if len(scenes) > mid_idx:
        sm = scenes[mid_idx]
        print(f"\n--- SCENE {mid_idx+1} (BODY/THÂN BÀI) ---")
        print(f"Summary: {sm.get('summary')}")
        print(f"Visual setup: {sm.get('visual_setup') or sm.get('description')}")
        print(f"Narration: {sm.get('narration')}")

    # Check Final Scene (Conclusion)
    if len(scenes) > 0:
        sf = scenes[-1]
        print(f"\n--- SCENE {len(scenes)} (CONCLUSION/KẾT THÚC) ---")
        print(f"Summary: {sf.get('summary')}")
        print(f"Visual setup: {sf.get('visual_setup') or sf.get('description')}")
        print(f"Narration: {sf.get('narration')}")

# 2. Check anchor_used.json & visual_mapping.json
anchor_path = Path(r"d:\STORYBOARD_AI\studio\productions\v-tranh\episode_001\anchor_used.json")
if anchor_path.exists():
    print("\n--- ANCHOR USED ---")
    print(anchor_path.read_text(encoding="utf-8"))

v_map_path = Path(r"d:\STORYBOARD_AI\studio\productions\v-tranh\episode_001\visual_mapping.json")
if v_map_path.exists():
    print("\n--- VISUAL MAPPING (first 500 chars) ---")
    print(v_map_path.read_text(encoding="utf-8")[:500])
