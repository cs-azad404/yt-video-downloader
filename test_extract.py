import yt_dlp

url = 'https://youtu.be/xVe-Qa8mNr4'
opts = {'skip_download': True, 'quiet': True}
with yt_dlp.YoutubeDL(opts) as ydl:
    info = ydl.extract_info(url, download=False)
    print('TITLE:', info.get('title'))
    print('ID:', info.get('id'))
    formats = info.get('formats') or []
    print('FORMATS:', len(formats))
    # print a few formats
    for f in formats[:5]:
        print(f"format_id={f.get('format_id')} ext={f.get('ext')} vcodec={f.get('vcodec')} acodec={f.get('acodec')}")
