
## 2026-10-12 — Full-color hand drawing
Implemented hand_color selection and local renderer; 3 acceptance checks, real cached media render, HTTP offline episode and style-cache transitions passed.
Verified checkpoint: D:\STORYBOARD_AI\studio\checkpoints\hand_color_verified_20261012_190022

## 2026-10-12 — Studio flicker fix
Real-browser reproduction RED -> unchanged refresh and fresh form production GREEN. No preview reloads; cards retained; no new visible console windows in test.
Checkpoint: D:\STORYBOARD_AI\studio\checkpoints\flicker_verified_20261012_191212

## 2026-10-12 — Production button state / status safety
Verified actual /api/status RUNNING PLAN_BIBLE 12%, later ERROR 28%, exit_code=1 with STORYBOARD_IMAGE_REMOTE_UNCERTAIN_NO_RESUBMIT at image MCP rendering. No job restart or external render request made.
Patched web/index.html, web/app.js, web/style.css: disabled Start & Offline during active/request/pending-status states; visible muted gray Start label shows live percent; Stop only during running; startup requires first healthy status; ERROR red indicator and text instead of misleading Ready; CSS/JS cache query bumped.
Tests: node --check PASS, Chromium read-only browser production states RUNNING/COMPLETED/ERROR/503 PASS, browser preview refresh regression BROWSER_NO_FLICKER_PASS. Existing backend /api/produce already returns 409 when job_status.running; unchanged.
Before checkpoint: D:\STORYBOARD_AI\studio\checkpoints\production_button_state_20261012
Verified checkpoint: D:\STORYBOARD_AI\studio\checkpoints\production_button_state_verified_20261012

## 2026-10-12 — Kho phim & dọn dự án (non-destructive by default)
- Mục tiêu: xóa tập/dự án cũ từ giao diện, phân loại phim chính và bản thử nghiệm, sắp xếp/tìm kiếm, thùng rác và phục hồi. Không tự di chuyển dữ liệu production thật; QA/test vẫn giữ nguyên vị trí để không phá regression.
- Thay đổi: studio_library.py (inventory + sandboxed reversible trash/restore/purge), web_server.py (/api/productions metadata + /api/productions/manage with running lock, origin, path validation), web/app.js, web/index.html, web/style.css.
- Snapshot sản xuất trước khi khởi động lại backend: checkpoints/gallery_pre_cleanup_20261012/status_before_server_restart.json. Không chạy lại job; phục hồi UI JS cache với ?gallery1.
- Kết quả kiểm kê: 26 nhóm dự án, 33 tập; 2 phim chính và 24 nhóm QA/E2E/thử nghiệm; dữ liệu ~792623567 bytes; Thùng rác 0; 0 phim thực bị xóa.
- GREEN: Python compile, JS node --check, gallery isolated backend POST tests (403/400/415/409/trash/restore/purge), Playwright Chromium main/test/search/sort/cancel/mock POST, no-flicker regression, production-button browser E2E PASS. Backend Windows đã được khởi động lại với Python console ẩn (không dùng pythonw) và HTTP GET /api/productions trả 200.
- Backup gốc: checkpoints/gallery_pre_cleanup_20261012. Checkpoint GREEN: checkpoints/gallery_verified_20261012 (7 files).

## 2026-10-12 — D:\STORYBOARD_AI root reorganization
- Trước: 14 mục ở root. Sau: 7 mục (`LAUNCH_STUDIO.bat`, `studio`, `.venv`, `_STORYBOARD_RECYCLE_BIN`, `offline_smoke`, `storyboard-ai-main`, `_ARCHIVE`). Không dùng Git; không thay launcher/API key/media chính/thùng rác.
- Lưu vào `_ARCHIVE\\2026-10-11_tests`: fast_mode_stress.py + results, fullhd_smoke.py + results, offline_smoke.py, run_offline.py, TEST_REPORT.md. Sửa đường dẫn trong các script thử nghiệm cũ để vẫn chạy được từ thư mục mới; lưu file gốc trước sửa tại `_ARCHIVE\\2026-10-11_tests\\_original_scripts_20261012`.
- Lưu `_ARCHIVE\\2026-10-11_upstream\\source.zip` (hash SHA256 xác nhận không đổi). Thư mục mã gốc `storyboard-ai-main` thử chuyển nhưng Windows trả WinError 5; giữ nguyên nhằm tránh phá môi trường.
- Giữ `offline_smoke` ở gốc vì web_server.py và studio_gui_pro.py dùng video mẫu từ đó; kết quả HTTP Range GET demo 206 PASS.
- QA sau dọn: root Launcher/.venv/nguồn gốc tồn tại; live server `/api/status`=IDLE, `/api/productions` trả bình thường; test FullHD từ vị trí lưu trữ mới tạo 1920x1080 10.24s clip PASS (~4.575s render), Python scripts compile PASS.
- Kho phim tại thời điểm kiểm tra: 0 active, 26 dự án trong Thùng rác. Không thao tác xóa/di chuyển Thùng rác.
- Manifest và bản đồ để hoàn tác: studio\\docs\\ROOT_REORGANIZATION_20261012.json. Ghi chú: _ARCHIVE\\README.txt.

## 2026-10-12 — Storyboard private Google Flow MCP, independent of V2
- Cloned the standalone Google Flow MCP runtime under `studio/studio_mcp/node` (dist + node_modules + MIT license; ~107MB). Replaced original V2 one-shot RPC by `studio-flow-rpc.mjs`: image-only contract, account URL required, output root within Studio, independent CDP 9460..9629, isolated Chrome/state path, budget guard.
- Python private `studio_mcp/image_backend.py`, `transport.py`, `accounts.py`, `paths.py`; production adapters `mcp_v2_images.py` and `mcp_v2_batch.py` now import LOCAL backend (legacy config key retained only for compatibility). Journals and media at `studio/runtime/private_mcp_outputs`, not V2 outputs/projects.
- Studio-owned registry kept at `studio/runtime/storyboard_accounts.json`: replaced only default shared CDP 9333 and Chrome profile by fresh standalone CDP 9550 and new Chrome/state folder. Existing Studio-owned account_... CDP 9460 kept intact. No Google cookies, passwords, tokens, or V2 key copied.
- New per-account Web Tool URL field in settings; validate Google Flow APP URL, explicit save/login/health. Blank URL => fail-closed, no fallback to old Web Tool or V2. Node MCP URL resolved by account on demand rather than fixed V2 project ID.
- `web_server.py` /api/produce now blocks unconfigured live MCP jobs with HTTP 409 BEFORE requesting Gemini/script/Flow credit. Existing V2 TuanStor image provider remains a separate optional legacy route, clearly labeled as V2-dependent in UI; not part of independent MCP.
- Safety GREEN: Python/Node syntax, account profile disjoint, own Node RPC gate checks, offline mock 4 scenes 4 PNG PASS, Chromium account UI/mock save PASS, HTTP invalid URL 400, HTTP live production fail-fast no inbox/project creations PASS, production button state regression PASS.
- Real Google login + paid remote image production NOT VERIFIED: a separate Google account and own Flow APP URL must be supplied through Studio settings and verified by user. No paid render was called during this migration.
- Backup before: `studio/checkpoints/private_mcp_before_20261012` (8 files). Verified source checkpoint: `studio/checkpoints/private_mcp_verified_20261012`; installed Node runtime remains under studio_mcp/node (large dependency tree not duplicated for disk efficiency). Guide: `docs/STUDIO_PRIVATE_MCP_20261012.md`.
- V2 code/config and its running process were not modified or stopped. No Git.

## 2026-10-12 — Google Flow shared/tool link URL handling (safe fix)
- Người dùng cung cấp: https://flow.google.com/shared/tool/69da86fb-6c79-43d2-a387-ef47b0fda4db. Trong Chrome riêng Studio CDP 9550, xác minh đúng tab mở là https://flow.google.com/project/79dfa39d-8ec4-4ab7-aaa2-2be03bd1bdd0/tool/69da86fb-6c79-43d2-a387-ef47b0fda4db (Google Flow đã chuyển URL shared về project/tool).
- Thực tế Flow mở app không có ?mode=APP. Chỉnh PRIVATE accounts._canonical_storyboard_tool_url, _resolve_shared_tool_url: chỉ chấp nhận link shared khi đã thấy chính xác một tab project/tool cùng tool UUID trong Chrome profile CDP thuộc Studio. Cấm tự đoán project id, cấm domain khác, cấm tái dùng Chrome V2.
- PRIVATE Node scripts: sửa studio-flow-rpc.mjs nhận canonical /project/.../tool/... với mode APP tùy chọn; sửa matcher tool-tab.js cho phép query rỗng hoặc ?mode=APP nhưng bắt đúng host+project+tool (không nới lỏng match khác).
- Đã lưu URL canonical vào trạng thái riêng của account default Storyboard, không sửa Chrome cookie/session hay V2. Tiến trình Studio được restart khi IDLE.
- Kiểm tra: frame bridge queue/SDK image capability TRUE; browser hiện có 1 mục trong queue, giữ nguyên không xóa/chạy; verify("default") -> MCP_APP_CAPABILITIES_PASS; Playwright Chrome UI click verify -> PASS; no paid image requests. Node matcher 7 cases PASS; test isolation, budget guards, failfast in-process mock và UI PASS. Live /api/config mcp_ready=True, /api/mcp/accounts active_tool_url canonical.
- Chưa test tạo ảnh trả phí; đây là connection / capability E2E, không phải render E2E.
- Checkpoint trước: checkpoints/shared_tool_url_before_20261012; checkpoint sau: checkpoints/shared_tool_url_verified_20261012.

