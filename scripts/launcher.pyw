import sys
import os
import subprocess
import time
import datetime
import threading
from PIL import Image, ImageDraw
import pystray
import webbrowser

# --- SABİT PROJE KONUMU ---
PROJECT_DIR = r"D:\ai\mami_ai_v4" 
LOG_FILE = os.path.join(PROJECT_DIR, "logs", "launcher.log")

# --- 1. BÖLÜM: AKILLI BAŞLANGIÇ (VENV KONTROLÜ) ---
def restart_with_venv():
    venv_pythonw = os.path.join(PROJECT_DIR, "venv", "Scripts", "pythonw.exe")
    if os.path.exists(venv_pythonw) and sys.executable.lower() != venv_pythonw.lower():
        subprocess.Popen([venv_pythonw, __file__], cwd=PROJECT_DIR, creationflags=subprocess.CREATE_NO_WINDOW)
        sys.exit()

restart_with_venv()

# --- 2. BÖLÜM: ASIL PROGRAM ---

# Forge Ayarları
FORGE_DIR = r"D:\ai\forge\stable-diffusion-webui-forge-main"
LAUNCH_SCRIPT = "launch.py"
FORGE_SCRIPT_PATH = os.path.join(FORGE_DIR, LAUNCH_SCRIPT)

process_backend = None
process_forge = None

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except: pass

def create_icon():
    width = 64; height = 64
    image = Image.new('RGB', (width, height), "#667eea")
    dc = ImageDraw.Draw(image)
    dc.rectangle((width // 4, height // 4, width * 3 // 4, height * 3 // 4), fill="#764ba2")
    return image

def get_forge_python():
    """Forge için doğru Python.exe'yi bulur."""
    forge_venv_python = os.path.join(FORGE_DIR, "venv", "Scripts", "python.exe")
    if os.path.exists(forge_venv_python): return forge_venv_python
    
    forge_sys_python = os.path.join(FORGE_DIR, "system", "python", "python.exe")
    if os.path.exists(forge_sys_python): return forge_sys_python

    current_python = sys.executable
    if "pythonw.exe" in current_python.lower():
        return current_python.lower().replace("pythonw.exe", "python.exe")
    return current_python

def start_servers():
    global process_backend, process_forge
    
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

    log(f"--- Mami AI v4.2 Başlatılıyor ---")

    # 1. Backend Başlat
    try:
        BACKEND_CMD = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
        with open(LOG_FILE, "a") as log_f:
            process_backend = subprocess.Popen(
                BACKEND_CMD, cwd=PROJECT_DIR, startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW, stdout=log_f, stderr=log_f
            )
        log(f"Backend PID: {process_backend.pid}")
    except Exception as e:
        log(f"Backend Hatası: {e}")

    # 2. Forge Başlat
    try:
        if os.path.exists(FORGE_SCRIPT_PATH):
            forge_python = get_forge_python()
            log(f"Forge başlatılıyor... Python: {forge_python}")
            
            forge_env = os.environ.copy()
            forge_env["PYTHONUNBUFFERED"] = "1"
            
            # --- DÜZELTİLEN KISIM ---
            # --no-auto-launch komutunu sildik çünkü hata veriyordu.
            # Sadece --api ve --listen ekliyoruz.
            forge_env["COMMANDLINE_ARGS"] = "--api --listen"

            forge_args = [forge_python, LAUNCH_SCRIPT]

            process_forge = subprocess.Popen(
                forge_args,
                cwd=FORGE_DIR,
                env=forge_env,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=open(LOG_FILE, "a"), 
                stderr=open(LOG_FILE, "a")
            )
            log(f"Forge PID: {process_forge.pid}")
        else:
            log(f"UYARI: launch.py bulunamadı: {FORGE_SCRIPT_PATH}")
    except Exception as e:
        log(f"Forge Hatası: {e}")

def stop_servers(icon, item):
    log("Çıkış yapılıyor...")
    icon.stop()
    if process_backend: subprocess.call(['taskkill', '/F', '/T', '/PID', str(process_backend.pid)])
    if process_forge: subprocess.call(['taskkill', '/F', '/T', '/PID', str(process_forge.pid)])
    sys.exit(0)

def open_chat_ui(icon, item): webbrowser.open("http://127.0.0.1:8000")
def open_forge_ui(icon, item): webbrowser.open("http://127.0.0.1:7860")

if __name__ == "__main__":
    try:
        start_servers()
        menu = (
            pystray.MenuItem("Sohbeti Aç (Mami AI)", open_chat_ui),
            pystray.MenuItem("Forge Arayüzünü Aç", open_forge_ui),
            pystray.MenuItem("Çıkış", stop_servers)
        )
        icon = pystray.Icon("Mami AI", create_icon(), "Mami AI Server", menu)
        icon.run()
    except Exception as e:
        log(f"Tray Hatası: {e}")