# -------------------------------------------------
# Script Name:   Song Metadata Editor
# Language:      Python 3
# Description:   Edit audio file metadata using MusicBrainz data
# Usage:         python song_metadata_editor.py
# Author:        Pranto, SMSS
# -------------------------------------------------

import sys
import os
import re
import json
import time
import shutil
import argparse
import urllib.request
import urllib.parse
import subprocess

# ===========================================================================
# DEPENDENCY CHECK
# ===========================================================================

def ensure_mutagen():
    """Auto-install mutagen via pip if not present."""
    try:
        import mutagen
        return mutagen
    except ImportError:
        pass

    print("[!] mutagen not found. Installing via pip...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "mutagen", "-q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print("[-] Failed to install mutagen. Run manually:")
        print("    pip install mutagen")
        sys.exit(1)

    import mutagen
    print("[+] mutagen installed.\n")
    return mutagen

mutagen = ensure_mutagen()

from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TDRC, TCON, TSRC, ID3NoHeaderError
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4, MP4Tags
from mutagen.asf import ASF

SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".ogg", ".m4a", ".aac", ".wma"}

MUSICBRAINZ_BASE = "https://musicbrainz.org/ws/2"
USER_AGENT = "UsefulScripts-SongMetadataEditor/1.0 (https://github.com/pranto-smss/useful-scripts)"

last_request_time = 0.0

# ===========================================================================
# RATE-LIMITED HTTP
# ===========================================================================

def rate_limited_get(url):
    """GET with enforced 1-second gap between MusicBrainz requests."""
    global last_request_time
    elapsed = time.time() - last_request_time
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            last_request_time = time.time()
            return data
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("  [!] Rate limited by MusicBrainz. Waiting 3 seconds...")
            time.sleep(3)
            last_request_time = time.time()
            return rate_limited_get(url)
        print(f"  [!] HTTP error {e.code} from MusicBrainz")
        last_request_time = time.time()
        return None
    except Exception as e:
        print(f"  [!] Network error: {e}")
        last_request_time = time.time()
        return None

# ===========================================================================
# MUSICBRAINZ API
# ===========================================================================

def search_musicbrainz(query, limit=5):
    """Search for recordings by name. Returns list of results."""
    encoded = urllib.parse.quote(query)
    url = f"{MUSICBRAINZ_BASE}/recording?query={encoded}&fmt=json&limit={limit}"
    data = rate_limited_get(url)
    if not data:
        return []
    return data.get("recordings", [])

def get_recording_details(mbid):
    """Fetch full recording details including artist, releases, tags."""
    url = f"{MUSICBRAINZ_BASE}/recording/{mbid}?fmt=json&inc=artist-credits+releases+tags+isrcs"
    return rate_limited_get(url)

# ===========================================================================
# FILENAME UTILS
# ===========================================================================

def clean_filename(filename):
    """Convert a filename into a search query."""
    name = os.path.splitext(filename)[0]
    # Replace common separators with spaces
    name = re.sub(r"[_\-]+", " ", name)
    # Remove trailing numbers like "(1)", "(2)", "copy"
    name = re.sub(r"\s*\(\d+\)\s*$", "", name)
    name = re.sub(r"\s+copy\s*$", "", name, flags=re.IGNORECASE)
    # Remove leading track numbers like "01.", "01 -"
    name = re.sub(r"^\d+[\.\-\s]+", "", name)
    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name).strip()
    return name

def sanitize_filename(name):
    """Remove characters that are illegal in Windows filenames."""
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    return name.strip()

def unique_filepath(folder, name, ext):
    """Return a unique filepath, appending (1), (2), etc. if needed."""
    candidate = os.path.join(folder, f"{name}{ext}")
    if not os.path.exists(candidate):
        return candidate
    n = 1
    while os.path.exists(os.path.join(folder, f"{name} ({n}){ext}")):
        n += 1
    return os.path.join(folder, f"{name} ({n}){ext}")

