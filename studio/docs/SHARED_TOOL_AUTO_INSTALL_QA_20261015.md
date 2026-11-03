# Storyboard AI — Verified Shared Web Tool Auto-Install, 15/10/2026

Scope: D:\STORYBOARD_AI\studio, DESKTOP-EE8BGVF. No changes to D:\YOUTUBE_SEO_PRO_V2 or D:\FLOW_MCP_SERVER. No Git. No paid media requests.

## Confirmed user-supplied link
https://flow.google.com/shared/tool/69da86fb-6c79-43d2-a387-ef47b0fda4db
This link was supplied by the user and tested against real Google Flow UIs with separate Studio-owned Chrome profiles, not derived by guessing a project-specific Tool URL.

- Profile default (CDP 9550): official shared page -> "Dùng thử trong một dự án" -> choose known QA project "Tháng 10 13 - 17:44" -> "Mở" -> exact route /project/1f806e0b-5184-448b-8ab4-eab64ee163f0/tool/69da...; verified __STORYBOARD_MCP__ queue, addToQueue, startImageProduction, and dynamic flow-sdk image entrypoint: PASS.
- Profile second (CDP 9460): distinct signed-in Google account/Flow project list (privacy-preserving match, emails not saved). A single isolated QA project "Tháng 10 15 - 10:42" was created (Project ID 0a0fa44c-faab-435e-95c5-0265c89866c2). Official shared page -> project picker -> "Mở" -> exact route /project/0a0.../tool/69da...; read-only bridge, queue and SDK: PASS.
- Zero image generation, zero video generation, zero paid Flow credit in all tests.
- Initial 9 submit_uncertain receipts in the original Studio runtime retained; NEVER resubmitted.
- Account two successfully enrolled through the new real Python -> Node -> Chrome -> Flow -> MCP -> register() path, exit code 0. Its registry now includes one verified QA project; Studio's selected main/default account remains unchanged. Subsequent standalone ensure_ready("auto",account=second) returned AUTO_FLOW_READY, ready=true.
- Browser CDP 9550 and 9460 both confirmed listening after regression suite. During development an early test disconnected both Chrome sessions, which were separately and safely restored via existing open_login() per-profile flow. Production was IDLE.

## Changes implemented in Storyboard AI source
1. studio_mcp/flow_tool.json: corrected bundled shared link and Tool ID from unverified 8fbef6e9... to user-provided, proven 69da86fb....
2. New studio_mcp/node/auto-flow-shared-install.mjs: strict account-local CDP validation; real Google Flow UI Share -> Project -> Open; waits for asynchronously loaded project title; rejects ambiguous project names and duplicate Tool tabs; read-only native bridge SDK proof; retains verified Tool tab for Python registry. For first-time account without a project, creates at most ONE dedicated project using a write-before-click durable receipt, resumes only if known project ID, and refuses retry if remote create state is uncertain.
3. New studio_mcp/shared_tool_install.py: validates Chrome ownership, local-only CDP, no production busy, pinned V2 baseline and exact shared Tool identity, then executes Node helper and verifies result.
4. studio_mcp/auto_flow_manager.py: when there are no registered projects and login/browser is available, invoke shared install, register only after native bridge PASS. No hidden retry of old image receipts. status() checks local Chrome CDP before reporting cached READY to prevent false ready after browser exits.
5. studio_mcp/RELEASE_CONTENTS.json includes new Python/Node helper and changes stale share-link warning.
6. test_flow_onboarding_automatic_no_chrome.py first-run fixture now mocks a clean account with no registered URL. This avoids accidentally using the working default account's existing project.
7. New test_shared_tool_autoinstall_no_paid_20261015.py: cold-start routing, mismatch fail-closed, durable uncertain receipt, stale-ready fail-closed, exact configured share.

## Real test findings / targeted fixes
- First experimental Python->Node worker had a CDP websocket kept open, so Python timed out waiting for worker exit despite successful native bridge. Fixed short-lived worker exit without requesting Chrome to close.
- Project page initially displayed generic app title "AI Creative Studio" rather than its async project title; caused picker lookup timeout. Now poll until genuine project title resolves.
- One instrumentation trace call was scoped incorrectly in finally, causing nonzero exit after recording verified receipt. Removed.
- Retested actual second Chrome QA project; native bridge verified and register succeeded (exit=0); no second project created.

## No-paid regressions
- test_shared_tool_autoinstall_no_paid_20261015.py: PASS.
- test_flow_auto_attach_no_paid.py: PASS.
- test_flow_onboarding_automatic_no_chrome.py: PASS.
- test_auto_flow_manager_no_paid_20261013.py: PASS.
- test_auto_flow_project_provision_no_paid_20261013.py: PASS.
- Python py_compile new modules: PASS.
- node --check auto-flow-shared-install.mjs: PASS.
- studio_mcp.v2_baseline checksum: PASS, 38 upstream files identical, 4 pinned Studio adapter hashes unchanged.

## Boundaries, not yet claimed
- Existing Storyboard AI desktop process has not been forcibly restarted to avoid losing unsaved user input. Source changes are fully installed on disk; desktop server boot reload required for new auto-install branch to become live.
- Actual zero-project cold-start with automatic CREATE+SHARE+REGISTER in *one continuous call* is modeled with no-paid tests and its steps are separately real-tested, but not full live E2E on a fresh third account. Do not claim full first-run production/commercial GREEN.
- Switching to an arbitrary newly chosen Google Flow project *while old known projects remain* still needs dedicated Project Resolver/Tool Locator integration. Cross-machine migration with a different Windows profile is not implemented or tested; do not copy Chrome cookies/credentials.
- No paid one-image E2E in this integration run; only read-only native capability proof.
- Shared Tool is currently public at the user's explicit request for experimentation; before distributing to customers, review Tool source/media visibility and access-control policy.

## Checkpoints
Before: D:\STORYBOARD_AI\studio\checkpoints\shared_tool_autoinstall_before_20261015
After: D:\STORYBOARD_AI\studio\checkpoints\shared_tool_autoinstall_source_verified_20261015
References: docs/POC_SHARED_TOOL_NEW_ACCOUNT_20261015.md and docs/MASTER_PLAN_FLOW_AUTORECONNECT_MULTIMACHINE_20261015.md.
