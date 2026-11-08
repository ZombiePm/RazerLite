# Changelog

## 0.1.1 — 2026-11-09

- Stop synchronizing keyboard firmware game mode with foreground-window changes. Windows-key blocking stays in the software helper; the old hardware lock is cleared only once when a keyboard is discovered.
- Keep each filtered key press and its release paired across Alt+Tab, fullscreen changes, stale detection and color-button setting changes. Ordinary keys always pass through; injected events do not alter physical press tracking.
- Remove the shared game-state file and its write-error path, which could spuriously clear the helper's game state.
- Add regression tests for focus transitions and stable keyboard firmware state.

## 0.1.0 — 2026-11-04

First public release for the Razer Basilisk V3 and Cynosa Lite.

- Automatic Windows service for static lighting and fixed maximum DPI.
- Lower mouse button: tap for the next color; hold to blend colors; release to keep the selected shade.
- Windows-key blocking in configured games or fullscreen applications.
- Saved colors, per-profile button backups, and an uninstall/restore script.
- Responsive color worker and 20 ms service polling, with retries for temporary state-file write failures.
- Python source distribution, vendored HID protocol, Windows/Linux unit checks.
