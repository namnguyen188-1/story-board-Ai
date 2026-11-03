from pathlib import Path
import hashlib,json,shutil,datetime
root=Path(__file__).resolve().parent
names=["studio_hand_color.py","studio_modes.py","series_studio.py","web/index.html",
       "test_hand_color_no_api.py","test_hand_color_cache_no_api.py",
       "test_hand_color_http_offline.py"]
backup=root/"checkpoints"/("hand_color_verified_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
backup.mkdir(parents=True)
hashes={}
for name in names:
    target=backup/name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/name,target)
    hashes[name]=hashlib.sha256(target.read_bytes()).hexdigest()
(backup/"sha256.json").write_text(json.dumps(hashes,indent=2),encoding="utf-8")
docs=root/"docs";docs.mkdir(exist_ok=True)
note="""# Full-color hand drawing — 2026-10-12
Status: implemented and locally verified.
- New selectable visual style: hand_color / Vẽ tay toàn bộ ảnh màu.
- Blank whiteboard -> progressive serpentine color strokes with bundled hand ->
  completed full-color artwork, hand removed during final hold.
- Audio controls drawing duration. Aspect ratio is preserved with white padding.
- Streaming BGR frames directly to FFmpeg/H.264; no video/image/TTS API calls for the effect.
- Existing genre art rules retained, with full-color requirement for source artwork.
- Cache style receipt prevents reuse of the old encoded video when entering or leaving hand_color.
- Existing auto, whiteboard, cinematic and animation modes retained.
Verification:
- 3 new local unit/MP4 acceptance checks passed.
- Real cached color artwork + cached speech -> 8.00s 1280x720 H.264/AAC
  through render_one, QC passed, 4.91s measured render time on this device.
- Actual HTTP produce route -> offline two-scene episode, subtitles, concatenation:
  PASS, 6.043s H.264/AAC; backend exit 0.
- Style switch hand_color -> color_cinematic -> hand_color passed;
  artwork/audio SHA256 unchanged.
- Existing multimode, locked silent scene and dialogue-duration guard checks passed.
- Existing eight-scene offline episode regression passed via checkpoint resume.
- Python compile and JavaScript syntax checks passed.
Limits:
- This is simulated hand-drawing of a raster image with broad horizontal strokes.
  It does not reconstruct artist-specific vector pen paths or animate actors.
- Live fresh image generation for this new style has not been charged/tested;
  source prompt is checked and real previously generated artwork was used.
- No new 1-2 hour production stress test was performed.
"""
(docs/"HAND_COLOR_DRAWING_20261012.md").write_text(note,encoding="utf-8")
ledger=docs/"SDD_LEDGER.md"
with ledger.open("a",encoding="utf-8") as f:
    f.write("\n## 2026-10-12 — Full-color hand drawing\n")
    f.write("Implemented hand_color selection and local renderer; 3 acceptance checks, real cached media render, HTTP offline episode and style-cache transitions passed.\n")
    f.write("Verified checkpoint: "+str(backup)+"\n")
print("HAND_COLOR_CHECKPOINT_SAVED",str(backup))
