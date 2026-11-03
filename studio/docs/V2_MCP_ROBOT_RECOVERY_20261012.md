# V2 MCP and robot recovery — 2026-10-12
Machine: DESKTOP-EE8BGVF

## Problem confirmed
- At first V2 process PID 11400 existed but its main window was minimized; floating robot PID 17764 remained running with visible top-level window.
- Default V2 Google Flow MCP CDP port 9333 was offline; alternate V2 port 9340 also offline.
- V2 account registry and isolated Chrome profile were intact, unchanged since 2026-10-11.
- Existing shared bridge at D:\FLOW_MCP_SERVER\scripts\v2-native-ui.mjs had a health action rule which explicitly called Browser.close even when a LIVE desktop still required that browser.
- Reproduced: Chrome process/CDP disappeared around 3 seconds into a read-only image MCP health call, while the health method ultimately reported MCP_APP_CAPABILITIES_PASS.
- During later testing, V2 desktop itself was closed (desktop_owner.json closed=true), which correctly triggered the old after-exit cleanup and made one transient health result misleading. Reopened V2 using its native desktop_bootstrap.py. New V2 owner PID 31576, live.

## Targeted fix
- Patched only D:\FLOW_MCP_SERVER\scripts\v2-native-ui.mjs and its Node regression test.
- New health policy: when desktop_owner.json references a live V2 desktop PID with closed=false, do NOT close Chrome as a side effect of a read-only health check.
- When V2 has closed, retain previous cleanup for empty and unstarted queues.
- Preserve existing close-after-render rules and shared browser safety.
- No changes to D:\YOUTUBE_SEO_PRO_V2 source, original profiles, credentials, browser cookies, or existing V2 video projects.
- Checkpoint: D:\FLOW_MCP_SERVER\backups\mcp_health_keep_connected_20261012_182505

## Verified
- Node --check PASS and 12/12 Node tests PASS, including live owner health preservation, closed owner cleanup, finished render cleanup, concurrent task protection.
- Opened default V2 Chrome 9333 using V2 storyboard_accounts.open_account_login.
- Real MCP health result: ok=true, reason=MCP_APP_CAPABILITIES_PASS, read-only; no image/video generation.
- Real Chrome CDP 9333 remained available at 3s, 6s, 9s, 12s, 15s after the health call.
- Restored V2 main window; Windows reports visible=true, minimized=false.
- Restored V2 floating robot window PID 17764; Windows reports visible=true and topmost.
- Current V2 desktop owner PID 31576, closed=false.
- No third-party Studio account changes in this repair.

## Remaining consideration
- Automatic MCP browser startup on every future V2 launch was NOT changed in this targeted repair. The current live V2 MCP is verified connected. Chrome may still be launched on demand on future launches.
- User should confirm the robot is visible and manually open Web Tool via robot if desired.
