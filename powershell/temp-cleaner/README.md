# Temp Cleaner

**Clean up the junk.** Reclaim disk space by clearing Windows temp files, caches, and crash dumps — with a full preview before anything is touched. Nothing happens until you confirm.

## Usage

```powershell
./temp-cleaner.ps1
temp-cleaner.bat          # or double-click the .bat wrapper
```

Then just answer the prompts:

1. **Choose a cleanup level** — user temp only (no admin needed), user + system temp, or full cleanup including thumbnails and dumps.
2. **Set an age filter** — only files older than N days are deleted (default: 7). Recent files are always kept.
3. **Preview** — see the largest files that would be deleted, total file count, and estimated space freed.
4. **Confirm** — say yes and it runs. Say no and nothing changes.

### Parameters

| Parameter | Description |
|-----------|-------------|
| `-Mode <1-3>` | Skip the interactive level prompt. `1` = User temp, `2` = User + System temp, `3` = Full cleanup. |

**Examples:**
```powershell
./temp-cleaner.ps1 -Mode 1    # user temp only, no admin needed
./temp-cleaner.ps1 -Mode 3    # full cleanup, auto-elevates if needed
temp-cleaner.bat -Mode 2     # via .bat wrapper
```

## What gets cleaned

| Level | Targets |
|-------|---------|
| **1 — User** | `%TEMP%` (current user) |
| **2 — System** | `C:\Windows\Temp`, Windows Update cache |
| **3 — Full** | Above + thumbnail cache, crash dumps, Windows Error Reporting |

## Safety features

- **Preview always** — full list of files shown before deletion.
- **Age filter** — default 7 days keeps recent files safe.
- **Skip locked files** — in-use files are skipped automatically, never forced.
- **No browser data** — cookies, sessions, and bookmarks are never touched.
- **No user documents** — only temp and cache paths.
- **Admin handling** — Level 1 works with standard user privileges. Levels 2-3 auto-elevate via UAC when needed.
