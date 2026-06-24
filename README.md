# Music Downloader

A clean, lightweight Tkinter-based YouTube audio/video downloader for Windows.

## Features
- Paste any YouTube URL and auto-fetch metadata
- Download audio as MP3 or video in selected quality
- Supports standard YouTube links, `youtu.be`, `shorts`, `embed`, and playlists
- Bundled with `ffmpeg.exe` for conversion
- Uses `yt-dlp` for robust YouTube extraction

## Quick Start

### 👥 For Non-Technical Users (Windows)
Download and run the standalone executable:
- Download `MusicDownloader.exe` from the [Releases](../../releases) page.
- Double-click to run — no installation needed!

### 👨‍💻 For Developers (Python Source)
1. Clone the repository:
   ```bash
   git clone https://github.com/cs-azad404/yt-video-downloader.git
   cd music-downloader
   ```
2. Run the one-step setup script:
   ```powershell
   .\setup.ps1
   ```
3. Launch the app:
   ```powershell
   .\venv\Scripts\python.exe main.py
   ```

## Requirements
- **For standalone EXE**: Windows 10/11 (no additional software needed)
- **For source code**: Python 3.8+ and the dependencies in `requirements.txt`

## Installation

If you're using the source code, follow the "For Developers" section above. The `setup.ps1` script automates everything.

For macOS/Linux users, use the shell script:

```bash
./setup.sh
```

## Run from source or executable
This repository includes both the full source code and a ready-to-run executable at `dist\MusicDownloader.exe`.

- Non-technical users can run `dist\MusicDownloader.exe` directly.
- Developers can run the source version with `python main.py` after installing dependencies.

## Rebuilding the Executable (Developers)

A pre-built `MusicDownloader.exe` is available in [Releases](../../releases) for end users.

To rebuild the executable yourself:

1. Install PyInstaller:
   ```powershell
   python -m pip install pyinstaller
   ```

2. Ensure `ffmpeg.exe` is in the project root (use `.\setup.ps1` to download it).

3. Run the build command:
   ```powershell
   pyinstaller --onefile --noconsole --icon=app.ico --add-binary "ffmpeg.exe;." --name MusicDownloader main.py
   ```

4. The executable will be created at `dist\MusicDownloader.exe`.

## Distributing the Executable
- Upload `dist\MusicDownloader.exe` to GitHub Releases for end users.
- Users can download and run the EXE without needing Python or any setup.

## Notes
- Keep `ffmpeg.exe` next to `main.py` for source code development.
- For the standalone executable, `ffmpeg.exe` is bundled by PyInstaller when using `--add-binary`.
- If YouTube extraction fails, update `yt-dlp` with:
  ```powershell
  python -m pip install -U yt_dlp
  ```
- For cleaner filenames, the app uses `restrictfilenames` option.
- For cleaner filenames, the app uses `restrictfilenames`.

## Project Files
- `main.py` — application source
- `requirements.txt` — Python dependencies
- `ffmpeg.exe` — bundled FFmpeg binary
- `app.ico` — application icon

## License
Use freely for personal or educational purposes.
