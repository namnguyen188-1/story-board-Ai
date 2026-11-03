# Storyboard AI Pro — Responsive UI Dock v2.6 (2026-10-13)

Root: D:\STORYBOARD_AI\studio; device DESKTOP-EE8BGVF.

Original issue: CSS forced three desktop columns minimum 1150px (340+420+390); viewport 1024px/800px clipped the right monitor behind overflow:hidden. Scene cards were min 170px and very small text in a crowded deck of 62 scenes.

Changes: only web/style.css, web/index.html and web/app.js for responsive 3 docks on >=1200px, monitor drawer on 801..1199px, tabbed setup/scenes/monitor on <=800px. Increased scene min width to ~268px, label, input and preview size. CSS and visibility-only JS; existing pipeline, MCP, credentials, provider, credit and production APIs unchanged. Ctrl+R to see the new version.

Checks: real headless Edge with 62 temporary cards at viewport widths 1920,1440,1280,1024,800,540: no horizontal clipping, drawer controls operate, input values retained; PASS. Image credit UI guard PASS. Multi Flow project settings UI PASS. Saved Stoic 62-scene episode resume PASS. Fixed an outdated QA test selecting a unique incomplete episode when more than one exists; did not alter gallery production code.

Backup: checkpoints/ui_docks_layout_before_20261013. Verified checkpoint: checkpoints/ui_docks_layout_verified_20261013. No paid API calls and no render in UI QA.
