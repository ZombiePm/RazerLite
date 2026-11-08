# RazerLite

A small background controller for **Razer Basilisk V3** and **Razer Cynosa Lite** on Windows. Static lighting, hold-to-select colors, fixed DPI, and a Windows-key game mode — without keeping Synapse running.

[Русская инструкция](README.ru.md) · [Download](https://github.com/ZombiePm/RazerLite/releases) · [Changelog](CHANGELOG.md)

## Features

- **Tap** the lower button behind the mouse wheel to select the next color.
- **Hold** it to blend through colors; **release** to keep the selected shade on both devices.
- Keep Basilisk V3 at **26,000 DPI** by default. The scroll-mode button keeps its normal function.
- Block both Windows keys in configured games or fullscreen applications.
- Restore the selected color after restarting the service.
- Run as an automatic Windows service plus a small background helper at sign-in. No account, GUI, telemetry, or network listener in the RazerLite runtime.

## Supported hardware

| Device | USB ID | Support |
|---|---|---|
| Razer Basilisk V3 (wired, original 26K model) | `1532:0099` | Lighting, DPI enforcement, color button |
| Razer Cynosa Lite | `1532:023f` | Lighting |

These two devices were tested together on Windows. Other models, including Basilisk V3 Pro/35K, are **not supported by this release**. The vendored library contains more device definitions; RazerLite intentionally controls only the two IDs above.

## Install

Requirements: Windows 10/11 x64, **64-bit Python 3.10+ installed for all users**, and administrator access. Hardware testing used Python 3.14; CI also checks 3.10. Python must be accessible to the Windows service account; a per-user Microsoft Store installation is not suitable.

1. Download and extract `RazerLite-0.1.1-windows-source.zip` from [Releases](https://github.com/ZombiePm/RazerLite/releases).
2. Open PowerShell **as Administrator**, using your usual desktop account, and change to the extracted directory.
3. Check prerequisites, then install. Adjust the Python path to your installation:

```powershell
.\install.ps1 -PythonPath 'C:\Python314\python.exe' -CheckOnly
.\install.ps1 -PythonPath 'C:\Python314\python.exe'
```

If downloaded scripts are blocked, review them and use `Unblock-File .\*.ps1`. Python does not need any pip packages for this application.

The installer copies the application to `C:\Program Files\RazerLite`, creates the automatic `RazerLite` service and the `RazerLiteSession` sign-in task, and starts both. **It backs up and disables Razer/Chroma background services, matching scheduled tasks and current-user startup entries**, so they do not compete for the devices. It does not uninstall Razer software or drivers. Other Razer applications may need these services; use the restore script to return to Synapse.

This is a source release, not a self-contained executable. Do not reinstall over an existing installation: restore first so that the original backups remain available.

## Controls and settings

The lower top mouse button becomes the color selector. The button immediately behind the wheel still changes the scroll mode. A tap selects the next palette color; after a 350 ms hold, colors blend with a 1.4 second transition per palette segment. Release stops at the chosen shade.

Edit `C:\Program Files\RazerLite\config.json` as administrator; it is reloaded automatically:

| Setting | Meaning |
|---|---|
| `dpi` | Target mouse DPI, capped at the device maximum; default 26000 |
| `brightness` | Lighting brightness, 0–100 |
| `color_button` | Enable the color-selection helper; default true |
| `color` | Initial/fallback RGB; saved selection takes priority when the button is enabled |
| `mode` | `fullscreen`, `games` (explicit executable list), or `always` for Windows-key blocking |
| `games` | Executable names, e.g. `["game.exe"]`, including windowed games |
| `exclude` | Executable names exempt from automatic fullscreen blocking |

Browsers, common video players, Explorer, Remote Desktop and Windows Terminal are excluded by default. Fullscreen detection is a heuristic, not a game detector. Add explicit executable names for reliable windowed-game handling.

The helper reserves **F24** for the color button and consumes physical F24 events, including those from other keyboards. Without the helper, the remapped button produces F24. Changing `color_button` to false does not undo the hardware assignment; use the restore script to remove it.

Colors and original button assignments are kept under `C:\ProgramData\RazerLite`. The service handles lighting/DPI before sign-in; key filtering and color-button input require the interactive helper. Start Synapse only after restoring its settings to avoid competing controllers.

## Restore Synapse / uninstall the service

Connect the mouse and run from an elevated PowerShell window under the same account used for installation:

```powershell
& 'C:\Program Files\RazerLite\restore.ps1'
```

This restores saved button assignments and Razer startup settings, then removes the RazerLite service/task. Sign out and back in to reopen Razer's user interface. Application files, logs and backups are retained for inspection; they can be removed manually afterward.

## Focus changes and keyboard input

Windows-key blocking is software-only. Keyboard firmware game mode is not switched when entering, leaving or minimizing a game. A legacy hardware game lock is cleared once when the keyboard is discovered. Each Windows/F24 press keeps its original forwarding decision through repeats and release; ordinary game keys and modifiers always pass through, with no synthesized input.

## Performance and validation

Color input wakes a dedicated worker immediately; the service checks the selected RGB every 20 ms. Device discovery runs every 3 seconds and DPI/profile checks every second. Animation uses volatile device settings; the selected RGB is persisted locally. Temporary state-file write failures are retried without discarding the selection.

On the tested Windows machine, a synthetic callback-to-live-HID benchmark delivered 55 frames per device: **22.0 ms / 24.3 ms median**, **38.1 ms / 40.1 ms maximum** for mouse/keyboard. This measures software processing and device acknowledgements, **not physical switch-to-light latency**. The user confirmed the improved behavior. Approximately 50 MB combined working set was measured while idle; results vary by machine.

```powershell
python -m unittest test_color_cycle test_mouse_binding test_key_filter test_keyboard_mode
```

`test_session.py` runs Windows hook-policy tests without injecting desktop input. Run it in a separate session from the active helper. `benchmark_color.py` needs the service running and the helper task stopped; it temporarily changes lighting and restores the previous color. `verify.py` needs the service stopped to avoid concurrent HID requests.

Known limits: no physical reboot/hotplug validation yet; mouse-wide brightness readback is unavailable on the tested firmware, though lighting writes succeed. Hardware support and the measurements above are limited to the listed models. No game anti-cheat compatibility claim is made.

Logs: `C:\ProgramData\RazerLite\hardware.log` and `session\session.log`. For a bug report, include device model/USB ID, Windows/Python versions, and a small sanitized error excerpt. Do not upload your entire ProgramData backup directory.

## License

GPL-3.0-or-later. Upstream code and protocol attributions are in [THIRD_PARTY.md](THIRD_PARTY.md); original notices are preserved. Independent community software, not affiliated with Razer.
