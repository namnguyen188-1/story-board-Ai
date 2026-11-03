"""Prepare a 6-scene, two-character, two-place, three-prop, isolated E2E.
Explicit states are aligned across scene boundaries and never mutate old
production episodes. Reuses the existing approved Lan/living-room/phone
master assets, and asks Muse only for the newly needed masters.
"""
from pathlib import Path
import sys,json,copy
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from cinematic_engine.drama_asset_first import build_manifest,validate_assets,atomic_write,slug
ep=Path(r"D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e\episode_001")
old=json.loads((ep/"drama_plan.json").read_text(encoding="utf-8"))
prior=old["scenes"][0]
living=prior["setting"]
office="Company office - dark oak desk centered facing a large north window, black leather chairs, white plaster walls, bookcase west wall, door on right, natural daylight"
lan=old["cast"]["Lan"]
minh={"appearance_lock":"Vietnamese male, 38, high cheekbones, scar along right jawline, pale olive skin, short black hair graying temples, dark navy wool vest over charcoal shirt, worn brown leather apron.",
      "attire":"dark navy wool vest, charcoal rolled-sleeve shirt, worn brown leather apron; dark pants"}
# A structured prop state describes physical state at scene START and END.
def st(who,where,hand=None):
    return {"holder":who,"position":where,"hand":hand}
a=st("Lan","held","left");b=st("Minh","held","right")
c=st(None,"on_wood_table");keyp=st("Minh","in_pocket");keyl=st("Lan","held","right")
desk=st(None,"on_office_desk")
def shot(n,setting,chars,props,desc,prev,next_,line,actor):
    pstate={}
    for k in set(prev)|set(next_):
        pstate[k]={"start":prev.get(k),"end":next_.get(k)}
    return {"scene_number":n,"setting":setting,"location_id":"vietnamese_family_living_room_warm_beige_walls_one_grey_fabric_co" if n<=3 else "company_office",
      "sequence_id":"living_room_sequence" if n<=3 else "company_office_sequence",
      "summary":desc,"visual_setup":desc+" Photorealistic cinematic scene still, medium shot, correctly identify characters, never alter wardrobe, room geometry, phone, dossier or key.",
      "start_state":"Continuing from previous state: "+str(prev),
      "end_state":"At end: "+str(next_),"characters_present":chars,
      "props_required":props,"prop_state":pstate,
      "wardrobe_state":{slug(x):"outfit_01" for x in chars},
      "dialogue_beats":[{"speaker":actor,"text":line,"tone":"confrontational" if n<=3 else "serious",
        "action":"Character holds the right item as shown in the frame"}],
      "camera_motion":"slow_dolly_in","bgm_mood":"emotional_revelation","sfx_cues":[]}
# Scenes 1-3 share the identical living-room master. 4-6 use company office.
scenes=[
shot(1,living,["Lan"],["dien_thoai"],
 "Lan stands by gray sofa in the original warm beige family living room, holding dark phone in LEFT hand while looking down at it",
 {"dien_thoai":a},{"dien_thoai":a},"Anh đã giấu em điều gì?","Lan"),
shot(2,living,["Lan","Minh"],["dien_thoai"],
 "Minh in navy vest and dark shirt approaches Lan in beige coat in same living room; Lan passes a dark phone from her LEFT hand to Minh RIGHT hand",
 {"dien_thoai":a},{"dien_thoai":b},"Em muốn biết sự thật.","Minh"),
shot(3,living,["Lan","Minh"],["dien_thoai","ho_so"],
 "Lan looks toward Minh, who holds the dark phone in his RIGHT hand; a red dossier lies on wooden coffee table in the same family living room",
 {"dien_thoai":b,"ho_so":c},{"dien_thoai":b,"ho_so":c},"Chúng ta phải nói chuyện.","Lan"),
shot(4,office,["Lan","Minh"],["ho_so","chia_khoa"],
 "Lan and Minh stand opposite each other in the company office with oak desk and north window; red dossier on the desk; Minh holds the small brass key in his pocket",
 {"ho_so":desk,"chia_khoa":keyp},{"ho_so":desk,"chia_khoa":keyl},"Chìa khóa ở đây.","Minh"),
shot(5,office,["Lan","Minh"],["ho_so","chia_khoa"],
 "Medium two-shot in same company office; Lan holds small brass key RIGHT hand, red dossier rests on oak office desk, Minh in same navy vest watches",
 {"ho_so":desk,"chia_khoa":keyl},{"ho_so":desk,"chia_khoa":keyl},"Anh đã nói dối em.","Lan"),
shot(6,office,["Lan","Minh"],["ho_so","chia_khoa"],
 "Lan sets small brass key on office desk while Minh takes red dossier in his LEFT hand, same office, exact furniture and clothing",
 {"ho_so":desk,"chia_khoa":keyl},{"ho_so":st("Minh","held","left"),"chia_khoa":desk},"Anh sẽ giải thích tất cả.","Minh")
]
# Preserve existing old approval hashes; use exactly same Lan data and style.
old.update(cast={"Lan":lan,"Minh":minh},scenes=scenes,
 locations={office:{"name":"Company office","spec":office}},
 props={"ho_so":{"name":"Red dossier","spec":"single red paper case file, maroon-red cardboard, gold clip, no visible company logo"},
        "chia_khoa":{"name":"Small brass key","spec":"small gold brass door key with triangular single-tooth head and one round hole, 5cm long"}})
# The original E2E sample has already passed; staging only.
atomic_write(ep/"drama_plan.json",old)
m=build_manifest(ep,old)
q=validate_assets(ep,m)
print("SIX_SCENE_PLAN_READY",json.dumps({"scenes":len(m["scenes"]),
 "characters":list(m["characters"]),"locations":list(m["locations"]),
 "props":list(m["props"]),"qc":q},ensure_ascii=False),flush=True)
