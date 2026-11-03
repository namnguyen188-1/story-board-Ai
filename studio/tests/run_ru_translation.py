import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add studio to sys.path
studio_dir = Path(__file__).resolve().parent.parent
if str(studio_dir) not in sys.path:
    sys.path.insert(0, str(studio_dir))

from resilient_gemini import ResilientClient
from series_studio import force_translate_chunk_to_language, validate_scene_language, get_api_keys

def main():
    plan_path = Path("studio/productions/DRAMA-2/episode_002/plan.json")
    if not plan_path.exists():
        print(f"Error: {plan_path} does not exist")
        return 1
    
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    chunk = {"scenes": plan["scenes"]}

    print("Initial validation:")
    for sc in chunk["scenes"]:
        is_valid = validate_scene_language(sc.get("narration", ""), "Russian")
        print(f"Scene {sc.get('scene_number')}: valid_ru={is_valid}")

    keys = get_api_keys()
    if not keys:
        print("Error: No API keys found")
        return 1
    client = ResilientClient(api_keys=keys)
    translated_chunk = force_translate_chunk_to_language(client, "gemini-3.5-flash", chunk, "Russian")

    print("\nPost-translation validation:")
    all_ok = True
    for sc in translated_chunk["scenes"]:
        valid = validate_scene_language(sc.get("narration", ""), "Russian")
        print(f"Scene {sc.get('scene_number')}: valid_ru={valid}")
        print(f"  Summary: {sc.get('summary')}")
        print(f"  Narration: {sc.get('narration')}")
        print(f"  Overlay: {sc.get('text_overlay')}")
        if not valid:
            all_ok = False

    if all_ok:
        plan["scenes"] = translated_chunk["scenes"]
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\nSUCCESS: DRAMA-2 plan.json updated with Russian scenes!")
        return 0
    else:
        print("\nFAILED: Some scenes are still not valid Russian.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
