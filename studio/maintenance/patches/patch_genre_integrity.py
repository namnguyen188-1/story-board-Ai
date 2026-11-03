"""Targeted production reliability improvements. No API calls."""
from pathlib import Path
import shutil,datetime,py_compile
r=Path(r"D:\STORYBOARD_AI\studio")
sfile=r/"series_studio.py"
cp=r/"checkpoints"/("genre_integrity_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
cp.mkdir(parents=True,exist_ok=True)
shutil.copy2(sfile,cp/sfile.name)
s=sfile.read_text(encoding="utf-8")
a='''    # Freeze the visual anchor per episode for reliable restarts.
    style_anchor=series_dir/"series_style_anchor.png"'''
b='''    # Style anchors MUST be isolated by story and genre, otherwise a new
    # cinematographic film can inherit a whiteboard frame from another film.
    style_anchor=(series_dir/"style_anchors"/
                 (args.genre+"_"+args.visual_style+"_"+
                  hash_of(prompt[:2400])[:16]+".png"))
    style_anchor.parent.mkdir(parents=True,exist_ok=True)
    # Freeze the visual anchor per episode for reliable restarts.'''
assert a in s
s=s.replace(a,b,1)
a='''        audio=scene_dir/"audio.wav"
        if not audio.exists() or audio.stat().st_size<2000:'''
b='''        audio=scene_dir/"audio.wav"
        if not audio.exists() or audio.stat().st_size<2000:'''
assert a in s
# Check script audio length against locked scene. Never distort the supplied dialog.
a='''            if Path(generated).resolve()!=audio.resolve():
                shutil.copy2(generated,audio)
    silent=scene_dir/"silent.mp4"'''
b='''            if Path(generated).resolve()!=audio.resolve():
                shutil.copy2(generated,audio)
        if scene.get("locked_script"):
            with wave.open(str(audio),"rb") as recorded:
                spoken_seconds=recorded.getnframes()/max(1,recorded.getframerate())
            allowed_seconds=float(scene.get("script_seconds",job.get("scene_seconds",8)))
            if spoken_seconds>allowed_seconds*1.25+0.4:
                raise RuntimeError(
                    "LOCKED_SCRIPT_DIALOGUE_TOO_LONG: speech %.2fs exceeds "
                    "scene %.2fs. Original words have NOT been changed. "
                    "Shorten the dialogue or extend the scene duration."
                    %(spoken_seconds,allowed_seconds))
    silent=scene_dir/"silent.mp4"'''
assert a in s;s=s.replace(a,b,1)
a='''                    "existing queue work must not be altered")):'''
b='''                    "existing queue work must not be altered",
                    "locked_script_dialogue_too_long")):'''
assert a in s;s=s.replace(a,b,1)
sfile.write_text(s,encoding="utf-8")
py_compile.compile(str(sfile),doraise=True)
print("GENRE_SCOPED_STYLE_ANCHOR_COMPILE_PASS")
print("LOCKED_DIALOGUE_DURATION_GUARD_COMPILE_PASS")
print("CHECKPOINT",cp)
