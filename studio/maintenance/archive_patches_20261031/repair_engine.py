from pathlib import Path
import re, json, py_compile
root = Path(r"D:\STORYBOARD_AI\studio\engine")
patched = []
for name in ("draw_animation.py","image_gen.py","tts.py","reference_search.py","segmentation.py","video_gen.py"):
    p = root / "tools" / name
    s = p.read_text(encoding="utf-8")
    count = s.count("timestamp = int(time.time())")
    if count:
        s = "import uuid\n" + s
        s = s.replace("timestamp = int(time.time())", "timestamp = uuid.uuid4().hex")
        p.write_text(s, encoding="utf-8")
        patched.append({"path":name,"uuid_replacements":count})
p = root / "tools" / "draw_animation.py"
s = p.read_text(encoding="utf-8")
s = s.replace("    video_object = cv2.VideoWriter(", "    video_object = cv2.VideoWriter(", 1)
needle = "    # canvas initialized to white"
if "if not video_object.isOpened()" not in s:
    assert needle in s
    s = s.replace(needle, "    if not video_object.isOpened():\n        raise RuntimeError('Failed to open OpenCV VideoWriter; codec/disk unavailable')\n\n" + needle, 1)
p.write_text(s,encoding="utf-8")
p=root/"tools"/"director.py"
s=p.read_text(encoding="utf-8")
marker="        # Fallback to a basic structure if parsing fails"
assert marker in s
s=s[:s.index(marker)] + "        raise RuntimeError('Director failed: invalid or missing story plan; refusing to render placeholder scenes') from e\n"
p.write_text(s,encoding="utf-8")
p=root/".env.example"
p.write_text('# Separate Storyboard Studio API key; never share with V2\nGEMINI_API_KEY=\n',encoding="utf-8")
for p in [root/"tools"/n for n in ("draw_animation.py","image_gen.py","tts.py","reference_search.py","segmentation.py","video_gen.py")]+[root/"tools"/"director.py"]:
    py_compile.compile(str(p),doraise=True)
print("PATCH_OK",json.dumps(patched))
