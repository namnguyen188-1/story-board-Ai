from pathlib import Path
import shutil,datetime
root=Path(__file__).resolve().parent
backup=root/"checkpoints"/("hand_color_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
backup.mkdir(parents=True)
names=["studio_modes.py","series_studio.py","web/index.html"]
for name in names:
    target=backup/name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/name,target)
def replace(name,old,new):
    path=root/name;text=path.read_text(encoding="utf-8")
    if text.count(old)!=1:raise RuntimeError("Patch anchor mismatch "+name+repr(old))
    path.write_text(text.replace(old,new),encoding="utf-8")
replace("studio_modes.py",'"color_animation","whiteboard"}','"color_animation","whiteboard","hand_color"}')
replace("studio_modes.py",'def image_instruction(genre,style):\n',
'''def image_instruction(genre,style):
    if style=="hand_color":
        art=ART["animation"] if genre=="whiteboard" else ART[genre]
        return art+" Full-color completed artwork across the entire scene. Rich but natural colors on subjects and background. No monochrome-only line art; no artist, hand, pen or brush in the source artwork."
''')
replace("web/index.html",'<option value="whiteboard">Vẽ tay trên bảng trắng</option>',
'''<option value="hand_color">Vẽ tay toàn bộ ảnh màu</option>
                <option value="whiteboard">Vẽ tay trên bảng trắng</option>''')
replace("series_studio.py",
'''        if job.get("visual_style","whiteboard")!="whiteboard" and job["mode"]=="live":
            from studio_color_render import color_video
            raw=color_video(image,audio,silent,width,height)''',
'''        if job.get("visual_style")=="hand_color":
            from studio_hand_color import hand_color_video
            raw=hand_color_video(image,audio,silent,width,height)
        elif job.get("visual_style","whiteboard")!="whiteboard" and job["mode"]=="live":
            from studio_color_render import color_video
            raw=color_video(image,audio,silent,width,height)''')
# A style switch must not reuse an older scene's encoded video.
replace("series_studio.py",'    silent=scene_dir/"silent.mp4"\n',
'''    render_style=job.get("visual_style","whiteboard")
    style_receipt=scene_dir/"render_style.json"
    previous_style=(read_json(style_receipt).get("visual_style") if style_receipt.exists() else None)
    if render_style=="hand_color" or previous_style=="hand_color":
        if previous_style!=render_style:
            for name in ("silent.mp4","merged.mp4","final.mp4","result.json"):
                cached=scene_dir/name
                if cached.exists():cached.unlink()
    silent=scene_dir/"silent.mp4"
''')
replace("series_studio.py",'    merged=scene_dir/"merged.mp4"\n',
'''    write_json(style_receipt,{"visual_style":render_style})
    merged=scene_dir/"merged.mp4"
''')
print("HAND_COLOR_INSTALLED",backup)
