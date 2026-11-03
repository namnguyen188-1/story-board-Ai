# Storyboard AI — Single Google Flow login / no duplicate browser windows
Date: 2026-10-15. PC: DESKTOP-EE8BGVF. Worktree D:\STORYBOARD_AI\studio.
No V2 changes, no Git, no image/video generation.

## Issue reproduced
Robot panel showed "Mở trực tiếp trên trình duyệt này (Tab mới)", "Mở cửa sổ phụ", "Thu nhỏ Taskbar" and "Tự động dò", while Settings had separate direct-tab and login/window toggles.
- robotOpenDirectTab used window.open(url, "_blank") in the Edge-based Studio app window, causing an unrelated Edge tab.
- Studio open_login() opened --new-window on repeated login clicks when the expected Tool tab was absent.
- Studio open_project() opened --new-window even for an already running account Chrome, duplicating windows.
- Frontend previously had stale "Đã kết nối" text unrelated to current Chrome health; earlier Google-auth fixes already corrected source, but browser must reload to see latest JS.

## Changes
1. web/index.html: Robot has ONE user action "Đăng nhập / Hiện Google Flow"; remove direct Edge tab / auxiliary window / manual minimize / extra reconnect buttons from robot. Settings retains ONE login button and technical Check/Reconnect. No cookie or password access.
2. web/app.js: robotLoginOnly delegates to mcpAccountAction("login"), also backwards-compatible aliases from stale tab/restore handlers to same dedicated Chrome flow, no window.open call. Shared per-login busy guard prevents concurrent UI requests. Error status no longer reports successful opening if backend failed.
3. studio_flow_accounts.py: repeated login click only raises/reuses the existing Studio-owned Chrome window, never creates a fresh --new-window when a saved Tool tab is absent. If Chrome process exists but CDP unusable, fail closed instead of launching duplicates. Opening a registered project in existing Chrome uses --new-tab.
4. Tests adapted to enforce new single-login contract; rollback checkpoint created first.

## Evidence
- Real direct open_login called twice consecutively: first opened own Chrome PID 10692; second returned reused=True, same PID 10692 and same owned HWND count (7 before and 7 after), CDP connected.
- After 14 seconds: OWNED_CHROME_ALIVE True, CDP_READY True, WINDOW_MINIMIZED True, AUTH_STATE AUTHENTICATED, MCP AUTO_FLOW_READY True.
- Live Studio HTTP / returned exactly one robotBtnGoogleLogin; no three old robot buttons; /app.js has no Edge window.open direct-tab call; Studio production IDLE.
- test_single_google_login_ui_no_paid_20261015.py PASS (3-click mocked UI idempotence, single robot login, reuse tabs).
- test_flow_onboarding_automatic_no_chrome.py PASS; test_project_open_actual_visibility_contract_20261013.py PASS; test_robot_assistant_and_smart_login.py PASS; test_google_login_auth_autohide_no_paid_20261015.py PASS; test_shared_tool_autoinstall_no_paid_20261015.py PASS.
- JS/Python compile PASS, V2 baseline 38 original hashes + 4 reviewed adapters verified.

## Limitations
- Existing open Edge app retains old in-memory HTML and JS until page refresh or app restart. To avoid losing potentially unsaved prompt text, did not force-reload the user's active UI. Save draft before refreshing. Source files are live served from Studio port 8765.
- A true 24h stress test or cross-machine EXE distribution not done.
- Screenshot's "Default IME" belongs to Windows input method user interface, not a Google Flow browser tab; this change does not alter system keyboard settings.
- Only the Studio-owned Chrome profile is managed. Unrelated personal Chrome/Edge tabs were not closed.
