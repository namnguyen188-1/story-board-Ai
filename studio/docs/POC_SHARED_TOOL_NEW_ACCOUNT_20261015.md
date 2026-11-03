# POC — Web Tool shared link into new Google Flow account, 2026-10-15

## Scope
Isolated real Chromium/Playwright inspection on DESKTOP-EE8BGVF, Storyboard AI only. No changes to production app modules, registry, user projects, queue, cookies or V2. No media generation or credits. All disposable Playwright tabs were closed. Second account's dedicated login Chrome window intentionally remains open for user sign-in.

## Live observations
1. Second account: id account_1e27b5002a50, CDP 9460, saved project count=0. Chrome dedicated profile was initially stopped. Invoked existing studio_flow_accounts.open_login, opened visible Chrome successfully, browser CDP connected, but needs_signin=true; still visiting bundled /shared/tool link, no /project/.../tool/... tab. Cannot proceed without the legitimate Google sign-in by the user.
2. Configured bundled shared URL points to https://flow.google.com/shared/tool/8fbef6e9-a6e4-4b21-a8b0-0be7a559273d. With original authenticated account in a temporary browser tab, page loads HTTP 200, displays 'Công cụ được chia sẻ: Storyboard Director AI', and a button 'Dùng thử trong một dự án'.
3. Clicked 'Dùng thử trong một dự án' in disposable tab, saw project chooser dialog and buttons 'Huỷ'/'Mở'. Did NOT select/modify a project, did not click 'Mở', no media/credit usage.
4. Directly opening the older saved tool URL with project a48a51c1-a8a7-4b54-81a2-8789f7bc4c1f + tool 8fbef6e9... in disposable tab DID NOT expose the expected __STORYBOARD_MCP__ and flow-sdk image bridge during the bounded probe. This is **not** proof shared-tool -> selected-project installation would fail; that complete path remains untested.
5. Another manually inferred /shared/tool/642784b8... URL returned page HTML with semantic 'not found'. Tool IDs in project URLs MUST NOT be assumed to be valid *shared links*. This was a test candidate only, not a verified source sharing URL.
6. The ACTUAL currently selected and already registered project/tool ...:642784b8-d39f-4e7b-b168-fe6218bbc45b passed existing read-only probe_v2_compatible_tool (True) from Chrome CDP 9550. Thus the known production bridge is healthy while bundled link identity is unverified.
7. No paid/image calls. All original tabs/user queues untouched; no integration/registry changes.

## Verdict
POC PARTIAL — SHARED LINK LANDING & PROJECT DIALOG CONFIRMED; NEW ACCOUNT INSTALL + V2 BRIDGE END-TO-END NOT VERIFIED; DO NOT INTEGRATE.

## Required next step
Operator completes Google login in the Studio Chrome window for second account. After login, use a verified, explicitly shared link from the *currently working* V2-compatible tool (not one guessed from its project URL). In a disposable project or explicitly permitted project, repeat: shared link -> choose project -> open Tool -> read-only V2 native bridge health; only then consider integrating the auto-attach path. Protect all existing 9 submit_uncertain receipts from auto-retry.

Official Flow instructions: https://support.google.com/flow/answer/17104535

## Addendum — Full three-click Flow share POC (after user corrected sequence)
- Ran a REAL Google Flow browser UI test on logged-in default account and dedicated known QA project, id 1f806e0b-5184-448b-8ab4-eab64ee163f0, UI name "Tháng 10 13 - 17:44".
- From shared page 8fbef6e9... clicked "Dùng thử trong một dự án", selected the exact QA project option, verified aria-selected=true, clicked "Mở". PASS: Google Flow navigated to /project/1f806.../tool/8fbef6e9... . No image generation.
- Repeated 28-second read-only native bridge probe against the newly opened Tool: __STORYBOARD_MCP__, queue, startImageProduction, addToQueue and image SDK did NOT satisfy expected MCP readiness. Thus Google Flow install/open operation PASSES, MCP READY on shared version FAILS.
- Reference: 642784b8... in already active production project was confirmed read-only native bridge PASS before this test; original Studio /api/mcp/auto/status remained READY; tests did not change active account or production mapping.
- Inspected the active 642784... Tool share dialog by clicking "Chia sẻ" on a throwaway tab. Found "Sao chép đường liên kết" and warning: anyone with link can view/copy/share the Tool and referenced media. DID NOT click the link-copy/share action or publish the working Tool; explicit user approval required.
- Second-account CDP profile still needs manual Google login. No account secrets/cookies accessed; no V2 edits, no paid calls, no integration. Share test may have associated 8fbef6e9... with the dedicated QA project on Google Flow (non-production).

## Addendum — explicit user authorization to share working Tool (15/10)
- User approved sharing the verified Web Tool freely during testing; commercial distribution privacy restrictions to be considered later.
- Opened share dialog on known healthy live Tool project b5a2.../tool/642784..., clicked "Sao chép đường liên kết" in dedicated disposable Chrome tab. Share UI accepted click. Separate Windows clipboard read did NOT yield a verified flow.google.com/shared/tool URL, so no trusted new share URL is available for follow-up tests.
- Re-checked manually derived /shared/tool/642784... route after the click: Google Flow still reports not found. Important: a project Tool ID is not necessarily its public share ID.
- Account2 remains on bundled shared Tool link, no registered projects. Complete authenticated account2 real share -> project -> bridge verification still pending.
- POC scripts archived to studio/scratch/poc_working_tool_share_20261015/; main modules untouched. No paid image calls. Never mark bridge PASS based solely on Google Flow URL loading.
