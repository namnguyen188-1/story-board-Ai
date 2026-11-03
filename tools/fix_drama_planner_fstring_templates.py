from pathlib import Path
p=Path(r"D:\STORYBOARD_AI\studio\cinematic_engine\drama_planner.py")
t=p.read_text(encoding="utf-8")
pairs=[
 ('"wardrobe_state": {"Character 1": "outfit_id_stable_for_this_act"},','"wardrobe_state": {{"Character 1": "outfit_id_stable_for_this_act"}},'),
 ('"prop_state": {"hero_prop_id": {"holder": "Character 1", "hand": "left", "position": "held"}},','"prop_state": {{"hero_prop_id": {{"holder": "Character 1", "hand": "left", "position": "held"}}}},'),
 ('"locations": {"living_room": {"name": "Living room", "spec": "Exact furniture, windows, door and lighting layout; same across all scenes"}},','"locations": {{"living_room": {{"name": "Living room", "spec": "Exact furniture, windows, door and lighting layout; same across all scenes"}}}},'),
 ('"props": {"black_phone": {"name": "Lan black phone", "spec": "Same exact model, color, size, finish throughout story"}},','"props": {{"black_phone": {{"name": "Lan black phone", "spec": "Same exact model, color, size, finish throughout story"}}}},'),
 ('"wardrobe_state": {"Character 1": "outfit_act_1"},','"wardrobe_state": {{"Character 1": "outfit_act_1"}},'),
 ('"prop_state": {"black_phone": {"holder": "Character 1", "hand": "left", "position": "held"}},','"prop_state": {{"black_phone": {{"holder": "Character 1", "hand": "left", "position": "held"}}}},')
]
for old,new in pairs:
 n=t.count(old)
 if n!=1:raise RuntimeError("FORMAT_TEMPLATE_NOT_UNIQUE: "+old+" count "+str(n))
 t=t.replace(old,new)
p.write_text(t,encoding="utf-8")
print("PLANNER_FSTRING_SAMPLES_ESCAPED",len(pairs))
