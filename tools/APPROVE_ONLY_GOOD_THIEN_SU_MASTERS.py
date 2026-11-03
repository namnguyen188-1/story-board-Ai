"""Direct visual review decisions, inspected master sheet contact images.
Only approve matching actors and pure prop/empty environments; bad masters excluded.
"""
import sys,json,datetime
from pathlib import Path
sys.path.insert(0,r"D:\STORYBOARD_AI\studio")
from drama_asset_review_api import review
from cinematic_engine.drama_asset_first import validate_assets,atomic_write
ep=Path(r"D:\STORYBOARD_AI\studio\productions\THI-N-S-HUY-N-PH-TR-N-QU\episode_001")
approved={
 "characters":["luc_thanh_y","huyen_dao_nhan","tran_vo_canh","lao_dan_lang","linh_ba_bong_ao_do"],
 "locations":["thanh_van_dao_quan","tran_hon_shrine"],
 "props":["thien_thu_book","chu_sa_brush","dong_bell","red_lantern"]
}
rejected={
 "locations":["thanh_van_mountain_pass","hong_dang_village_gate","hong_dang_old_street"],
 "props":["tui_phu_pouch","huyen_phu_talisman","bamboo_walking_staff"]
}
rows=[]
for kind,names in approved.items():
 for aid in names:
  r=review(ep,kind,aid,True)
  rows.append({"kind":kind,"id":aid,"approved":r["approved"]})
for kind,names in rejected.items():
 for aid in names:
  rows.append({"kind":kind,"id":aid,"approved":False,
               "reason":"PHOTO_QC: unrequested people/modern clothes appear in location master or hero prop sheet"})
report={"scope":"THIEN_SU_EP01","reviewer":"assistant direct visual inspection 2026-10-31",
        "approved_count":len([x for x in rows if x["approved"]]),
        "rejected_count":len([x for x in rows if not x["approved"]]),"decisions":rows}
atomic_write(ep/"master_visual_review_20261031.json",report)
qc=validate_assets(ep)
print("MASTER_APPROVAL_RESULT",json.dumps({"approved":report["approved_count"],
"rejected_for_targeted_repair":report["rejected_count"],"status":qc["status"],
"remaining":qc["blocked"]},ensure_ascii=False),flush=True)
