# Media Compressor

**Ship that clip.** Crush any video down to a target file size in one drag-and-drop.  
Discord's 25 MB wall? Twitter's upload limit? Highlight reel too thicc?  
This thing uses 2-pass ffmpeg sorcery to squeeze every last megabyte — no quality lottery, no guesswork, just drop it and go.

## Requirements

- Python 3.6+

**ffmpeg & ffprobe** — on Windows, the script **auto-installs them via winget** if they're missing (other OS: install manually, see below).  
Otherwise, grab them manually:
- **Windows:** `winget install Gyan.FFmpeg`
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

## Usage

```bash
python media_compressor.py
```

The script launches an interactive prompt:
1. **Drag & drop** your video file onto the terminal window, then press Enter.
2. **Enter** the desired target file size in MB (e.g. `25`).
3. The script probes the video, calculates the optimal bitrate, and runs a 2-pass ffmpeg encode.

The output file is saved alongside the input as `<original>_compressed.mp4`.

## How it works

1. **Probe** — `ffprobe` extracts the exact video duration.
2. **Calculate** — target size is converted to bits, a 5% overhead buffer is subtracted, audio is allocated 128 kbps, and the remaining bitrate goes to the video track.
3. **2-pass encode** — ffmpeg's libx264 runs two passes for optimal quality at the given bitrate.

## Caveats

- Very small target sizes for long videos will produce poor quality. The script enforces a minimum video bitrate floor of 100 kbps and warns you if the target is too aggressive.
- Log files (`ffmpeg2pass-0.log`, `ffmpeg2pass-0.stats`) are cleaned up automatically after encoding.