## 2026-10-12 — Flow Web Tool bundled identity, auto-onboard per account (no manual URL in UI)
- Project resource: studio_mcp/flow_tool.json contains fixed Google Flow shared Tool identity, not the publisher project-specific URL. Account login opens the bundled share in each Studio-owned Chrome profile; when Flow redirects to /project/.../tool/<tool-id>, account code reads only that profile's Chrome CDP and persists the detected URL under its own state_dir. Never copies cookie/token or guesses project UUID.
- Public settings and /api/mcp/accounts now expose only tool_linked boolean; URL field and Save URL button removed. POST set_tool_url action disabled. Chrome's own address bar or extracted app files can still reveal a nonsecret share URL; access control belongs to Google.
- Bundled standalone Node.exe v24.19.0 was copied under studio_mcp/node/node.exe (SHA256 verified) and transport prefers it to system Node; no V2 server/runtime required for private MCP. This increases install payload ~89 MB. Full clean-machine distribution remains subject to Node licenses/notices, Chrome availability, Python runtime packaging and Google's access permissions.
- Verified tests PASS: bundled identity, per-account auto-resolution with mocked browser redirect, wrong-tool rejection, first-login and already-running Chrome launch simulation, browser UI contains no URL, public accounts JSON contains no URL, portable Node transport selection, Node budget/approval guards, private MCP isolation.
- Current active production detected at PLAN_BIBLE 13-15% while checking: did NOT restart Studio or terminate any worker. Changes on disk will fully load on next backend startup after that job finishes. No paid generation requested.
- No-Git backup before: checkpoints/auto_flow_tool_before_20261012. Source GREEN checkpoint: checkpoints/flow_auto_attach_verified_20261012 (15 checked source files and SHA256 of bundled node.exe). Release file list: studio_mcp/RELEASE_CONTENTS.json; packaging guidance: docs/FLOW_AUTO_ATTACH_PACKAGING_20261012.md.

## 2026-10-12 — 62 scenes / 20 images fail-fast and resume
- Actual failed episode: RELA-JATE-Y-MANIFESTARA-S-TODO-LO-QUE-DESEES-ESTOICISMO episode_001, link mode, 25.8 min, scene_seconds=25, 62 planned scenes, cap=20. Scene plan saved in plan.json, no rendered scene files at failure. Gemini 503 fallbacks recovered the complete plan.
- Root cause: mcp_v2_batch guarded budget AFTER extensive Gemini calls. New studio_image_budget.py validates budget at HTTP preflight and CLI before planning. Unique requires at least scene_count images; user must explicitly confirm and click Produce again to increase cap. Reuse option deliberately creates up to the approved max key visuals and shares them across all scenes with clear quality warning. Never silently raises paid budget.
- mcp_v2_batch: deterministic anchors and scene_to_anchor map in visual_mapping.json; 62 scenes, 20 mocked remote images and 42 reused scene frames passed, all scene image.png verified. Never triggers extra MCP paid requests from tests.
- Gallery has a Tiếp tục button for incomplete saved episode. It restores title, reference link, duration/pacing, genre, style, language, model. Does not start production. Original cached plan hash remains 75A58470307365891640DC5BCABE4F11FE44115E3F8FBAA7C6E03BDFF24277AA; read-only produce_plan cache test made no Gemini request.
- GREEN tests: Python compile, node --check, 62/20 budget policy, actual saved plan cache, HTTP rejected unapproved 62 image start (409), invalid policy 400, Chromium 62 manual approval no POST, Chromium reuse 20 mocked POST, Chromium Gallery resume, original 4-scene mocked MCP images.
- New separate Whiteboard Chronicles production later failed PLAN_BIBLE 13% because Gemini 429 quota and 503 transient, unrelated to this image-budget fix. Did not claim long-form paid E2E PASS.
- No Git, no changes to V2, no unrequested paid render. Backups: checkpoints/image_budget_before_20261012; verified checkpoint: checkpoints/image_budget_verified_20261012 (11 files with SHA256).

## 2026-10-13 — Production preflight requires Studio private Chrome + exact bundled Web Tool
- User failure 06:27:24 after 62 scenes: STUDIO_ERROR: STORYBOARD_PRIVATE_BROWSER_NOT_CONNECTED. Browser CDP 9550 listener was absent, no Studio Chrome process. Gemini planning had recovered from 429 quota and 503 via fallback, completed 62 scenes; budget 62 unique validated, no image receipts generated.
- Root cause: MCP preflight in web_server/CLI only checked stored account_tool_url, but that persisted URL survives browser shutdown. Actual browser connection_check only ran in transport after costly 62-scene Gemini planning.
- Fix: require_production_browser() in studio_mcp/accounts.py checks Studio account CDP, matching profile pid, and EXACT bundled Flow tool tab as nonpaid local checks. HTTP /api/produce now rejects with 409 and actionable manual login/verify guidance BEFORE worker/Gemini starts. series_studio.py also checks before reference analysis / planning to protect direct CLI starts. Never opens Chrome silently, never falls back to V2, never auto-increases paid image budget.
- Real negative validation on machine with 9550 closed: `test_preflight_browser_closed_no_api.py` PASS, no new inbox prompt, no worker spawn, no Gemini or Flow paid requests. Simulated valid own tab and wrong tool tab PASS. Regression `test_http_budget_failfast_existing_plan.py`, `test_scene_budget_62_no_credit.py`, `test_private_mcp_node_guards.py` PASS. No paid render performed. Backend safely restarted while idle and now running updated guard.
- Both 62-scene scripts saved: `productions/Whiteboard-Chronicles/episode_001/plan.json` SHA256 8DCA5FF2F5CB4F21FE610DE75DE8DFE3AB059D372A931D9DF3AA4F908C99D885, and `productions/RELA-JATE-Y-MANIFESTARA-S-TODO-LO-QUE-DESEES-ESTOICISMO/episode_001/plan.json` SHA256 75A58470307365891640DC5BCABE4F11FE44115E3F8FBAA7C6E03BDFF24277AA. Both manifests BLOCKED_MCP_IMAGE, no scene completed.
- Before checkpoint: `checkpoints/browser_preflight_before_20261013`. After: `checkpoints/browser_preflight_verified_20261013` source + tests with SHA256. No Git. Real paid image E2E still pending a login/verification by operator.

## 2026-10-13 — Private MCP real-image canary and failure reconciliation
- User explicitly requested actual repair/run. Machine: DESKTOP-EE8BGVF, D:\STORYBOARD_AI\studio. Original Chrome 9550 was closed; opened Studio-only profile using /api/mcp/account login; Google Flow redirected bundled share to exact own project/tool; live MCP health MCP_APP_CAPABILITIES_PASS. V2 profile, MCP process and config untouched.
- Detected original Flow tool browser queue contains one pending video shot_1 with ~2348-character prompt; preserved unchanged. Tested disposable secondary tab: clearQueue in secondary did not change original queue; separate fresh tab still showed initial shot. Added scoped canary target ID selector in installed private MCP Node/browser/session.js; health and dry_run in disposable tab PASS without producing media.
- Fixed STUDIO private Node image queue's stale V2_FLOW_MCP_* environment checks: uses STORYBOARD_MCP_APPROVED and STORYBOARD_MCP_MAX_NEW_IMAGES bounded by 1..1000; no V2 runtime required. Verified portable Node and ffprobe accessible, syntax and budget/approval regression GREEN.
- With explicit user request, attempted ONE real Nano Banana 2 Lite image job (max_new_images=1, fallback=false) in disposable account tab, no batch 62. Existing source queue stayed unchanged. Actual Flow queue changed to failed status within 2255ms; Studio MCP log error POLICY_BLOCKED: Image queue partially failed; all completed receipts saved; no automatic retry. Python and Node durable journals both remain submit_uncertain (1 reserved slot each), no image output or completed receipt. Unknown if provider consumed credits; do not claim zero credit cost.
- Ran ONLY read-only reconciliation for the SAME job: STORYBOARD_IMAGE_PARTIAL_UNCERTAIN_NO_RESUBMIT:1, no further image submission. Isolated real Flow dry_run PASS on 1 different uncharged prompt, validating queue wiring; first paid image attempt remains unresolved. Never purge/delete uncertain journal or auto-resubmit.
- Improvements for diagnosis of future failures: node studio-flow-rpc.mjs propagates sanitized FlowError message instead of code alone; Node image queue records failed state + bounded error reason while saving completed receipts. Keeps no-auto-retry safety. Test suite node --check, Python compile, Node cost gates, portable Node, mocked closed/wrong browser and real standalone health, isolated dry-run passed. HTTP negative test skipped safely while user's Chrome was opened to avoid accidentally launching a paid job.
- Backend currently IDLE, Studio canary output missing, existing 62-scene plans preserved. Live end-to-end image generation NOT GREEN, pending external Flow error diagnosis/account quota and explicit approval before another potentially charged canary. Do not report production end-to-end as passing.
- Pre-change backup: checkpoints/private_mcp_runtime_before_real_canary_20261013. Post-change checkpoint: checkpoints/private_mcp_canary_diagnostics_verified_20261013.

