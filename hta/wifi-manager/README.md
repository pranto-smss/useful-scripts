# WiFi Manager (HTA)

A GUI WiFi manager for Windows. View, connect, disconnect, and forget saved WiFi networks with a clean interface.

## Features

- **Network List** — Browse all saved WiFi profiles with a connected badge
- **Show / Hide Password** — Toggle password visibility inline
- **Copy to Clipboard** — One-click copy next to the password
- **Connect / Disconnect** — Toggle WiFi connection (button auto-updates based on state)
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

## UI Layout

- **Toolbar** — 3 buttons: Refresh, Show/Hide Password, Connect/Disconnect
- **Network list** — Scrollable list with "Connected" badge on active network
- **Inline password** — Expands below the selected network with Copy link and Forget link
- **Status bar** — Feedback messages at the bottom

## Notes

- Passwords are shown only on explicit click (preview-before-act)
- "Connected" badge shows which network you're currently on
- Button text and color update automatically (Connect turns to Disconnect when connected)
- No data is stored or transmitted — everything runs locally via `netsh`
- Safe for personal use; do not use on networks you do not own
