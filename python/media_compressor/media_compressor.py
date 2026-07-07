#!/usr/bin/env python3
# -------------------------------------------------
# Script Name:   Media Compressor
# Language:      Python 3
# Description:   Compress a video to a target file size using 2-pass ffmpeg encoding
# Usage:         python media_compressor.py  (interactive — drag & drop or type path)
# Depends:       ffmpeg, ffprobe (auto-installed via winget on Windows if missing)
# -------------------------------------------------

import sys
import subprocess
import json
import os
import shutil
from pathlib import Path

def ensure_ffmpeg():
    """Check if ffmpeg/ffprobe are on PATH; on Windows, auto-install via winget if missing."""
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return

    if os.name != "nt":
        print("[-] ffmpeg and ffprobe are required.")
        print("    macOS: brew install ffmpeg")
        print("    Linux: sudo apt install ffmpeg")
        sys.exit(1)

    print("\n[!] ffmpeg not found. Installing FFmpeg Essentials via winget...")
    try:
        subprocess.run(
            ["winget", "install", "Gyan.FFmpeg", "--accept-package-agreements", "--accept-source-agreements"],
            check=True
        )
    except subprocess.CalledProcessError:
        print("[-] Winget install failed. Install ffmpeg manually:")
        print("    winget install Gyan.FFmpeg")
        sys.exit(1)

    # Winget installs to %ProgramFiles%\FFmpeg\bin — add to PATH for this session
    ffmpeg_bin = Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "FFmpeg" / "bin"
    if (ffmpeg_bin / "ffmpeg.exe").exists() and (ffmpeg_bin / "ffprobe.exe").exists():
        os.environ["PATH"] = str(ffmpeg_bin) + os.pathsep + os.environ.get("PATH", "")
        print("[+] FFmpeg installed and loaded into PATH.\n")
        return

    print("[-] ffmpeg was installed but could not be found in PATH. Restart the terminal.")
    sys.exit(1)

def get_video_duration(input_path: Path) -> float:
    """Uses ffprobe to extract the exact duration of the video in seconds."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", str(input_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except (subprocess.CalledProcessError, KeyError, ValueError) as e:
        print(f"\n[-] Error probing file metadata with ffprobe: {e}")
        return 0.0

def compress_video(input_path: Path, target_size_mb: float):
    """Compresses video to target size using a calculated 2-pass encoding approach."""
    output_path = input_path.parent / f"{input_path.stem}_compressed{input_path.suffix}"

    print(f"\n[*] Analyzing '{input_path.name}'...")
    duration = get_video_duration(input_path)

    if duration == 0.0:
        print("[-] Could not read video duration. Aborting.")
        return

    print(f"[*] Video duration: {duration:.2f} seconds")

    # --- Bitrate Math Logic ---
    target_total_bits = (target_size_mb * 1024 * 1024 * 8) * 0.95
    audio_bitrate_bps = 128000

    total_bitrate_bps = target_total_bits / duration
    video_bitrate_bps = total_bitrate_bps - audio_bitrate_bps

    if video_bitrate_bps < 100000:
        print("\n[!] Warning: Target size is incredibly small for this video length.")
        print("[!] The output video quality will look heavily pixelated.")
        video_bitrate_bps = 100000

    video_bitrate_kbps = int(video_bitrate_bps / 1000)
    audio_bitrate_kbps = int(audio_bitrate_bps / 1000)

    print(f"[*] Optimization Target: Video {video_bitrate_kbps} kbps | Audio {audio_bitrate_kbps} kbps")

    # --- Pass 1 ---
    print("\n[*] Launching Pass 1/2 (Analyzing frame vectors)...")
    pass1_cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-c:v", "libx264", "-b:v", f"{video_bitrate_kbps}k",
        "-pass", "1", "-an", "-f", "null", "-"
    ]
    subprocess.run(pass1_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # --- Pass 2 ---
    print("[*] Launching Pass 2/2 (Finalizing compression)...")
    pass2_cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-c:v", "libx264", "-b:v", f"{video_bitrate_kbps}k",
        "-pass", "2", "-c:a", "aac", "-b:a", f"{audio_bitrate_kbps}k",
        str(output_path)
    ]
    subprocess.run(pass2_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # Clean up 2-pass log files
    for log_file in Path(".").glob("ffmpeg2pass-0.*"):
        try:
            log_file.unlink()
        except FileNotFoundError:
            pass

    if output_path.exists():
        final_size = output_path.stat().st_size / (1024 * 1024)
        print(f"\n[+] Success! File compressed to: {final_size:.2f} MB")
        print(f"[+] Output Location: {output_path}")
    else:
        print("\n[-] Error: FFmpeg execution finished but no file was generated.")

def main():
    ensure_ffmpeg()

    print("=" * 55)
    print("      🎬 UNIVERSAL INTERACTIVE MEDIA COMPRESSOR 🎬      ")
    print("=" * 55)
    print("Hint: You can drag and drop your video directly into this window.\n")

    # 1. Interactive File Selection Loop
    while True:
        user_file = input("👉 Drop your video file here and press Enter: ")

        # CRUCIAL: Strip out quotes or trailing spaces added by OS drag-and-drop mechanisms
        clean_path = user_file.strip("'\" ").strip()
        input_path = Path(clean_path)

        if input_path.is_file():
            break
        print("[-] Invalid file. Make sure you dropped a valid video asset file.\n")

    # 2. Interactive Target Size Loop
    while True:
        user_size = input("👉 Enter your desired target file size in MB (e.g. 25): ")
        try:
            target_mb = float(user_size.strip())
            if target_mb > 0:
                break
            print("[-] Target size must be greater than 0 MB.\n")
        except ValueError:
            print("[-] Please input a numeric value only.\n")

    # Run processing
    compress_video(input_path, target_mb)

    # Keeps terminal alive if user executed it via a desktop double-click
    print("\n" + "=" * 55)
    input("Press Enter to close this window...")

if __name__ == "__main__":
    main()
