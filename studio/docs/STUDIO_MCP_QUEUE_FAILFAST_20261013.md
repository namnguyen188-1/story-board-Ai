# Storyboard AI — MCP queue guard at every entrypoint, 13/10/2026

## Applied
- Real Storyboard app, DESKTOP-EE8BGVF, D:\STORYBOARD_AI\studio. Preserved V2, the old whiteboard submit_uncertain journal, previous films, and Google account credentials.
- studio_mcp/image_backend.py: refactored pure read-only `validate_image_tool_readiness()` and enforce preflight inside `render_one_queue()` for **all new image jobs**, including direct single-image callers, before reserving slots or writing submit_uncertain. Previously only full-episode batch invoked preflight explicitly.
- web_server.py: for LIVE + private MCP, after input/project/dependency/episode-conflict checks but before saving inbox or contacting Gemini, perform read-only health for the exact selected account/project/tool. If queue has completed image, active work or user prompt, return 409 `MCP_QUEUE_PREFLIGHT_BLOCKED` with no production start or spend.
- web/app.js: show localized human-readable modal explaining the blocked queue, without offering an automatic retry. web/index.html: cache-bust script to `20261013_mcp_queue_guard_v6`.
- No auto-clearing user prompts or re-submitting old uncertain jobs, no new paid image request.

## Verified
- Synthetic health guards: empty + truly blank initial video shot allowed; completed image, busy queue, populated user's pending video shot, foreign queue rejected before credit reservation. PASS.
- Single-image render backend direct call with spending enabled: completed image and populated user pending prompt blocked with only a read-only health call, **no file or slot created**. PASS.
- Actual Playwright click **Sản Xuất Tập Phim Bằng AI** on Studio UI with registered MCP genre whiteboard while user's original pending shot_1 was open: returned HTTP 409 with correct localized message; UI preserved draft; no /inbox files, no production folder, no actual render or paid image request. PASS (initial test).
- Regression checks: multi-project route HTTP 409, saved-account UI, batch four-image mock, private node spend guard, color renderer unit tests PASS.
- One old test `test_http_budget_failfast_existing_plan.py` could not run due to missing referenced archived/removed Stoic plan under productions; not counted PASS; no recycle-bin restoration.
- Later, when repeating the actual UI test, Chrome project tab had been closed externally (GET /api/mcp/projects open_tabs=[]). UI returned early `STORYBOARD_PRIVATE_WEB_TOOL_NOT_OPEN` 409; this is expected safe browser preflight, not an MCP queue regression. We did not reopen or replace the user's browser tab or claim a second PASS.
- At last check Studio IDLE and registered projects intact. No paid request during this continuation.

## Live E2E status carried over
- Offline actual GUI hand_color & whiteboard: both PASS, 2/2 scenes each.
- Live actual GUI hand_color: PASS, 1 MCP image / 1 scene.
- Live actual GUI whiteboard old production: `BLOCKED_MCP_IMAGE`; image journal remains `submit_uncertain`, not resubmitted. Whether the earlier request cost credit remains unknown.
- Live black-white after new guard **not paid-retested** because old job uncertain and private Chrome tool tab currently absent. Full multi-scene/1080p not verified.

## Files and checkpoints
- Existing backup: `checkpoints/all_image_entrypoints_preflight_before_20261013`
- New verified: `checkpoints/all_image_entrypoints_preflight_verified_20261013`
- Earlier backup: `checkpoints/mcp_queue_preflight_before_20261013`
- This report: `docs/STUDIO_MCP_QUEUE_FAILFAST_20261013.md`
