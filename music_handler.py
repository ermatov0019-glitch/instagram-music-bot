import asyncio
import os
try:
    from ShazamAPI import Shazam
    SHAZAM_AVAILABLE = True
except ImportError:
    SHAZAM_AVAILABLE = False

async def identify_music(file_path: str):
    """
    Identifies music using ShazamAPI (Pure Python version).
    """
    if not SHAZAM_AVAILABLE:
        return {'success': False, 'message': "Kechirasiz, ushbu serverda Shazam funksiyasi vaqtincha o'chirilgan. 🔍"}
    
    if not os.path.exists(file_path):
        return {'success': False, 'message': "Fayl topilmadi. ❌"}

    try:
        # ShazamAPI synchronous bo'lgani uchun uni thread-da ishlatamiz
        with open(file_path, 'rb') as f:
            content = f.read()
        
        shazam = Shazam(content)
        recognize_generator = shazam.recognizeSong()
        
        # Birinchi natijani olamiz
        try:
            res = next(recognize_generator)
            # res -> (offset, data)
            data = res[1]
            
            if data and 'track' in data:
                return parse_track_data(data['track'])
            
            return {'success': False, 'message': "Musiqa topilmadi. 😔"}
        except StopIteration:
            return {'success': False, 'message': "Musiqa topilmadi. 😔"}
            
    except Exception as e:
        print(f"ShazamAPI Error: {e}")
        return {'success': False, 'message': "Xatolik yuz berdi. ❌"}

def parse_track_data(track):
    title = track.get('title', 'Noma\'lum')
    subtitle = track.get('subtitle', 'Noma\'lum')
    url = track.get('url', '')
    
    # Metadata
    metadata = {}
    for item in track.get('sections', []):
        if item.get('type') == 'SONG':
            for meta in item.get('metadata', []):
                metadata[meta.get('title')] = meta.get('text')
    
    album = metadata.get('Album', 'Noma\'lum')
    released = metadata.get('Released', 'Noma\'lum')
    genres = track.get('genres', {}).get('primary', 'Noma\'lum')
    
    # Images
    images = track.get('images', {})
    cover = images.get('coverarthq') or images.get('coverart')
    
    # Lyrics
    lyrics = None
    for section in track.get('sections', []):
        if section.get('type') == 'LYRICS':
            lyrics = "\n".join(section.get('text', []))
            break

    # Songlink
    songlink = f"https://song.link/s/{track.get('key')}" if track.get('key') else url

    return {
        'success': True,
        'title': title,
        'artist': subtitle,
        'album': album,
        'released': released,
        'genre': genres,
        'url': url,
        'songlink': songlink,
        'cover': cover,
        'lyrics': lyrics
    }
