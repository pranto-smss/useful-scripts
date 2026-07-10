# Song Metadata Editor

Edit audio file metadata (title, artist, album, year, genre, ISRC) using data from MusicBrainz. Fetches album art from Cover Art Archive. Renames files to "Artist - Title.ext". Supports single file, batch mode, and CLI arguments.

## Features

- **Single File Mode** — Pick one file via file dialog, search MusicBrainz, write tags
- **Batch Mode** — Pick a folder, iterate through all audio files automatically
- **CLI Arguments** — `--file`, `--folder`, `--recursive`, `--dry-run`, `--backup`, `--auto`, `--no-art`
- **Album Art** — Fetches cover art from Cover Art Archive and embeds it (can skip with `--no-art`)
- **Auto-Rename** — Renames files to `Artist - Title.ext` after updating tags (skips if already named correctly)
- **Smart Filename Parsing** — Strips track numbers, separators, and extra text from filenames to build search queries
- **Interactive Matching** — Shows top 5 results, lets you pick, skip, or type a custom search
- **Dry-Run Mode** — Preview what would change without touching files
- **Backup Mode** — Creates `.bak` copies before modifying (`--backup`)
- **Recursive Scan** — Scans subfolders with `--recursive`
- **Auto Mode** — Auto-picks first match, no prompts (`--auto`)
- **Rate Limiting** — Respects MusicBrainz's 1 req/s limit automatically
- **Auto-Install** — Installs `mutagen` via pip if missing

## Supported Formats

| Format | Extension | Tag Type | Album Art |
|--------|-----------|----------|-----------|
| MP3 | `.mp3` | ID3v2.3 | APIC |
| FLAC | `.flac` | Vorbis Comments | PICTURE |
| OGG Vorbis | `.ogg` | Vorbis Comments | METADATA_BLOCK_PICTURE |
| M4A / AAC | `.m4a`, `.aac` | MP4 Atoms | covr |
| WMA | `.wma` | ASF | WM/Picture |

## Requirements

- Python 3.7+
- `mutagen` (auto-installed if missing)
- tkinter (built into Python on Windows, used for file/folder pickers)

## Usage

### Interactive mode (default)

```bash
python song_metadata_editor.py
```

1. Choose edit mode (1 = Single File, 2 = Multiple Files)
2. Select file or folder via dialog
3. Choose whether to fetch album art
4. For each song:
   - Script searches MusicBrainz by filename
   - Pick a match, skip, or type a custom search term
   - Tags are written, album art embedded, file renamed
5. Summary of updated/skipped songs

### CLI mode

```bash
# Process a single file
python song_metadata_editor.py --file song.mp3

# Process a folder
python song_metadata_editor.py --folder C:\Music

# Recursive scan with backup
python song_metadata_editor.py --folder C:\Music --recursive --backup

# Dry run (preview only)
python song_metadata_editor.py --folder C:\Music --dry-run

# Auto mode (no prompts, first match)
python song_metadata_editor.py --folder C:\Music --auto

# Skip album art
python song_metadata_editor.py --folder C:\Music --no-art
```

### All flags

| Flag | Description |
|------|-------------|
| `--file PATH` | Single audio file to process |
| `--folder PATH` | Folder to scan for audio files |
| `--recursive` | Scan subfolders recursively |
| `--dry-run` | Show what would change without writing |
| `--backup` | Create `.bak` copies before modifying |
| `--auto` | Auto-pick first match (no interactive prompts) |
| `--no-art` | Skip album art embedding |

## Metadata Written

- Title
- Artist
- Album
- Track Number
- Year / Release Date
- Genre (from MusicBrainz tags)
- ISRC (if available)
- Album Art (from Cover Art Archive, unless `--no-art`)

## Notes

- MusicBrainz is a free, open music database. No API key required.
- Rate limited to 1 request per second automatically.
- Only non-commercial use of the MusicBrainz API is free.
- Files are renamed to `Artist - Title.ext` after updating tags. If the file already matches that format, renaming is skipped.
