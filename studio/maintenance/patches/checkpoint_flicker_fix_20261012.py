from pathlib import Path
import shutil,hashlib,json,datetime,py_compile
root=Path(__file__).resolve().parent
names=["web/app.js","web_server.py","series_studio.py","studio_hand_color.py","studio_color_render.py",
"engine/tools/merge_audio_video.py","engine/tools/video_subtitle.py","engine/tools/concatenate_videos.py",
"test_ui_flicker_browser.py","test_hand_color_ui_e2e_flicker.py","test_photo_hand_color_flicker.py"]
for name in names:
    if name.endswith(".py"):py_compile.compile(str(root/name),doraise=True)
checkpoint=root/"checkpoints"/("flicker_verified_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
checkpoint.mkdir(parents=True)
hashes={}
for name in names:
    target=checkpoint/name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/name,target)
    hashes[name]=hashlib.sha256(target.read_bytes()).hexdigest()
(checkpoint/"sha256.json").write_text(json.dumps(hashes,indent=2),encoding="utf-8")
docs=root/"docs";docs.mkdir(exist_ok=True)
report="""# Studio flicker fix — 2026-10-12
Root cause reproduced in real Edge/Chromium:
- Four unchanged episode-detail refreshes replaced the scene card DOM.
- Preview fired five loadstart events, reset from 2s to the beginning and resumed a paused video.
- Every renderer/ffprobe child process lacked CREATE_NO_WINDOW on Windows.
Fix:
- Preserve same video source, currentTime and paused state.
- Scene/log signatures avoid redraw when data is unchanged.
- Reconcile cards by ID; stable asset version URLs derive from file modification time.
- Prevent overlapping polls and discard stale episode responses.
- Record first selected scene before rendering cards, avoiding a selection mismatch.
- Hide worker/FFmpeg/ffprobe processes on Windows with per-call creationflags.
- Resolve actual offline episode folder so the real form can show production outputs.
Verification:
- Real browser unchanged refresh: card preserved, loads=0, currentTime=2s, paused=true.
- Fresh offline job started with actual UI controls, two scenes -> MP4 with audio/subtitles.
  Final 6.043s, 150 frames, H.264/AAC; backend exit 0 and manifest PASS.
- During automatic status polling: reloads=0, playback position/pause retained, card preserved.
- Visible console window monitor sampled every 25ms: 0 newly visible consoles.
- Existing 3 hand-color checks, multimode checks, cache switches, silent scene passed.
- Fresh real cached-photo/speech render tested separately; no new AI generation/TTS calls.
Scope:
These checks cover UI, local rendering, media playback and output assembly.
They do not establish fresh external AI provider availability or multi-hour production stability.
"""
(docs/"STUDIO_FLICKER_FIX_20261012.md").write_text(report,encoding="utf-8")
with (docs/"SDD_LEDGER.md").open("a",encoding="utf-8") as f:
    f.write("\n## 2026-10-12 — Studio flicker fix\n")
    f.write("Real-browser reproduction RED -> unchanged refresh and fresh form production GREEN. No preview reloads; cards retained; no new visible console windows in test.\n")
    f.write("Checkpoint: "+str(checkpoint)+"\n")
print("FLICKER_VERIFIED_CHECKPOINT",checkpoint)
