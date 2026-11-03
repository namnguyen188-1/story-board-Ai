import json
from pathlib import Path

drama_plan_path = Path(r"d:\STORYBOARD_AI\studio\productions\ho-t-h-nh-3d\episode_001\drama_plan.json")
if drama_plan_path.exists():
    data = json.loads(drama_plan_path.read_text(encoding="utf-8"))
    scenes = data.get("scenes", [])
    print("=== AUDIT: ho-t-h-nh-3d / episode_001 ===")
    print(f"Title: {data.get('title')}")
    print(f"Logline: {data.get('logline')}")
    print(f"Total scenes: {len(scenes)}")
    print("Cast defined in plan:")
    for name, p in data.get("cast", {}).items():
        print(f"  - {name} ({p.get('role')}, voice {p.get('voice_id')}): {p.get('appearance_lock')[:80]}...")

    # Check Hook (Scene 1-3)
    print("\n--- HOOK (SCENE 1) ---")
    s1 = scenes[0]
    print("Setting:", s1.get("setting"))
    print("Summary:", s1.get("summary"))
    print("Dialogue:", [(b.get("speaker"), b.get("text")) for b in s1.get("dialogue_beats", [])])
    print("Start state:", s1.get("start_state"))
    print("End state:", s1.get("end_state"))

    # Check Midpoint / Escalation (Scene 45)
    print("\n--- BODY / MIDPOINT (SCENE 45) ---")
    s45 = scenes[44]
    print("Setting:", s45.get("setting"))
    print("Summary:", s45.get("summary"))
    print("Dialogue:", [(b.get("speaker"), b.get("text")) for b in s45.get("dialogue_beats", [])])
    print("Start state:", s45.get("start_state"))
    print("End state:", s45.get("end_state"))

    # Check Climax & Conclusion (Scene 89-90)
    print("\n--- CLIMAX & CONCLUSION (SCENE 89-90) ---")
    s89 = scenes[88]
    s90 = scenes[89]
    print("Scene 89 Summary:", s89.get("summary"))
    print("Scene 90 Summary:", s90.get("summary"))
    print("Scene 90 Dialogue:", [(b.get("speaker"), b.get("text")) for b in s90.get("dialogue_beats", [])])
    print("Scene 90 End state:", s90.get("end_state"))
