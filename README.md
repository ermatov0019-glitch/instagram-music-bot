# 🤖 Instagram Music & Video Downloader Bot

Ushbu bot Instagram, TikTok va YouTube-dan media fayllarni yuklash, musiqalarni Shazam orqali aniqlash va ularning to'liq versiyasini topish imkoniyatiga ega professional Telegram botdir.

## ✨ Imkoniyatlar

- 🎬 **Video yuklash**: Instagram (Reels, Posts), TikTok va YouTube-dan yuqori sifatli videolarni yuklash.
- 🎵 **Musiqani ajratish**: Videolardagi audio qismini alohida yuklab olish.
- 🔍 **Shazam Integratsiyasi**: Videodagi musiqani aniqlash va albom, janr, yil kabi ma'lumotlarni ko'rsatish.
- 🎼 **To'liq Versiya**: Aniqlangan musiqaning to'liq versiyasini (YouTube Search orqali) topib berish.
- 📑 **Qo'shiq Matni (Lyrics)**: Musiqa so'zlarini topish va AI yordamida o'zbek tiliga tarjima qilish.
- 🧠 **AI Yordamchi**: Gemini yoki Groq AI orqali foydalanuvchilar bilan muloqot qilish.
- 🛠 **Avtomatik FFmpeg**: Serverda FFmpeg bo'lmasa, bot uni o'zi avtomatik sozlab oladi.

## 🚀 O'rnatish va Ishga tushirish

1. **Repozitoriyani klonlash**:
   ```bash
   git clone https://github.com/ermatov0019-glitch/instagram-music-bot.git
   cd instagram-music-bot
   ```

2. **Kutubxonalarni o'rnatish**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Muhit o'zgaruvchilarini sozlash (.env)**:
   `.env` faylini yarating va quyidagilarni kiriting:
   ```env
   BOT_TOKEN=Sizning_Bot_Tokeningiz
   GEMINI_API_KEY=Sizning_Gemini_API_Keyingiz
   GROQ_API_KEY=Sizning_Groq_API_Keyingiz (Ixtiyoriy)
   ```

4. **Botni ishga tushirish**:
   ```bash
   python main.py
   ```

## 🛠 Texnologiyalar

- **Python** (aiogram 3.x)
- **yt-dlp** (Media yuklash uchun)
- **Shazamio** (Musiqa aniqlash uchun)
- **Google Generative AI** & **Groq** (Sun'iy intellekt)
- **imageio-ffmpeg** (FFmpeg boshqaruvi)

## 📝 Muallif

- **Ermatov Ilyosbek** - [@ermatov_ilyosbek](https://t.me/ermatov_ilyosbek)

---
⭐️ Agar loyiha sizga yoqqan bo'lsa, GitHub-da "Star" bosing!
