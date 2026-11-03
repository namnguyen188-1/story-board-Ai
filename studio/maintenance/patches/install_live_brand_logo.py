from pathlib import Path
import base64,hashlib,shutil,re,datetime
from PIL import Image
root=Path(r"D:\STORYBOARD_AI\studio")
web=root/"web"
assets=web/"assets"
p=assets/"brand-logo.b64"
image=base64.b64decode(p.read_text(encoding="ascii"))
assert hashlib.sha256(image).hexdigest()=="839e9b2e2e0579bfa63a62832b3be6ac9d4db1123031e6871afd7ddecd877415"
logo=assets/"storyboard_ai_icon.png"
logo.write_bytes(image)
with Image.open(logo) as im:
    im=im.convert("RGBA")
    im.save(assets/"storyboard_ai_icon.ico",sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(96,96)])
    im.save(assets/"storyboard_ai_favicon.png")
html=web/"index.html"
css=web/"style.css"
stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup=root/"checkpoints"/("ui_logo_"+stamp)
backup.mkdir(parents=True,exist_ok=True)
shutil.copy2(html,backup/html.name)
shutil.copy2(css,backup/css.name)
before=html.read_text(encoding="utf-8")
old=before
old_icon=re.search(r'(?m)^[ \t]*<link\s+rel="icon"[^\n]*\n',before)
assert old_icon,"favicon not found"
before=before[:old_icon.start()]+'  <link rel="icon" type="image/png" href="assets/storyboard_ai_favicon.png?v=20261012">\n'+before[old_icon.end():]
old_brand=re.search(r'<div class="logo-badge">.*?</div>',before,flags=re.S)
assert old_brand,"logo badge not found"
before=before[:old_brand.start()]+'''<div class="logo-badge">
        <img class="studio-pro-brand-logo" src="assets/storyboard_ai_icon.png?v=20261012" width="34" height="34" alt="Storyboard AI Studio Pro">
      </div>'''+before[old_brand.end():]
style=css.read_text(encoding="utf-8")
style+='''
/* STORYBOARD_AI_PRO_LOGO_20261012 */
.header .brand .logo-badge {
  background: transparent !important;
  border: 0 !important;
  box-shadow: none !important;
  width: 34px !important;
  height: 34px !important;
  padding: 0 !important;
  flex: 0 0 34px !important;
  display: flex;
  align-items: center;
  justify-content: center;
}
.header .brand .logo-badge .studio-pro-brand-logo {
  width: 34px;
  height: 34px;
  display: block;
  object-fit: contain;
  border-radius: 8px;
}
'''
html.write_text(before,encoding="utf-8")
css.write_text(style,encoding="utf-8")
assert "studio-pro-brand-logo" in html.read_text(encoding="utf-8")
assert (assets/"storyboard_ai_icon.ico").stat().st_size>1000
print("LOGO_UI_INSTALLED_PASS")
print("BACKUP",backup)
print("ICON_FILES",[(x.name,x.stat().st_size) for x in assets.glob("storyboard_ai_*")])
