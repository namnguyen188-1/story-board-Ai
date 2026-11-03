# One connected Web Tool tab and bounded image-batch recovery
Device: DESKTOP-EE8BGVF. Storyboard only; no V2 or secondary-machine edits.

## User-visible behavior
Production borrows the selected connected tab's exact CDP target. Preparing, completing and abandoning a session do not create or close any page. Chrome remains minimized on the taskbar. Completed queue entries are cleared only by verified worker release after image receipts have been saved. Uncertain/running queues remain protected.

An unsent default shot_1 draft is copied into the account's private pinned_tab_drafts directory before the approved image batch replaces it. Preparing a session itself does not submit or erase that draft.

## Production blocker
The old episode output scope counted historical reservations against later changed scripts: 20 old completed records plus 52 newly reserved records filled the native cap72. Current72-scene request had zero matching completed receipts and failed inside reserve(), before startImageProduction. Exact job IDs were checked against the saved plan and native error trace.

The batch now has a deterministic scope derived from image specs and selected model. Same content resumes the same durable journal; changed input uses a separate bounded scope. Cap72 remains unchanged. Old images, journals and reservations remain intact and were additionally checkpointed.

## Changes
- studio_mcp/node/production-job-tab.mjs: reuse exact existing target; no newPage/goto/page.close/browser.close.
- studio_mcp/production_tab.py: require one registered existing Tool; pass private state directory for draft archive.
- mcp_v2_batch.py: deterministic per-content batch scope.

## Evidence
- Node lifecycle contract failed before fix and passes create/close/abandon with no page creation/closure.
- Python integration regression failed before fix and passes same-batch reuse / changed-content separate-budget behavior.
- Prior6 ownership, worker-release and taskbar test cases pass. Python/Node syntax and pinned38-core/4-adapter baseline pass.
- diagnostics/existing_tab_live_20261017.json: actual prepare/health/abandon preserved PID27216, target DE0B249A777830C2C7692551A72E8A2A and one minimized taskbar window.
- Actual saved DRAMA episode2 resumed at08:35:55,72scenes, unchanged approved cap72. First image receipt at08:36:31;25 completed by08:40:52. No second tab or budget failure observed.
- Latest read-only production observation: diagnostics/production_observation_20261017.json.
- Before checkpoint: checkpoints/FLOW_PINNED_BUDGET_BEFORE_20261017 (sources, saved plan, both legacy journal/slot trees).

Full video E2E is not yet certified. No automatic replay of ambiguous historical paid jobs or deletion of old images.

## Live outcome at08:50–08:51
The entire72-image batch completed/imported at08:49:43 with no extra tab or budget failure.
Actual scene1 and scene2 MP4s passed the pipeline's media QC (24.36s/23.32s,h264 video,aac audio,burned subtitles). Production advanced toscene3; full-film assembly remains underway.
