import asyncio
import os
import logging
import uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    FSInputFile, 
    InputMediaPhoto, 
    InputMediaVideo, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    WebAppInfo, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    MenuButtonWebApp,
    BotCommand,
    BotCommandScopeChat
)
from dotenv import load_dotenv

from downloader import download_media, cleanup_files, search_and_download_music
from ai_handler import get_ai_response
from music_handler import identify_music
import database as db

# Temporary storage for URLs and broadcast state
url_cache = {}
admin_state = {}

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID") # Add your Telegram ID here
# Mini App havolasi    # YouTube Mobil havolasi
WEBAPP_URL = "https://m.youtube.com/" 

# Setup logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """
    Handle the /start command.
    """
    # Register user
    db.add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    
    # Set Commands for Admin
    if str(message.from_user.id) == str(ADMIN_ID):
        admin_cmds = [
            BotCommand(command="start", description="Botni qayta tushirish"),
            BotCommand(command="search", description="Musiqa qidirish"),
            BotCommand(command="admin", description="Boshqaruv paneli")
        ]
        await bot.set_my_commands(commands=admin_cmds, scope=BotCommandScopeChat(chat_id=message.from_user.id))
    else:
        user_cmds = [
            BotCommand(command="start", description="Botni qayta tushirish"),
            BotCommand(command="search", description="Musiqa qidirish")
        ]
        try:
            await bot.set_my_commands(commands=user_cmds, scope=BotCommandScopeChat(chat_id=message.from_user.id))
        except: pass

    # Mini App Button
    try:
        await bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(text="Mini App", web_app=WebAppInfo(url=WEBAPP_URL))
        )
    except Exception as e:
        logging.error(f"Menu button error: {e}")

    # Keyboards
    if str(message.from_user.id) == str(ADMIN_ID):
        # Admin Keyboard
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Mini App-ni ochish", web_app=WebAppInfo(url=WEBAPP_URL))],
                [KeyboardButton(text="🛠 Boshqaruv Paneli"), KeyboardButton(text="👨‍💻 Admin bilan bog'lanish")]
            ],
            resize_keyboard=True
        )
    else:
        # User Keyboard
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Mini App-ni ochish", web_app=WebAppInfo(url=WEBAPP_URL))],
                [KeyboardButton(text="👨‍💻 Admin bilan bog'lanish")]
            ],
            resize_keyboard=True
        )

    welcome_text = (
        f"Salom, {message.from_user.full_name}! 👋\n\n"
        "Men Instagram, TikTok va YouTube-dan media yuklovchi botman.\n"
        "Link yuboring va men sizga video yoki musiqasini topib beraman. 🎬🎵\n\n"
        "Bundan tashqari, men bilan shunchaki suhbatlashishingiz ham mumkin! 🧠"
    )
    if str(message.from_user.id) == str(ADMIN_ID):
        welcome_text += "\n\nSiz adminsiz! /admin buyrug'ini ishlatishingiz mumkin."
    
    await message.answer(welcome_text, reply_markup=reply_markup)
    
    # Inline button for contact
    inline_contact = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👨‍💻 Admin bilan bog'lanish", url="https://t.me/ermatov004")]
    ])
    await message.answer("Agarda yordam kerak bo'lsa, admin bilan bog'lanishingiz mumkin:", reply_markup=inline_contact)

@dp.message(F.text == "👨‍💻 Admin bilan bog'lanish")
async def contact_admin_handler(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Habar yuborish", url="https://t.me/ermatov004")]
    ])
    await message.answer("Sizda biron savol yoki taklif bormi? Admin bilan bog'laning: 👇", reply_markup=kb)

@dp.message(F.text == "🛠 Boshqaruv Paneli")
@dp.message(Command("admin"))
async def admin_command(message: types.Message):
    """
    Admin panel menu.
    """
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    count = db.get_user_count()
    kb = [
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=kb)
    
    await message.answer(f"🔧 **Boshqaruv Paneli**\n\n📊 Foydalanuvchilar: `{count}` ta\n📅 Status: `Faol`", reply_markup=reply_markup, parse_mode="Markdown")

@dp.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: types.CallbackQuery):
    count = db.get_user_count()
    await callback.answer(f"Botdan {count} ta foydalanuvchi ro'yxatdan o'tgan.", show_alert=True)

@dp.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: types.CallbackQuery):
    admin_state[callback.from_user.id] = "waiting_broadcast"
    await callback.message.answer("Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni kiriting (matn, rasm yoki video):")
    await callback.answer()

@dp.message(lambda message: admin_state.get(message.from_user.id) == "waiting_broadcast")
async def process_broadcast(message: types.Message):
    admin_state.pop(message.from_user.id, None)
    users = db.get_all_users()
    
    status = await message.answer(f"Xabar {len(users)} ta foydalanuvchi-ga yuborilmoqda... ⏳")
    
    count = 0
    for user_id in users:
        try:
            await message.copy_to(chat_id=user_id)
            count += 1
            await asyncio.sleep(0.05) # Rate limit protection
        except Exception:
            pass
            
    await status.edit_text(f"Xabar {count} ta foydalanuvchiga muvaffaqiyatli yuborildi! ✅")
    
    # 3. Inline tugma
    inline_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Mini App-ga kirish", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    
    await message.answer(
        "Salom! 👋\n\nMen **Instagram, TikTok** va **YouTube** videolarini yuklab beruvchi hamda **Gemini AI** yordamchingizman.\n\n"
        "Pastdagi tugmalar orqali botning maxsus Mini App interfeysiga kirishingiz mumkin:",
        reply_markup=reply_markup
    )
    # Shuningdek Inline tugmani ham yuborib qo'yamiz
    await message.answer("Siz uchun qulay usulni tanlang:", reply_markup=inline_markup)

@dp.message(F.web_app_data)
async def handle_webapp_data(message: types.Message):
    """
    Mini App dan yuborilgan linkni qabul qilish va yuklash
    """
    url = message.web_app_data.data
    # Linkni oddiy link handleriga yo'naltiramiz
    await message.answer(f"Mini App-dan havola qabul qilindi... 🚀")
    
    # handle_link funksiyasiga o'xshash mantiq
    status_message = await message.answer("Media tayyorlanmoqda... ⏳")
    try:
        file_paths = await asyncio.to_thread(download_media, url)
        if file_paths == "COOKIE_REQUIRED":
            await status_message.edit_text("Xatolik: Instagram/YouTube cookies talab qilmoqda. 🔒\nIltimos, cookies.txt faylini yangilang.")
            return
        if file_paths == "RATE_LIMITED":
            await status_message.edit_text("Xatolik: IP manzil bloklangan (Rate-limit). ⏳\nBirozdan so'ng qayta urinib ko'ring.")
            return

        if file_paths:
            media_group = []
            for path in file_paths:
                ext = path.lower().split('.')[-1]
                if ext in ['mp4', 'mov', 'mkv', 'webm']:
                    media_group.append(InputMediaVideo(media=FSInputFile(path)))
                elif ext in ['jpg', 'jpeg', 'png', 'webp', 'heic']:
                    media_group.append(InputMediaPhoto(media=FSInputFile(path)))
            
            if media_group:
                if len(media_group) > 1:
                    await message.answer_media_group(media=media_group[:10])
                else:
                    item = media_group[0]
                    if isinstance(item, InputMediaVideo):
                        await message.answer_video(item.media, caption="Tayyor! ✅")
                    else:
                        await message.answer_photo(item.media, caption="Tayyor! ✅")
                await status_message.delete()
            else:
                await status_message.edit_text("Xatolik: Media topilmadi. ❌")
            cleanup_files(file_paths)
        else:
            await status_message.edit_text("Kechirasiz, yuklashda xatolik yuz berdi. 😔")
    except Exception as e:
        logging.error(f"WebApp data error: {e}")
        await status_message.edit_text("Xatolik yuz berdi. 😔")

@dp.message(F.text.regexp(r"(https?://(?:www\.)?(?:instagram\.com|tiktok\.com|youtube\.com|youtu\.be)/\S+)"))
async def handle_link(message: types.Message):
    import re
    url_match = re.search(r"(https?://\S+)", message.text)
    if not url_match:
        return
    url = url_match.group(1)
    
    # Store URL for callbacks
    unique_id = str(uuid.uuid4())[:8]
    url_cache[unique_id] = url
    
    # Premium Main Choice Buttons
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Videoni yuklab olish", callback_data=f"download_video:{unique_id}"),
        ],
        [
            InlineKeyboardButton(text="🎵 To'liq musiqa", callback_data=f"full_music:{unique_id}"),
            InlineKeyboardButton(text="✂️ Musiqani qirqish", callback_data=f"extract_audio:{unique_id}")
        ]
    ])
    
    await message.answer(
        f"📥 **Media topildi!**\n\nNima yuklamoqchisiz? Tanlang: 👇", 
        reply_markup=inline_kb, 
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("download_video:"))
async def cb_download_video(callback: types.CallbackQuery):
    unique_id = callback.data.split(":")[1]
    url = url_cache.get(unique_id)
    if not url:
        await callback.answer("Xatolik: Havola eskirgan. ❌", show_alert=True)
        return

    status = await callback.message.answer("🎬 **Video tayyorlanmoqda...** ⏳")
    video_files = await asyncio.to_thread(download_media, url, audio_only=False)
    
    if video_files == "COOKIE_REQUIRED":
        await status.edit_text("❌ **Xatolik:** Cookies talab qilinadi. 🔒")
        return
    
    if video_files and isinstance(video_files, list):
        for path in video_files:
            await callback.message.answer_video(FSInputFile(path), caption="✅ **Video tayyor!**")
        cleanup_files(video_files)
        await status.delete()
    else:
        await status.edit_text("😔 **Videoni yuklab bo'lmadi.**")
    await callback.answer()

@dp.callback_query(F.data.startswith("full_music:"))
async def cb_full_music(callback: types.CallbackQuery):
    unique_id = callback.data.split(":")[1]
    url = url_cache.get(unique_id)
    if not url:
        await callback.answer("Xatolik: Havola eskirgan. ❌", show_alert=True)
        return

    status = await callback.message.answer("🔍 **Musiqa aniqlanmoqda...**")
    
    audio_files = await asyncio.to_thread(download_media, url, audio_only=True)
    if not audio_files or not isinstance(audio_files, list):
        await status.edit_text("Musiqani aniqlash imkoni bo'lmadi. 😔")
        return

    shazam_res = await identify_music(audio_files[0])
    cleanup_files(audio_files)

    if shazam_res['success']:
        query = f"{shazam_res['artist']} {shazam_res['title']}"
        caption = f"✅ **Musiqa topildi!**\n\n" \
                  f"💿 **Nomi:** `{shazam_res['title']}`\n" \
                  f"👤 **Ijrochi:** `{shazam_res['artist']}`\n" \
                  f"💽 **Albom:** {shazam_res['album']}\n" \
                  f"🎭 **Janr:** {shazam_res['genre']}\n" \
                  f"📅 **Yili:** {shazam_res['released']}\n\n" \
                  f"📥 **To'liq versiya yuklanmoqda...** ⏳"
        
        kb = []
        if shazam_res.get('lyrics'):
            lyrics_id = f"lyr_{unique_id}"
            url_cache[lyrics_id] = shazam_res['lyrics']
            kb.append([
                InlineKeyboardButton(text="📑 Qo'shiq so'zlari", callback_data=f"show_lyrics:{lyrics_id}"),
                InlineKeyboardButton(text="🇺🇿 Tarjimasi", callback_data=f"translate_lyrics:{lyrics_id}")
            ])
        kb.append([
            InlineKeyboardButton(text="🌐 Barcha platformalar", url=shazam_res['songlink']),
            InlineKeyboardButton(text="🔍 Shazam", url=shazam_res['url'])
        ])
        shazam_kb = InlineKeyboardMarkup(inline_keyboard=kb)

        if shazam_res['cover']:
            await callback.message.answer_photo(shazam_res['cover'], caption=caption, reply_markup=shazam_kb, parse_mode="Markdown")
            await status.delete()
        else:
            await status.edit_text(caption, reply_markup=shazam_kb, parse_mode="Markdown")
        
        full_audio = await asyncio.to_thread(search_and_download_music, query)
        if full_audio and isinstance(full_audio, list):
            for path in full_audio:
                await callback.message.answer_audio(FSInputFile(path), caption=f"🎵 {shazam_res['title']} — {shazam_res['artist']}\n✅ To'liq versiya")
            cleanup_files(full_audio)
        else:
            await callback.message.answer("To'liq versiyani topib bo'lmadi. 😔")
    else:
        search_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔍 Qo'lda qidirish", callback_data="manual_search_prompt")]])
        await status.edit_text("Musiqa topilmadi. 😔", reply_markup=search_kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("extract_audio:"))
async def cb_extract_audio(callback: types.CallbackQuery):
    unique_id = callback.data.split(":")[1]
    url = url_cache.get(unique_id)
    if not url:
        await callback.answer("Xatolik: Havola eskirgan. ❌", show_alert=True)
        return

    status = await callback.message.answer("✂️ **Musiqa ajratib olinmoqda...** ⏳")
    audio_files = await asyncio.to_thread(download_media, url, audio_only=True)
    
    if audio_files and isinstance(audio_files, list):
        for path in audio_files:
            await callback.message.answer_audio(FSInputFile(path), caption="✂️ **Videodagi musiqa tayyor!**")
        cleanup_files(audio_files)
        await status.delete()
    else:
        await status.edit_text("😔 **Musiqani ajratib bo'lmadi.**")
    await callback.answer()

@dp.callback_query(F.data == "manual_search_prompt")
async def cb_manual_search_prompt(callback: types.CallbackQuery):
    await callback.message.answer("Musiqa nomini yoki ijrochini yozib yuboring (masalan: `Rayhon Aldama`). Bot uni YouTube-dan qidiradi. 🔍", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("show_lyrics:"))
async def cb_show_lyrics(callback: types.CallbackQuery):
    lyrics_id = callback.data.split(":")[1]
    lyrics = url_cache.get(lyrics_id)
    if not lyrics:
        await callback.answer("Matn topilmadi. ❌", show_alert=True)
        return
    
    # Send lyrics in a separate message if too long, or as an alert
    if len(lyrics) > 1000:
        await callback.message.answer(f"📑 **Qo'shiq matni:**\n\n{lyrics}", parse_mode="Markdown")
    else:
        await callback.message.answer(f"📑 **Qo'shiq matni:**\n\n{lyrics}", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("translate_lyrics:"))
async def cb_translate_lyrics(callback: types.CallbackQuery):
    lyrics_id = callback.data.split(":")[1]
    lyrics = url_cache.get(lyrics_id)
    if not lyrics:
        await callback.answer("Matn topilmadi. ❌", show_alert=True)
        return
    
    status = await callback.message.answer("Tarjima qilinmoqda... 🇺🇿⏳")
    
    # AI tarjima
    prompt = f"Quyidagi qo'shiq matnini o'zbek tiliga badiiy tarzda tarjima qilib ber:\n\n{lyrics}"
    translation = await get_ai_response(prompt)
    
    await status.edit_text(f"🇺🇿 **O'zbekcha tarjimasi:**\n\n{translation}", parse_mode="Markdown")
    await callback.answer()

@dp.message(Command("search"))
async def search_command(message: types.Message):
    """
    Search music by title or artist.
    """
    query = message.text.replace("/search", "").strip()
    if not query:
        await message.answer("Iltimos, qidirmoqchi bo'lgan musiqa nomini yozing. 🔍\n\nMisol: `/search Rayhon - Aldama`", parse_mode="Markdown")
        return
    
    await process_music_search(message, query)

async def process_music_search(message: types.Message, query: str):
    status = await message.answer(f"🔍 **{query}** qidirilmoqda...")
    
    # Use search function
    files = await asyncio.to_thread(search_and_download_music, query)
    if files and isinstance(files, list):
        # We don't have Shazam info here easily unless we Shazam the downloaded file
        # But for now, let's just send it.
        for path in files:
            await message.answer_audio(FSInputFile(path), caption=f"🎵 {query}\n✅ Qidiruv natijasi")
        cleanup_files(files)
        await status.delete()
    else:
        await status.edit_text("Afsuski, hech narsa topilmadi. 😔")

@dp.message(F.text)
async def handle_general_message(message: types.Message):
    text = message.text.strip()
    
    # 1. Havolalarni tekshirish
    link_patterns = ["http", "https", "www.", "instagram.com", "tiktok.com", "youtube.com", "youtu.be"]
    if any(pattern in text.lower() for pattern in link_patterns):
        return # handle_link funksiyasi buni hal qiladi

    # 2. Agar havola bo'lmasa, yo'riqnoma beramiz
    if not text.startswith('/'):
        await message.answer("Iltimos, Instagram, TikTok yoki YouTube havolasini yuboring. 📥")

@dp.callback_query(F.data.startswith("search_text:"))
async def cb_search_text(callback: types.CallbackQuery):
    query = callback.data.split(":")[1]
    await callback.message.edit_reply_markup(reply_markup=None)
    await process_music_search(callback.message, query)
    await callback.answer()

@dp.message(F.video | F.audio | F.voice | F.video_note)
async def handle_music(message: types.Message):
    """
    Handles video, audio, voice and video notes for music identification.
    """
    status_message = await message.answer("Musiqa tahlil qilinmoqda... 🎧")
    
    # Get the file id
    if message.video:
        file_id = message.video.file_id
    elif message.audio:
        file_id = message.audio.file_id
    elif message.voice:
        file_id = message.voice.file_id
    else:
        file_id = message.video_note.file_id

    # Create temporary file path
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    file_path = os.path.join(temp_dir, f"{file_id}.ogg")
    
    try:
        # Download file from Telegram
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, file_path)
        
        # Identify music
        result = await identify_music(file_path)
        
        if result['success']:
            query = f"{result['artist']} {result['title']}"
            caption = f"🎵 **Topilgan musiqa:**\n\n" \
                      f"📝 **Nomi:** {result['title']}\n" \
                      f"👤 **Ijrochi:** {result['artist']}\n\n" \
                      f"🔗 [Shazam-da ko'rish]({result['url']})"
            
            # Button for full version
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📥 To'liq versiyani yuklash", callback_data=f"search_text:{query[:30]}")]
            ])

            if result['cover']:
                await message.answer_photo(result['cover'], caption=caption, reply_markup=kb, parse_mode="Markdown")
                await status_message.delete()
            else:
                await status_message.edit_text(caption, reply_markup=kb, parse_mode="Markdown")
        else:
            await status_message.edit_text(result['message'])
            
    except Exception as e:
        logging.error(f"Shazam handler error: {e}")
        await status_message.edit_text("Musiqani aniqlashda xatolik yuz berdi. ❌")
    finally:
        # Cleanup temp file
        if os.path.exists(file_path):
            os.remove(file_path)

async def main():
    """
    Main entry point for the bot.
    """
    # Start web server for Render health check
    from aiohttp import web
    
    async def handle(request):
        return web.Response(text="Bot is running!")

    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render provides PORT environment variable
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    # Web serverni birinchi bo'lib va tezroq ishga tushiramiz
    print(f"Starting web server on port {port}...")
    await site.start()
    
    # Render portni topishi uchun biroz kutamiz
    await asyncio.sleep(2) 
    
    print("Starting bot polling...")
    # Pollingni barcha eski xabarlarni o'chirib yuboradigan qilib yoqamiz (skip_updates=True)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
