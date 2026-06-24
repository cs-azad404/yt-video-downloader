import os
import yt_dlp

url = 'https://youtu.be/xVe-Qa8mNr4'
output_dir = 'downloads'
os.makedirs(output_dir, exist_ok=True)
ffmpeg_path = os.path.join(os.getcwd(), 'ffmpeg.exe')

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': os.path.join(output_dir, '%(title)s - %(id)s.%(ext)s'),
    'restrictfilenames': True,
    'noplaylist': True,
    'quiet': False,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'ffmpeg_location': ffmpeg_path,
}

print('Starting download test...')
try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.download([url])
        print('ydl.download returned:', result)
except Exception as e:
    print('Download failed:', repr(e))
else:
    # List files in downloads
    files = os.listdir(output_dir)
    print('Files in', output_dir, ':')
    for f in files:
        print('-', f)
