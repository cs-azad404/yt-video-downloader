import io
import json
import os
import re
import sys
import threading
import webbrowser
import shutil
import requests
import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse

# --------------- Configuration ---------------

BASE = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
FFMPEG_PATH = os.path.join(BASE, 'ffmpeg.exe')
SETTINGS_FILE = os.path.join(BASE, 'settings.json')
DEFAULT_DOWNLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'Downloads', 'MusicDownloader')

# --------------- Utility Functions ---------------

def normalize_social_media_url(url: str) -> str:
    url = (url or '').strip()
    if not url:
        return ''

    if not re.match(r'^(https?://|www\.)', url, re.I):
        url = 'https://' + url

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith('www.'):
        host = host[4:]

    query = dict(parse_qsl(parsed.query))
    path = parsed.path

    if host == 'youtu.be':
        video_id = path.lstrip('/')
        if len(video_id) == 11:
            query['v'] = video_id
            return 'https://www.youtube.com/watch?' + urlencode(query)
        return ''

    if host in ('youtube.com', 'm.youtube.com', 'youtube-nocookie.com'):
        if path.startswith('/watch'):
            video_id = query.get('v')
            if video_id and len(video_id) == 11:
                return 'https://www.youtube.com/watch?' + urlencode(query)
        if path.startswith('/shorts/') or path.startswith('/embed/'):
            parts = path.split('/')
            if len(parts) >= 3 and len(parts[2]) == 11:
                query['v'] = parts[2]
                return 'https://www.youtube.com/watch?' + urlencode(query)
        if path.startswith('/playlist') and 'list' in query:
            return 'https://www.youtube.com/playlist?' + urlencode({'list': query['list']})
        return ''

    if host.endswith('instagram.com') or host == 'ig.me':
        return url

    if host.endswith('facebook.com') or host == 'fb.watch':
        return url

    return ''


def find_ffmpeg() -> str | None:
    if os.path.isfile(FFMPEG_PATH):
        return FFMPEG_PATH
    return shutil.which('ffmpeg')


