# Storyboard MCP hidden Chrome lifetime — 2026-10-17
Device: DESKTOP-EE8BGVF. Project: D:\STORYBOARD_AI\studio.
Only projects.py and web_server.py production sources changed. V2 and secondary PC unchanged.

## Evidence and reproduction
- Initial owned Chrome absent and CDP 9550 offline.
- Restored exact existing signed-in project. Six real MCP health calls and a 30-second heartbeat observation kept Chrome PID 22028, hidden HWND, and original target unchanged.
- Actual production-tab adapter prepare/abandon test then failed: original target disappeared before releasing the untouched temporary tab. Chrome/CDP subsequently went offline.
- Deterministic regression reproduces ownership defect: CDP order [new job tab, original tool, unrelated blank] led cleanup_duplicate_tool_tabs to close the ORIGINAL and blank tabs. No live browser or media changes in this unit test.
- Verification endpoint also used this cleanup while claiming to be read-only. New regression catches this.
- Worker finalizer had a second unsafe path: if close_completed refused, raw /json/close bypassed its guard even for failed/uncertain jobs.

## Fix
- projects.cleanup_duplicate_tool_tabs preserves unowned tabs. Ordering and duplicate URL are not proof of ownership. Existing verification reports duplicate conflicts instead.
- Worker finalizer releases only the exact target if verified completed, or if abandon_fresh verifies an untouched placeholder. Otherwise preserves the tab and logs PRESERVED_UNCERTAIN. Removed raw forced-CDP close.
- A normal production uses its disposable exact target while keeping the original Web Tool alive. Unknown/user duplicate tabs are preserved, so a genuine unresolved duplicate conflict can require review rather than automatic destructive cleanup.

## Validation
- tests/test_flow_tab_ownership_20261017.py: 2 tests observed RED before fix, GREEN after.
- tests/test_flow_failed_worker_preserves_tab_20261017.py: uncertain release observed RED, both tests GREEN after.
- Existing tests/test_duplicate_flow_tabs_guard_no_paid_20261013.py and tests/test_private_mcp_isolation.py PASS.
- py_compile both touched source files PASS.
- verify_v2_baseline PASS: 38 V2-identical pinned files, 4 reviewed Studio adapters. No original V2 changes.
- Restarted verified IDLE backend only via existing EXE watchdog; main UI and Chrome retained. New backend PID 27788.
- Re-ran the SAME actual production-tab prepare/abandon test: PASS. Original target 5D03E587DD87CA3BC616F58BC2864048 and Chrome PID 27216 remained hidden/connected.
- Reports: diagnostics/flow_hidden_live_20261017.json and diagnostics/flow_session_no_render_20261017.json.

## Limits/current production
No billable image/video requests were initiated by these diagnostics. Full video E2E is not certified.
User independently started DRAMA episode 2, 30 minutes / 72 scenes, around 08:17. No further runtime edits/restarts while active.
No full test discovery: legacy directory includes live/paid scripts and fixture-dependent tests; only the targeted safe checks above were run.

## Checkpoint
checkpoints/FLOW_TAB_OWNERSHIP_BEFORE_20261017 contains original projects.py, web_server.py, production_tab.py.
