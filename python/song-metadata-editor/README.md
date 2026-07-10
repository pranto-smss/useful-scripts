# Song Metadata Editor

Edit audio file metadata (title, artist, album, year, genre, ISRC) using data from MusicBrainz. Supports single file or batch mode.

## Features

- **Single File Mode** — Pick one file via file dialog, search MusicBrainz, write tags
- **Batch Mode** — Pick a folder, iterate through all audio files automatically
- **Smart Filename Parsing** — Strips track numbers, separators, and extra text from filenames to build search queries
- **Interactive Matching** — Shows top 5 results, lets you pick, skip, or type a custom search
- **Rate Limiting** — Respects MusicBrainz's 1 req/s limit automatically
- **Auto-Install** — Installs `mutagen` via pip if missing

## Supported Formats

| Format | Extension | Tag Type |
|--------|-----------|----------|
| MP3 | `.mp3` | ID3v2.3 |
| FLAC | `.flac` | Vorbis Comments |
| OGG Vorbis | `.ogg` | Vorbis Comments |
| M4A / AAC | `.m4a`, `.aac` | MP4 Atoms |
| WMA | `.wma` | ASF |

## Requirements

- Python 3.7+
- `mutagen` (auto-installed if missing)
- tkinter (built into Python on Windows)

## Usage

```bash
python song_metadata_editor.py
```

1. Choose edit mode (1 = Single File, 2 = Multiple Files)
2. Select file or folder via dialog
3. For each song:
   - Script searches MusicBrainz by filename
   - Pick a match, skip, or type a custom search term
   - Tags are written automatically
4. Summary of updated/skipped songs

## Metadata Written

- Title
- Artist
- Album
- Track Number
- Year / Release Date
- Genre (from MusicBrainz tags)
- ISRC (if available)

## Notes

- MusicBrainz is a free, open music database. No API key required.
- Rate limited to 1 request per second automatically.
- Only non-commercial use of the MusicBrainz API is free.
- Original filenames are not changed — only the internal tags are updated.
