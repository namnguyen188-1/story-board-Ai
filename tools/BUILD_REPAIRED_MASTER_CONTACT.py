"""Review six repaired Muse master sheets in one smaller contact sheet."""
from PIL import Image,ImageDraw,ImageOps
from pathlib import Path
import json
ep=Path(r"D:\STORYBOARD_AI\studio\productions\THI-N-S-HUY-N-PH-TR-N-QU\episode_001")
m=json.loads((ep/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
target={"locations":["thanh_van_mountain_pass","hong_dang_village_gate","hong_dang_old_street"],
"props":["tui_phu_pouch","huyen_phu_talisman","bamboo_walking_staff"]}
cards=[]
for kind,ids in target.items():
 for id in ids:
  folder=ep/"00_ASSET_PACK"/(m[kind][id]["folder"]+"_repair_20261031")
  p=folder/"muse_original_4views.png"
  if not p.is_file():
   print("REPAIR_NOT_READY",kind,id,flush=True)
   continue
  im=Image.open(p).convert("RGB")
  im=ImageOps.contain(im,(860,500))
  cards.append((kind+"/"+id,im))
panel=Image.new("RGB",(1720,1560),(12,19,29))
for j,(name,im) in enumerate(cards):
 x=(j%2)*860+(860-im.width)//2
 y=(j//2)*520+45+(470-im.height)//2
 panel.paste(im,(x,y))
 ImageDraw.Draw(panel).text(((j%2)*860+15,(j//2)*520+10),name,fill="white")
out=ep/"review_repaired_six_assets.jpg"
panel.save(out,quality=81,optimize=True)
print("SIX_REPAIR_REVIEW_IMAGE",out,"images",len(cards),"size",out.stat().st_size,flush=True)
