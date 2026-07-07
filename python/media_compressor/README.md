# Media Compressor

Compress a video to a precise target file size using 2-pass ffmpeg encoding.

## Requirements

- Python 3.6+
- `ffmpeg` and `ffprobe` on your system PATH

Install ffmpeg via your package manager:
- **Windows:** `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/)
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

## Usage

```bash
python media_compressor.py <input_file> <target_size_in_mb>
```

**Example:**
```bash
python media_compressor.py gameplay.mp4 25
```

The output file is saved alongside the input as `<original>_compressed.mp4`.

## How it works

1. **Probe** — `ffprobe` extracts the exact video duration.
2. **Calculate** — target size is converted to bits, a 5% overhead buffer is subtracted, audio is allocated 128 kbps, and the remaining bitrate goes to the video track.
3. **2-pass encode** — ffmpeg's libx264 runs two passes for optimal quality at the given bitrate.

## Caveats

- Very small target sizes for long videos will produce poor quality. The script enforces a minimum video bitrate floor of 100 kbps.
- Log files (`ffmpeg2pass-0.log`, `ffmpeg2pass-0.stats`) are cleaned up automatically after encoding.
