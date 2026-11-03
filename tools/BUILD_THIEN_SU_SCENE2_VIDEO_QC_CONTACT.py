from PIL import Image,ImageOps,ImageDraw
from pathlib import Path
import subprocess
folder=Path(r"D:\STORYBOARD_AI\studio\productions\THI-N-S-HUY-N-PH-TR-N-QU\episode_001\scenes\scene_0002")
video=folder/"scene_final.mp4"
panel=Image.new("RGB",(1200,240))
for j,t in enumerate((0.5,5,9)):
 out=folder/f"scene2_qc_{t}.jpg"
 p=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-ss",str(t),"-i",str(video),"-frames:v","1",str(out)],capture_output=True,text=True,timeout=35)
 if p.returncode:raise RuntimeError(p.stderr[-400:])
 with Image.open(out) as im:
  thumb=ImageOps.fit(im.convert("RGB"),(400,225))
  panel.paste(thumb,(400*j,15))
 ImageDraw.Draw(panel).text((400*j+8,2),f"SCENE2 Muse VIDEO {t}s",fill="white")
out=folder/"scene2_video_moving_contact.jpg"
panel.save(out,quality=89)
print("SCENE2_MOVING_VIDEO_CONTACT_SAVED",out,out.stat().st_size,flush=True)
