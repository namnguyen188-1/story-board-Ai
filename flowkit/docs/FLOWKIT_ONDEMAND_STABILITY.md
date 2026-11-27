# FlowKit On-Demand Stability (2026-10-28)

Only `D:\FLOWKIT` on main PC was modified. Flow Direct and Muse remain independent. Original Storyboard AI and YouTube SEO Pro V2 were not edited.

## Policy
- `browser_mode = on_demand`, `browser_idle_close_seconds = 90`.
- Scriptwriting and API health: Web Tool browser stays closed; lightweight localhost API stays up.
- Real media job: private Chrome starts, exact remixed Web Tool opens, extension/Bridge becomes available; duplicate tabs are collapsed only if no unique pending or unsaved completed work would be lost.
- While queued, rendering, exporting, or unresolved recovery: Chrome cannot be closed by the idle watcher; only closes after verified artifacts and grace period.
- The user-requested login-unlock setting is not cleared by headless startup.
- If a job was interrupted, automatic reconciliation is **read-only** and only queues a known shot in a verifiable generating, completed, or validated prepared state. It does not resend ambiguous remote submissions.
- No silent fallback from Web Tool to Flow Direct or Muse.
- The API is available at `http://127.0.0.1:18110`. Secured endpoints: `GET /v1/runtime/browser`, `POST /v1/runtime/browser/stop`, `GET /v1/jobs/{job_id}`. Reuse an identical Idempotency-Key to avoid duplicate billing.

## Verified results
- Cold start from `browser_running=false` -> one remote Web Tool render -> `succeeded`.
- Job `70f37044-abc1-436e-8dd0-920414a9c17b`: 8.043s, 720x1280, video and audio, size 4,472,002 bytes, SHA256 `3c128c5cc92698adcb05f79e915631e66d88b3c330643668a590c25e47b392a1`.
- FFprobe PASS, full FFmpeg decode PASS, stored artifact SHA256 PASS.
- Automatic idle close PASS with temporary 30-second setting; configuration restored to 90 seconds.
- After browser stopped, API health PASS; browser state `sleeping=true` not treated as disconnected failure.
- Idempotent replay PASS: same request key returned original job ID and did not trigger a new render.
- Safe recovery regression mocked six interrupted job states; only three safe scenarios were requeued, dangerous/ambiguous cases remained protected.
- Storyboard AI independent browser (port 9550) remained running.

## Known limitation
A hard browser crash can erase Web Tool in-memory queues. A FlowKit ledger is not a Google Flow server-side resumable job ID; missing remote shots cannot be reconstructed without supported remote status/result methods. In ambiguous cases FlowKit records `recovery_needed`, prevents duplicate production, and requires manual inspection. Long sequential runs and true power-loss mid-render have not been proven end-to-end.

## Restore
Local checkpoint: `D:\FLOWKIT\state\checkpoint_stability_GREEN_20261028`.
Before any rollback, stop new jobs and snapshot the current jobs database. Copy code/config from checkpoint back to `D:\FLOWKIT` and restart only this kit's API.
