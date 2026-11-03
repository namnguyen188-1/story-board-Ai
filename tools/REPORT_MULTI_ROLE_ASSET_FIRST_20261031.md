# STORYBOARD AI — MULTI-ROLE ASSET-FIRST E2E & RELEASE CANDIDATE
Date: 2026-10-31 (Asia/Bangkok)
Device: DESKTOP-EE8BGVF
Scope: cinema drama branch only, preserving narrative, SEO V2, Flow/Muse auth, multi-account scheduler.
Status: **TECHNICAL SIX-SCENE E2E COMPLETE; MANUAL RELEASE QC REMAINS; v1.3.12 RC2 PACKAGED, NOT PUBLISHED.**

## 1. Actual code changes on MAIN PC
- `studio/cinematic_engine/drama_asset_first.py`: build three asset registries with immutable IDs, real four-angle photo hashes and approvals, per-scene bindings, state/wardrobe/prop continuity, explicit cross-location transfer, safe master reuse in subsequent episodes.
- `studio/muse_asset_images.py`: create **real Muse image sheet** with four distinct angles (not Pillow mirror), durable image receipts, no automatic duplicates, actor full-length framing.
- `studio/muse_scene_image.py`: compose real Muse scene still from approved cast, location and hero prop references, receipt/hash proof.
- `studio/cinematic_engine/drama_planner.py`, `drama_schema.py`, `drama_skill9.py`, `drama_voice_director.py`: preserve strict skill 9 fields, propagate location/prop/wardrobe and transition metadata. Cinema-only skill overlay.
- `studio/cinematic_engine/drama_orchestrator.py`: master-first, scene-still-first, pause for approvals, no falsely passing still-motion fallback, no auto-YouTube publish without episode QC.
- `studio/muse_video_provider.py`, `studio/muse_gateway_worker.py`: Muse image input scene composition; unique remote image names by index/SHA to prevent overwriting two different actors' front.png; locked receipts survive changed prompts, failures or pending jobs without automatic resubmission.
- `studio/cinematic_engine/drama_aspect_repair.py`: preserves native 3:2 Muse original and creates explicitly marked 16:9 full-frame-preserving side-fill adaptation, no new paid video call, no claim of native widescreen.
- `studio/drama_asset_review_api.py`, `studio/web/drama_asset_review.js`, `studio/web/index.html`, `studio/web_server.py`: in-app master/scene image review with explicit approval/reject.

## 2. Isolated real Muse E2E, NOT production series overwritten
- Workbench: `D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e\episode_006`
- Inputs: 6 scenes, 2 original Muse actors (Lan, Minh), 2 approved physical sets (living room, office), 3 hero props (phone, red dossier, brass key).
- 7/7 master image groups generated with real Muse reference sheets, image SHA stored. Minh waist-cropped 4-angle image was rejected; targeted repair generated four genuine full-body views.
- 6/6 Muse scene stills created from approved references. Scene 1 sofa wrong angle and scene4 key position were each corrected with a targeted single still redo. 6/6 approved stage scene stills; storyboard contact sheet `six_scene_storyboard_contact_sheet.jpg`.
- 6/6 real Muse videos generated, 10s each. Scene1,2,5 near-native 16:9; scene3,4,6 returned native Muse 1152x768 (3:2), original MP4 preserved and aspect adapted to 1280x720 with blurred side extension; all conversions explicitly labeled and must be visually reviewed.
- 6/6 original Vietnamese dialogue ASR text **exact** vs screenplay, native-audio subtitle word intervals, script_mismatch=false for each.
- Scene4 original showed a phantom key on clothing; single targeted Muse retake, handoff visibly correct at 0.5s/5s/9s, source and original preserved. Final review movie selects retake.
- FINAL REVIEW MOVIE: `D:\STORYBOARD_AI\studio\scratch\multi_role_asset_first_e2e\episode_006\SIX_SCENES_MUSE_E2E_60S_RETAKE4.mp4`
  Duration 60.178s, video+audio, 13,278,468 bytes, SHA256 E26126DF0A887B6911A5784B579029A577AAB43F6FCE012055A0A7AE2C123A5.
- Visual frames inspected for all 6 videos (0.5,5,9) and retake scene4; no blanket guarantee of 100% continuity from sampled frames. Publish false until full-video human review.
- QC `six_scene_final_retaked_qc.json` status SIX_REAL_MUSE_SCENES_E2E_TECHNICAL_COMPLETE_REVIEW_NEEDED.

## 3. Regression and UI
- 10/10 test suites PASS, 39/39 tests including 10/10 Muse gateway receipt/dedup tests under bundled Muse Python (PyAV).
- Source Python compilation PASS. Headless Chrome clicked drama mode -> review button -> 13/13 asset preview cards; staging API/photo HTTP 200.
- Live main backend restarted only after verifying production running=false, queue.active=false, queue.items empty. Launcher auto-respawned backend PID 53936. Live app `/api/status` HTTP 200, new review UI JS HTTP 200, new index script tag HTTP 200. Existing launcher PID 12848 preserved.

## 4. Verified update package (NOT published)
- `D:\STORYBOARD_AI\dist\Storyboard_AI_Studio_Pro_v1.3.12_RC2.zip`
- Source v1.3.11, preserves original native launcher EXE, UI, Muse runtime and dependency tree, 24 source-file overlays.
- ZIP 286,321,864 bytes, 10,222 files, SHA256 A3C83F7ACC3AE8A91900B5C27E7EC9474E63389701F4498A6B73AAF2AD9336C8.
- Baseline CRC of all unmodified files verified; no missing/duplicate entries, 24 overlays verified and version.json says v1.3.12.
- Package receipt `D:\STORYBOARD_AI\dist\Storyboard_1_3_12_RC2_report.json`.
- Not pushed GitHub; not applied to secondary offline PC. No false claims of successful public release.
- Caveat: Main on-disk source is the updated branch; packaged ZIP must be checked from a clean extraction / secondary before release.

## 5. Next release gates
- End-user watch the full 60s movie and verify any remaining animation/prop anomalies not visible in sampled images; allow publish only after explicit approval. Three native Muse 3:2 clips were adapted, NOT truly native 16:9.
- Clean package installation & main/secondary EXE/login/multi-account/update tests (secondary offline).
- GitHub tagged release plus updating GitHub latest.json and secondary update only after the above gates pass.
