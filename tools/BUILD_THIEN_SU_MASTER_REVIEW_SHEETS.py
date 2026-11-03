from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
import json,math
ep=Path(r"D:\STORYBOARD_AI\studio\productions\THI-N-S-HUY-N-PH-TR-N-QU\episode_001")
m=json.loads((ep/"00_ASSET_PACK"/"asset_bible.json").read_text(encoding="utf-8"))
for kind in ("characters","locations","props"):
 entries=list(m[kind].items())
 width=930;height=540;cols=2
 result=Image.new("RGB",(width*cols,math.ceil(len(entries)/cols)*height),(16,23,34))
 for i,(aid,asset) in enumerate(entries):
  p=ep/"00_ASSET_PACK"/asset["folder"]/"muse_original_4views.png"
  with Image.open(p) as im:
   im=ImageOps.contain(im.convert("RGB"),(width-20,height-60))
   x=(i%cols)*width+(width-im.width)//2
   y=(i//cols)*height+52+(height-60-im.height)//2
   result.paste(im,(x,y))
  dr=ImageDraw.Draw(result)
  dr.text(((i%cols)*width+14,(i//cols)*height+10),f"{kind.upper()} | {aid}",fill=(251,251,251),stroke_width=1,stroke_fill=(0,0,0))
 output=ep/f"review_contact_{kind}.jpg"
 result.save(output,quality=87,optimize=True)
 print("REVIEW_SHEET",kind,len(entries),output,result.size,flush=True)
