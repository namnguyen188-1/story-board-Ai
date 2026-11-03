from pathlib import Path
import subprocess
from PIL import Image,ImageOps,ImageDraw
base=Path("D:/STORYBOARD_AI/studio/scratch/multi_role_asset_first_e2e/episode_006")
scenes=base/"scenes"
W,H=480,270
image=Image.new("RGB",(W*6,H*3),(18,22,35))
for col in range(6):
 d=scenes/("scene_%04d"%(col+1))
 src=d/"scene_final.mp4"
 if not src.is_file():raise RuntimeError("MISSING_VIDEO_%d"%(col+1))
 for row,t in enumerate((0.5,5,9)):
  name=d/("motion_qc_%d.png"%int(t*10))
  cmd=["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(t),
      "-i",str(src),"-frames:v","1",str(name)]
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=35)
  if r.returncode:raise RuntimeError("FFMPEG_SNAPSHOT_FAILED "+str(r.stderr[-300:]))
  with Image.open(name) as im:
   frame=ImageOps.fit(im.convert("RGB"),(W,H))
   if row==0:
    dr=ImageDraw.Draw(frame)
    dr.rectangle((0,0,177,30),fill=(24,32,40))
    dr.text((7,8),f"SCENE {col+1} | {t}s",fill="white")
   image.paste(frame,(W*col,H*row))
out=base/"six_moving_scene_contact_3_times.jpg"
image.save(out,quality=91)
print("MOVING_VIDEO_VISUAL_CONTACT_SHEET",out,str(out.stat().st_size),flush=True)