def load_settings() -> dict:
    if os.path.isfile(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass

# --------------- Main Application ---------------

class YouTubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎵 YouTube Downloader")
        self.geometry("720x560")
        self.minsize(640, 520)
        self.resizable(True, True)
        self.configure(bg='#121212')

        # State
        self.download_folder = DEFAULT_DOWNLOAD_FOLDER
        self.video_info = None
        self.thumb_img = None
        self._fetch_after_id = None

        # Variables
        self.url_var           = tk.StringVar(self)
        self.status_var        = tk.StringVar(self, value='Paste a URL below…')
        self.progress_var      = tk.DoubleVar(self, value=0.0)
        self.playlist_var      = tk.BooleanVar(self, value=False)
        self.dl_type_var       = tk.StringVar(self, value='audio')
        self.quality_var       = tk.StringVar(self, value='192')
        self.folder_var        = tk.StringVar(self, value=self.download_folder)

        self.settings = load_settings()
        self.download_folder = self.settings.get('download_folder', self.download_folder)
        os.makedirs(self.download_folder, exist_ok=True)
        self.folder_var.set(self.download_folder)

        # Qualities
        self.audio_qualities = ['128', '192', '256', '320']
        self.video_qualities = ['highest', '1080', '720', '480', '360', '240', '144']

        self._setup_style()
        self._build_menu()
        self._build_widgets()

        # Automatically fetch when URL changes
        self.url_var.trace_add('write', self._on_url_change)

    # ----- Style -----
    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use('clam')
        s.configure('TFrame', background='#121212')
        s.configure('Header.TFrame', background='#121212')
        s.configure('Card.TFrame', background='#1d1d1d')
        s.configure('Header.TLabel', background='#121212', foreground='#ffffff', font=('Segoe UI', 18, 'bold'))
        s.configure('SubHeader.TLabel', background='#121212', foreground='#cccccc', font=('Segoe UI', 10))
        s.configure('Label.TLabel', background='#1d1d1d', foreground='#f2f2f2', font=('Segoe UI', 10))
        s.configure('Info.TLabel', background='#1d1d1d', foreground='#f0f0f0', font=('Segoe UI', 10))
        s.configure('Status.TLabel', background='#121212', foreground='#d0d0d0', font=('Segoe UI', 10))
        s.configure('TLabel', background='#121212', foreground='#f0f0f0', font=('Segoe UI', 10))
        s.configure('TEntry', fieldbackground='#2a2a2a', foreground='#ffffff', background='#2a2a2a')
        s.configure('TButton', font=('Segoe UI', 10, 'bold'), foreground='#ffffff', background='#0078d7', padding=8)
        s.map('TButton', background=[('active', '#005a9e')], foreground=[('disabled', '#888')])
        s.configure('Action.TButton', foreground='#ffffff', background='#0066cc')
        s.map('Action.TButton', background=[('active', '#005a9e')])
        s.configure('Download.TButton', foreground='#ffffff', background='#2dbe60')
        s.map('Download.TButton', background=[('active', '#27934b')])
        s.configure('Check.TCheckbutton', background='#1d1d1d', foreground='#ffffff', font=('Segoe UI', 10))

    # ----- Menu -----
    def _build_menu(self):
        menubar = tk.Menu(self)
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label='Set Download Folder…', command=self._choose_folder)
        filem.add_command(label='Open Download Folder', command=self._open_folder)
        filem.add_separator()
        filem.add_command(label='Exit', command=self.quit)
        menubar.add_cascade(label='File', menu=filem)
        self.config(menu=menubar)

    def _choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_folder)
        if folder:
            self.download_folder = folder
            self.folder_var.set(folder)
            self.status_var.set(f'Folder set to:\n{self.download_folder}')
            self.settings['download_folder'] = folder
            save_settings(self.settings)

    def _open_folder(self):
        if os.path.isdir(self.download_folder):
            os.startfile(self.download_folder)

    # ----- Layout -----
    def _build_widgets(self):
        padx, pady = 18, 10

        # Header
        header_frame = ttk.Frame(self, padding=(20, 10), style='Header.TFrame')
        header_frame.pack(fill='x')
        ttk.Label(header_frame, text='YouTube & Social Media Downloader',
                  style='Header.TLabel').pack(anchor='w')
        ttk.Label(header_frame, text='Download audio, video, Instagram reels, Facebook clips, and more.',
                  style='SubHeader.TLabel').pack(anchor='w', pady=(5,0))

        # URL Entry Frame
        entry_frame = ttk.Frame(self, relief='flat', padding=15, style='Card.TFrame')
        entry_frame.pack(fill='x', padx=padx, pady=(0, pady))
        entry_frame.columnconfigure(0, weight=1)
        entry_frame.columnconfigure(1, weight=1)
        entry_frame.columnconfigure(2, weight=1)
        entry_frame.columnconfigure(3, weight=0)

        ttk.Label(entry_frame, text='URL:', style='Label.TLabel').grid(row=0, column=0, sticky='w')
        url_entry = ttk.Entry(entry_frame, textvariable=self.url_var, font=('Segoe UI', 11))
        url_entry.grid(row=1, column=0, columnspan=3, pady=8, sticky='ew')
        url_entry.focus()
        self._install_context_menu(url_entry)

        self.fetch_btn = ttk.Button(entry_frame, text='Fetch Info', style='Action.TButton', command=self._fetch_info, state='disabled')
        self.fetch_btn.grid(row=1, column=3, padx=(10,0), sticky='n')
        self.url_var.trace_add('write', self._update_fetch_button)

        ttk.Label(entry_frame, text='Save to folder:', style='Label.TLabel').grid(row=2, column=0, sticky='w', pady=(10,0))
        folder_entry = ttk.Entry(entry_frame, textvariable=self.folder_var, font=('Segoe UI', 10))
        folder_entry.grid(row=3, column=0, columnspan=3, sticky='ew', pady=5)
        ttk.Button(entry_frame, text='Browse', style='Action.TButton', command=self._choose_folder).grid(row=3, column=3, padx=(10,0), sticky='n')

        # Info Display Frame
        self.info_frame = ttk.Frame(self, style='Card.TFrame', padding=15)
        self.info_frame.pack(fill='both', expand=True, padx=padx, pady=(0, pady))
        self.info_frame.columnconfigure(1, weight=1)

        self.thumb_label   = ttk.Label(self.info_frame, background='#1e1e1e')
        self.thumb_label.grid(row=0, column=0, rowspan=3, padx=(0,15), sticky='nsew')
        self.title_label   = ttk.Label(self.info_frame, text='', style='Info.TLabel', wraplength=460)
        self.title_label.grid(row=0, column=1, sticky='nw')
        self.author_label  = ttk.Label(self.info_frame, text='', style='Info.TLabel')
        self.author_label.grid(row=1, column=1, sticky='nw', pady=(6,0))
        self.duration_label= ttk.Label(self.info_frame, text='', style='Info.TLabel')
        self.duration_label.grid(row=2, column=1, sticky='nw', pady=(6,0))

        # Options Frame
        opts = ttk.Frame(self, padding=15, style='Card.TFrame')
        opts.pack(fill='x', padx=padx, pady=(0, pady))
        opts.columnconfigure(0, weight=1)
        opts.columnconfigure(1, weight=0)
        opts.columnconfigure(2, weight=0)
        opts.columnconfigure(3, weight=0)
        opts.columnconfigure(4, weight=0)

        ttk.Checkbutton(opts, text='Download Playlist', variable=self.playlist_var, style='Check.TCheckbutton').grid(row=0, column=0, sticky='w')
        ttk.Label(opts, text='Type:', style='Label.TLabel').grid(row=0, column=1, padx=(20,5), sticky='e')
        type_cb = ttk.Combobox(opts, width=10, state='readonly', textvariable=self.dl_type_var, values=['audio','video'])
        type_cb.grid(row=0, column=2, sticky='w')
        ttk.Label(opts, text='Quality:', style='Label.TLabel').grid(row=0, column=3, padx=(20,5), sticky='e')
        self.quality_cb = ttk.Combobox(opts, width=10, state='readonly', textvariable=self.quality_var, values=self.audio_qualities)
        self.quality_cb.grid(row=0, column=4, sticky='w')
        self.dl_type_var.trace_add('write', self._on_type_change)

        # Download Button
        self.download_btn = ttk.Button(self, text='⬇ Start Download', style='Download.TButton', command=self._start_download, state='disabled')
        self.download_btn.pack(fill='x', padx=padx, pady=(10,5))

        # Progress & Status
        progress_frame = ttk.Frame(self, padding=(0,0,0,10), style='Card.TFrame')
        progress_frame.pack(fill='x', padx=padx)
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill='x', padx=5, pady=(10,5))
        ttk.Label(progress_frame, textvariable=self.status_var, style='Status.TLabel', wraplength=680).pack(anchor='w')

    def _install_context_menu(self, widget):
        menu = tk.Menu(self, tearoff=0)
        for lbl, evt in [('Cut','<<Cut>>'),('Copy','<<Copy>>'),('Paste','<<Paste>>')]:
            menu.add_command(label=lbl, command=lambda e=evt: widget.event_generate(e))
        widget.bind('<Button-3>', lambda e: menu.tk_popup(e.x_root,e.y_root))

    # ----- Auto-Fetch Logic -----
    def _on_url_change(self, *args):
        if self._fetch_after_id:
            self.after_cancel(self._fetch_after_id)
        self._fetch_after_id = self.after(800, self._auto_fetch_if_valid)

    def _auto_fetch_if_valid(self):
        url = self.url_var.get().strip()
        if normalize_social_media_url(url):
            self.fetch_btn.config(state='normal')
            self.status_var.set('Ready to fetch video info')
        else:
            self.fetch_btn.config(state='disabled')
            self.status_var.set('Enter a valid YouTube, Instagram, or Facebook URL…')

    def _update_fetch_button(self, *args):
        url = self.url_var.get().strip()
        if normalize_social_media_url(url):
            self.fetch_btn.config(state='normal')
        else:
            self.fetch_btn.config(state='disabled')

    # ----- Metadata Fetch -----
    def _fetch_info(self):
        url = self.url_var.get().strip()
        if not url:
            self.status_var.set('Enter a valid URL…')
            return

        self.status_var.set('Fetching info…')
        self.download_btn.config(state='disabled')

        def worker():
            try:
                info = self._extract_info(url)
                self.video_info = info
                self._display_info(info)
                self.status_var.set('Info loaded — ready to download')
                self.download_btn.config(state='normal')
            except Exception as e:
                self.status_var.set('Error fetching info')
                messagebox.showerror('Fetch Error', str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _extract_info(self, url):
        normalized = normalize_social_media_url(url)
        opts = {'quiet': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(normalized, download=False)

    def _display_info(self, info):
        title  = info.get('title','Unknown Title')
        author = info.get('uploader','Unknown')
        dur    = info.get('duration')
        dur_str= f"{int(dur//60)}:{int(dur%60):02d}" if dur else 'N/A'
        self.title_label.config(text=title)
        self.author_label.config(text=f'By: {author}')
        self.duration_label.config(text=f'Duration: {dur_str}')

        thumb_url = info.get('thumbnail')
        if thumb_url:
            try:
                data = requests.get(thumb_url, timeout=5).content
                im = Image.open(io.BytesIO(data)).resize((140, 100))
                self.thumb_img = ImageTk.PhotoImage(im)
                self.thumb_label.config(image=self.thumb_img, text='')
            except Exception:
                self.thumb_label.config(image='', text='No Thumbnail')
        else:
            self.thumb_label.config(image='', text='No Thumbnail')

    # ----- Download -----
    def _on_type_change(self, *args):
        if self.dl_type_var.get() == 'audio':
            self.quality_cb['values'] = self.audio_qualities
            self.quality_var.set(self.audio_qualities[1])
        else:
            self.quality_cb['values'] = self.video_qualities
            self.quality_var.set(self.video_qualities[0])

    def _start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror('Invalid URL', 'Please enter a valid URL.')
            self.status_var.set('Enter a valid URL…')
            return

        normalized_url = normalize_social_media_url(url)
        if not normalized_url:
            messagebox.showerror('Invalid URL', 'Please enter a supported YouTube, Instagram, or Facebook URL.')
            self.status_var.set('Enter a valid URL…')
            return

        opts = {
            'playlist': self.playlist_var.get(),
            'dl_type': self.dl_type_var.get(),
            'quality': self.quality_var.get()
        }

        ffmpeg_exe = find_ffmpeg()
        if opts['dl_type'] == 'audio' and not ffmpeg_exe:
            self.status_var.set('No ffmpeg found; downloading audio in original stream format.')

        self.download_folder = self.folder_var.get().strip() or self.download_folder
        self.settings['download_folder'] = self.download_folder
        save_settings(self.settings)
        self.download_btn.config(state='disabled', text='Downloading…')
        self.status_var.set('Starting download…')
        self.progress_var.set(0.0)

        def worker():
            try:
                os.makedirs(self.download_folder, exist_ok=True)
                base_opts = {
                    'outtmpl': os.path.join(self.download_folder, '%(title)s.%(ext)s'),
                    'restrictfilenames': True,
                    'noplaylist': not opts['playlist'],
                    'progress_hooks':[self._progress_hook]
                }
                if ffmpeg_exe:
                    base_opts['ffmpeg_location'] = ffmpeg_exe

                is_social = any(h in normalized_url for h in ('instagram.com','fb.watch','facebook.com','youtu.be','youtube.com'))
                if opts['dl_type']=='audio':
                    ydl_opts = {
                        **base_opts,
                        'format': 'bestaudio/best',
                    }
                    if ffmpeg_exe:
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': opts['quality'],
                        }]
                    else:
                        self.status_var.set('No ffmpeg found; downloading audio in original stream format.')
                else:
                    q = opts['quality']
                    if ffmpeg_exe:
                        fmt = 'bestvideo+bestaudio/best' if q=='highest' else f'bestvideo[height<={q}]+bestaudio/best'
                    else:
                        fmt = 'best' if q=='highest' else f'best[height<={q}]/best'
                        self.status_var.set('No ffmpeg found; downloading video without merging. Quality may vary.')
                    ydl_opts = {
                        **base_opts,
                        'format': fmt,
                    }
                if 'instagram.com' in normalized_url or 'fb.watch' in normalized_url or 'facebook.com' in normalized_url:
                    ydl_opts['no_warnings'] = True
                    ydl_opts['concurrent_fragment_downloads'] = 4
                    ydl_opts['retries'] = 5
                    ydl_opts['http_chunk_size'] = 1048576

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([normalized_url])

                self.status_var.set('✅ Download complete!')
                self.progress_var.set(100.0)
                self.download_btn.config(text='⬇ Start Download')
                webbrowser.open(self.download_folder)
            except Exception as e:
                self.status_var.set('❌ Download failed')
                self.progress_var.set(0.0)
                self.download_btn.config(text='⬇ Start Download')
                messagebox.showerror('Download Error', str(e))
            finally:
                self.download_btn.config(state='normal')

        threading.Thread(target=worker, daemon=True).start()

    def _progress_hook(self, d):
        if d['status']=='downloading':
            p = d.get('_percent_str','0%').strip().replace('%','')
            try:
                val = float(p)
                self.progress_var.set(val)
                self.status_var.set(f'Downloading… {p}%')
                self.download_btn.config(text=f'⬇ {int(val)}%')
            except:
                pass
        elif d['status']=='finished':
            self.status_var.set('Merging/Converting…')
            self.progress_var.set(100.0)
            self.download_btn.config(text='⬇ Finalizing...')

# --------------- Run ---------------

if __name__ == '__main__':
    app = YouTubeDownloader()
    app.mainloop()