## 2026-10-13 — Multi-project Google Flow routing per genre
- User requested project switching, one Google Flow project per film genre, with correct Web Tool and no V2 dependency.
- Added `studio_mcp/projects.py` per-account registry in account state_dir, schema 1. Registers only exact project/tool pairs seen through account-owned Chrome CDP. Stores label, genre, active and genre mappings. Keeps legacy linked project as default virtual entry; never copies cookies/key/credentials.
- UI adds scanning open Flow tabs, register/assign genre, switch, open selected registered project, status. JavaScript dynamically updates selected genre; removes any need to enter URLs manually. API GET `/api/mcp/projects` and POST `/api/mcp/project` actions register/select/open with idle production lock and origin guard.
- Production HTTP chooses mapping by specified genre; if `auto` idea/script, uses existing detect_genre and registered route; link mode uses manually active default because source analysis is not available prior to preflight. `--mcp-project-url` passed and frozen at CLI start in STORYBOARD_FROZEN_PROJECT_URL. Transport verifies selected URL belongs to active Studio account registry; exact target Chrome profile/project/tool tab validated BEFORE Gemini. Real MCP image bridge health runs at CLI preflight and blocks incompatible apps without paid image call. Switching account/project blocked during production.
- `studio_flow_accounts` opens selected registered tool in account's Chrome on user click only, no V2 tab/process, and genre-specific verify health for currently selected film genre.
- GREEN: Python compile and Node JS syntax, multi-account two-genre registry isolation, project exact URL validation, Chromium UI registration/select/open mock, HTTP unmapped-genre and wrong-tab failfast 409 before Gemini/Flow, private MCP spend guards, portable node, four-scenes mocked render. Runtime production E2E for two distinct live Google Flow projects NOT VERIFIED. New shared Tool 8fbef6e9... previously lacked V2 Director bridge (`UI_NOT_FOUND`); registration != compatibility.
- Backups: checkpoints/multi_flow_projects_before_20261013; verified checkpoint: checkpoints/multi_flow_projects_verified_20261013; guide docs/FLOW_MULTI_PROJECTS_20261013.md. Release contents include projects.py. No Git and no modifications to D:/FLOW_MCP_SERVER or D:/YOUTUBE_SEO_PRO_V2.

## 2026-10-13 — Drawn-video MP4 actual E2E validation
- Real offline production via POST /api/produce: 2/2 scenes, `hand_color`, karaoke subtitles, ffmpeg concat; status COMPLETED exit_code=0 and manifest PASS, 6.043s 640x360 H.264/AAC, full ffmpeg decode/Range 206 and all scene media confirmed.
- Separate real cached MCP artwork + local Windows SAPI speech (`Microsoft David Desktop`) run: 2/2 hand_color drawing scenes with hand overlay and correct subtitle/audio, 18.246s 1280x720 H.264/AAC, 455 frames, 1,323,610 bytes, MP4 full decode, FFprobe QC and Range 206 PASS. Distinct real artwork input was cached; no new Flow images/credits and no new Gemini model calls.
- Both local videos/preview_contact_sheet.jpg stored under productions/E2E-Drawn-Video-Oct13-2026---Offline-Test/episode_001 and productions/Drawing-Color-Real-Art-Voice-E2E-20261013/episode_001; both visible in gallery inventory; originals and recycle bin untouched.
- Fixed QA test script's incorrect episode slug causing false 404 despite successful video production. Added `--verify-only` to revalidate existing media without launching a second job; exact previously created MP4 QC passes.
- Online Flow image-generation E2E still unverified because current Chrome 9550 tool tab is a different Project/Tool from registered Studio mapping; never auto-spend or silently use wrong project. Not a paid production PASS.
- Runtime audit report: docs/REAL_DRAW_VIDEO_E2E_20261013.md. Checkpoint: checkpoints/real_draw_video_e2e_verified_20261013 (first revision of source; corrected script maintained separately at studio/test_real_hand_drawing_video_e2e_20261013.py).

## 2026-10-13 09:53+07 — User-requested live MCP E2E probe
- RDC online DESKTOP-EE8BGVF. Studio currently idle; previous offline E2E complete.
- Active Studio account default. Selected registered Flow project a48a51c1-a8a7-4b54-81a2-8789f7bc4c1f, Tool 8fbef6e9-a6e4-4b21-a8b0-0be7a559273d. CDP 9550 reachable. Browser originally showed a different tool d31be7ec... which had image SDK but lacked the V2 Storyboard Director MCP bridge.
- Opened exact registered Flow project/tool in Chrome and waited ~28s. Required window.__STORYBOARD_MCP__ and native image SDK not available in frames observed.
- Actual Studio POST /api/mcp/account verify (default, genre auto) returned HTTP success with result.ok=false, reason STORYBOARD_PRIVATE_MCP_FAILED:UI_NOT_FOUND: Actual Storyboard Director production bridge unavailable. Server remains idle.
- Live E2E image-to-drawn-video blocked before paid submit; no new paid image, no Gemini call, no new live MP4. This particular new Google Flow app is incompatible with the copied V2 Storyboard Director MCP. Needs compatible native Web Tool or adapter; do not bypass guard or silently redirect to another project/account.

## 2026-10-13 — User reopened real MCP Web Tool; LIVE 1-image/1-scene hand-drawn video E2E PASS
- RDC device DESKTOP-EE8BGVF, local Studio Chrome on CDP 9550. Active account default, current saved project was a48a51c1.../8fbef6e9... (wrong/incompatible app), but user opened a DIFFERENT working Storyboard Director tool at project 7a7f7f89-c38d-4237-b4aa-ba499acd7507 / tool 642784b8-d39f-4e7b-b168-fe6218bbc45b with URL query ?fromViewSource=tools. Browser frame had __STORYBOARD_MCP__, addToQueue, startImageProduction, startProduction, image/video SDK.
- Fixed strict-scoped Flow URL matching to accept exact query fromViewSource=tools on same hostname, project ID and tool ID (not arbitrary query); Node and Python matching tests PASS. Backups in checkpoints/opened_web_tool_project_switch_before_20261013.
- Registered user's observed account-owned project/tool via Studio /api/mcp/project as "Storyboard Director - Video ve tay", genre=whiteboard. Previously saved project remains in registry and active switches to the working tool; no V2 profile/cookie/network shared. GET /api/mcp/projects shows exact recognized tab.
- Actual POST /api/mcp/account verify with genre=whiteboard returned {ok:true,reason:MCP_APP_CAPABILITIES_PASS}; browser connected. No false E2E PASS from health.
- User had pending video shot_1 with 2348-character prompt in original Web Tool tab. Created disposable tab, selected it by validated CDP target ID ONLY for canary, preserving ordinary strict one-tab routing. Targeted canary health PASS; one real Nano Banana 2 Lite image generation succeeded: 1536x864, 2,458,658 bytes. Original user's shot_1 queue metadata was identical before/after (pending, untouched); disposable tab closed. One paid image request max, no retries.
- FULL LIVE MINIMAL E2E PASS: Google Flow MCP real image → hand_color hand drawing animation → Microsoft David Desktop local spoken narration (~9.33s) → karaoke_viral subtitles burned into frames → H.264/AAC MP4 at 1280x720, duration 9.406016s, 234 frames, 727,493 bytes. Full FFmpeg decode PASS; FFprobe PASS; scene manifest PASS; video HTTP range 206; six frame contact sheet plus QC JSON. This is 1-scene integration validation, not full 10-30 minute production or multi-scene/credit-load regression.
- Output: productions/MCP-Live-Hand-Draw-E2E-Oct13-2026/episode_001/episode_final.mp4
- Image: productions/MCP-Live-Hand-Draw-E2E-Oct13-2026/episode_001/scenes/scene_0001/image.png
- QC report: productions/MCP-Live-Hand-Draw-E2E-Oct13-2026/episode_001/REAL_MCP_E2E_QC_REPORT.json
- Contact sheet: productions/MCP-Live-Hand-Draw-E2E-Oct13-2026/episode_001/preview_contact_sheet.jpg
- New nonpaid tests: Studio Python exact redirect URL scope and Node tool-tab exact path allowlist PASS. No changes to V2. Production server left running idle. Bundled default share in flow_tool.json still 8fb...; it is NOT the working tool of this account, and generic new account packaging remains unverified.

## 2026-10-13 — Responsive Storyboard UI dock layout
- Measured forced 1150px three-column layout clipping right monitor at 1024/800 widths and densely packed 62 scene cards.
- Modified only web style/index/app visibility and responsive controls; no production, Flow MCP, account or credit changes.
- Real Edge six widths (1920,1440,1280,1024,800,540) with 62 test cards PASS. Drawer controls and input persistence PASS. Flow project UI, 62-scene image-budget guard, saved stoic episode resume tests PASS. Updated old QA script selection to target Stoic project when multiple incomplete episodes exist.
- Backup checkpoints/ui_docks_layout_before_20261013. Verified checkpoint checkpoints/ui_docks_layout_verified_20261013; report docs/UI_DOCKS_LAYOUT_VERIFIED_20261013.md. Ctrl+R to reload. No render requested.

## 2026-10-13 — Hand color contour-fill v2, real cached MCP artifact
- Replaced horizontal stripe reveal in studio_hand_color.py with stroke-aware contour outline + connected LAB color regions + clean full-color hold implemented in studio_hand_color_strokes.py. Does not change engine/tools/draw_animation.py B/W; SHA256 engine BFD5D7B0EBE046E014AE5A9583B0AEB47D2A8AC3184BED0483C31B7BADDF455F.
- Visual review on genuine stored Flow MCP image found late square white holes with first prototype (172 small regions), then pruned islands to 71 regions, blurred paint front and finished painting earlier. Six-frame new vs old screenshot comparison saved. Rendered 1-scene full MP4 with existing MCP image/audio, subtitles, H264/AAC 1280x720 duration 9.406s, 234 frames, 1,632,102 bytes, FFmpeg complete decode PASS; no new paid API calls.
- Three hand-color unit checks, synthetic non-horizontal and non-flash deterministic tests PASS. Versioned scene render_style cache: contour_fill_v2_20261013 invalidates only derived videos on first subsequent render, never user images/audio; cache reuse thereafter PASS.
- Docs docs/HAND_COLOR_CONTOUR_V2_20261013.md; backups checkpoints/hand_color_contour_before_20261013; verified checkpoint checkpoints/hand_color_contour_verified_20261013. Commercial distribution must include new helper studio_hand_color_strokes.py. E2E multi-scene/1080p not yet validated, don't claim full production release green.

