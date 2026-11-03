# Storyboard AI Studio - V2 MCP Image Integration
Date: 2026-10-12

## Implemented
- Storyboard GUI offers 3 selectable image providers: "MCP V2 (web)", "Tuan Stor (V2)", and direct Gemini.
- For MCP, user can select Nano Banana Pro, Nano Banana 2 Lite (default), or Nano Banana 2.1, and an explicit maximum number of new images (default 1).
- Confirm via GUI before submissions; no automatic paid API fallback to Tuấn Stor if MCP fails.
- MCP web queue uses 1 worker only; guard rejects 2-3 render workers to prevent overlapping shared web queue.
- Uses existing V2 code as a read-only import: auto_studio.storyboard_image_backend, transport D:\FLOW_MCP_SERVER.
- Existing V2 MCP mandates output scope under D:\YOUTUBE_SEO_PRO_V2\outputs\projects. Adapter creates a NEW, isolated "storyboard_studio_mcp_<series>_ep<no>" folder there. Original V2 projects/code/config/keys untouched.
- MCP returns verified image receipt with job ID, media integrity and SHA256. Adapter pads 16:9 without stretching and copies a PNG to Storyboard Studio scene assets.
- MVP per-scene mode: one queued image request per scene; no automatic re-submit on uncertain request.
- No extra Gemini prompt-generation call for MCP scenes (uses existing scene descriptions, direction and Story Bible). Gemini TTS still required unless audio is already cached.
- On existing completed episode with another provider, changing provider is refused; use a new episode number rather than silently reusing stale images.
- Running a previously completed scene again reuses existing image/scene MP4.
- Opening the GUI after integration: desktop pythonw process restarted, PID 26120 (as observed).

## Verified
1. Prior REAL browser MCP canary: Nano Banana 2 Lite, 1 image generated, JPEG 1376x768, 365560 bytes; validated SHA256 and receipt, copied to D:\STORYBOARD_AI\studio\mcp_image_test_result.
2. Integration mock transport with REAL canary fixture: valid image, receipt caching no duplicate request, 1-image budget guard, CLI selector parse; tests PASS, no new AI calls.
3. Existing completed episode provider-switch guard PASS.
4. GUI hidden Tk instantiation and 3 provider option discovery PASS.
5. 2-scene offline regression PASS, MP4 constructed.
6. Actual MCP-generated image + previously saved genuine TTS WAV: local whiteboard rendering, burned subtitles, H264/AAC 1280x720 MP4 32.92 seconds PASS. Output D:\STORYBOARD_AI\studio\productions\MCP-Studio-Render-QA\episode_001\scenes\scene_0001\final.mp4.
7. Compileall/doctor PASS. MCP V2 bridge installed and independently reachable at least at last health check.
8. NO fresh paid web generation requests submitted in this integration turn.

## Important limitations
- Multi-scene new-image MCP production from the new GUI has NOT yet passed a full live E2E test; do not claim 4/4 new MCP images.
- V2 Web Tool image queue is shared. Existing completed/pending web tasks may block new submissions. Do not automatically clear or overwrite a shared queue: clear it manually only after checking completed receipts, or develop a safe reconciled queue coordinator.
- Web credits/costs were NOT verified current; "0 credits" seen in older screen is not guaranteed.
- For >1 hour feature-length movies, one job-per-scene and MCP process startup are not optimized. User confirmation and throughput benchmarking required before bulk jobs.
- MCP text-only image requests do NOT currently pass a literal reference image to the model, only character consistency prompts. Review continuity.
- No V2 source/config edits. V2 outputs/projects contains only isolated new integration test folder and separate older canary folder.

## Files
- D:\STORYBOARD_AI\studio\mcp_v2_images.py
- D:\STORYBOARD_AI\studio\series_studio.py
- D:\STORYBOARD_AI\studio\studio_gui.py
- D:\STORYBOARD_AI\studio\test_mcp_integration_safe.py
- D:\STORYBOARD_AI\studio\test_mcp_provider_lock.py
- D:\STORYBOARD_AI\studio\test_mcp_image_local_render.py
- D:\STORYBOARD_AI\studio\checkpoints\mcp_provider_integration_20261012
