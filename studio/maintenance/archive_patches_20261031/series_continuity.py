from pathlib import Path
import py_compile
p=Path(r"D:\STORYBOARD_AI\studio\series_studio.py")
s=p.read_text(encoding="utf-8")
needle='    first=task(0,"")'
assert needle in s
replacement='''    # Freeze the visual anchor per episode for reliable restarts.
    style_anchor=series_dir/"series_style_anchor.png"
    episode_anchor=episode_dir/"anchor_used.json"
    if episode_anchor.exists():
        anchor_value=read_json(episode_anchor).get("path","")
    else:
        anchor_value=str(style_anchor) if style_anchor.exists() else ""
        write_json(episode_anchor,{"path":anchor_value,"created":stamp()})
    first=task(0,anchor_value)'''
s=s.replace(needle,replacement,1)
needle2='''    if first["status"]!="FAILED":
        first_image=first["image_path"]
        if args.workers==1:'''
assert needle2 in s
replacement2='''    if first["status"]!="FAILED":
        first_image=first["image_path"]
        if not style_anchor.exists() and Path(first_image).is_file():
            shutil.copy2(first_image,style_anchor)
        if args.workers==1:'''
s=s.replace(needle2,replacement2,1)
p.write_text(s,encoding="utf-8")
py_compile.compile(str(p),doraise=True)
print("SERIES_STYLE_ANCHOR_PATCH_PASS")