def rename_file(old_path, metadata, dry_run=False):
    """Rename file to 'Artist - Title.ext'. Returns new path or old path on failure."""
    artist = sanitize_filename(metadata.get("artist", "Unknown"))
    title = sanitize_filename(metadata.get("title", "Unknown"))
    if not artist or not title:
        return old_path

    folder = os.path.dirname(old_path)
    ext = os.path.splitext(old_path)[1]
    current_stem = os.path.splitext(os.path.basename(old_path))[0]
    new_name = f"{artist} - {title}"

    # Skip if filename already matches
    if current_stem == new_name:
        return old_path

    new_path = unique_filepath(folder, new_name, ext)

    if dry_run:
        if new_path != old_path:
            print(f"  [dry-run] Would rename: {os.path.basename(new_path)}")
        return old_path

    try:
        os.rename(old_path, new_path)
        return new_path
    except OSError as e:
        print(f"  [!] Rename failed: {e}")
        return old_path

def backup_file(filepath):
    """Create a .bak copy of a file. Returns True on success."""
    bak_path = filepath + ".bak"
    if os.path.exists(bak_path):
        return True
    try:
        shutil.copy2(filepath, bak_path)
        return True
    except OSError as e:
        print(f"  [!] Backup failed: {e}")
        return False

# ===========================================================================
# DISPLAY
# ===========================================================================

def format_duration(ms):
    """Convert milliseconds to M:SS format."""
    if not ms:
        return "?"
    seconds = int(ms / 1000)
    return f"{seconds // 60}:{seconds % 60:02d}"

def show_results(results):
    """Display search results and let user pick."""
    if not results:
        return None

    print()
    for i, rec in enumerate(results[:5], 1):
        title = rec.get("title", "Unknown")
        artist = "Unknown"
        if rec.get("artist-credit"):
            artist = "".join(ac.get("name", "") for ac in rec["artist-credit"])

        album = "Unknown"
        year = "?"
        if rec.get("releases"):
            rel = rec["releases"][0]
            album = rel.get("title", "Unknown")
            date = rel.get("date", "")
            if date:
                year = date[:4]

        duration = format_duration(rec.get("length"))

        print(f"  {i}. {artist} - {title}")
        print(f"     Album: {album} | Year: {year} | Duration: {duration}")

    print()
    return True

def pick_match(count):
    """Prompt user to pick a result, skip, or custom search."""
    while True:
        choice = input(f"  Pick a match (1-{count}, 'skip', 'custom'): ").strip().lower()

        if choice == "skip":
            return "skip", None
        if choice == "custom":
            custom = input("  Enter new search term: ").strip()
            if custom:
                return "custom", custom
            print("  Empty input. Try again.")
            continue
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= count:
                return "pick", idx - 1
        print(f"  Invalid input. Enter 1-{count}, 'skip', or 'custom'.")

# ===========================================================================
# TAG WRITING
# ===========================================================================

def write_tags_mp3(filepath, metadata):
    """Write ID3v2.3 tags to an MP3 file."""
    try:
        tags = ID3(filepath)
    except ID3NoHeaderError:
        tags = ID3()

    tags["TIT2"] = TIT2(encoding=3, text=[metadata.get("title", "")])
    tags["TPE1"] = TPE1(encoding=3, text=[metadata.get("artist", "")])
    tags["TALB"] = TALB(encoding=3, text=[metadata.get("album", "")])

    if metadata.get("track"):
        tags["TRCK"] = TRCK(encoding=3, text=[str(metadata["track"])])
    if metadata.get("year"):
        tags["TDRC"] = TDRC(encoding=3, text=[str(metadata["year"])])
    if metadata.get("genre"):
        tags["TCON"] = TCON(encoding=3, text=[metadata["genre"]])
    if metadata.get("isrc"):
        tags["TSRC"] = TSRC(encoding=3, text=[metadata["isrc"]])

    tags.save(filepath)

def write_tags_flac(filepath, metadata):
    """Write Vorbis comments to a FLAC file."""
    audio = FLAC(filepath)
    audio["TITLE"] = metadata.get("title", "")
    audio["ARTIST"] = metadata.get("artist", "")
    audio["ALBUM"] = metadata.get("album", "")
    if metadata.get("track"):
        audio["TRACKNUMBER"] = str(metadata["track"])
    if metadata.get("year"):
        audio["DATE"] = str(metadata["year"])
    if metadata.get("genre"):
        audio["GENRE"] = metadata["genre"]
    if metadata.get("isrc"):
        audio["ISRC"] = metadata["isrc"]
    audio.save()

