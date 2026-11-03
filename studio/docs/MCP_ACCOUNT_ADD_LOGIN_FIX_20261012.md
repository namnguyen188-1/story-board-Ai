# Storyboard AI Studio Pro — MCP account add/login repair
Date: 2026-10-12
Machine: DESKTOP-EE8BGVF
Scope: Studio MCP account user interface only; no V2 source/config edits

## Confirmed user-facing issue
The previous Add action created and selected a Studio profile but did NOT launch a Google sign-in window. New non-default accounts were also routed to the pinned V2 Google Flow project/tool URL, which could be inaccessible to another Google account. A profile is not itself a logged-in Google account.

## Corrective changes
- Added profile automatically opens its OWN Chrome Google Flow HOME window for manual sign-in; not somebody else's pinned V2 project.
- Existing default V2-compatible profile retains its original login route.
- Account creation is preserved even if Chrome launch fails; UI shows precise partial success and offers a manual retry.
- Account selection no longer falsely says ready to produce; it prompts verification.
- Clear "Add & open sign-in" button, actionable login/check/verify statuses, and guidance that a new account has no automatic permissions to the pinned Web Tool project.
- Updated HTML/JS cache version, desktop app restarted after confirming no live film-production workers.

## Verified
1. Before repair, real localhost HTTP POST /api/mcp/account created and selected one temporary test profile, persisted in Studio account registry; temporary test record cleaned.
2. Headless Chrome clicked old "Add" button: UI and backend returned account created and selected but no login action (the original bug).
3. After repair, headless Chrome clicked the new button with isolated temporary Studio account registry and mocked Chrome process launch. Exactly one Chrome launch was requested, with --app=https://flow.google.com/ and a fresh per-account profile/port. No reuse of V2 project URL.
4. HTTP 200 for UI and backend, no browser JavaScript exceptions. Backend POST returned 200; selected account was persisted; partial vs ready statuses correct.
5. Python compile and Node JS parse PASS.
6. Desktop process restarted successfully as PID 13880; HTML shows "Thêm & mở đăng nhập" and updated app.js version; /api/mcp/accounts returns one real default account.
7. No real Google login attempted. No real Google Flow project authorization or MCP image generation with a second account has been certified.
8. No stored cookies, passwords, auth tokens or V2 credentials copied. Test account registry records were cleaned.

## Known limitation
Current V2 MCP image backend and Node RPC have a trusted fixed project/tool URL. Signing in a different Google account DOES NOT automatically grant that account access to this project, create a project, or rotate among projects. New accounts need authorized access to the existing tool for current image generation, or a separately designed dynamic project binding extension. Do not claim full new-account MCP production is PASS until this is verified.

## Checkpoint
D:\STORYBOARD_AI\studio\checkpoints\mcp_account_login_fix_20261012_*

## Files
D:\STORYBOARD_AI\studio\studio_flow_accounts.py
D:\STORYBOARD_AI\studio\web_server.py
D:\STORYBOARD_AI\studio\web\index.html
D:\STORYBOARD_AI\studio\web\app.js
D:\STORYBOARD_AI\studio\diagnostics\test_account_new_ui_and_login.py
