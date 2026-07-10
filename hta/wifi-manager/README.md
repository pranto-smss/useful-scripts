# WiFi Manager (HTA)

A GUI WiFi manager for Windows. View, connect, disconnect, and forget saved WiFi networks with a clean interface.

## Features

- **Network List** — Browse all saved WiFi profiles in one place
- **Show Password** — Reveal the stored password for any network
- **Copy to Clipboard** — One-click password copy
- **Connect / Disconnect** — Toggle WiFi connection from the GUI
- **Forget Network** — Remove old networks with confirmation prompt

## Requirements

- Windows 7 or later
- Built-in `netsh` (comes with Windows)
- No admin rights needed for viewing passwords; admin required for connect/disconnect/forget

## Usage

1. Double-click `wifi-manager.hta` to open
2. Networks load automatically on launch
3. Click a network to select it
4. Use the toolbar buttons to manage it

```
wifi-manager.hta
```

## Screenshot

Dark-themed GUI with:
- Toolbar buttons at top (Refresh, Show Password, Copy, Connect, Disconnect, Forget)
- Scrollable network list in the center
- Password display panel at the bottom
- Status bar with feedback messages

## Notes

- Passwords are shown only on explicit click (preview-before-act)
- No data is stored or transmitted — everything runs locally via `netsh`
- Safe for personal use; do not use on networks you do not own
