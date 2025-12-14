@echo off
echo Mami AI Sunucusu Baslatiliyor...

REM Proje kök dizinine geç
cd /d %~dp0..

echo FastAPI sunucusu baslatiliyor...
start cmd /k "cd /d %~dp0.. && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Tamamlandi! Sunucu baslatildi.
echo Kapatmak icin terminal penceresini kapatin.
pause
