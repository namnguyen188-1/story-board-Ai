# Multi-role cinematic drama — ASSET FIRST (branch-specific overlay)

Scope: production_mode=cinematic_drama ONLY. This document overrides the generic SKILL.md line 'Text-to-video độc lập, không đòi ảnh tham chiếu' ONLY for multi-role cinematic drama. All other modes retain their 9-field text-only contract unchanged.

1. INPUT: idea/script/competitor link -> preserve screenplay meaning, scene dialogue and source evidence.
2. Extract cast, physical locations, and hero props into immutable IDs and the Episode Story Bible BEFORE any video prompt is submitted.
3. Generate real photo references in preproduction: EACH character MUST have actual front, 3/4, side and back images. Do NOT crop one portrait into four false angle images, flip/mirror/blur a portrait, or use grey line silhouettes as completed references.
4. Generate and version physical location reference plates with stable architecture/furniture geometry and clear light direction. Generate and version prop reference plates with identical material/color/size and identifying features.
5. No scene video until the 3 required asset groups are present AND approved; version each by hash and mark stale if changed. Missing assets are BLOCKED_PREPRODUCTION, not PASS.
6. For every scene create scene_asset_binding.json: cast IDs, wardrobe, location ID, prop IDs, physical ownership/positions, start/end-state and hashes. Image generation uses exactly approved assets. The approved scene image is scene_master.png, distinct from actor portraits.
7. MUSE VIDEO MUST take approved scene_master.png as a real image-to-video input using an operation that truly supports image conditioning, not a text instruction claiming it does. If unverified, do NOT present it as I2V.
8. All nine canonical fields and order stay unchanged. Reference paths, hashes and IDs travel in sidecar JSON, not extra top-level TXT fields.
9. START/END states preserve who holds what in which hand, room/door geometry and lighting. A changed prop requires scripted action.
10. Voice and captions align to rendered audio; one voice per character, no subtitle before words. Native Muse audio only counts as matched if checked.
11. QC: ASSET_VALID, IMAGE_VALID, I2V_VERIFIED, SCENE_CONTINUITY, SPEECH_SYNC, EPISODE_PASS. Still-motion fallback is NEVER PASS for I2V. No auto-publish of missing/fallback scenes.
