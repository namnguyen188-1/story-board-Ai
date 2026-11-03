import sys,json
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
ep=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
out=ep/"six_scene_storyboard_contact_sheet.jpg"
slots=[]
for i in range(1,7):
 path=ep/"scenes"/("scene_%04d"%i)/"scene_master.png"
 if not path.is_file():
  print("MISSING_SCENE_IMAGE",i,flush=True)
  continue
 with Image.open(path) as src:
  frame=ImageOps.fit(src.convert("RGB"),(640,360))
  d=ImageDraw.Draw(frame)
  d.rectangle((0,0,168,30),fill=(20,20,20))
  d.text((10,7),"SCENE %02d"%i,fill="white")
  slots.append((i,frame.copy()))
if len(slots)==6:
 panel=Image.new("RGB",(1920,720))
 for j,(num,im) in enumerate(slots):
  panel.paste(im,((j%3)*640,(j//3)*360))
 panel.save(out,quality=88)
 print("SIX_SCENE_CONTACT_SHEET",out,flush=True)
else: print("SIX_IMAGES_INCOMPLETE",len(slots),flush=True)
