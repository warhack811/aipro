@echo off
title Mami AI - MOBIL SUNUCU (Tailscale)
color 0E
cls

:: ===================================================================
:: Mami AI v4.2 - Mobil Sunucu Modu
:: Tailscale agi uzerinden mobil cihazlardan erisim icin
:: ===================================================================

:: 1. Ana klasore git (scripts/ klasorunun bir ust dizini)
cd /d %~dp0..
echo [1] Calisma dizini ayarlandi: %CD%

:: 2. Tailscale IP adresini al (kullanici kendisi girebilir)
set TAILSCALE_IP=100.93.11.128
echo [2] Tailscale IP: %TAILSCALE_IP%
echo.

:: ---------------------------------------------------------
:: 3. ADIM: OLLAMA (Disari erisim ayarlariyla)
:: ---------------------------------------------------------
:: Ollama'yi tum IP'lere aciyoruz ki telefondan baglanti sorunu olmasin
set OLLAMA_HOST=0.0.0.0
set OLLAMA_ORIGINS=*

netstat -an | find "11434" >nul
if %errorlevel%==0 goto :ollama_skip
echo [3] Ollama (Mobil Mod) baslatiliyor...
start "Mami AI - Ollama Mobile" /min cmd /k "ollama serve"
timeout /t 4 /nobreak >nul
goto :forge_adim

:ollama_skip
echo [3] Ollama zaten acik, geciliyor.

:forge_adim
:: ---------------------------------------------------------
:: 4. ADIM: FORGE (Resim Cizme) - Opsiyonel
:: ---------------------------------------------------------
echo [4] Forge (Flux) kontrol ediliyor...
set "FORGE_PATH=D:\ai\forge\stable-diffusion-webui-forge-main"
if exist "%FORGE_PATH%\webui-user.bat" (
    echo [4] Forge baslatiliyor...
    pushd "%FORGE_PATH%"
    start "Mami AI - Forge" cmd /k "webui-user.bat"
    popd
    timeout /t 3 /nobreak >nul
) else (
    echo [4] Forge yolu bulunamadi. (Opsiyonel - resim cizme calismayabilir)
)

:: ---------------------------------------------------------
:: 5. ADIM: BACKEND (TAILSCALE AGINA ACILIS)
:: ---------------------------------------------------------
echo [5] Backend baslatiliyor...

:: Sanal ortam kontrolu ve aktif etme
set PYTHON_CMD=python
set VENV_ACTIVE=0
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    set PYTHON_CMD=python
    set VENV_ACTIVE=1
    echo [5a] venv aktif edildi
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    set PYTHON_CMD=python
    set VENV_ACTIVE=1
    echo [5a] .venv aktif edildi
) else (
    echo [5a] Sanal ortam bulunamadi, sistem Python kullaniliyor
)

:: Paket kontrolu (kritik paketler)
echo [5b] Gerekli paketler kontrol ediliyor...
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
    echo [5c] Eksik paketler yukleniyor... (bu biraz zaman alabilir)
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
    echo [5c] Paketler basariyla yuklendi.
) else (
    echo [5b] Paketler kontrol edildi, her sey hazir.
)

echo.
echo ==================================================
echo  MOBIL ERISIM ADRESI:
echo  http://%TAILSCALE_IP%:8000/ui/login.html
echo ==================================================
echo.
echo  (Mobil tarayicindan bu adrese girip kullanabilirsin)
echo  (Tailscale aginda oldugundan emin ol!)
echo.
echo  Sunucu baslatiliyor...
echo.

:: Backend'i baslat (app.main:app veya main:app - her ikisi de calisir)
%PYTHON_CMD% -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

:: Eger hata olursa pencere kapanmasin
if %errorlevel% neq 0 (
    echo.
    echo [KRITIK HATA] Sunucu coktu veya Python bulunamadi.
    echo.
    echo Kontrol edin:
    echo  1. Python yuklu mu? (python --version)
    echo  2. Sanal ortam aktif mi?
    echo  3. Gerekli paketler yuklu mu? (pip install -r requirements.txt)
    echo  4. Port 8000 bos mu?
    echo.
    pause
)

echo.
echo [DIKKAT] Sunucu kapandi.
pause