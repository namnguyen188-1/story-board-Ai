# FlowKit Web Tool Adapter (27/28-10-2026)

Module: `D:\FLOWKIT\app\flow_webtool_direct.py`
API: `http://127.0.0.1:18110` (local-only)
Auth: `X-API-Key` from `state/api.key` (do not put the key in logs).

## Modes
- `active`: working Director AI tool in `settings.json.flow_webtool_url` (old/rendered Web Tool)
- `hidden`: GUI-hidden shared tool in `settings.json.flow_hidden_webtool_url` (test mode)
- Both run in FlowKit's private Chrome profile on CDP 9233, without MCP V2.
- App iframes are selected by the exact parent tab ID using CDP `Target.getTargets().targetInfos[].parentFrameId`; never mix iframe state across tools.
- Existing Flow Direct and Muse endpoints are unchanged. Storyboard AI and YouTube SEO Pro V2 are untouched.

## Endpoints (all require X-API-Key)
- GET `/v1/webtool/status?mode=active|hidden`:
  Returns `connected`, processing state, model, queue shot statuses, and supported capabilities; does not submit anything.
- POST `/v1/webtool/start-existing`:
  JSON `{"mode":"active","expected_shot_id":"shot_1","request_id":"unique-key-0001","confirm":true}`.
  Starts only exactly one pending shot using an available native UI button. Stores an at-most-once attempt ledger BEFORE clicking. Cannot arbitrarily submit a new prompt.
  For the **hidden** Web Tool, the Bridge currently exposes only queue/config/isProcessing/setConfig/setRefImage/capabilities. No start/submit function or rendered button. Hence the endpoint correctly responds `503 WEBTOOL_START_API_NOT_EXPOSED` and DOES NOT submit media.
- POST `/v1/webtool/export`:
  JSON `{"mode":"active","shot_id":"shot_1"}`.
  Exports a completed MP4 from the tool iframe to `D:\FLOWKIT\outputs\webtool_exports\<sha256>.mp4`, validates ISO MP4 signature and ffprobe, and returns dimensions/duration/hash/download path. No new media generated.
- GET `/v1/webtool/files/<sha256>.mp4`:
  Serves only verified hash-named files to authenticated API clients.

## Tests
- Active: connected, queue completed, video present.
- Hidden: connected, queue pending, no native submit/start or UI button.
- TestClient: status 200; no API key 401; hidden start 503; completed 8s video export 200 (720 x 1280, 2,798,894 bytes), MP4 download 200, valid ftyp header.
- Live API 18110: both statuses 200, Flow extension connected true.
- No new video generation during integration tests.

## Limitation and next step
The adapter does not make a private Google Flow RPC part of its API. For a truly invisible production engine, the hidden Web Tool itself MUST expose an authorized, documented, versioned `submit / status / result` bridge; it currently does not. It is impossible to synthesize such a function by merely reading its queue/config. Add a stable, narrow Bridge API **inside the Web Tool**, then extend this adapter to call that API and bind it to FlowKit `/v1/jobs` with remote idempotency. Never automatically resubmit unknown jobs; retain both providers independently.

## Update: REST job integration (2026-10-28)

The independent Web Tool provider is now available through the existing FlowKit API:

```json
{"provider":"webtool","webtool_mode":"active","kind":"video","prompt":"CẢNH 1: ...","aspect_ratio":"9:16","duration_seconds":8,"request_id":"unique-request-id"}
```

- POST `/v1/jobs` returns the Job ID. GET `/v1/jobs/{id}` reports state and phase.
- Successful jobs expose `/v1/jobs/{id}/files/video.mp4` as a verified artifact.
- `flow_webtool_jobs.py` imports one prompt into the existing Web Tool queue and invokes production only once, with a persistent request ledger.
- `flow_webtool_worker.py` polls, exports the completed video and verifies format.
- `webtool` jobs have one serialized worker, independent of `flow` and `muse`.
- Do not silently switch between the GUI-hidden and working Web Tool.
- If a remote submit outcome is uncertain, NEVER automatically resubmit. Only resume a known shot ID.
- For the GUI-hidden variant, source must expose `window.__STORYBOARD_MCP__.v1.submit/status/result`. It does not yet; this mode is NOT production-ready.
- Live E2E: Job ID `7ad82106-7785-4c76-9454-9598812c4e38` was accepted, imported and started, but the video service returned a terminal failure; no new MP4. Existing 8s MP4 export/recovery succeeded, verified SHA-256 and dimensions.
- API authentication, idempotent replay and provider isolation pass regression tests.

## Remixed hidden Web Tool – verified production (2026-10-28)

- Original shared Web Tool (unchanged): https://flow.google.com/shared/tool/9ea06a9a-5ff6-4393-a9c1-915dfc6d4c6e
- Created editable remix by clicking "shuffle – Công cụ tạo bản sao tuỳ chỉnh" from the project-installed shared tool:
  https://flow.google.com/project/a3d78d4d-55f8-4cf9-bdee-73b7deb8a211/tool/49c17a45-7dbe-437b-a5d7-f5a006130714?mode=EDIT
- Default runtime view (hidden app):
  https://flow.google.com/project/a3d78d4d-55f8-4cf9-bdee-73b7deb8a211/tool/49c17a45-7dbe-437b-a5d7-f5a006130714
- Legacy Web Tool remains configured as backup; its browser tab was closed after the hidden job passed.

