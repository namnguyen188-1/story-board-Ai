# Storyboard AI One-Click Update Host

Date: 2026-10-18
Current feed: 1.2.7 (transfer-test build)

## How it works
- The primary PC serves latest.json and the installer over Tailscale only, bound to 100.88.57.89:8765.
- The Korea PC updater is installed under %LOCALAPPDATA%\StoryboardAI\Updater.
- Start Menu shortcut: Storyboard AI > Cap nhat Storyboard AI.
- Download uses 16 concurrent HTTP Range requests, retains completed 2 MiB chunks, and resumes them when relaunched.
- Before installation it checks manifest host/port, total byte length, and SHA-256.
- Inno Setup installs to the existing AutoSetup-Test folder; the updater stops only processes whose executable path is inside that install folder, then launches Storyboard AI again.
- It does not delete the Productions folder.

## Host start
- Running host process PID was started by Desktop Commander on the primary PC.
- A user Startup shortcut starts the host at next sign-in using D:\pythonw.exe.
- The primary PC must be awake, signed in, and connected to Tailscale during updates.
- This is a private two-machine feed, not a public CDN. storyboardai.store did not resolve on the primary PC when checked.

## Validation
- Korea PC manifest check: PASS (installed 1.2.1, update 1.2.7, 284562570 bytes).
- Range download probe: 8 MiB, 16 concurrent requests, HTTP 206, completed successfully.
- Installer SHA-256 from primary package metadata: FD9D380FF334F5BE586469945AA8F8FAD67C4D104A22A5F37C95407401C72177.
- 2026-10-18: full transfer through the updater completed; installer SHA-256 matched; Windows uninstall registry reports version 1.2.7.
- Post-install API health endpoint returned HTTP 200 and status IDLE; 79 existing production files remained in place.
- Korea Start Menu updater check passed after install: installed 1.2.7, feed 1.2.7.
