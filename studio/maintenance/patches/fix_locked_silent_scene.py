from pathlib import Path
import py_compile
p=Path(r"D:\STORYBOARD_AI\studio\series_studio.py")
txt=p.read_text(encoding="utf-8")
old="            shutil.copy2(generated,audio)"
new="            if Path(generated).resolve()!=audio.resolve():\n                shutil.copy2(generated,audio)"
assert old in txt,"AUDIO_SAMEFILE_ANCHOR_MISSING"
p.write_text(txt.replace(old,new,1),encoding="utf-8")
py_compile.compile(str(p),doraise=True)
print("SILENT_SCENE_AUDIO_SAMEFILE_GUARD_PASS")
