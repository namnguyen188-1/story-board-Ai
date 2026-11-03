# Storyboard AI Studio — V2 Tuấn Stor integration and live E2E (2026-10-11)

## Connection
- Source (read-only): D:\YOUTUBE_SEO_PRO_V2\.env.
- Image gateway: https://tuansuapi.store/v1, image route /images/generations.
- Model from V2: gemini-3.1-flash-image-preview.
- Never log or copy the V2 API key.
- No source/config edits to YouTube SEO Pro V2.
- GUI choice: "Tuấn Stor (V2)" is default, "Gemini trực tiếp" remains optional.
- Story Bible, script planning, image prompt, and TTS still use Studio's separately configured Gemini API key.
- Whiteboard drawing, subtitles and FFmpeg remain local.

## Live API verification
- GET gateway /models HTTP 200; expected image model advertised.
- POST /images/generations HTTP 200, valid base64 PNG, initial test 1024x1024.
- Real series: Whiteboard Chronicles, Episode 001, The City That Lost Time.
- Reused previous verified 4-scene screenplay; no repeat story-plan generation.
- Images created via Tuấn Stor (V2). Narration via Gemini TTS; whiteboard and MP4 locally rendered.
- Scene durations: 32.92, 31.8, 32.24, 33.64 seconds.
- FINAL E2E: PASS 4/4 scenes; no failed scenes.
- Final MP4: D:\STORYBOARD_AI\studio\productions\Whiteboard-Chronicles\episode_001\episode_final.mp4.
- ffprobe: 1280x720 H.264 video, AAC audio, duration 130.642667s, size 6,069,970 bytes.
- Manifest status: PASS.
- Desktop GUI restarted, new provider dropdown now available.

## Safety/quality notes
- Tuấn Stor gateway usage can incur the V2 account's image API costs; do not exceed provider credit limits.
- Image API currently uses tested size 1024x1024, then pads without distortion to 16:9. It does NOT pass character reference images as image-to-image; continuity relies on prompt and series bible. Treat this as a quality limitation for long-running animated series.
- Do a human playback review of narration and subtitle timing before a full 30-minute episode.
- This is successful REAL 2-minute-class AI E2E, not a 30-minute production test.
