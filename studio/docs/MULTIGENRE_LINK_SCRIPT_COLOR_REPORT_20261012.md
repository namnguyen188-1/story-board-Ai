# Storyboard AI Studio Pro - multi-genre, original video URL analysis, locked-script and color rendering
Date: 2026-10-12
VERDICT: IMPLEMENTED WITH TESTED CORE. New public-YouTube live analysis and accent audio have NOT yet been tested with paid calls.

## User-facing controls in the REAL Desktop web UI
- Production genre: Auto (keyword classifier for text; Gemini video analysis for YouTube), Stoicism, family drama, Western, action, history, documentary, animation, and whiteboard.
- Visual style: auto by genre, cinematic full color, colorful 2D/3D animation, or original whiteboard.
- Language, region/accent: Auto (YouTube), Spain Spanish, Mexico Spanish, Vietnam, US, UK, France, Brazil and Japan.
- Narrator voice: Auto by genre, region, and language, with the existing eight explicit voice choices retained. This mode is SINGLE NARRATOR; multi-character casting is not yet implemented.
- Input: idea (LLM creates original script); YouTube URL (Gemini analyzes PUBLIC YouTube video and constructs a distinct original creative premise); locked user screenplay, with SHOT 1 / SHOT 2 / CẢNH 1 / CẢNH 2 headers.
- Public YouTube URLs go to official Gemini video understanding via google.genai Content/Part(FileData), no full YouTube file download required. Rejects unknown/private hosts and malformed video IDs.
- Script mode bypasses AI screenplay rewriting; preserves the original dialogue extracted from audio/dialogue blocks, scene order, scene descriptions, and scene count. Missing spoken dialogue => local silence; no TTS call and no empty subtitles.

## Production mechanics
- Narrative/country style resolution: studio_modes.py.
- Script parsing and YouTube analysis: studio_input_modes.py.
- New color/image effects renderer: studio_color_render.py, local ffmpeg zoompan (full-color image from scene beginning, no black-and-white whiteboard reveal).
- MCP Nano Banana image prompts are genre-aware. Direct Gemini / Tuấn Stor color prompts bypass whiteboard-only prompt-generator; whiteboard mode remains explicit and intact.
- Gemini 3.8 TTS uses per-shot metadata for genre/accent and one stable chosen voice. Does NOT claim a guarantee that the model truly reproduces an exact accent; needs listening tests.
- Old plan art/voice/provider guards and checkpoint policy remain in place. No changes to source/config of D:\YOUTUBE_SEO_PRO_V2.
- Code backups made under checkpoints/multigenre_modes_20261012_153314 and checkpoints/multigenre_desktop_20261012_153446.

## Verifications actually executed (no paid API calls)
1. Parsed the real 8-SHOT HOA script from prior Episode 3: 8/8 scenes preserved, original Vietnamese dialogue found. Scene 6 has no speech.
2. A new locked screenplay production with all eight scenes finished: offline full episode MP4, 8/8 clips, 24.043 seconds, manifest PASS, exit 0. File productions/Locked-Screenplay-Eight-Scenes-E2E-QA/episode_001/episode_final.mp4. Synthetic offline audio/visuals used: this proves structural mapping/assembly, not real TTS.
3. Real, previously verified MCP-generated image and prerecorded human-speech WAV -> new color clip with actual audio + burned subtitles, H.264/AAC, 640x360, 4.0s, QC PASS. Path productions/Colored-Stoic-Render-QA/episode_001/scenes/scene_0001/final.mp4.
4. Fully silent 3.0s color clip with proper WAV/AAC, no Gemini TTS call, no subtitles file, QC PASS.
5. Mocked Gemini public YouTube URL analysis via SDK structure, URL allowlist and server validation PASS. NO real paid YouTube link analysis request.
6. Region/genre voice mapping and color image prompt checks PASS.
7. Full code compileall and JS syntax checks exit 0.

## Caveats and follow-up
- Official Gemini docs support public YouTube URLs; real access depends on account/model, video visibility and quotas, so do a one-link canary before relying on it.
- Preview stills with camera motion are not genuine moving live-action video; for character performance, a video generation/animation engine remains necessary.
- AI voice custom regional accent has NOT been auditioned in Spanish or Vietnamese; no fabricated accent quality claims.
- Existing scripts with no numbered scene headers are rejected before charge, rather than silently re-written.
- Video editing and TTS for 1-2h movie has not been verified; do 3-5 minute canary and long-run stress checks before production.