## 2026-10-13 — Actual Studio UI two drawing mode E2E
- Tested through actual Edge UI buttons at localhost:8765, not direct render_one or mocked POST. First real GUI offline color failed missing cv2 because server D:\python.exe spawned wrong worker. Fixed web_server.py to use Studio .venv worker and preflight cv2/numpy/PIL before production; preserves source failed episode and V2.
- GUI Offline hand_color PASS (2 scenes,6.043s,640x360,H264/AAC, subtitles, player), GUI Offline whiteboard PASS (2 scenes,6.043s,640x360,H264/AAC, subtitles, player).
- GUI Live MCP hand_color PASS (1 scene,one MCP image request limit,5.843s H264/AAC, subtitle/player).
- GUI Live MCP whiteboard FAIL: STORYBOARD_IMAGE_REMOTE_UNCERTAIN_NO_RESUBMIT with receipt submit_uncertain, BLOCKED_MCP_IMAGE, no MP4. Do not retry; credit charge unknown.
- Used separate private CDP target for live E2E. User original queued video shot_1 unchanged; test tab safely closed and original server restored without canary env; read-only MCP health PASS and Studio idle.
- Reports: docs/REAL_STUDIO_UI_E2E_BOTH_DRAWING_MODES_20261013.md and runtime/actual_studio_ui_e2e_both_modes_report_20261013.json. Backup checkpoints/real_tool_e2e_python_fix_before_20261013.

## 2026-10-13 — Actual GUI E2E continuation / queue-safe fix
- Actual Studio GUI/Test Offline color and whiteboard: 2/2 scenes each PASS. GUI Live Google Flow MCP color 1/1 new image and MP4 PASS; mono Live job BLOCKED_MCP_IMAGE with submit_uncertain receipt, no resubmit, credit status unknown.
- Root: Studio backend D:\python.exe lacked cv2; corrected render worker .venv and checked dependencies before starting.
- Native image queue preflight now read-only checks completed/busy/foreign queues before paid journals/slots. Real queue currently contains user-owned shot_1 pending with 2348-char prompt; preflight and native worker now refuse to clear it unless an explicitly scoped disposable Chrome target is used. Only boolean has_prompt is exposed, never prompt content.
- Read-only old mono receipt check: still unresolved. Original journal preserved; no credit submission during continuation. Existing original tab and pending shot unchanged.
- Real no-paid health and guard regression PASS; independent 3 MP4 FFmpeg audits PASS. Report docs/REAL_STUDIO_UI_E2E_BOTH_DRAWING_MODES_20261013.md; checkpoint checkpoints/actual_studio_ui_e2e_queue_guard_verified_20261013. No Git and no V2 edits.

## 2026-10-13 13:2x — All MCP image entrypoints guarded before paid journal
- Implemented shared read-only validate_image_tool_readiness in studio_mcp/image_backend.py and called from preflight plus render_one_queue new jobs, including single-image paths. Queue stale/user prompt blocks before slot reservation and submit_uncertain journal. Exact account-selected Web Tool health added in web_server.py POST /api/produce before inbox/Gemini; user-facing 409 and app.js modal, version bump in index.html.
- Real unmocked GUI click live MCP returned 409 MCP_QUEUE_PREFLIGHT_BLOCKED, no inbox or production created while user shot_1 had populated prompt. Regression tests for direct image backend, mock four-image queue, account mapping, color, UI all PASS. No credit spent.
- Subsequent GUI retest blocked earlier at correct browser preflight because project tab was no longer open (open_tabs=[]). Did not forcibly reopen user's tool. Historical mono receipt still unresolved submit_uncertain, no retry. Old plan-dependent test skipped/missing fixture; not counted PASS.
- Backup: checkpoints/all_image_entrypoints_preflight_before_20261013; verified checkpoint: checkpoints/all_image_entrypoints_preflight_verified_20261013. Details docs/STUDIO_MCP_QUEUE_FAILFAST_20261013.md. No changes to V2.

## 2026-10-13 — Studio private Chrome Google Flow open_project false success corrected
- User reported Web Tool could not open. Reproduced CDP 9550 connected but open_tabs=[], Chrome private process persisted. Existing open_project returned opened:true immediately after Popen without checking actual tab/window.
- Fixed studio_flow_accounts.py: _confirmed_visible_project verifies PID, exact registered Tool tab via account CDP and visible Chrome HWND; existing tab restores window without duplication; new tab opens with bounded 12s wait; returns actionable error instead of false success if no visible window/tab. Does not touch V2/profile/login cookies or queues.
- Mocked contract test 4/4 PASS; actual Edge UI click Mở dự án PASS, confirmed window_visible:true tool_tab_verified:true, 1 correct Flow tool tab. Read-only MCP verify returned MCP_APP_CAPABILITIES_PASS, Studio IDLE. No paid Flow jobs.
- Backup checkpoints/flow_open_project_before_20261013; verified checkpoints/flow_open_project_verified_20261013. Details docs/FLOW_PROJECT_OPEN_FIXED_20261013.md.

## 2026-10-13 — Read-only MCP V2 baseline comparison
- Compared D:\FLOW_MCP_SERVER/dist to Storyboard private studio_mcp/node/dist: package 0.3.1 both; 38/42 matching JS/JSON SHA256-identical; 4 differ in browser session, tool tab matching, native image guard, native tool URL. Syntax all 4 PASS.
- V2 native tool ID 642784b8..., Storyboard bundled default tool ID 8fbef6e9... mismatched; verified working Studio project uses tool 642784b8... with dynamic project ID. Different Python orchestration/Chrome profile/queue and credit policies. V2 CDP 9333 currently unavailable, no live benchmark claims.
- No V2 edit and no paid requests. Detailed audit docs/MCP_V2_VS_STORYBOARD_CODE_AUDIT_20261013.md.

## 2026-10-13 – Pinned MCP V2 0.3.1 baseline in Storyboard (no V2 modification)
- Studio private Node MCP: 38/42 dist JS/JSON byte-identical to V2, four reviewed adapter forks pinned by SHA. package.json matches V2 byte-for-byte; copied V2 package-lock exact hash, SDK=1.32.1 playwright-core=1.62.1 zod=4.5.4 installed versions match. Added studio_mcp/v2_baseline.py; transport verifies pinned files+dependencies before RPC, without consulting V2 directory at runtime.
- New read-only node/verify-v2-compatible-tool.mjs plus projects.probe_v2_compatible_tool rejects registering a Web Tool that lacks Storyboard Director bridge+image SDK. No hardcoded account project ID. Installer include-files updated. Actual registered Tool compatibility probe passed.
- Negative 4/4 pinned drift checks PASS; nine no-paid regression suites PASS; 17 release file entries present. Studio restarted only while idle; actual read-only MCP health MCP_APP_CAPABILITIES_PASS, registered account tool open, Studio IDLE. No paid image calls.
- Bundle share link tool ID 8fbef6e9 differs from proven V2-compatible native app tool 642784b8. Need verified compatible share for commercial onboarding. Prior whiteboard submit_uncertain receipt left unchanged; no paid E2E re-run. Audit docs/MCP_V2_BASELINE_SYNC_VERIFIED_20261013.md; original backups checkpoints/v2_baseline_sync_before_20261013; verified checkpoint checkpoints/v2_baseline_sync_verified_20261013.

## 2026-10-13 15:xx — MCP verify failure after successful mono E2E traced to duplicate tabs
- Latest actual Studio mono live E2E 15:07 PASS, Google Flow MCP image imported and MP4 H264/AAC produced. Later verify failed UI_NOT_FOUND because Chrome CDP 9550 had TWO identical registered Tool tabs: one completed image, one user-authored shot_1 pending video prompt. Both contained user state, none automatically closed.
- Fixed exact_tool_tab_count on own CDP, duplicate-aware verify result and early production guard; open_project refuses false success, UI now says 2 same-tool tabs and instructs safe review, without touching prompts, cookies, V2 or credits. Real GUI verify button PASS for explicit Vietnamese message; 5 no-paid test suites PASS. Studio IDLE. Backup checkpoints/duplicate_flow_tabs_before_20261013; verified checkpoint checkpoints/duplicate_flow_tabs_verified_20261013. Report docs/DUPLICATE_FLOW_TABS_VERIFY_FIX_20261013.md.

## 2026-10-13 — Fix actual Studio GUI Sản Xuất launcher: clean isolated Flow per-job tab
- Reproduced user's screenshot failure: actual GUI 409 MCP_QUEUE_PREFLIGHT_BLOCKED because one account-owned Flow tab had a completed image. Earlier double-tab condition also caused UI_NOT_FOUND. No credits spent reproducing this.
- Implemented dedicated auto-managed Flow tab per production via studio_mcp/production_tab.py + node/production-job-tab.mjs; per-worker scoped 32-hex CDP target; preflight checks exact Bridge/SDK and own Chrome; successful verified MP4 => close only Studio-owned tab, failed/uncertain jobs retain target for review. Core V2 unchanged, user image queue never cleared. Strict normal CDP guards preserved.
- Live GUI clicked real Sản Xuất mode whiteboard: 1 new MCP image, 1 scene PASS, H264/AAC MP4 5.403s 309844 bytes, ffmpeg full decode PASS, audio+subtitles present, in-app video loads; newly created tab auto-closed, original tab count 1. `MCP_APP_CAPABILITIES_PASS` after production and backend restart; Studio IDLE.
- Added automatic genre fallback to selected V2-compatible account project only for UI genre auto with no explicit genre map; manual genres unmapped remain blocked. Regression tests and HTTP no-paid fallback test PASS. Release includes both production job helpers. Old stale paid E2E helper disabled from unintended retrigger.
- Additional GUI color offline QA collided with a separately restarted backend during the test, left incomplete, NOT PASS. No live hand_color re-test after scoped change; avoid commercial release claim. Full report docs/SCOPED_FLOW_SESSION_REAL_UI_E2E_20261013.md. Backup checkpoints/isolated_production_tab_before_20261013; checkpoint checkpoints/isolated_production_tab_live_e2e_verified_20261013. V2 untouched.

