import asyncio
import os
from aiogram import Bot
from aiogram.types import MenuButtonWebApp, WebAppInfo
from dotenv import load_dotenv

async def setup():
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    # YouTube Mobil havolasi
    WEBAPP_URL = "https://m.youtube.com/" 
    
    bot = Bot(token=BOT_TOKEN)
    
    print(f"Menyuni sozlash boshlandi: {WEBAPP_URL}")
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Mini App", web_app=WebAppInfo(url=WEBAPP_URL))
        )
        print("Muvaffaqiyatli! Endi botingiz menyusida Mini App tugmasi paydo bo'ldi.")
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(setup())