def write_tags_ogg(filepath, metadata):
    """Write Vorbis comments to an OGG Vorbis file."""
    audio = OggVorbis(filepath)
    audio["TITLE"] = metadata.get("title", "")
    audio["ARTIST"] = metadata.get("artist", "")
    audio["ALBUM"] = metadata.get("album", "")
    if metadata.get("track"):
        audio["TRACKNUMBER"] = str(metadata["track"])
    if metadata.get("year"):
        audio["DATE"] = str(metadata["year"])
    if metadata.get("genre"):
        audio["GENRE"] = metadata["genre"]
    if metadata.get("isrc"):
        audio["ISRC"] = metadata["isrc"]
    audio.save()

def write_tags_m4a(filepath, metadata):
    """Write MP4 atoms to an M4A/AAC file."""
    audio = MP4(filepath)
    try:
        audio.add_tags()
    except Exception:
        pass
    tags = audio.tags
    tags["\xa9nam"] = [metadata.get("title", "")]
    tags["\xa9ART"] = [metadata.get("artist", "")]
    tags["\xa9alb"] = [metadata.get("album", "")]
    if metadata.get("track"):
        tags["trkn"] = [(int(metadata["track"]), 0)]
    if metadata.get("year"):
        tags["\xa9day"] = [str(metadata["year"])]
    if metadata.get("genre"):
        tags["\xa9gen"] = [metadata["genre"]]
    if metadata.get("isrc"):
        tags["\xa9cmt"] = [f"ISRC: {metadata['isrc']}"]
    audio.save()

def write_tags_wma(filepath, metadata):
    """Write ASF tags to a WMA file."""
    audio = ASF(filepath)
    audio["Title"] = [metadata.get("title", "")]
    audio["Author"] = [metadata.get("artist", "")]
    audio["WM/AlbumTitle"] = [metadata.get("album", "")]
    if metadata.get("track"):
        audio["WM/TrackNumber"] = [str(metadata["track"])]
    if metadata.get("year"):
        audio["WM/Year"] = [str(metadata["year"])]
    if metadata.get("genre"):
        audio["WM/Genre"] = [metadata["genre"]]
    if metadata.get("isrc"):
        audio["WM/ISRC"] = [metadata["isrc"]]
    audio.save()