## 2026-10-13 — Auto Flow Manager, live UI E2E + project auto-creation proof
- Added studio_mcp/auto_flow_manager.py with startup bootstrap, V2-compatible project lookup/verified reuse, per-genre assignment/failover, account profile login recovery and read-only status. /api/mcp/auto/status GET and /api/mcp/auto POST; GUI automatic state display/reconnect; no V2 edits.
- Auto manager /api/produce preflight moved ahead of job_lock after finding real HTTP 409 AUTO_FLOW_PRODUCTION_BUSY deadlock; on new E2E after fix live color 1 new MCP image 1/1 scene, MP4 ~5.28s H264/AAC with WAV/subtitles/full ffmpeg decode and in-app playback PASS; production tab auto-closed, original tab preserved. First 409 attempt no media submitted.
- Real GUI offline color and whiteboard both 2/2 scenes, MP4 ~6.043s each PASS. GUI Auto Manager ready+reconnect PASS.
- Actual Google Flow homepage New Project clicked once, created project 1f806e0b-5184-448b-8ab4-eab64ee163f0; V2-compatible tool 642784b8... bridge+image SDK verified, registered as fallback, original active project restored. No images/videos generated in provisioning proof.
- Added node/auto-flow-provision-project.mjs and auto_project_provision.py with create_requested/project_created/verified durable journal, no duplicate remote create on uncertainty, history rotation only after successful registration, 2/day safety limit. Manager fallback only from prior V2-verified Tool ID; simulated without paid creations PASS. Two historic submit_uncertain image receipts remain unchanged and must not auto-resubmit.
- 10 no-paid regression suites PASS, V2 pinned 0.3.1 38 core identical/4 adapters reviewed; release manifest includes new modules. Desktop app owns live backend: final provisioning code may require one normal desktop restart to load, so no false claim about uninterrupted hot reload. Details docs/AUTO_FLOW_MANAGER_VERIFIED_20261013.md, verified checkpoint checkpoints/auto_flow_manager_verified_20261013.


## 2026-10-15 Desktop robot visible + live status
- User requested V2-style floating robot reporting Storyboard results directly.
- Added studio_desktop_robot.ps1: native transparent topmost desktop window, movable, read-only /api/status polling every 2 seconds with 3-second timeout, disconnected/error/completed/idle states, single-instance mutex, owner-process and observed Studio window lifetime checks.
- desktop_app.py launches it automatically with the Studio launcher PID. Existing active Studio session was attached without restart.
- Artwork rendered once from V2 vector art into web/assets/desktop_robot_v2.png. Runtime requires Windows PowerShell/.NET only; does not import V2 or require PySide6. V2 source unchanged.
- Checkpoint before launcher edit: checkpoints/desktop_robot_20261015/desktop_app.py.
- RED: missing desktop robot test failed. GREEN: 6 status behavior checks PASS; desktop_app.py compile PASS; duplicate-launch process exits 0; absent-owner process exits 0; real desktop screenshot shows robot and correct live stopped/ready message. No production job or paid API started.
- Scope: text result notifications. Voice was not added. Full media production E2E not run for this display change. Close-event code monitors Studio window and launcher; actual user Studio was not closed during validation.


## 2026-10-15 Correction: user wants small assistant INSIDE Studio
- Previous desktop robot implementation was based on a misunderstanding. Stopped its process and removed the exact launcher insertion; unwanted PowerShell implementation/test moved to checkpoints/small_in_tool_robot_20261015.
- Retained original in-tool robot and its production-status bindings. Changed avatar from 54px to 44px; right/bottom inset 12px; bounded status badge width. Bumped stylesheet version.
- Initial Edge inspection confirmed original widget existed and was clickable inside Studio. Browser tests validate 44px bounds and panel open/close at 1400x750, 1024x768, 540x850.
- Sent targeted browser refresh to the existing Studio window. No production job started or stopped. V2 untouched.


## 2026-10-15 Actual-window visibility root cause verified
- Prior visibility claims were premature: Playwright considers opacity-zero elements visible, so earlier is_visible/click checks missed hidden ancestors.
- Actual app DOM showed #aiRobotFloatingWidget nested inside .modal-dialog; modal ancestor opacity hid the widget. Stale-cache explanation was unconfirmed and not the root cause.
- Minimal fix reparents the existing robot under document.body before app.js starts. Badge width max-content prevents narrow vertical text. Kept 44px size and original production bindings.
- Verified live headed app over temporary local CDP: bodyChild=true, all ancestor opacity=1/display visible; button toggles panel. Screenshot of ORIGINAL user profile, project khắc kỷ / Tập 2, shows robot and status at lower-right. Backend was found offline during investigation and restored.
- Regression check now tests parent and ancestor opacity, plus bounds/panel interaction. Temporary inspection profile is closed after validation. No V2 modifications or paid generation.


## 2026-10-15 Live model/provider comparison (inspection only)
- Studio get_all_api_keys reads one unique Google key from GEMINI_API_KEY; no TUANSU key in Studio .env. Gateway configured/enabled through v2_inherited config; list/models HTTP 200 with 93 models. Credentials never printed.
- Two small JSON probes/model, direct HTTP without retries: Google gemini-3.8-flash 1/2 success (other 429); gemini-3.5-flash 0/2 (429); gemini-3.1-flash-lite-preview 2/2 success ~1.41s. Tuansu gemini-flash-3.8-fast 2/2 ~2.41-3.08s; high 2/2 ~3.50-9.62s; qwen3.8-flash 2/2 ~2.73-3.67s.
- Synthetic 6s video with 3 labeled color scenes: Google 3.8 429; Lite initial 35s timeout, second probe HTTP 200 and correctly recognized RED 1, BLUE 2, GREEN 3 in order / shot_count=3 (~12.81s). Short test is not long-video validation.
- Tuansu chat/completions video_url:data MP4 returned HTTP 200 but UNAVAILABLE; this tested transport does not establish video support. Same model with image_url PNG frames correctly returned all 3 labels/colors (~5.92s). Native-video endpoints have not been tested.
- Direct native AUDIO sentence: gemini-3.8-flash-tts 429; gemini-2.5-flash-preview-tts HTTP 200 returned 63886 audio bytes (~3.72s). This does not establish long narration reliability or voice quality.
- Code review: series_studio initializes explicit [own_api_key()] rather than full pool; current configuration has only one anyway. Resilient gateway fallback converts multimodal contents to str, losing video/image input. Current TTS fallback maps 3.8 TTS to ordinary 3.8 Flash rather than verified 2.5 TTS; Edge fallback then used on failure.
- Evidence: diagnostics/provider_inventory_20261015.json, provider_compare_20261015.json, provider_modalities_20261015.json, provider_multimodal_detail_20261015.json. No provider configuration or production implementation changed during this comparison.


## 2026-10-15 Follow-up: verified source video timeline + TTS patch (Storyboard-only)
- Pre-change checkpoint: checkpoints/reference_timeline_before_20261015_081345 (6 existing source files copied before mutation); V2 project never modified.
- New reference_video_timeline.py analyzes PUBLIC YouTube URL itself through Google Gemini video input and requests timestamps, subjects, framing, palette and shot descriptions spanning start/middle/end; strict timeline validation; no thumbnail-only claims; JSON timeline cached by source ID.
- competitor_cloner.py still uses thumbnail for character hint, but saves separate actual video timeline and sets whole_video_verified. Failure surfaces video_analysis_error; never fabricate a video timeline.
- series_studio.py consumes time-relative beats to vary storyboard scenes; stops LIVE link production early if only thumbnail is available; removed forced "main character in every scene"; pooled configured Google keys for planning.
- resilient_gemini.py blocks text gateway fallback from silently flattening image/video Content/Part; TTS model fallback now changes only between audio-capable models.
- engine/config.py now defaults to gemini-2.5-flash-preview-tts (env override STORYBOARD_TTS_MODEL); engine/tools/tts.py passes available Google key pool.
- mcp_v2_batch.py image prompts no longer force stone/bronze just because genre is stoic; character reference is conditional on character actually appearing in scene.
- Verified: py_compile 6 touched files PASS, mcp_v2_batch.py py_compile PASS; unit tests scratch/test_reference_timeline_20261015.py 5/5 PASS; integration tests scratch/test_cloner_integration_20261015.py 2/2 PASS; frame-prompt no-forced-statue PASS.
- Live Google URL video experiment using supplied Shorts video hkpWx4lo-oI: model gemini-3.1-flash-lite-preview returned 6 timestamped observations (0,10,20,30,40,47s) with mixed shot sizes, HTTP/SDK success in ~29.7s; diagnostics/youtube_timeline_live_20261015.json. This does NOT certify exact visual match by human comparison, nor 30-minute reliability.
- Live TTS pipeline: Gemini 2.5 Flash preview TTS with Spanish Charon succeeded, generated valid 4.53-second mono WAV (217530 bytes), ~5.25s; diagnostics/tts_live_pipeline_20261015.json. Long-form voice consistency not tested.
- Legacy test_multimode_no_api.py blocked after first pass by missing fixture productions/Whiteboard-Chronicles/episode_003/plan.json; no claim of full legacy regression PASS.
- Desktop application + web_server were running while sources changed; no forced restart and no paid MCP image/video renders; running processes may retain old imports until normal restart. Full live end-to-end render/30-minute verification remains pending. 


