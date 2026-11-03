from pathlib import Path
p=Path(r"D:\STORYBOARD_AI\studio\cinematic_engine\drama_planner.py")
s=p.read_text(encoding="utf-8")
s=s.replace("placement.\\n6. 'props'", "placement.\n6. 'props'")
s=s.replace("same prop.\\n7. 'outline'", "same prop.\n7. 'outline'")
p.write_text(s,encoding="utf-8")
print("PLANNER_LINES_FIXED",flush=True)
