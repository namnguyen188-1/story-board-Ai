# Storyboard AI — Google Login, Console Flicker, Chrome Auto-Hide (15/10/2026)
PC DESKTOP-EE8BGVF. Scope D:\STORYBOARD_AI\studio. No changes to V2, no Git or paid media.

## Reproduced
- Chrome CDP remained connected after Google signout. New fresh Google Flow check returned LOGIN_REQUIRED: connected browser does not prove authentication.
- Studio account PID discovery launched powershell.exe without CREATE_NO_WINDOW, causing visible flashes on frequent status polling.
- Browser was lost after a background cycle. Studio-owned CDP helpers were calling browser.close() on a borrowed Chrome connection, a possible contributor. Replaced helper cleanup with worker-only exit.

## Changes
- studio_mcp/accounts.py: Powershell CREATE_NO_WINDOW; fresh authenticated Flow home check via separate read-only Node worker; 12s auth cache; account-scoped manual-login marker; fail closed when auth is missing.
- studio_mcp/node/read-only-google-flow-auth.mjs: background CDP target; no reading cookies/tokens/credentials, no image requests; no Chrome close.
- studio_mcp/auto_flow_manager.py: READY revoked after logout; ensure_ready gated on real authentication; auto-finish login and minimize Chrome only after Google + exact MCP native bridge success, including login performed directly in Chrome.
- studio_flow_accounts.py, web_server.py and web/app.js, web/index.html: separate Chrome connected versus Google verified versus MCP ready; remove static false-connected messages.
- Node helpers verify-v2-compatible-tool, production-job-tab, auto-flow-provision-project no longer close borrowed Chrome.
- RELEASE_CONTENTS includes the new auth probe for later EXE packaging.

## Real evidence
- Signed-out browser: CDP connected=true, Google auth LOGIN_REQUIRED: PASS.
- After Google login: fresh auth AUTHENTICATED, exact native MCP tool checked, AUTO_FLOW_READY: PASS.
- Win32 minimize live: minimized=true while Chrome CDP still reachable: PASS.
- Waited after login in dedicated Studio Chrome: Chrome remains running, minimized, MCP READY, login request marker cleared: PASS.
- Seven no-paid safety assertions including no hide before login or MCP, no stale READY, and direct Chrome relogin auto-hide mocks: PASS.
- Routing/provisioning/shared-tool no-paid regressions: PASS. Node and Python compile PASS. V2 pinned hashes 38 original core plus 4 adapters PASS.
- Nine existing submit_uncertain jobs not resubmitted; production remained IDLE.

## Remaining limits
- Not a 24-hour Chrome soak test, not a paid video E2E, and not a clean-machine deployment audit.
- No direct measurement of visual console flashing, but confirmed the subprocess creation flag is installed.
- Any pending unsaved draft on the desktop app may be affected by the guarded app restart; the user should save before future restarts.
- Google sign-in and account verification remain user-controlled.

Checkpoints: studio/checkpoints/google_auth_window_flicker_before_20261015 and google_auth_window_flicker_verified_20261015.