## 2026-10-15 08:45 — Studio startup recovery, hook/climax QC, four-style test, cleanup
- Details/evidence: docs/QA_CLEANUP_STORY_ARC_20261015.md; existing user plans and V2 unchanged.
- Desktop 8765 HTTP blank responses under pythonw fixed by safe StudioRequestHandler.log_message override; EXE launcher restored from dist with identical SHA256 and successfully relaunched, returned HTTP 200 IDLE.
- New story_arc_quality.py supplies genre-specific HOOK→CLIMAX→RESOLUTION narrative contract and nonfatal warning for premature endings. Existing HOA episode 001 scene 8 flagged for early conclusion. Fake opening greeting triggers bounded retry. Story-arc integration tests 2/2 PASS. Film effect on audience not independently verified.
- Cached-media full render_one + audio AAC + ASS subtitle PASS for 4/4 styles: cinematic, whiteboard, hand_color, color_animation; original media production not modified and no credits spent.
- Existing MP4 files 22/22 ffprobe audio/video PASS. No claim of narrative quality from tech checks.
- Scratch cleanup: 2 old test mp4s (27,226,444 bytes) moved to _ARCHIVE/SCRATCH_QA_MEDIA_20261015 with SHA256 checked; no permanent deletion or disk space reclaimed.
- Long-flow paid MCP E2E and new 30min film validation not repeated; legacy test fixture missing, not counted PASS. Distribution zip not rebuilt.

## 2026-10-15 10:00 — Design only: Google Flow Web Tool auto-reconnect cross-machine
- Reviewed Auto Flow Manager, account/project/transport code and official Google/Chrome/Playwright docs. Found project Tool locator gap, /u/N/ URL mismatch, separate account registry portability risks, and an unused helper path inconsistency; no code changed or credit spent.
- Plan: docs/MASTER_PLAN_FLOW_AUTORECONNECT_MULTIMACHINE_20261015.md. Existing 9 submit_uncertain receipts remain untouched.


## 2026-10-15 — POC shared Web Tool on second Google account (TEST ONLY)
- Test account Chrome profile/CDP 9460 opened in visible desktop window; signed-in Google session not yet present. Second account still has 0 registered projects. No auth bypass.
- Shared link 8fbef6e9... shows Storyboard Director AI and "Dùng thử trong một dự án"; read-only test clicked it and verified project chooser UI.
- Direct old project/tool 8fbef6e9... did NOT expose expected V2 bridge; inferred shared-tool URL from live tool ID 642784b8... was not found. Actual live tool 642784b8... itself passed read-only V2 bridge check.
- NO auto-install integration, no credit, no project selection/modification, user production untouched. Need manual login in account 2 and verified share link of the working tool before true installation test.
- Evidence: docs/POC_SHARED_TOOL_NEW_ACCOUNT_20261015.md

## 2026-10-15 — Full Google Flow share three-click UI test
- Real UI clicked share -> selected known QA project -> clicked Open; navigated correct project/tool. MCP bridge on bundled shared Tool did NOT pass. Did not integrate.
- Working bridge Tool displays share dialog warning that anyone with link can view/copy tool and referenced media; no link generated/copy clicked pending user permission.
- Report docs/POC_SHARED_TOOL_NEW_ACCOUNT_20261015.md

## 2026-10-15 — Working Tool share attempt (no production integration)
- Authorized user permitted POC sharing. Clicked verified live Web Tool share/copy-link UI. Could not securely verify resulting public share URL from Windows clipboard; derived URL failed. No production integration or paid image request.
- Evidence in docs/POC_SHARED_TOOL_NEW_ACCOUNT_20261015.md.

## 2026-10-15 — Verified public shared Web Tool installed in second Studio Chrome profile
- User-supplied public share ID 69da...; real Google Flow Share > Project > Open on both Chrome profiles passed read-only native bridge and Flow SDK. Account2 QA project provisioned once and registered via Python->Node->Google Flow path, exit code 0; subsequent Auto Flow READY verified. No paid media requests.
- Corrected bundled flow_tool.json; added shared_tool_install.py, auto-flow-shared-install.mjs, Auto Flow cold-start registration and dynamic CDP READY state check; updated release manifest. All five targeted no-paid tests, syntax/compile, V2 hash baseline PASS.
- No live desktop restart to protect unsaved drafts. One-call cold-start auto-create, arbitrary project switching, machine migration and paid E2E remain UNVERIFIED.
- Report docs/SHARED_TOOL_AUTO_INSTALL_QA_20261015.md. Checkpoints shared_tool_autoinstall_before_20261015 and shared_tool_autoinstall_source_verified_20261015. No edits to V2 or its MCP server.

## 2026-10-15 — Google login truthful status + browser console/Chrome lifetime fixes
- Real signed-out test: Chrome CDP connected but Flow LOGIN_REQUIRED; UI and Auto Flow now require fresh Google authentication and MCP capability checks before READY.
- Own Chrome PID PowerShell discovery hidden via CREATE_NO_WINDOW; login watcher minimizes after verified auth+bridge, including user sign-in directly in Chrome.
- Studio-only Node CDP helpers do not call browser.close() on borrowed Chrome; preserve user session, tabs and queue.
- No-paid tests, Python/JS/Node compile and pinned V2 hash baseline PASS; real Chrome minimized while CDP and MCP stayed connected.
- Report docs/GOOGLE_LOGIN_TRUE_STATUS_NO_FLICKER_AUTOHIDE_20261015.md. Checkpoints google_auth_window_flicker_before_20261015 and google_auth_window_flicker_verified_20261015.
- No V2 modifications, no paid media or resubmission of nine uncertain receipts.

## 2026-10-15 — Robot and Google Flow login UI single-window consolidation
- Removed duplicate Robot buttons to open Edge tabs, additional Chrome windows or extra minimize controls; one login/show Google Flow action in Robot and one in Settings both use the same account-owned Chrome login API. Backend repeated login reuses same window; project tabs reused via --new-tab instead of --new-window.
- Real Chrome double-click: same PID and HWND count; Chrome auto minimized after Google auth+MCP, AUTO_FLOW_READY true. No media credits; V2 checksum untouched.
- Tested five targeted regression scripts, syntax, live-served HTTP. User's current Edge app page requires refresh to load latest DOM; no forced reload to protect unsaved input.
- Report docs/SINGLE_GOOGLE_LOGIN_NO_EXTRA_WINDOWS_20261015.md. Checkpoints one_google_login_ui_before_20261015 and one_google_login_ui_verified_20261015.

## 2026-10-15 — EXE/native window & backend lifetime root-cause fix
- Reproduced: stale EXE + Edge app, dead localhost:8765 Python backend; second EXE launch opened web browser. Root: Python used transient Edge subprocess poll() to terminate Studio, while EXE remained active.
- New native EXE built and installed: single-instance reopen event and backend HTTP watchdog; Python backend lifetime independent from Edge browser child, native EXE opens one app-mode window after healthy HTTP; no default-browser fallback.
- Real double-open test: one EXE, one Edge --app, backend PID unchanged. Real IDLE backend crash test: watchdog restored server within ~10s (new pythonw PID) with Edge count unchanged. After recovery authenticated Google Flow Chrome CDP and Auto Flow READY, no paid requests or replay of 9 uncertain jobs.
- Checkpoints studio/checkpoints/launcher_backend_lifecycle_before_20261015 and launcher_backend_lifecycle_verified_20261015; report studio/docs/EXE_BACKEND_LIFECYCLE_MCP_RECOVERY_20261015.md. No V2 edits.

## 2026-10-17 — Main PC MCP hidden-browser tab ownership repair
- DESKTOP-EE8BGVF / D:\STORYBOARD_AI only. See docs/FLOW_TAB_OWNERSHIP_20261017.md.
- Reproduced original-tab disappearance during production-session prepare/abandon; Chrome then exited after last disposable tab release.
- Regression proves duplicate cleanup closed original tab solely from CDP ordering; verify endpoint also invoked destructive cleanup.
- projects.py now preserves unowned tabs; worker finalizer no longer bypasses safe-release refusal with raw CDP close. Completed or verified untouched own targets only; uncertain work preserved.
- Four new tests RED→GREEN; existing duplicate guard, private isolation, py_compile, pinned V2 baseline PASS.
- Live no-render session test failed before and PASS after backend watchdog reload; original target/Chrome PID preserved hidden and bridge healthy.
- Checkpoint: checkpoints/FLOW_TAB_OWNERSHIP_BEFORE_20261017.
- User started DRAMA episode 2 (30min/72 scenes) around 08:17; no runtime changes while active. Full paid E2E remains unverified.