**Critical architectural finding:** The inherited hook `hooks/useStoryboardBridge.ts` already exposes functions `window.__STORYBOARD_MCP__.capabilities.addToQueue`, `updateItem`, `retryItem`, etc. These functions are omitted from JSON serialization and were previously misread as an empty object. The hidden interface therefore remains controllable through the existing React bridge. No external or unauthorized Google Flow endpoints are called by the Web Tool adapter.

The FlowKit compatibility adapter now enqueues exactly one video job, patches its aspect ratio/duration, and invokes `retryItem(shotId)` on **that shot alone**. Existing sample/pending scenes remain untouched. A persistent request ledger is written before enqueue and before render; ambiguous results are never automatically resubmitted. A stuck `enqueued` job with known shot ID may be safely started exactly once via `resume`.

**Verified E2E job:** `232185a8-31ce-4886-b7b4-ec3feab54b1e`; success after recovering an unstarted enqueued shot, file `D:\FLOWKIT\outputs\232185a8-31ce-4886-b7b4-ec3feab54b1e\video.mp4`; 4,916,569 bytes; 8.042667 seconds; 720x1280; H.264 video, AAC audio; complete ffmpeg decode PASS; SHA256 `34897c56b29d34d62d3f120bd1eaab76fdd75db980dbf7e567322d28bc86bbfc`; authenticated API artifact endpoint returns HTTP 200, SHA match.

**Defaults updated:** `gateway.JobRequest.webtool_mode = hidden`, the providers summary reports the hidden adapter, and the FlowKit hidden-Chrome launcher prefers `flow_hidden_webtool_url`. Only the remixed hidden Web Tool tab remains; legacy tab closed. Other FlowKit providers and all other apps untouched. No changes were successfully made to Google Flow's source through the tool builder—the project Remix retains inherited hook code, with compatibility added locally in FlowKit. For long-term portability a documented stable `v1.submit/status/result` interface can still be added in the editable Remix; the existing `capabilities` API is currently sufficient for 8-second video jobs, but should be treated as a potentially changing interface. Multi-job throughput and Chrome-restart recovery during active generation have not been fully E2E verified.

Checkpoint snapshots:
- `D:\FLOWKIT\state\checkpoint_remix_native_20261028`
- `D:\FLOWKIT\state\checkpoint_remix_default_20261028`

## FlowKit On-Demand mode (2026-10-28)

Files:
- `D:\FLOWKIT\settings.json`
- `app\browser_lifecycle.py`: tracks in-process job leases, the persistent queue, uncertain jobs, active Web Tool render status and browser ownership; opens on demand, closes after idle, never touches other Chrome profiles.
- `app\launcher.py`: launches the API and Flow extension broker without opening Chrome/Web Tool at startup.
- `app\gateway.py`: on a claimed `flow` or `webtool` media job, acquires a browser lease then opens FlowKit's Chrome, keeps it until verified output / terminal result, releases lease; includes idle watcher.
- `app\flow_window_guard.ps1`: hides FlowKit's Chrome window; auto restart is DISABLED in on-demand mode.
- The Web Tool selected is the hidden remixed tool; URL stored in `settings.json`.

Configuration:
```json
"browser_mode": "on_demand",
"browser_idle_close_seconds": 90
```
Keep the lightweight API process available at `http://127.0.0.1:18110`. No browser is needed during scriptwriting.

Lifecycle:
1. Scriptwriting / querying health -> API available, Chrome/Web Tool not launched.
2. Job is claimed by `provider=webtool` or `provider=flow` -> open FlowKit dedicated Chrome profile + hidden Remix Web Tool (unless already running).
3. While any media job is queued or running, or a worker lease exists -> NEVER close. Unresolved `recovery_needed` jobs also block automatic closure.
4. After each job's MP4 is verified and saved, hold Chrome during the idle grace period. If no relevant jobs or uncertain outcomes and Web Tool reports no active render, close FlowKit Chrome after idle delay.
5. Cold Chrome may restore duplicate Web Tool tabs. Check React Bridge state in *each* duplicate, and close extras ONLY if all tabs idle; refuse unsafe deletion.
6. Do not auto-resubmit an uncertain remote job. Do not touch Storyboard AI Chrome (9550) or default user Chrome.

Endpoints (X-API-Key required):
- `GET /v1/runtime/browser`: mode, browser running, active and unresolved jobs, worker leases, idle time, active URL, protection policy. DOES NOT open browser.
- `POST /v1/runtime/browser/stop`: immediately closes only if safe; returns 409 with reason otherwise.
- `GET /`: compact dashboard with the exact lifecycle.
- `GET /health`, `GET /v1/providers`, scriptwriting and Muse jobs do not trigger FlowKit Chrome startup.

Verification:
- Python compile PASS.
- Safety tests with worker lease: `WORKER_USING_BROWSER`; pending recovery: `JOBS_ACTIVE_OR_RECOVERY_NEEDED`.
- API authentication: status 200 with key, 401 without key.
- Live manual safe stop: `closed=true, reason=IDLE_SHUTDOWN`, Chrome/debug port 9233 closed, API remains available.
- GET health and providers with Chrome closed leaves browser_running=false.
- Cold worker startup: Chrome starts; extension installs; after deduplicating restored tabs, exactly one Remix Web Tool tab and readable Bridge.
- No additional media generation/credits used for these lifecycle tests.
