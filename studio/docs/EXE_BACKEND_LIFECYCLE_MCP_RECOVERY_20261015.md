# Storyboard AI — Native EXE / HTTP backend supervisor recovery (2026-10-15)

PC DESKTOP-EE8BGVF. Production root D:\STORYBOARD_AI. No changes to D:\YOUTUBE_SEO_PRO_V2 or D:\FLOW_MCP_SERVER. No Git; no Flow media requests/credits.

## Root cause reproduced
- Old EXE PID 7796 and one Edge app process remained running, but no Python Studio backend was present. localhost 127.0.0.1:8765 refused connections; Chrome CDP 9550 and 9460 also offline.
- Old native launcher mutex branch called Process.Start(url) on a second launch, opening default browser rather than returning to app window.
- desktop_app.py incorrectly used the transient Edge launch subprocess poll() as an indication that Studio had been closed. Chrome/Edge can hand an app-mode request to existing Edge process, and the spawned subprocess may exit while the UI persists. It then shut down the Python web server, orphaning the EXE and Edge UI.

## Changes implemented
- desktop_app.py: no longer shuts backend down based on Edge child PID. In EXE mode (STORYBOARD_NATIVE_WINDOW_OWNER=1) Python starts backend only, C# owns one native-style app-mode window after HTTP health. No default-web-browser fallback.
- launcher_src/Storyboard_AI_Studio.cs: second launch signals running EXE via named EventWaitHandle; no Process.Start(url), no redundant dialog/browser. The EXE probes /api/status periodically; if its own Python child exited, it safely relaunches with bounded retry (max 4 failures/10 minutes) without killing Chrome or opening more UI windows.
- Compiled and deployed root Storyboard_AI_Studio.exe via .NET Framework csc /target:winexe. Original EXE and sources checkpointed. Existing Edge window retained to protect unsaved text.

## Real E2E QA
1. EXE deployed SHA256 verified. One main EXE PID 38176, backend pythonw PID 13736 initially, HTTP 200 IDLE.
2. Launched same EXE a second time: transient second instance exited; one running EXE, same backend PID, Edge --app process count unchanged at 1.
3. While production IDLE, simulated own-backend crash by stopping only verified pythonw PID 13736. EXE watchdog revived HTTP backend as PID 17204 within about 10 seconds. Edge --app count remained 1.
4. After recovery: Chrome CDP 9550 connected; fresh Google Flow auth AUTHENTICATED; Chrome minimized without being closed; Auto Flow AUTO_FLOW_READY true; Studio HTTP 200 IDLE. Nine submit_uncertain receipts kept and not resubmitted.
5. Python compile and C# build passed.

## Limits
No 24-hour soak, new-machine deployment audit or billable end-to-end video test today. Chrome minimization applies only to the isolated Google Flow Chrome, not to the main Studio Edge app. Distinct local CDP ports remain required to isolate signed-in Google accounts; user does not need to select or manage them.

## Checkpoints
- Before: D:\STORYBOARD_AI\studio\checkpoints\launcher_backend_lifecycle_before_20261015
- After: D:\STORYBOARD_AI\studio\checkpoints\launcher_backend_lifecycle_verified_20261015
