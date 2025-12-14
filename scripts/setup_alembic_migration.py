"""
Alembic Migration Setup Script
================================

Bu script mevcut veritabanı şemasını Alembic baseline olarak kaydeder.

Çalıştırma:
    python scripts/setup_alembic_migration.py
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd: list, description: str):
    """Komutu çalıştır ve sonucu göster"""
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print(f"{'='*60}")
    print(f"Komut: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"✓ {description} başarılı!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ HATA: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def main():
    """Ana setup fonksiyonu"""
    print("""
╔══════════════════════════════════════════════════════════╗
║         ALEMBIC MIGRATION SETUP                          ║
║         Mevcut şema baseline olarak kaydediliyor         ║
╚══════════════════════════════════════════════════════════╝
""")
    
    # 1. Alembic kurulu mu kontrol et
    print("1. Alembic kurulu mu kontrol ediliyor...")
    try:
        result = subprocess.run(["alembic", "--version"], capture_output=True, text=True)
        print(f"   ✓ Alembic bulundu: {result.stdout.strip()}")
    except FileNotFoundError:
        print("   ✗ Alembic bulunamadı!")
        print("   Yüklemek için: pip install alembic")
        sys.exit(1)
    
    # 2. alembic.ini var mı kontrol et
    print("\n2. alembic.ini kontrol ediliyor...")
    alembic_ini = Path("alembic.ini")
    if not alembic_ini.exists():
        print("   ✗ alembic.ini bulunamadı!")
        print("   Oluşturmak için: alembic init alembic")
        sys.exit(1)
    print("   ✓ alembic.ini mevcut")
    
    # 3. Mevcut migration'ları kontrol et
    print("\n3. Mevcut migration'lar kontrol ediliyor...")
    versions_dir = Path("alembic/versions")
    if versions_dir.exists():
        migrations = list(versions_dir.glob("*.py"))
        if migrations:
            print(f"   ⚠ {len(migrations)} migration dosyası bulundu")
            response = input("   Devam edilsin mi? (y/n): ")
            if response.lower() != 'y':
                print("   İşlem iptal edildi.")
                sys.exit(0)
        else:
            print("   ✓ Migration dizini boş")
    else:
        print("   ✓ Migration dizini henüz yok")
    
    # 4. Initial migration oluştur
    if not run_command(
        ["alembic", "revision", "--autogenerate", "-m", "initial_schema_baseline"],
        "Initial migration oluşturuluyor"
    ):
        print("\n✗ Migration oluşturulamadı!")
        sys.exit(1)
    
    # 5. Migration dosyasını bul ve göster
    print("\n5. Oluşturulan migration dosyası:")
    migrations = sorted(versions_dir.glob("*_initial_schema_baseline.py"))
    if migrations:
        latest = migrations[-1]
        print(f"   📄 {latest}")
        print(f"\n   İlk 20 satır:")
        print("   " + "-"*50)
        with open(latest) as f:
            lines = f.readlines()[:20]
            for line in lines:
                print(f"   {line.rstrip()}")
        print("   " + "-"*50)
    
    # 6. Bilgilendirme
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                  KURULUM TAMAMLANDI!                     ║
╚══════════════════════════════════════════════════════════╝

✓ Initial migration oluşturuldu
✓ Mevcut şema baseline olarak kaydedildi

SONRAKI ADIMLAR:

1. Migration dosyasını kontrol edin:
   alembic/versions/*_initial_schema_baseline.py

2. Migration'ı uygulayın (opsiyonel - ilk kurulumda gerekli değil):
   alembic upgrade head

3. Yeni model değişiklikleri için:
   alembic revision --autogenerate -m "açıklama"
   alembic upgrade head

4. Rollback için:
   alembic downgrade -1

NOT: app/core/database.py'deki init_database_with_defaults()
     fonksiyonu artık otomatik migration uygulayacak.
""")

if __name__ == "__main__":
    main()