# STORYBOARD AI STUDIO — Production Reliability Gate, 2026-10-11

## Scope
Machine: DESKTOP-EE8BGVF
Standalone: D:\STORYBOARD_AI\studio
Upstream pristine: D:\STORYBOARD_AI\storyboard-ai-main
No modifications to D:\YOUTUBE_SEO_PRO_V2.

## Implementation
- Windows desktop GUI, standalone launcher (LAUNCH_STUDIO.bat).
- Episode/series folders, durable story bible and global visual style anchor across episodes.
- Episode prompt/config fingerprint; persist story plan, batches, scene assets, logs, scene result and manifest.
- Separate subprocess and scratch directory per scene; UUID temp filenames (parallel collision fix).
- Sequenced mode for continuity (default 1 worker); 2-3 worker mode with same style anchor.
- Up to 3 retries per failing scene; retry-bypass for authorization errors.
- FFprobe QC and safe concat; no final MP4 produced if missing scenes.
- Resume without repeating previously healthy image/TTS/render stage, and re-render only corrupt/missing scene.
- Models verified against official docs (2026-10-11): Gemini 3.8 Flash, Nano Banana 2.1, Gemini 3.8 Flash TTS.
- TTS handles RIFF/WAV and headerless PCM formats without double-wrapping.
- Separate Gemini API key from studio\.env only; no V2 keys used.

## Executed real local tests

- Source / GUI / engine compileall: PASS.
- Import of full engine incl. google.genai: PASS.
- Python/Tkinter GUI initialization, hidden test: PASS.
- Original engine: three simultaneous draws only 1/3 PASS (confirmed source bug).
- New engine sequential 2 scenes: 2/2 PASS, 6.043-second H264/AAC MP4.
- New engine concurrent 3 scenes: 3/3 PASS, 9.043-second MP4.
- 60-scene orchestration stress with 3 workers: 60/60 PASS in 36.0 seconds; final synthetic video 180.043 seconds. THIS IS NOT A REAL 30-MINUTE AI VIDEO.
- Resume healthy scene: RESUMED 1, RESUMED 2; no repeat render.
- Delete scene 2 final.mp4 and re-run: RESUMED scene 1, regenerated scene 2 PASS.
- Two independent series episodes: 2/2 PASS, style anchor created and reused.
- TTS mocked 3.8 response: WAVE passthrough and raw PCM wrapper, both PASS.
- Original Full HD drawing smoke: 1920x1080 PASS, 4.629-second render for a simple synthetic still; not representative of detailed art.

## Remaining production gates

- NO separate Gemini key provided/configured -> no API-based live E2E yet.
- Test Gemini 3.8 text planning, Nano Banana 2.1 image, 3.8 TTS with an actual key.
- Quality review of character continuity, narration naturalness, speech duration, subtitle timing.
- Test an actual 1–2 minute Gemini-generated episode first; then 30-minute real production with expenses monitored.
- Voice/subtitle script timing remains approximate, not forced alignment.
- This is whiteboard animation (static drawings revealed by hand), not cinematic Veo film.

## Paths
Launcher: D:\STORYBOARD_AI\LAUNCH_STUDIO.bat
Main code: D:\STORYBOARD_AI\studio\series_studio.py
GUI: D:\STORYBOARD_AI\studio\studio_gui.py
Documentation: D:\STORYBOARD_AI\studio\README_STUDIO.md
Real final (synthetic regression): D:\STORYBOARD_AI\studio\productions\Long-Form-Stress\episode_001\episode_final.mp4
Manifest: D:\STORYBOARD_AI\studio\productions\Long-Form-Stress\episode_001\manifest.json

Verdict: OFFLINE ENGINE AND SERIES ORCHESTRATION PASS. LIVE AI PRODUCTION NOT YET VERIFIED.
