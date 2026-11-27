# FlowKit — Flow safety and cold-start E2E QA (28-10-2026)

**Status: R&D / RELEASE_BLOCKED.** Only `D:\FLOWKIT` was modified. Existing signed-in Chrome profile `D:\FLOWKIT\runtime\flow_profile` (CDP 9233), existing Google Flow project `CLI_LAB_20261021`. No Muse, Storyboard AI, or MCP V2 code/config was modified. No new Google Flow project. No package, release, or secondary-PC deployment.

## Findings
1. Flow Direct API engine 18100, same authorized Chrome profile, and extension work after on-demand cold start; GET Flow credit/permissions check returned HTTP **200** (response keys only: `note`, `userPaygateTier`). This establishes authenticated read-only connectivity **but does not verify generation or quota**.
2. Old Direct image job `1da7ab3e-814d-4d93-a348-484976fde3e1` remains `recovery_needed` due HTTP **502 RpcError**, unknown remote outcome and no confirmed media ID. It is parked for manual review. **Do not retry** it. The underlying Direct image generation RPC failure is NOT fixed or re-tested by a paid submission.
3. Flow Direct previously permitted an authenticated tab from a different project; pinned verification now requires exact approved Web Tool tab URL (path, scheme, host) and an authenticated page.
4. Job-request `project_id` mismatches are rejected before submitting media. No remote mutation.
5. Chrome extension CDP API may briefly return `CHROME_EXTENSION_API_UNAVAILABLE` on cold start while the authorized extension reconnects. Browser startup now checks the existing live extension first and waits/retries only transient extension management faults, without opening another Chrome profile.
6. FlowClient batch RPC no longer automatically fails over/replays requests across a second extension/profile. Earlier `RpcError [8]` auto-retry of image generation remains blocked.

## Actual regression (no media charge)
- `state/test_flow_direct_project_guard.py`: six checks PASS (right tab, foreign project, foreign tool, unauthenticated, wrong host, job project mismatch).
- `state/test_flow_extension_reuse.py`: 3/3 PASS (authorized extension, wrong project, disconnected).
- `state/test_flow_no_extension_failover.py`: PASS for generation and read-only RPC; second mock extension received 0 calls.
- `state/test_flow_direct_no_ambiguous_retry.py`: PASS, simulated RpcError [8] generated only one RPC call.
- `state/test_recovery_parking.py`: PASS, cannot resume unresolved old 502.
- `app/test_gateway.py`: 4/4 PASS, no live browser opened.
- `state/qa_flow_cold_start_two_cycles.py`: two **real** authorized-profile cold starts PASS, one approved tab each, authenticated Flow Direct page, browser returned to stopped state; outputs `state/flow_cold_start_two_cycles_20261028.json`.
- `state/qa_final_api_no_credit.py`: PASS on restarted API; auth, four prior artifacts downloaded and SHA-256 verified, idempotency, isolated batch/cancel, unresolved job resume rejected.

## Post-patch real media E2E
- New image job `43ad0df1-4599-4845-92bc-e17fffc70d23` via **Web Tool hidden**, 16:9 PNG **1376×768**, **1,743,761 bytes**.
- Verified actual PNG, SHA-256 `0a358f7dedf3847c43c4fb63bfb5bd4f8bef16aab980fcd003bc1c29167bd6ca`, authenticated API download identical.
- Journal `state/qa_flow_after_guard_image_20261028.json`.
- These results confirm Web Tool still works. **They are not a Flow Direct image-generation E2E success.**

## Remaining blockers
- Direct RPC image 502 remains unresolved on Google's generation path; do not bypass Google's anti-abuse systems or blindly replay.
- Need safe remote reconciliation mechanism/verified server media ID to recover unknown remote outcomes; crash during render not proven end-to-end.
- Cross-machine portability and release package not verified. No authorization to distribute cookies, profiles, API keys or saved Muse accounts.
- Keep `RELEASE_BLOCKED`. Do not add an approval file merely because Web Tool succeeded.

## Running services
- FlowKit gateway `http://127.0.0.1:18110`; Flow engine `http://127.0.0.1:18100`; Chrome 9233 on-demand and expected to close while idle. Storyboard Chrome 9550 left untouched.