## 2026-10-17 — User correction: minimize Chrome ON TASKBAR, never SW_HIDE
- User explicitly requires the Chrome window to stay running and minimized on taskbar, rather than fully hidden.
- studio_flow_accounts.minimize_chrome_window now uses SW_SHOWMINNOACTIVE (7) only; removed SW_HIDE (0). Existing async lock uses the same taskbar-minimize function, preserving manual login/restore behavior.
- tests/test_flow_minimize_taskbar_20261017.py: observed RED on [6,0] window operations, GREEN on [7] only. Two taskbar tests plus four tab-ownership/failed-worker tests PASS; py_compile PASS.
- Checkpoint: checkpoints/FLOW_TASKBAR_BEFORE_20261017/studio_flow_accounts.py.
- Verified IDLE backend only reloaded via EXE watchdog as PID19836; Chrome PID27216 retained.
- Live checks: Chrome HWND visible=true, minimized=true, tool_window=false; same PID and targets; actual scoped MCP bridge health passes. Evidence diagnostics/flow_taskbar_live_20261017.json.
- Separate latest production blocker: 08:19:59 native MCP POLICY_BLOCKED Image budget exhausted; surfaced at 08:20 as REMOTE_UNCERTAIN_NO_RESUBMIT. Chrome still running. No automatic re-submission, no quota/journal modifications.
- This change does not certify full production E2E or unlimited lifetime connectivity.

## 2026-10-17 — Pin production to connected tab; isolate changed image-batch budget
- User requires exactly the existing Web Tool tab; no per-production new tab.
- production-job-tab.mjs now borrows the exact existing target and never calls newPage, goto, page.close, or browser.close. Completed own queue is cleared only after verified worker release; borrowed tab stays. Fresh abandon also keeps it.
- production_tab.py passes private state directory; unsent default shot_1 draft is archived locally before an approved image batch replaces it. Preparation itself does not erase/submit the draft.
- mcp_v2_batch.py uses a deterministic output scope derived from full image specs/model. Identical batch resumes same journals; changed script has a separate bounded budget, leaving old journals/slots/images intact.
- Root cause of latest budget failure: legacy scope had 20 old completed + 52 current reserved records filling 72 native slots; current batch had no matching completed receipts. Reserve loop failed BEFORE startImageProduction for that request. Matching failed request and saved plan verified by job IDs. No old uncertain work was blindly resubmitted.
- Legacy journals and reservations archived under checkpoints/FLOW_PINNED_BUDGET_BEFORE_20261017; originals kept.
- Tests observed RED→GREEN: exact-tab create/close/abandon (3 Node cases), revision persistence/separation (Python case). Prior six tab-ownership/worker/taskbar unit cases PASS; Python/Node syntax and pinned V2 runtime baseline PASS.
- Live verify_existing_tab test PASS: Chrome PID27216, target DE0B249A777830C2C7692551A72E8A2A, one tab, taskbar minimized, MCP healthy, release kept=true/closed=false.
- Studio was closed when resuming; relaunched exact EXE once. Authorized DRAMA episode2 resumed from saved 72-scene plan at 08:35:55, same selected model and cap72.
- At 08:36:31 first actual new-batch image receipt completed; same Chrome/one target remained. Remaining production observed via diagnostics/production_observation_20261017.json; full E2E not yet certified.

### Live validation update 08:50–08:51
- At08:49:43: MCP_BATCH_ALL_IMAGES_PASS72 remote_jobs72; all72 native receipts completed and imported.
- Same Chrome PID27216 and exact target DE0B249A777830C2C7692551A72E8A2A remained throughout the full14-minute image batch; one page; taskbar minimized.
- Scene1 final.mp4 passed QC:24.36s,3164274bytes,h264/aac, burned karaoke subtitles.
- Scene2 final.mp4 passed QC:23.32s,2964544bytes,h264/aac, burned karaoke subtitles.
- Worker proceeded to scene3. Full episode assembly/package remains in progress; do not claim final full-film E2E PASS yet.
- Details: docs/PINNED_TAB_BATCH_BUDGET_20261017.md; source hashes/checkpoint at checkpoints/FLOW_PINNED_BUDGET_VERIFIED_20261017.


## 2026-10-18 — Fix exact-clone YouTube caption download
- Root cause: the video exposes Vietnamese automatic captions, but `transcript_cloner.fetch_youtube_transcript` fetched the caption URL with a raw `urllib` request. YouTube rejected that request, so exact-clone production stopped before scene generation with `CLONE_CAPTIONS_MISSING_OR_UNAVAILABLE`.
- Updated `studio/transcript_cloner.py` on the main machine and the Korea installation to let yt-dlp download the selected JSON3 subtitle into a temporary folder with `skip_download=True`; the folder is removed after parsing. The existing requirement for verified transcript and visual evidence remains.
- Backups: `backups/caption_fetch_fix_20261018/transcript_cloner.py` on main; `studio/checkpoints/caption_fetch_fix_20261018/transcript_cloner.py` on Korea.
- Verification on both machines: `py_compile` PASS; live caption extraction from the current reference video returned 610 Vietnamese timed lines over 2,662 seconds; temporary caption folders returned to zero. Updated file SHA-256 matches on both machines: `D47E8FE24D34ABD7CEEDC2036EC76ECC5343D1C2B20B79C14FA2017B99BF02D0`.
- Both production backends were IDLE after the fix. Full film generation was not started, so paid Gemini/Flow production remains unverified.
- This is an in-place hotfix; the displayed app version and already-built installer remain 1.2.9 until the next packaged release includes this file.

## 2026-10-19 — Korea ComfyUI GPU discovery and readiness fix
- Root causes: the current AutoSetup-Test provider did not search `C:\ComfyUI` and only accepted `.venv`, while the installed ComfyUI uses `C:\ComfyUI\venv\Scripts\python.exe`. The UI also hardcoded the label `RTX 3060 Ti`; the actual GPU is an RTX 4060. Startup took longer than the app's 70-second limit, and health probes of 0.25–0.4 seconds falsely reported not ready; first `/system_stats` response was about 0.38 seconds.
- Updated main source and Korea AutoSetup-Test: discover `C:\ComfyUI` and portable ComfyUI paths, accept the standard Windows `venv`, raise startup wait to 240 seconds and readiness checks to 2 seconds, and remove the incorrect static GPU label.
- Closed the older Pro instance and restarted only the current AutoSetup-Test app. Live API now reports RTX 4060, ComfyUI installed and ready at `C:\ComfyUI`, checkpoint `DreamShaper_8_pruned.safetensors`, and ComfyUI device `cuda:0 NVIDIA GeForce RTX 4060 Laptop GPU`.
- CUDA check passed with PyTorch `2.6.0+cu124`. A single 512×512 local image smoke test through the Storyboard ComfyUI provider completed in 33.7 seconds; the temporary image and newly created ComfyUI output were removed. No full film production was run.
- ComfyUI warns that cu130+ is needed for optimized CUDA operations and that optional metadata enrichment lacks SQLAlchemy; neither prevented the CUDA smoke image. Torch was not upgraded.
- `py_compile` passed for the modified provider and web server on both main source and Korea AutoSetup-Test. Backups were saved beside the modified files. App display/version and installer remain 1.2.9; no new installer was built.


## 2026-10-21 — Muse saved-session provider
- Checkpoint: D:\STORYBOARD_AI\backups\muse_cli_before_integration_20261021.
- Replaced the prior Muse API-key/guessed-endpoint flow with the validated muse-cli gateway worker; durable per-scene receipt, no automatic render resubmission, resumed binary download, full media decode.
- Added native SCENE_001 timeline input compatibility and saved-session connection settings. Muse keeps the existing narration pipeline.
- Verification: 14 unit checks, 4 UI logic checks, 4 HTTP checks, 4 cached legacy render modes, 2 actual silent-scene E2Es (16:9 and 9:16), same-session resume and preview integrity checks.
- Main source content matches tested staging. Running v-tranh job on port 8765 remains active; no backend/UI restart. New backend and UI load after the next full application restart.
- Details: docs/MUSE_CLI_INTEGRATION_20261021.md. Evidence: feature_staging/muse_cli_20261021. No V2 or second-machine changes.


## 2026-10-21 — Muse login button and Instagram redirect correction

Added visible scoped Muse sign-in, verified session export, pending-account protection, auth-specific timeout/process-tree cleanup. Official root reproducibly redirects through Meta session checks to Instagram; sign-in entry now muse.ai/business, exposing phone/email form. Existing valid Muse session preserved in actual HTTP tests. 25 unit + 6 UI cases + 5 actual HTTP checks pass. Seven source/test files match staging; main backend activation awaits restart after active v-tranh production finishes. No production interruption. Checkpoint: D:\STORYBOARD_AI\backups\muse_login_before_20261021. Details: docs/MUSE_LOGIN_FIX_20261021.md.


### Muse activation after completed production — 2026-10-21

Main v-tranh finished COMPLETED/100%, exit 0. Restarted owned native/backend processes after idle; refreshed the one desktop UI window. New login API/buttons active on 8765, existing Muse session READY. Five actual login HTTP checks PASS. Two new main-app E2Es PASS: 16:9 1280x720/8.043s in 155.093s; 9:16 720x1280/8.043s in 134.344s. Both full FFmpeg decode and HTTP 206 playback PASS. These use the existing saved account; new manual account login not completed by the user. Detailed activation evidence in feature_staging\muse_login_20261021\main_activation_result.json; docs/MUSE_LOGIN_FIX_20261021.md updated. Activation no longer pending.


## 2026-10-21 — Multi-account cookie recognition diagnosis

Three isolated saved cookies confirmed against Muse /api/session: HTTP 200 for all, three distinct assigned VMs. Initial third-account auth worker held a lock for >349s; stopped only its owned process tree. Applied checkpointed muse_login.py changes: remove unconditional duplicate legacy-session overwrite, bound Gateway verification step to 35s. Three new regression tests + 14 existing scoped Muse units pass. Outstanding: live login/complete still observed a 121s timeout, auth probe MUSE_LOGIN_BROWSER_NOT_READY, and second profile gateway MUSE_CONNECTION_INTERRUPTED on two checks. Registry READY does not establish full gateway availability. No full multi-account E2E performed. Do not mark auto-recognition fully fixed. Details: docs/MUSE_MULTI_ACCOUNT_DIAG_20261021.md; checkpoint backups\muse_autodetect_recovery_20261021.


