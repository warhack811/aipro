@echo off
title Mami AI - KONTROL MERKEZI
color 0B
cls


:: --- GÖSTERİŞLİ GİRİŞ EKRANI ---
echo.
echo.
echo  ===================================================================
echo.
echo  __  __                 _      _    ___ 
echo ^|  \/  ^| __ _ _ __ ___ (_)    / \  ^|_ _^|
echo ^| ^|\/^| ^|/ _` ^| '_ ` _ \^| ^|   / _ \  ^| ^| 
echo ^| ^|  ^| ^| (_^| ^| ^| ^| ^| ^| ^| ^|  / ___ \ ^| ^| 
echo ^|_^|  ^|_^|\__,_^|_^| ^|_^| ^|_^|_^| /_/   \_\___^|
echo.
echo                   AKILLI ZEKA ASISTANI v4.2
echo  ===================================================================
echo.
echo  [BILGI] Sistem saati: %TIME%
echo  [KONUM] %CD%
echo.
echo  Sistemler kontrol ediliyor, lutfen bekleyin...
echo.
timeout /t 2 /nobreak >nul

:: 1. Ana klasore git (scripts/ klasorunun bir ust dizini)
cd /d %~dp0..
echo [1] Calisma dizini ayarlandi: %CD%

:: 2. Ollama Kontrolu
netstat -an | find "11434" >nul
if %errorlevel%==0 goto :ollama_acik
echo [2] Ollama baslatiliyor...
start "Mami AI - Ollama" /min cmd /k "ollama serve"
timeout /t 4 /nobreak >nul
goto :forge_baslat

:ollama_acik
echo [2] Ollama zaten acik, geciliyor.

:forge_baslat
:: 3. Forge Baslatma
echo [3] Forge (Flux) baslatiliyor...
set FORGE_PATH=D:\ai\forge\stable-diffusion-webui-forge-main
if exist "%FORGE_PATH%\webui-user.bat" (
    pushd "%FORGE_PATH%"
    start "Mami AI - Forge" cmd /k "webui-user.bat"
    popd
) else (
    echo [UYARI] Forge yolu bulunamadi!
)

:: 4. Python Ortami ve Baslatma
echo [4] Backend baslatiliyor...

:: Venv kontrolu (proje kok dizininde)
set PYTHON_CMD=python
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    set PYTHON_CMD=python
    echo [4a] venv aktif edildi
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    set PYTHON_CMD=python
    echo [4a] .venv aktif edildi
) else (
    echo [4a] Sanal ortam bulunamadi, sistem Python kullaniliyor
)

:: Paket kontrolu (kritik paketler)
echo [4b] Gerekli paketler kontrol ediliyor...
set MISSING_PACKAGES=0
%PYTHON_CMD% -c "import sqlmodel" >nul 2>&1
if %errorlevel% neq 0 (
    echo [UYARI] sqlmodel paketi bulunamadi!
    set MISSING_PACKAGES=1
)
%PYTHON_CMD% -c "import aiohttp" >nul 2>&1
if %errorlevel% neq 0 (
    echo [UYARI] aiohttp paketi bulunamadi!
    set MISSING_PACKAGES=1
)
%PYTHON_CMD% -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [UYARI] fastapi paketi bulunamadi!
    set MISSING_PACKAGES=1
)

if %MISSING_PACKAGES%==1 (
    echo [4c] Eksik paketler yukleniyor... (bu biraz zaman alabilir)
    %PYTHON_CMD% -m pip install -r requirements.txt --quiet
    if %errorlevel% neq 0 (
        echo [HATA] Paket yukleme basarisiz oldu!
        echo.
        echo Lutfen manuel olarak calistirin:
        echo   %PYTHON_CMD% -m pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo [4c] Paketler basariyla yuklendi.
) else (
    echo [4b] Paketler kontrol edildi, her sey hazir.
)

echo.
echo Uygulama calistiriliyor...
%PYTHON_CMD% -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

:: Eger hata olursa pencere kapanmasin
if %errorlevel% neq 0 (
    echo.
    echo [KRITIK HATA] Sunucu coktu veya Python bulunamadi.
    pause
)

pause