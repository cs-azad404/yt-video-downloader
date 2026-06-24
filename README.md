# Music Downloader

A clean, lightweight Tkinter-based YouTube audio/video downloader for Windows.

## Features
- Paste any YouTube URL and auto-fetch metadata
- Download audio as MP3 or video in selected quality
- Supports standard YouTube links, `youtu.be`, `shorts`, `embed`, and playlists
- Bundled with `ffmpeg.exe` for conversion
- Uses `yt-dlp` for robust YouTube extraction

## Requirements
- Windows 10/11
- Python 3.8+ for development
- `ffmpeg.exe` must remain in the same folder as `main.py`

If you prefer a one-step setup, run the included `setup.ps1` (Windows) which
creates a virtual environment, installs dependencies, and downloads `ffmpeg.exe`.
## Installation
1. Open PowerShell in the project folder.
2. Create a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

## Running
```powershell
python main.py
```

## One-step setup (recommended for Windows)

Run the PowerShell setup script from the project root. This will create a
`venv`, install required packages, and download `ffmpeg.exe` automatically:

```powershell
./setup.ps1
```

For macOS/Linux users, use the shell script:

```bash
./setup.sh
```
## Build standalone executable
Install PyInstaller and run:
```powershell
python -m pip install pyinstaller
pyinstaller --onefile --noconsole --icon=app.ico --add-binary "ffmpeg.exe;." main.py
```

Then use the generated `dist\main.exe`.

## Notes
- Keep `ffmpeg.exe` next to `main.py` or the executable.
- If YouTube extraction fails, update `yt-dlp` with:
  ```powershell
  python -m pip install -U yt_dlp
  ```
- For cleaner filenames, the app uses `restrictfilenames`.

## Project Files
- `main.py` — application source
- `requirements.txt` — Python dependencies
- `ffmpeg.exe` — bundled FFmpeg binary
- `app.ico` — application icon

## License
Use freely for personal or educational purposes.
