Storyboard MCP - V2 private clone (2026-10-13)

Source: D:\FLOW_MCP_SERVER\dist, copied read-only into D:\STORYBOARD_AI\studio\studio_mcp\node\dist.
Four V2 original modules cloned: flow/storyboard-native.js, flow/storyboard-native-image.js, browser/session.js, browser/tool-tab.js. Minimal Studio-only adaptations: dynamic per-account URL, Studio output folder, Studio approval/budget env, optional Flow APP mode query. V2 source and session not changed.
New shared tool: https://flow.google.com/shared/tool/8fbef6e9-a6e4-4b21-a8b0-0be7a559273d
Own Studio project: https://flow.google.com/project/a48a51c1-a8a7-4b54-81a2-8789f7bc4c1f/tool/8fbef6e9-a6e4-4b21-a8b0-0be7a559273d
Chrome 154 Playwright compatibility patched only in Studio local node_modules. Node CDP PASS. Python account isolation PASS. Node budget guards PASS. Portable Node PASS. Four-scene mock pipeline PASS.
Real Web Tool health: UI_NOT_FOUND: Actual Storyboard Director production bridge unavailable. The new Tool UI appears to be a different custom clone tool and lacks window.__STORYBOARD_MCP__ required by V2. Switching from editor to project preview did not produce bridge; returned browser to correct tool tab. No image paid calls in this validation. Real E2E NOT VERIFIED. Need correct compatible Web Tool app or a different adapter.
Before-change backup: checkpoints/v2_mcp_clone_before_20261013. Final checkpoint: checkpoints/v2_mcp_cloned_private_20261013.
