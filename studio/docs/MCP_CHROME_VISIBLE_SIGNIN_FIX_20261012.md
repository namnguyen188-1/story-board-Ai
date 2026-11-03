# Storyboard Studio Pro – invisible Chrome sign-in repair
Date 2026-10-12, DESKTOP-EE8BGVF.

## Observed user blocker
Studio current active account id account_1e27b5002a50 (display name "1") created its isolated Chrome profile on CDP port 9460, but the browser process PID 15668 had NO visible top-level window. CDP health showed Chrome connected and Google Flow page loaded. Studio had incorrectly treated successful Popen / CDP connection as evidence the sign-in window was visible.

## Direct recovery
- Verified isolated browser contained only Google Flow and internal Chrome tabs. Did not inspect or copy credentials/cookies.
- Gracefully closed ONLY the windowless browser for the selected new account using CDP Browser.close; preserved user-data-dir, cookie/session profile and all V2 files.
- Relaunched same account, same CDP port 9460 using ordinary Chrome --new-window https://flow.google.com/ instead of --app=, no CREATE_NO_WINDOW flag.
- WIN32 EnumWindows confirmed a VISIBLE top-level Chrome window (new main PID 17468); PASS.
- Actual live Studio profile check: connected=true, window_visible=true.
- Current active selected account remains unchanged. No Google authentication was attempted.

## Permanent Studio fixes
- Studio's studio_flow_accounts.py now launches NORMAL Chrome window, waits for actual visible UI and only returns opened=true if visible.
- Existing account reuse restores/focuses its visible window (best effort).
- Legacy invisible, non-default Chrome can be recovered ONLY if its tabs consist of Google Flow and browser internals; no unrelated user tabs or shared default V2 Chrome are restarted.
- Studio's browser-check response now includes window_visible, and UI warns when CDP is connected but Chrome is hidden.
- Cache-bumped frontend script to app.js?v=20261012_visible_login_v4.
- Studio Desktop backend restarted after verifying no live production jobs.
- LIVE localhost /api/mcp/account POST action=check: connected=true, window_visible=true, status OK.
- LIVE localhost /api/mcp/account POST action=login: ok=true, opened=true, window_visible=true, reused=true.
- Fresh UI HTTP 200 and new JavaScript HTTP 200.
- Original V2 code/config, and other Chrome profiles were untouched.

## Boundaries
- Visible browser != Google signed in. User must manually authenticate in Chrome.
- MCP image-production project access for this new Google account still needs separate verification; no free credits or inherited permissions promised.
- Chrome may be behind other apps, such as the user's foreground Antigravity process. Use Alt+Tab or Windows taskbar.
- Checkpoints under D:\STORYBOARD_AI\studio\checkpoints\chrome_visible_login_* and chrome_window_status_*.