def write_tags(filepath, metadata):
    """Route to the correct tag writer based on file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    writers = {
        ".mp3": write_tags_mp3,
        ".flac": write_tags_flac,
        ".ogg": write_tags_ogg,
        ".m4a": write_tags_m4a,
        ".aac": write_tags_m4a,
        ".wma": write_tags_wma,
    }
    writer = writers.get(ext)
    if writer:
        writer(filepath, metadata)
        return True
    return False

# ===========================================================================
# COVER ART
# ===========================================================================

COVERART_BASE = "https://coverartarchive.org/release"

def _caa_get(url, timeout=30):
    """GET with retry for Cover Art Archive (can be slow)."""
    for attempt in range(3):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429:
                time.sleep(3)
                continue
            return None
        except Exception:
            if attempt < 2:
                time.sleep(2)
                continue
            return None
    return None

def fetch_album_art(release_mbid):
    """Fetch album art from Cover Art Archive. Returns raw image bytes or None."""
    if not release_mbid:
        return None

    # Step 1: Get the JSON manifest to find the front image
    json_url = f"{COVERART_BASE}/{release_mbid}"
    json_data = _caa_get(json_url)
    if not json_data:
        return None

    try:
        manifest = json.loads(json_data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    images = manifest.get("images", [])
    front_url = None
    for img in images:
        if img.get("front"):
            front_url = img.get("image")
            break
    if not front_url:
        return None

    # Step 2: Download the actual image
    time.sleep(1)
    return _caa_get(front_url)

def write_art(filepath, art_data):
    """Embed album art into an audio file based on its format."""
    if not art_data:
        return False
    ext = os.path.splitext(filepath)[1].lower()

    try:
        if ext == ".mp3":
            return write_art_mp3(filepath, art_data)
        elif ext == ".flac":
            return write_art_flac(filepath, art_data)
        elif ext == ".ogg":
            return write_art_ogg(filepath, art_data)
        elif ext in (".m4a", ".aac"):
            return write_art_m4a(filepath, art_data)
        elif ext == ".wma":
            return write_art_wma(filepath, art_data)
    except Exception as e:
        print(f"  [!] Failed to embed art: {e}")
        return False
    return False

def write_art_mp3(filepath, art_data):
    from mutagen.id3 import ID3, APIC, ID3NoHeaderError
    try:
        tags = ID3(filepath)
    except ID3NoHeaderError:
        tags = ID3()
    # Detect mime from magic bytes
    if art_data[:3] == b'\xff\xd8\xff':
        mime = "image/jpeg"
    elif art_data[:8] == b'\x89PNG\r\n\x1a\n':
        mime = "image/png"
    else:
        mime = "image/jpeg"
    tags["APIC"] = APIC(encoding=3, mime=mime, type=3, desc="Cover", data=art_data)
    tags.save(filepath)
    return True

def write_art_flac(filepath, art_data):
    from mutagen.flac import FLAC, Picture
    audio = FLAC(filepath)
    pic = Picture()
    pic.type = 3
    pic.mime = "image/jpeg"
    pic.desc = "Cover"
    pic.data = art_data
    audio.clear_pictures()
    audio.add_picture(pic)
    audio.save()
    return True

def write_art_ogg(filepath, art_data):
    from mutagen.oggvorbis import OggVorbis
    from mutagen.flac import Picture
    import base64
    audio = OggVorbis(filepath)
    pic = Picture()
    pic.type = 3
    pic.mime = "image/jpeg"
    pic.desc = "Cover"
    pic.data = art_data
    encoded = base64.b64encode(pic.write()).decode("ascii")
    audio["METADATA_BLOCK_PICTURE"] = [encoded]
    audio.save()
    return True

def write_art_m4a(filepath, art_data):
    from mutagen.mp4 import MP4, MP4Cover
    audio = MP4(filepath)
    try:
        audio.add_tags()
    except Exception:
        pass
    cover = MP4Cover(art_data, imageformat=MP4Cover.FORMAT_JPEG)
    audio.tags["covr"] = [cover]
    audio.save()
    return True

def write_art_wma(filepath, art_data):
    from mutagen.asf import ASF, ASFPicture
    audio = ASF(filepath)
    pic = ASFPicture()
    pic.type = 3  # Cover (front)
    pic.mime = "image/jpeg"
    pic.data = art_data
    audio["WM/Picture"] = [pic]
    audio.save()
    return True

# ===========================================================================
# METADATA EXTRACTION
# ===========================================================================

def extract_metadata(recording, release=None):
    """Extract a clean metadata dict from a MusicBrainz recording."""
    metadata = {
        "title": recording.get("title", ""),
        "artist": "",
        "album": "",
        "track": None,
        "year": "",
        "genre": "",
        "isrc": "",
        "release_mbid": "",
    }

    # Artist from artist-credit
    if recording.get("artist-credit"):
        metadata["artist"] = "".join(ac.get("name", "") for ac in recording["artist-credit"])

    # Use provided release or first available
    if not release and recording.get("releases"):
        release = recording["releases"][0]

    if release:
        metadata["album"] = release.get("title", "")
        metadata["release_mbid"] = release.get("id", "")
        date = release.get("date", "")
        if date:
            metadata["year"] = date[:4]

        # Track number
        if release.get("mediums"):
            medium = release["mediums"][0]
            if medium.get("tracks"):
                for track in medium["tracks"]:
                    if track.get("id") == recording.get("id"):
                        metadata["track"] = track.get("number", None)
                        break
                if metadata["track"] is None and medium["tracks"]:
                    # Fallback: match by position
                    for track in medium["tracks"]:
                        if track.get("title", "").lower() == recording.get("title", "").lower():
                            metadata["track"] = track.get("number", None)
                            break

    # ISRC
    if recording.get("isrcs"):
        metadata["isrc"] = recording["isrcs"][0]

    # Genre from tags
    if recording.get("tags"):
        tags = recording["tags"]
        if tags:
            metadata["genre"] = tags[0].get("name", "")

    return metadata

# ===========================================================================
# FILE/FOLDER PICKERS
# ===========================================================================

def pick_file():
    """Open a tkinter file picker for a single audio file."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        filetypes = [
            ("Audio Files", " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)),
            ("All Files", "*.*"),
        ]
        filepath = filedialog.askopenfilename(
            title="Select an audio file",
            filetypes=filetypes,
        )
        root.destroy()

        if filepath and os.path.isfile(filepath):
            return filepath
        return None
    except Exception:
        return None

