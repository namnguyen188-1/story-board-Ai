# Storyboard AI: grounded YouTube SEO — 2026-10-22
Goal: Produce episode-specific publication metadata and one thumbnail, with verifiable internal checks and no invented vidIQ/CTR/market results.
Authorization: User approved the six-part in-chat design and requested research and implementation.
Constraints: Do not edit V2. No Git; timestamped checkpoints and docs/SDD_LEDGER.md. Preserve production, account, voice, and provider settings. No automatic YouTube publication.
Research: YouTube Help 12340300 (accurate concise titles; branding at end), 12948449 (unique descriptions; 1-2 topic keywords), 146402 (tags secondary), 9884579 (chapters >=3, begin 00:00, >=10 seconds). vidIQ Help 9696241 distinguishes actionable metadata from observed performance.

Task 1 — Evidence and validation:
- Add seo_quality.py: read all episode scenes/dialogue and drama plan; normalize language without rejecting Spanish accents; derive content fingerprint; validate grounded keywords and claims; read actual durations.
- Tests: late-scene evidence, Spanish accents, no invented mailbox/camera/true-story details, missing/corrupt inputs, chapters skip unknown durations.
Task 2 — Package generation and truthful checks:
- Replace metadata generation/scoring in seo_packager.py, retaining the existing image renderer.
- Three title alternatives, one main image, five topical hashtags, bounded relevant tags; optional shorts derive from episode rather than stock HOA story.
- Cache keyed by engine version and content evidence. API failure yields explicit extractive fallback; no generic fabricated plot.
- Internal metadata/technical image checklists labeled internal; official vidIQ and analytics stay unknown without provenance.
Task 3 — UI and server integration:
- Update SEO rendering/copy labels in web/app.js and web/index.html; no default 100/CTR/market multipliers.
- Cached GET returns versioned content or regenerates; TXT/JSON/organized publishing copies stay in sync. Preserve compatibility keys.
- Update pipeline log to describe internal checks.
Task 4 — Verification and deployment:
- RED/GREEN unit tests, mocked-provider generation across English HOA, Spanish stoicism and another genre; cache/provider-failure cases.
- Check syntax and frontend rendering including score zero/null; test actual images; run a real episode regeneration when backend is idle.
- Stage on main machine, compare source hashes before apply, save checkpoints, run safe regression, review, then reload/restart only idle backend and verify HTTP/UI.
