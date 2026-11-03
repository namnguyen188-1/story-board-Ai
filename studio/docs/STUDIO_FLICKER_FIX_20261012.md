# Studio flicker fix — 2026-10-12
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
- Fresh cached-photo/speech render: 8.00s 1280x720 H.264/AAC; all 200 frames decoded, 0 white/black flashes; no new AI generation/TTS calls.
- Fresh two-scene original whiteboard regression: PASS, 6.043s H.264/AAC; exit 0.
Scope:
These checks cover UI, local rendering, media playback and output assembly.
They do not establish fresh external AI provider availability or multi-hour production stability.