def pick_folder():
    """Open a tkinter folder picker."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        folder = filedialog.askdirectory(title="Select folder containing audio files")
        root.destroy()

        if folder and os.path.isdir(folder):
            return folder
        return None
    except Exception:
        return None

def scan_audio_files(folder, recursive=False):
    """Find all supported audio files in a folder."""
    files = []
    if recursive:
        for dirpath, _, filenames in os.walk(folder):
            for entry in sorted(filenames):
                full = os.path.join(dirpath, entry)
                if os.path.isfile(full) and os.path.splitext(entry)[1].lower() in SUPPORTED_EXTENSIONS:
                    files.append(full)
    else:
        for entry in sorted(os.listdir(folder)):
            full = os.path.join(folder, entry)
            if os.path.isfile(full) and os.path.splitext(entry)[1].lower() in SUPPORTED_EXTENSIONS:
                files.append(full)
    return files

# ===========================================================================
# SONG PROCESSING
# ===========================================================================

def process_song(filepath, index, total, dry_run=False, backup=False, auto=False, no_art=False):
    """Process a single song file: search, pick, fetch, write."""
    filename = os.path.basename(filepath)
    print(f"\n[{index}/{total}] Processing: {filename}")

    query = clean_filename(filename)
    print(f"  Searching MusicBrainz for \"{query}\"...")

    # Search loop (allows custom re-search or skip)
    while True:
        results = search_musicbrainz(query)

        if not results:
            print(f"  No results found for \"{query}\".")
            if auto:
                print(f"  Skipped (auto mode): {filename}")
                return False, filepath
            choice = input("  Enter a different search term, or 'skip': ").strip()
            if choice.lower() == "skip":
                print(f"  Skipped: {filename}")
                return False, filepath
            if choice:
                query = choice
                print(f"  Searching for \"{query}\"...")
                continue
            print("  Empty input. Skipping.")
            print(f"  Skipped: {filename}")
            return False, filepath

        # Auto mode: pick first result
        if auto:
            selected = results[0]
            title = selected.get("title", "?")
            artist = "Unknown"
            if selected.get("artist-credit"):
                artist = "".join(ac.get("name", "") for ac in selected["artist-credit"])
            print(f"  Auto-picked: {artist} - {title}")
            break

        # Show results
        show_results(results)
        action, value = pick_match(len(results[:5]))

        if action == "skip":
            print(f"  Skipped: {filename}")
            return False, filepath
        elif action == "custom":
            query = value
            print(f"  Searching for \"{query}\"...")
            continue
        elif action == "pick":
            selected = results[value]
            break

    # Fetch full details
    mbid = selected.get("id")
    print(f"  Fetching full details...")
    details = get_recording_details(mbid)
    if not details:
        print(f"  [!] Failed to fetch details. Using search result.")
        details = selected

    # Extract metadata
    metadata = extract_metadata(details)

    artist = metadata.get("artist", "Unknown")
    title = metadata.get("title", "Unknown")
    album = metadata.get("album", "")
    year = metadata.get("year", "")
    extra = f" ({album}, {year})" if album else ""

    # Dry-run: show what would happen
    if dry_run:
        print(f"  [dry-run] Would write: {artist} - {title}{extra}")
        if metadata.get("release_mbid") and not no_art:
            print(f"  [dry-run] Would fetch album art from Cover Art Archive")
        new_path = rename_file(filepath, metadata, dry_run=True)
        return True, filepath

    # Backup before writing
    if backup:
        if backup_file(filepath):
            print(f"  Backed up: {filename}.bak")
        else:
            print(f"  [!] Continuing without backup...")

    # Write tags
    try:
        write_tags(filepath, metadata)
        print(f"  Written: {artist} - {title}{extra}")

        # Fetch and embed album art
        if not no_art:
            print(f"  [{index}/{total}] Fetching album art...", end="", flush=True)
            art_data = fetch_album_art(metadata.get("release_mbid", ""))
            bar_len = 20
            filled = int(bar_len * index / total)
            bar = "=" * filled + ">" + " " * (bar_len - filled - 1)
            if art_data:
                write_art(filepath, art_data)
                print(f"\r  [{bar}] {index}/{total} Album art embedded.  ")
            else:
                print(f"\r  [{bar}] {index}/{total} No album art found.   ")

        # Rename file
        new_path = rename_file(filepath, metadata)
        if new_path != filepath:
            print(f"  Renamed: {os.path.basename(new_path)}")
        return True, new_path
    except Exception as e:
        print(f"  [!] Failed to write tags: {e}")
        return False, filepath

# ===========================================================================
# MAIN
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Edit audio file metadata using MusicBrainz data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python song_metadata_editor.py                     # Interactive mode\n"
               "  python song_metadata_editor.py --folder C:\\Music   # Scan folder\n"
               "  python song_metadata_editor.py --folder Music --recursive --backup\n"
               "  python song_metadata_editor.py --file song.mp3 --dry-run\n"
               "  python song_metadata_editor.py --folder Music --auto --no-art",
    )
    parser.add_argument("--file", help="Single audio file to process")
    parser.add_argument("--folder", help="Folder to scan for audio files")
    parser.add_argument("--recursive", action="store_true", help="Scan subfolders recursively")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    parser.add_argument("--backup", action="store_true", help="Create .bak copies before modifying")
    parser.add_argument("--auto", action="store_true", help="Auto-pick first match (no interactive prompts)")
    parser.add_argument("--no-art", action="store_true", help="Skip album art embedding")
    args = parser.parse_args()

    print("=== Song Metadata Editor ===\n")
    if args.dry_run:
        print("  ** DRY RUN -- no files will be modified **\n")

    # Determine files to process
    if args.file:
        filepath = os.path.abspath(args.file)
        if not os.path.isfile(filepath):
            print(f"File not found: {filepath}")
            sys.exit(1)
        files = [filepath]
    elif args.folder:
        folder = os.path.abspath(args.folder)
        if not os.path.isdir(folder):
            print(f"Folder not found: {folder}")
            sys.exit(1)
        files = scan_audio_files(folder, recursive=args.recursive)
        if not files:
            print(f"No audio files found in: {folder}")
            sys.exit(0)
        print(f"Found {len(files)} audio file(s).\n")
    else:
        # Interactive mode (default)
        mode_input = input("Choose Edit Mode:\n  1 = Single File\n  2 = Multiple Files\nChoose [1]: ").strip()
        if not mode_input:
            mode_input = "1"

        if mode_input == "1":
            print("\nSelect an audio file...")
            filepath = pick_file()
            if not filepath:
                print("No file selected. Exiting.")
                sys.exit(0)
            files = [filepath]
        elif mode_input == "2":
            print("\nSelect a folder containing audio files...")
            folder = pick_folder()
            if not folder:
                print("No folder selected. Exiting.")
                sys.exit(0)
            files = scan_audio_files(folder)
            if not files:
                print(f"No audio files found in: {folder}")
                sys.exit(0)
            print(f"Found {len(files)} audio file(s).\n")
        else:
            print("Invalid choice. Exiting.")
            sys.exit(1)

    # Ask about album art (interactive mode only, unless --no-art)
    if not args.no_art and not args.file and not args.folder:
        art_choice = input("Fetch album art from internet? [Y/n]: ").strip().lower()
        if art_choice in ("n", "no"):
            args.no_art = True

    # Process each song
    updated = 0
    skipped = 0

    try:
        for i, filepath in enumerate(files, 1):
            success, new_path = process_song(
                filepath, i, len(files),
                dry_run=args.dry_run,
                backup=args.backup,
                auto=args.auto,
                no_art=args.no_art,
            )
            files[i - 1] = new_path
            if success:
                updated += 1
            else:
                skipped += 1
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")

    # Summary
    print(f"\nDone. {updated} of {len(files)} songs updated.", end="")
    if skipped > 0:
        print(f" {skipped} skipped.", end="")
    if args.dry_run:
        print(" (dry run -- nothing modified)", end="")
    print()

    if not args.auto:
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
