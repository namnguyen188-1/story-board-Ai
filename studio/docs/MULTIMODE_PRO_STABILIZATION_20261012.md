# Storyboard AI Studio Pro — multimode/color/voice stabilization report
Date: 2026-10-12, local computer
Status: INTEGRATED + OFFLINE REGRESSION PASS; LIVE LINK ANALYSIS BLOCKED BY PROVIDER 503

## Production UI and desktop
- Real desktop application restarted successfully as python PID 11020.
- localhost Studio web UI HTTP 200, JS HTTP 200. The six new controls were verified in HTML: genre, visual style, input mode, YouTube URL, narrator voice, region.
- Cache buster added for current JavaScript bundle.
- 3 input modes: idea -> AI script; public YouTube link -> provider analysis -> NEW original script; locked screenplay -> preserve 8 prestructured scenes without script rewrite.
- Genre visuals: Stoicism, family drama, Western, action, history, documentary, animation, whiteboard.
- Supported styles: photorealistic cinematic color; colorful 2D/3D illustrated; traditional whiteboard.
- Separate style anchors based on genre + visual style + premise hash prevent cross-genre references.
- Narrator voice auto-selected by genre/language or selected manually; region-specific style prompt for Spanish ES/MX and other languages. NO multi-character speaker casting yet.

## Evidence
1. Previously completed 8/8-scene locked HOA screenplay offline MP4 E2E PASS, no Gemini calls.
2. Cached MCP image + saved real speech audio generated and validated 4s color-cinematic video with subtitles: H264/AAC, passed.
3. Silent locked scene generates silent WAV, skips TTS/subtitles: 3s local E2E PASS.
4. Audio overflow regression: existing 31.8s WAV attached to locked 8s scene was blocked with LOCKED_SCRIPT_DIALOGUE_TOO_LONG, PASS.
5. Date 2026-10-12 live Gemini Spanish narrator: voice Charon, 5.28s WAV at 24 kHz, file under diagnostics/spanish_voice_one_probe, REAL API PASS.
6. Public YouTube video analysis against previous user's https://youtu.be/0ArKOVnNgio with Gemini 3.8 returned HTTP 503 (NOT PASS).
7. Alternate Gemini 3.6 analysis against documented short YouTube sample returned HTTP 503 (NOT PASS).
8. Official Google API docs confirm passing file_data.file_uri YouTube URL is supported in preview, but this does not override failure from current provider.
9. Improved user-visible link 503 message with manual idea/locked-script fallback, and NO fake video analysis. Mocked 503 error PASS.
10. test_multimode_no_api.py PASS: locked scenes, country voice, URL whitelist, URL mock analysis, color image prompt and render, rejection of invalid UI requests.
11. Desktop HTML and JavaScript verified directly after reboot; no active film production was interrupted.

## Remaining work / not claimed
- NOT certified: full new image-provider and full color long-episode LIVE end-to-end after genre upgrades. Next test should use explicit user-approved image budget.
- NOT certified: real YouTube URL analysis until Gemini server 503 resolves or compatible upstream provider is available.
- NOT built: multiple separate character voices or genuinely animated characters; narration is single-speaker and color renderer uses subtle camera zoom/pan over images.
- Film-length 1–2 hours stability, TTS scene pacing and speaker continuity need dedicated review.
- No original V2 source/config/key modifications, and no Git. Temporary QA outputs saved under Studio.
- Code checkpoints: multimode* and genre_integrity* folders in Studio/checkpoints.

## Verified files
D:\STORYBOARD_AI\studio\series_studio.py
D:\STORYBOARD_AI\studio\web_server.py
D:\STORYBOARD_AI\studio\web\index.html
D:\STORYBOARD_AI\studio\web\app.js
D:\STORYBOARD_AI\studio\studio_modes.py
D:\STORYBOARD_AI\studio\studio_input_modes.py
D:\STORYBOARD_AI\studio\studio_color_render.py
D:\STORYBOARD_AI\studio\mcp_v2_batch.py