## 2026-10-22 Grounded YouTube SEO
User authorized research and implementation of six-part design. V2 unchanged; no Git.
Checkpoint: D:\STORYBOARD_AI\backups\grounded_seo_before_20261022_014454
New engine reads all episode scenes/dialogue, supports native drama cast mappings, validates native-language metadata, creates three title alternatives and one thumbnail. Scores are internal checks, vidIQ/Analytics remain unknown without service data.
Independent review: nine findings fixed with RED/GREEN regressions (cache route/fingerprint, exact episode IDs, stale exports, same-file selection, malformed provider fields, fallback retry, manual import locking, manual schedules).
No YouTube publication or account changes.

Verification complete 2026-10-22: 33/33 new Python regressions on Windows; 5/5 existing international SEO tests; Node renderer/cache/schedule checks and 3 cinematic/narrative submit payload cases pass. Headless Edge against live backend: three title alternatives, one image, zero page errors; test browser blocked account/upload writes. DRAMA episode 003 package generated from all 20 saved scenes/dialogue and actual scene result durations (7 chapters). Actual configured Gemini API response captured during smoke, validated after keyword correction, replayed without additional API spend, and saved with response_source=recorded_real_api_response. Visual QA moved auto overlay below both upper faces. Checkpoint and source hashes verified before apply. Backend restarted only while IDLE and recovered under native launcher (PID 38584 at verification). Ready-to-publish TXT/JSON/main thumbnail synchronized; previous duplicates archived reversibly. No vidIQ service/Analytics measurement fabricated; those remain unavailable. No changes to V2, voice/account configuration; no YouTube upload.


## Automatic official vidIQ title ratings — 2026-10-22
- User requested automatic scoring when SEO generation finishes, no separate scoring button.
- Every package save now ensures up to three official title scores through https://mcp.vidiq.com/mcp. Results cached per key/title/format; ambiguous paid attempts are not retried automatically. Free connection failures remain retryable.
- Key entered once in SEO panel and stored with Windows DPAPI. No credential found in current Studio configuration; no real paid call made or score claimed.
- Provider scores remain distinct from internal metadata checks and observed YouTube Analytics. No aggregate extension SEO Score API is available in the exposed tool set. Thumbnail API requires videoId; prepublish thumbnail remains explicitly unscored.
- Local-origin checks added to GET/POST SEO and key-save routes. Independent review findings fixed.
- Validation: 38 grounded/new Python tests plus 5 existing standards on Windows, Node renderer/cache/schedule tests, syntax checks and DPAPI roundtrip. Initial Windows test harness import/CWD errors corrected before final passing run.
- No Git; no changes to YouTube SEO Pro V2. Checkpoint: D:\STORYBOARD_AI\backups\before_vidiq_auto_20261022_021108
- Post-restart live smoke: SEO DRAMA episode 3 retains three titles, automatic not_connected state, no invented scores; key UI served; cross-origin GET/POST scoring and key-save requests return 403.


## Restore complete SEO dashboard — 2026-10-22
- User reported missing SEO functions. Root cause: earlier grounded SEO change removed 12 schedule/benchmark display elements. Restored original card layout and all IDs, preserving competitor audit, thumbnail tools, upload controls and automatic vidIQ connection.
- Unknown schedules and market metrics stay unknown. Five internal comparison rows now visible; no invented percentile, CTR or recommendation multipliers.
- RED/GREEN layout regression, Node renderer/cache/schedule checks pass. Staged and live Edge browser checks: 12 restored fields visible, five comparison rows, three titles, one thumbnail, competitor/vidIQ inputs visible, no page errors. Browser QA blocks POST and serves existing episode metadata, without paid provider calls.
- Checkpoint: D:\STORYBOARD_AI\backups\before_seo_layout_restore_20261022_021747


## Compact SEO evidence UI — 2026-10-22
- User rejected oversized restored comparison dashboard. Replaced oversized score circles/cards/empty comparison table with compact internal checklist strip and collapsed vidIQ/tools summary.
- Retained title/thumbnail/edit/upload controls, key connection, competitor metadata audit and schedule tools. Key and audit forms open only on demand. Official numeric title scores stay beside their exact titles; missing scores are not zero. Removed repeated unmeasured CTR badges.
- No measured market dataset currently exists in backend; market result table stays hidden. No inferred or fabricated market/CTR/SEO-extension score supplied. Local checklist labeled internal.
- Node layout/renderer/cache/schedule regressions and syntax checks pass. Staged/live Edge tests: compact closed height <60px, forms open, schedule expands, real numeric zero renders correctly, 660px responsive check, no JS errors. QA uses saved episode metadata and blocks writes/provider charges.
- Checkpoint: D:\STORYBOARD_AI\backups\before_seo_compact_20261022_030330


## Fix Muse native-audio render failure — 2026-10-22
- Reproduced v-tranh episode 2 scene 1 failure: UnboundLocalError for merged. Native Muse video and audio existed, but native scale/audio branch referenced merged before later assignment.
- Moved merged path initialization above render branch; retained native Muse audio path and ordinary/cached rendering behavior.
- RED: exact native branch fails before fix; GREEN: three tests pass (new native clip, cached silent resume, ordinary image/TTS render).
- Actual saved Muse clip rendered in isolated staging with cached-media-only guard (no new provider requests). Final h264/aac 1280x720, duration 10.027s, karaoke subtitles, QC PASS. Production inputs untouched.
- Checkpoint: D:\STORYBOARD_AI\backups\before_muse_native_merged_20261022_063725

- Post-deploy validation: 3 native-audio merge regressions and 6 existing Muse provider/skill tests pass. Existing test_muse_video_integration.py wrapper then fails its legacy HTML assertion for id="inMusePython"; current HTML already lacked this ID before this render fix. This UI-contract mismatch is recorded and not changed by the merged-path fix. No claim of a fully green integration wrapper.


## Complete Muse integration fixes — 2026-10-22
- Replaced obsolete inMusePython HTML contract with current multi-account manager controls and handler bindings. Maintained actual provider/login/gateway/resume coverage; did not skip tests.
- Integration runner selects configured Muse interpreter for av/muse_cli dependencies instead of treating separate Studio runtime as Muse runtime. Initial missing dependencies and outdated single-account fixtures resolved.
- Updated login fixtures to isolated multi-account registries and browser paths; tests never touch real cookies or profiles.
- RED/GREEN fixes: reject stale/missing login token before auth-export; prevent account VM replacement while accepted/submission_uncertain scenes still belong to that VM. Independent account login remains allowed.
- Staging validation: 32 integration tests pass, covering provider, input formats, durable receipts, no repeated submission, download resume, login isolation, native-audio render and current UI contract.
- Production already running (past scene 1); no restart, interruption, new generation request or session change. Installed login code is used by new auth workers; already imported desktop controller retains its copy until normal app restart after production.
- Checkpoint: D:\STORYBOARD_AI\backups\before_muse_integration_complete_20261022_073607

- Post-deployment canonical command (Studio runtime -> configured Muse runtime): test_muse_video_integration.py PASS, 32/32, no skips/failures. Live browser manager PASS: 3 accounts / 3 ready, all actions bound, no JS errors. Actual production scene_0001/result.json PASS with 10.027s h264/aac final; ongoing production observed at scene 10/52, exit_code null. Full 52-scene movie completion is not claimed.


## YouTube API upload dispatch repair — 2026-10-22
- Reproduced NameError on normal upload: contains_synthetic_media was never assigned in POST /api/youtube/upload. Added initialization from body/channel settings, preserving false.
- Removed obsolete Shorts/both batch branch using undefined long_video/short_video; normalize disabled formats to long before resolving media.
- Restored displaced language-code mapping body. Null playlist title stays None; missing schedule time returns 400 instead of invented 20:00.
- RED/GREEN: 6 new route/metadata tests and 4 existing manager tests PASS, with all credential writes isolated to a temporary CHANNELS_FILE.
- Live Google channels.list HTTP200 and correct selected-channel identity; youtube.upload scope verified. Real YouTube resumable session initialization accepted, stopped before sending video bytes; no publication or complete upload claimed.
- Browser dispatch smoke PASS: correct request payload, UI resets on API failure, no JS errors. All browser POST requests intercepted.
- Windows denied atomic replacement of loaded web_server.py (write allowed, delete/rename denied). After verified checkpoints, wrote validated sources and compared complete text; both compile. Active production not restarted.
- Backend running=True. Request handler must reload at normal app restart after current movie finishes.
- Checkpoint: D:\STORYBOARD_AI\backups\before_youtube_upload_fix_20261022_080621


## 2026-10-22 — SEO topic alignment
- Checkpoint: backups/before_seo_topic_alignment_20261022_172552. Sources seo_quality.py, seo_packager.py and affected episode outputs backed up before edits. No Git; YouTube SEO Pro V2 untouched.
- Root cause: extractive fallback and chapter/tag extraction prioritized English visual scene summaries over Spanish narration. Updated context, prompt, fallback and native-language checks to prioritize produced spoken content/on-screen text. Reference title is topic guidance only, never evidence for unsupported claims. Cache fingerprint includes produced story content.
- Restored honest internal check scoring and unknown publishing schedule when analytics data absent; no fabricated vidIQ/performance/time data.
- Validation: 42 SEO regression tests passed; live source matches tested staging and compiles. Spanish episode_002 regenerated, source fingerprint and native titles verified; publish TXT mirrors organized. Actual generation method extractive_fallback, failure_stage validation, review_required true (not claimed AI/vidIQ validated). Primary keyword entusiasmo por la vida.
