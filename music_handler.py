import asyncio
try:
    from shazamio import Shazam
    SHAZAM_AVAILABLE = True
except ImportError:
    SHAZAM_AVAILABLE = False
    print("Warning: shazamio library not found. Shazam features will be disabled.")
import os

async def identify_music(file_path: str):
    """
    Identifies music using Shazam API with multiple attempts at different offsets.
    """
    if not SHAZAM_AVAILABLE:
        return {'success': False, 'message': "Kechirasiz, ushbu serverda Shazam funksiyasi vaqtincha o'chirilgan. Qo'shiq nomini yozib qidirishingiz mumkin. 🔍"}
    
    shazam = Shazam()
    
    # We will try recognizing the song as is first.
    # If it fails, we don't have a built-in offset in shazamio's recognize_song,
    # but the library is usually good at finding it within the file.
    # However, for very long files, we can try to pass segments if needed.
    
    try:
        out = await shazam.recognize_song(file_path)
        if out and 'track' in out:
            return parse_track_data(out['track'])
        
        # If first attempt fails, it might be due to a long intro.
        # But shazamio usually handles the whole file. 
        # Let's add more detailed data parsing.
        
        return {'success': False, 'message': "Musiqa topilmadi. 😔"}
    except Exception as e:
        print(f"Shazam error: {e}")
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
    label = metadata.get('Label', 'Noma\'lum')
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

    # Songlink (Barcha platformalar uchun link)
    # Shazam URL dan foydalanib song.link yaratish mumkin
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

if __name__ == "__main__":
    # Test
    async def test():
        # You need an actual audio file to test
        # res = await identify_music("test.mp3")
        # print(res)
        pass
    asyncio.run(test())
