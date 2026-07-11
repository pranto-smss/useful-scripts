# Batch Rename

**Just run it.** A clean interactive tool that walks you through renaming files step by step — folder picker, file filter, operation choice, preview, then apply. Nothing happens until you confirm.

## Usage

```powershell
./batch-rename.ps1
```

Or double-click `batch-rename.bat` (no PowerShell setup required):

```cmd
batch-rename.bat
```

Then just answer the prompts:

1. **Choose a folder** — graphical folder picker, type a path, or use the current folder.
2. **Filter files** — enter `*.jpg`, `mp4`, `.txt`, or `*` for all files. Subfolder support included.
3. **Pick an operation** — find/replace, prefix, suffix, sequential numbering, case change, or combine multiple.
4. **Preview** — see every rename before it happens. Collision detection built in.
5. **Confirm** — say yes and it runs. Say no and nothing changes.

## Undo

The script checks for a previous rename log when you open a folder. If one exists, it asks if you want to undo before continuing. Undo logs are stored safely in `%APPDATA%\BatchRenameTool\logs\`, keyed by folder path.

## Safety features

- **Preview always** — never modifies a file until you confirm.
- **Collision detection** — aborts if two files would get the same name or a target already exists.
- **Undo log** — every rename is logged. Run the script again in the same folder to undo.
- **No silent surprises** — every step is prompted with clear defaults.
