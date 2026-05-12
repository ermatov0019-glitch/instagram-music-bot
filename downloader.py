import yt_dlp
import os
import uuid

# Create downloads directory if not exists
DOWNLOADS_DIR = "downloads"
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)

def get_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None

def download_media(url: str, audio_only: bool = False):
    """
    Downloads media from various platforms.
    If audio_only is True, downloads best audio and converts to mp3.
    """
    unique_id = str(uuid.uuid4())[:8]
    suffix = "audio" if audio_only else "video"
    output_template = os.path.join(DOWNLOADS_DIR, f"media_{unique_id}_{suffix}_%(autonumber)03d.%(ext)s")
    
    ffmpeg_path = get_ffmpeg()
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'writethumbnail': True, # Download thumbnail for better quality preview
        'noplaylist': True,
        'merge_output_format': 'mp4', # Ensure output is mp4
        'ffmpeg_location': ffmpeg_path,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios'],
                'skip': ['hls', 'dash'],
            }
        }
    }

    if audio_only:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOADS_DIR, f"audio_{unique_id}.%(ext)s"),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best', # Fetch best streams
            'outtmpl': output_template,
        })

    # Cookie strategy
    cookies_path = "cookies.txt"
    if os.path.exists(cookies_path):
        ydl_opts['cookiefile'] = cookies_path
    
    downloaded_files = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Find the actual files created
            # yt-dlp might change extensions during post-processing
            search_pattern = f"audio_{unique_id}" if audio_only else f"media_{unique_id}"
            
            for f in os.listdir(DOWNLOADS_DIR):
                if f.startswith(search_pattern):
                    downloaded_files.append(os.path.join(DOWNLOADS_DIR, f))
            
            return list(set(downloaded_files))
    except Exception as e:
        error_msg = str(e)
        print(f"Error downloading media: {error_msg}")
        if "login required" in error_msg.lower() or "sign in" in error_msg.lower():
             return "COOKIE_REQUIRED"
        if "rate-limit" in error_msg.lower():
             return "RATE_LIMITED"
        return []

def search_and_download_music(query: str):
    """
    Searches for a song on SoundCloud and downloads the best audio.
    SoundCloud is generally more bot-friendly than YouTube.
    """
    unique_id = str(uuid.uuid4())[:8]
    output_template = os.path.join(DOWNLOADS_DIR, f"full_audio_{unique_id}.%(ext)s")
    
    ffmpeg_path = get_ffmpeg()
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'ffmpeg_location': ffmpeg_path,
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'scsearch1', # SoundCloud search
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        }
    }

    # Cookies strategy
    cookies_path = "cookies.txt"
    if os.path.exists(cookies_path):
        ydl_opts['cookiefile'] = cookies_path

    downloaded_files = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First attempt: SoundCloud
            print(f"Searching on SoundCloud: {query}")
            ydl.params['default_search'] = 'scsearch1'
            try:
                ydl.download([f"scsearch1:{query}"])
            except Exception as e:
                print(f"SoundCloud search error: {e}")
            
            # Check if downloaded
            downloaded = [f for f in os.listdir(DOWNLOADS_DIR) if f.startswith(f"full_audio_{unique_id}")]
            
            # Second attempt: YouTube (fallback)
            if not downloaded:
                print(f"Not found on SoundCloud, searching on YouTube: {query}")
                ydl.params['default_search'] = 'ytsearch1'
                try:
                    ydl.download([f"ytsearch1:{query}"])
                except Exception as e:
                    print(f"YouTube search error: {e}")
            
            for f in os.listdir(DOWNLOADS_DIR):
                if f.startswith(f"full_audio_{unique_id}"):
                    downloaded_files.append(os.path.join(DOWNLOADS_DIR, f))
            
            return list(set(downloaded_files))
    except Exception as e:
        print(f"Search total error: {e}")
        return []

def cleanup_files(filepaths: list):
    for filepath in filepaths:
        try:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Error deleting file {filepath}: {e}")
