<div align="center">
  <h1>🔧 useful-scripts</h1>
  <p><strong>Plug-and-play micro-scripts for everyday automation.</strong></p>
  <p>One file. One job. Zero setup.</p>
  <p>
    <a href="#script-directory">Scripts</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#contributing">Contributing</a>
  </p>
  <br>
</div>

---

## Script Directory

| Script | Language | Description | Usage |
|--------|----------|-------------|-------|
| [Media Compressor](python/media_compressor/media_compressor.py) | Python 3 | Ship that clip. Crush any video down to a target size in one drag-and-drop — Discord's 25 MB cap? Twitter upload limits? Highlight reel too chonky? This thing slims it down with surgical 2-pass precision. ffmpeg auto-installed if missing. | `media_compressor.py` |
| [Batch Rename](powershell/batch-rename/batch-rename.ps1) | PowerShell | **Just run it.** Picks a folder, filter, and rename operation through clean on-screen prompts — find/replace, prefix, suffix, numbering, case change, or combine them all. Shows a preview before touching anything. Undoes previous renames automatically. | `./batch-rename.ps1` |
| [Temp Cleaner](powershell/temp-cleaner/temp-cleaner.ps1) | PowerShell | Clean Windows temp files, caches, and crash dumps. Preview before deleting, age-based filter to keep recent files, skips locked files automatically. No admin needed for user temp. | `./temp-cleaner.ps1` |
| [WiFi Password Viewer](vbs/wifi-password-viewer/wifi-password-viewer.vbs) | VBScript | Show all saved WiFi passwords in one click. Zero dependencies -- uses built-in netsh. | `wifi-password-viewer.vbs` |

---

## Quick Start

1. **Clone the repo**
   ```bash
   git clone https://github.com/pranto-smss/useful-scripts.git
   cd useful-scripts
   ```

2. **Pick a script** from the table above and open its file.

3. **Run it** — each script is self-contained with instructions in its header or sub-README.

---

## Contributing

We'd love your help! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- How to fork, branch, and open a PR
- Script template and style guide
- Checklist for a "plug-and-play" submission

---

<div align="center">
  <sub>Built with ☕ by contributors like you.</sub>
</div>
