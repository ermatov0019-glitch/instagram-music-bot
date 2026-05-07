@echo off
title Instagram Downloader & Gemini AI Bot
echo Botni ishga tushirish tayyorlanmoqda...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo XATOLIK: Python topilmadi! 
    echo Iltimos, Pythonni o'rnating.
    pause
    exit /b
)

:: Web-serverni alohida oynada yoqish
echo Mini App serveri ishga tushmoqda (Port 8000)...
start "Mini App Server" cmd /c "cd webapp && python -m http.server 8000"

:: ngrok-ni alohida oynada yoqish
echo ngrok tunnel ishga tushmoqda...
:: Agar ngrok.exe shu papkada bo'lsa ./ngrok ishlatiladi
if exist "ngrok.exe" (
    start "ngrok Tunnel" cmd /c "ngrok http 8000"
) else (
    echo OGOHLANTIRISH: ngrok.exe topilmadi. Uni bot papkasiga tashlang!
)

echo.
echo ======================================================
echo DIQQAT: ngrok oynasidagi HTTPS linkni nusxalab, 
echo main.py faylidagi WEBAPP_URL qismiga qo'yishni unutmang!
echo ======================================================
echo.
echo Bot ishga tushirilmoqda...
python main.py

pause
