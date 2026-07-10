# WiFi Password Viewer

**One click, all your passwords.** Double-click this script and it shows every saved WiFi network name and password on your machine. Zero dependencies -- just VBScript and netsh, both built into Windows.

## Usage

```bash
wifi-password-viewer.vbs
```

That's it. A message box pops up with all your saved WiFi names and passwords.

A copy is also saved to your Desktop as `wifi-passwords.txt`.

## What it shows

- Network name (SSID)
- Password (plain text)
- Security type (WPA2, WPA3, etc.)

## Requirements

- Windows 10 or 11
- VBScript (built-in)
- netsh (built-in)

## Notes

- Only shows passwords for networks **you have already connected to**
- Must run with the same user account that saved the passwords
- Open networks show as "(hidden or open network)"
