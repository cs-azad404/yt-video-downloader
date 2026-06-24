import io
import os
import re
import sys
import threading
import webbrowser
import requests
import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
from urllib.parse import parse_qsl, urlencode, urlparse

# --------------- Configuration ---------------

BASE = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
FFMPEG_PATH = os.path.join(BASE, 'ffmpeg.exe')
DEFAULT_DOWNLOAD_FOLDER = os.path.join(BASE, 'downloads')

# --------------- Utility Functions ---------------

def normalize_youtube_url(url: str) -> str:
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

    if host in ('youtube.com', 'm.youtube.com'):
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

# --------------- Main Application ---------------

class YouTubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎵 YouTube Downloader")
        self.geometry("650x520")
        self.resizable(False, False)
        self.configure(bg='#f0f0f0')

        # State
        self.download_folder = DEFAULT_DOWNLOAD_FOLDER
        os.makedirs(self.download_folder, exist_ok=True)
        self.video_info = None
        self.thumb_img = None
        self._fetch_after_id = None

        # Variables
        self.url_var           = tk.StringVar(self)
        self.status_var        = tk.StringVar(self, value='Paste a YouTube URL below…')
        self.progress_var      = tk.DoubleVar(self, value=0.0)
        self.playlist_var      = tk.BooleanVar(self, value=False)
        self.dl_type_var       = tk.StringVar(self, value='audio')
        self.quality_var       = tk.StringVar(self, value='192')

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
        s.configure('TFrame',    background='#f0f0f0')
        s.configure('Header.TLabel', background='#f0f0f0',
                    font=('Segoe UI', 16, 'bold'))
        s.configure('TLabel',    background='#f0f0f0', font=('Segoe UI', 10))
        s.configure('Info.TLabel', background='#ffffff', font=('Segoe UI', 10))
        s.configure('TButton',   font=('Segoe UI', 10, 'bold'),
                    foreground='#fff', background='#0078d7')
        s.map('TButton',
              background=[('active', '#005a9e')],
              foreground=[('disabled', '#888')])
        s.configure('Download.TButton', background='#28a745')
        s.map('Download.TButton',
              background=[('active', '#1e7e34')])

    # ----- Menu -----
    def _build_menu(self):
        menubar = tk.Menu(self)
        filem = tk.Menu(menubar, tearoff=0)
        filem.add_command(label='Set Download Folder…', command=self._choose_folder)
        filem.add_separator()
        filem.add_command(label='Exit', command=self.quit)
        menubar.add_cascade(label='File', menu=filem)
        self.config(menu=menubar)

    def _choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_folder)
        if folder:
            self.download_folder = folder
            self.status_var.set(f'Folder set to:\n{self.download_folder}')

    # ----- Layout -----
    def _build_widgets(self):
        padx, pady = 15, 8

        # Header
        ttk.Label(self, text='YouTube Audio/Video Downloader',
                  style='Header.TLabel').pack(pady=(20, 5))

        # URL Entry Frame
        entry_frame = ttk.Frame(self, relief='solid', padding=10)
        entry_frame.pack(fill='x', padx=padx, pady=(0, pady))
        ttk.Label(entry_frame, text='YouTube URL:').pack(anchor='w')
        url_entry = ttk.Entry(entry_frame, textvariable=self.url_var, font=('Segoe UI', 11))
        url_entry.pack(fill='x', pady=5)
        url_entry.focus()
        # right-click menu
        self._install_context_menu(url_entry)

        # Info Display Frame
        self.info_frame = ttk.Frame(self, style='Info.TLabel', padding=10, relief='solid')
        self.info_frame.pack(fill='x', padx=padx, pady=(0, pady))
        self.thumb_label   = ttk.Label(self.info_frame, background='#ffffff')
        self.thumb_label.grid(row=0, column=0, rowspan=3, padx=(0,10))
        self.title_label   = ttk.Label(self.info_frame, text='', style='Info.TLabel', wraplength=450)
        self.title_label.grid(row=0, column=1, sticky='w')
        self.author_label  = ttk.Label(self.info_frame, text='', style='Info.TLabel')
        self.author_label.grid(row=1, column=1, sticky='w')
        self.duration_label= ttk.Label(self.info_frame, text='', style='Info.TLabel')
        self.duration_label.grid(row=2, column=1, sticky='w')

        # Options Frame
        opts = ttk.Frame(self, padding=10)
        opts.pack(fill='x', padx=padx, pady=(0, pady))
        ttk.Checkbutton(opts, text='Full Playlist',
                        variable=self.playlist_var).grid(row=0, column=0, sticky='w')
        ttk.Label(opts, text='Type:').grid(row=0, column=1, padx=(20,5))
        type_cb = ttk.Combobox(opts, width=8, state='readonly',
                               textvariable=self.dl_type_var,
                               values=['audio','video'])
        type_cb.grid(row=0, column=2)
        ttk.Label(opts, text='Quality:').grid(row=0, column=3, padx=(20,5))
        self.quality_cb = ttk.Combobox(opts, width=8, state='readonly',
                                       textvariable=self.quality_var,
                                       values=self.audio_qualities)
        self.quality_cb.grid(row=0, column=4)
        self.dl_type_var.trace_add('write', self._on_type_change)

        # Download Button
        self.download_btn = ttk.Button(self, text='⬇ Download',
                                       style='Download.TButton',
                                       command=self._start_download,
                                       state='disabled')
        self.download_btn.pack(pady=(5,20))

        # Progress & Status
        ttk.Progressbar(self, mode='determinate', length=580,
                        variable=self.progress_var,
                        maximum=100).pack(padx=padx)
        ttk.Label(self, textvariable=self.status_var,
                  wraplength=580).pack(pady=(10,5))

    def _install_context_menu(self, widget):
        menu = tk.Menu(self, tearoff=0)
        for lbl, evt in [('Cut','<<Cut>>'),('Copy','<<Copy>>'),('Paste','<<Paste>>')]:
            menu.add_command(label=lbl, command=lambda e=evt: widget.event_generate(e))
        widget.bind('<Button-3>', lambda e: menu.tk_popup(e.x_root,e.y_root))

    # ----- Auto-Fetch Logic -----
    def _on_url_change(self, *args):
        if self._fetch_after_id:
            self.after_cancel(self._fetch_after_id)
        # delay fetch by 800ms to allow paste completion
        self._fetch_after_id = self.after(800, self._auto_fetch_if_valid)

    def _auto_fetch_if_valid(self):
        url = self.url_var.get().strip()
        if normalize_youtube_url(url):
            self._fetch_info()
        else:
            self.status_var.set('Enter a valid YouTube URL…')

    # ----- Metadata Fetch -----
    def _fetch_info(self):
        url = normalize_youtube_url(self.url_var.get())
        if not url:
            self.status_var.set('Enter a valid YouTube URL…')
            return
        self.status_var.set('Fetching video info…')
        self.download_btn.config(state='disabled')

        def worker():
            try:
                opts = {'quiet': True, 'skip_download': True}
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                self.video_info = info
                self._display_info(info)
                self.status_var.set('Info loaded — ready to download')
                self.download_btn.config(state='normal')
            except Exception as e:
                self.status_var.set('Error fetching info')
                messagebox.showerror('Fetch Error', str(e))

        threading.Thread(target=worker, daemon=True).start()

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
        url = normalize_youtube_url(self.url_var.get())
        if not url:
            messagebox.showerror('Invalid URL', 'Please enter a valid YouTube video or playlist URL.')
            self.status_var.set('Enter a valid YouTube URL…')
            return

        if not os.path.isfile(FFMPEG_PATH):
            messagebox.showerror('Missing ffmpeg', 'ffmpeg.exe was not found in the application folder.')
            self.status_var.set('ffmpeg.exe not found')
            return

        opts = {
            'playlist': self.playlist_var.get(),
            'dl_type': self.dl_type_var.get(),
            'quality': self.quality_var.get()
        }
        self.download_btn.config(state='disabled')
        self.status_var.set('Starting download…')
        self.progress_var.set(0.0)

        def worker():
            try:
                os.makedirs(self.download_folder, exist_ok=True)
                base_opts = {
                    'outtmpl': os.path.join(self.download_folder, '%(title)s.%(ext)s'),
                    'ffmpeg_location': FFMPEG_PATH,
                    'restrictfilenames': True,
                    'noplaylist': not opts['playlist'],
                    'progress_hooks':[self._progress_hook]
                }

                if opts['dl_type']=='audio':
                    ydl_opts = {
                        **base_opts,
                        'format': 'bestaudio/best',
                        'postprocessors':[{
                            'key':'FFmpegExtractAudio',
                            'preferredcodec':'mp3',
                            'preferredquality':opts['quality'],
                        }]
                    }
                else:
                    q = opts['quality']
                    fmt = 'bestvideo+bestaudio/best' if q=='highest' else f'bestvideo[height<={q}]+bestaudio/best'
                    ydl_opts = {
                        **base_opts,
                        'format': fmt
                    }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                self.status_var.set('✅ Download complete!')
                webbrowser.open(self.download_folder)
            except Exception as e:
                self.status_var.set('❌ Download failed')
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
            except:
                pass
        elif d['status']=='finished':
            self.status_var.set('Merging/Converting…')
            self.progress_var.set(100.0)

# --------------- Run ---------------

if __name__ == '__main__':
    app = YouTubeDownloader()
    app.mainloop()
