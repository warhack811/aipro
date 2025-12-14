#!/usr/bin/env python3
"""
Otomatik Deployment Script - Kritik Düzeltmeler
================================================

Bu script 3 kritik düzeltmeyi otomatik olarak uygular ve test eder.

Kullanım:
    python scripts/deploy_critical_fixes.py

Veya adım adım:
    python scripts/deploy_critical_fixes.py --step 1  # Sadece ChromaDB
    python scripts/deploy_critical_fixes.py --step 2  # Sadece Circuit Breaker
    python scripts/deploy_critical_fixes.py --step 3  # Sadece Alembic
"""

import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


# Renkli çıktı için ANSI kodları
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Başlık yazdır"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_step(step, text: str):
    """Adım yazdır"""
    print(f"{Colors.OKCYAN}{Colors.BOLD}[ADIM {step}]{Colors.ENDC} {text}")

def print_success(text: str):
    """Başarı mesajı"""
    try:
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")

def print_warning(text: str):
    """Uyarı mesajı"""
    try:
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"{Colors.WARNING}[!] {text}{Colors.ENDC}")

def print_error(text: str):
    """Hata mesajı"""
    try:
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    except UnicodeEncodeError:
        print(f"{Colors.FAIL}[X] {text}{Colors.ENDC}")

def run_command(cmd: List[str], description: str, allow_fail: bool = False) -> Tuple[bool, str]:
    """
    Komut çalıştır ve sonucu döndür
    
    Returns:
        (success: bool, output: str)
    """
    print(f"  Çalıştırılıyor: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=not allow_fail,
            timeout=300  # 5 dakika timeout
        )
        
        if result.returncode == 0:
            print_success(f"{description} başarılı")
            return True, result.stdout
        else:
            if allow_fail:
                print_warning(f"{description} başarısız (izin veriliyor)")
                return False, result.stderr
            else:
                print_error(f"{description} başarısız!")
                print(f"  HATA: {result.stderr}")
                return False, result.stderr
                
    except subprocess.TimeoutExpired:
        print_error(f"{description} timeout!")
        return False, "Timeout"
    except Exception as e:
        print_error(f"{description} hata: {e}")
        return False, str(e)

def create_backup(path: Path, backup_suffix: str = ".backup") -> bool:
    """Dosya/dizin yedeği al"""
    if not path.exists():
        print_warning(f"Yedeklenecek yol bulunamadı: {path}")
        return True  # Dosya yoksa yedeklemeye gerek yok
    
    backup_path = Path(str(path) + backup_suffix)
    
    try:
        if path.is_dir():
            if backup_path.exists():
                shutil.rmtree(backup_path)
            shutil.copytree(path, backup_path)
        else:
            shutil.copy2(path, backup_path)
        
        print_success(f"Yedek alındı: {backup_path}")
        return True
    except Exception as e:
        print_error(f"Yedekleme hatası: {e}")
        return False

def check_prerequisites() -> bool:
    """Ön koşulları kontrol et"""
    print_step(0, "Ön Koşullar Kontrol Ediliyor")
    
    all_ok = True
    
    # Python version
    if sys.version_info < (3, 8):
        print_error("Python 3.8+ gerekli")
        all_ok = False
    else:
        print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # pip
    success, _ = run_command(["pip", "--version"], "pip kontrolü", allow_fail=True)
    if not success:
        print_error("pip bulunamadı")
        all_ok = False
    
    # Git (opsiyonel)
    success, _ = run_command(["git", "--version"], "git kontrolü", allow_fail=True)
    if not success:
        print_warning("git bulunamadı (opsiyonel)")
    
    # pytest
    success, _ = run_command(["pytest", "--version"], "pytest kontrolü", allow_fail=True)
    if not success:
        print_warning("pytest bulunamadı, yüklenecek")
        run_command(["pip", "install", "pytest"], "pytest kurulumu")
    
    return all_ok

def step1_chromadb_upgrade() -> bool:
    """Adım 1: ChromaDB Upgrade"""
    print_header("ADIM 1: ChromaDB WHERE Filter Fix")
    
    # 1.1 Yedek al
    print_step(1.1, "ChromaDB Yedekleniyor")
    chroma_path = Path("data/chroma_db")
    if not create_backup(chroma_path):
        return False
    
    # 1.2 ChromaDB versiyonunu kontrol et
    print_step(1.2, "Mevcut ChromaDB Versiyonu Kontrol Ediliyor")
    success, output = run_command(
        ["pip", "show", "chromadb"],
        "ChromaDB version check",
        allow_fail=True
    )
    if success:
        for line in output.split('\n'):
            if line.startswith('Version:'):
                current_version = line.split(':')[1].strip()
                print(f"  Mevcut versiyon: {current_version}")
    
    # 1.3 Upgrade yap
    print_step(1.3, "ChromaDB Upgrade Yapılıyor")
    success, _ = run_command(
        ["pip", "install", "--upgrade", "chromadb>=0.4.24"],
        "ChromaDB upgrade"
    )
    if not success:
        print_error("ChromaDB upgrade başarısız!")
        return False
    
    # 1.4 Yeni versiyonu kontrol et
    print_step(1.4, "Yeni ChromaDB Versiyonu Kontrol Ediliyor")
    success, output = run_command(
        ["pip", "show", "chromadb"],
        "ChromaDB version check"
    )
    if success:
        for line in output.split('\n'):
            if line.startswith('Version:'):
                new_version = line.split(':')[1].strip()
                print_success(f"Yeni versiyon: {new_version}")
    
    # 1.5 Test çalıştır
    print_step(1.5, "WHERE Filter Testleri Çalıştırılıyor")
    success, output = run_command(
        ["pytest", "tests/test_critical_fixes.py::TestChromaDBWhereFilter", "-v"],
        "ChromaDB WHERE filter testleri",
        allow_fail=True
    )
    
    if success:
        print_success("[OK] ADIM 1 TAMAMLANDI: ChromaDB WHERE Filter")
        return True
    else:
        print_error("[X] ADIM 1 BAŞARISIZ: Testler geçmedi")
        print_warning("Geri dönmek için: cp -r data/chroma_db.backup data/chroma_db")
        return False

def step2_circuit_breaker() -> bool:
    """Adım 2: Circuit Breaker + Placeholder Images"""
    print_header("ADIM 2: Forge Circuit Breaker + Error Handling")
    
    # 2.1 Pillow kur (gerekirse)
    print_step(2.1, "Pillow Kontrol Ediliyor")
    success, _ = run_command(
        ["pip", "show", "Pillow"],
        "Pillow check",
        allow_fail=True
    )
    if not success:
        print_warning("Pillow bulunamadı, yükleniyor")
        run_command(["pip", "install", "Pillow"], "Pillow kurulumu")
    else:
        print_success("Pillow zaten yüklü")
    
    # 2.2 Placeholder images oluştur
    print_step(2.2, "Placeholder Images Oluşturuluyor")
    
    # Dizin oluştur
    placeholder_dir = Path("data/images/placeholders")
    placeholder_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"Dizin oluşturuldu: {placeholder_dir}")
    
    # Script çalıştır
    if Path("scripts/create_placeholder_images.py").exists():
        success, _ = run_command(
            ["python", "scripts/create_placeholder_images.py"],
            "Placeholder images oluşturma",
            allow_fail=True
        )
        if not success:
            print_warning("Placeholder script çalışmadı, manuel oluşturma gerekebilir")
    else:
        print_warning("create_placeholder_images.py bulunamadı")
    
    # 2.3 Placeholder'ları kontrol et
    print_step(2.3, "Placeholder Images Kontrol Ediliyor")
    required_files = ["error.png", "timeout.png", "maintenance.png"]
    all_exist = True
    
    for filename in required_files:
        filepath = placeholder_dir / filename
        if filepath.exists():
            print_success(f"[OK] {filename} mevcut")
        else:
            print_warning(f"[X] {filename} EKSIK - Manuel oluşturulmalı")
            all_exist = False
    
    # 2.4 Circuit breaker test
    print_step(2.4, "Circuit Breaker Testleri Çalıştırılıyor")
    success, _ = run_command(
        ["pytest", "tests/test_critical_fixes.py::TestForgeCircuitBreaker", "-v"],
        "Circuit breaker testleri",
        allow_fail=True
    )
    
    if success:
        print_success("[OK] ADIM 2 TAMAMLANDI: Circuit Breaker")
        return True
    else:
        print_error("[X] ADIM 2 KISMEN BAŞARISIZ: Testler geçmedi")
        return False

def step3_alembic_migration() -> bool:
    """Adım 3: Alembic Migration Setup"""
    print_header("ADIM 3: Alembic Migration Sistemi")
    
    # 3.1 Alembic kur (gerekirse)
    print_step(3.1, "Alembic Kontrol Ediliyor")
    success, _ = run_command(
        ["pip", "show", "alembic"],
        "Alembic check",
        allow_fail=True
    )
    if not success:
        print_warning("Alembic bulunamadı, yükleniyor")
        run_command(["pip", "install", "alembic"], "Alembic kurulumu")
    else:
        print_success("Alembic zaten yüklü")
    
    # 3.2 alembic.ini kontrol
    print_step(3.2, "alembic.ini Kontrol Ediliyor")
    if Path("alembic.ini").exists():
        print_success("alembic.ini mevcut")
    else:
        print_error("alembic.ini bulunamadı!")
        print_warning("Oluşturmak için: alembic init alembic")
        return False
    
    # 3.3 Database yedek al
    print_step(3.3, "Database Yedekleniyor")
    db_path = Path("data/app.db")
    if not create_backup(db_path):
        print_warning("Database yedeği alınamadı")
    
    # 3.4 Setup script çalıştır
    print_step(3.4, "Initial Migration Oluşturuluyor")
    if Path("scripts/setup_alembic_migration.py").exists():
        print("  Bu adım interaktif olabilir, lütfen bekleyin...")
        success, _ = run_command(
            ["python", "scripts/setup_alembic_migration.py"],
            "Alembic setup",
            allow_fail=True
        )
    else:
        print_warning("setup_alembic_migration.py bulunamadı")
        print("  Manuel olarak: alembic revision --autogenerate -m 'initial_baseline'")
    
    # 3.5 Migration dosyalarını kontrol et
    print_step(3.5, "Migration Dosyaları Kontrol Ediliyor")
    versions_dir = Path("alembic/versions")
    if versions_dir.exists():
        migrations = list(versions_dir.glob("*.py"))
        if migrations:
            print_success(f"{len(migrations)} migration dosyası bulundu")
            for mig in migrations[-3:]:  # Son 3'ünü göster
                print(f"  - {mig.name}")
        else:
            print_warning("Migration dosyası bulunamadı")
    
    # 3.6 Test çalıştır
    print_step(3.6, "Alembic Testleri Çalıştırılıyor")
    success, _ = run_command(
        ["pytest", "tests/test_critical_fixes.py::TestAlembicMigration", "-v"],
        "Alembic migration testleri",
        allow_fail=True
    )
    
    if success:
        print_success("[OK] ADIM 3 TAMAMLANDI: Alembic Migration")
        return True
    else:
        print_error("[X] ADIM 3 KISMEN BAŞARISIZ: Testler geçmedi")
        return False

def run_integration_tests() -> bool:
    """Entegrasyon testlerini çalıştır"""
    print_header("ENTEGRASYON TESTLERİ")
    
    print_step(1, "Tüm Testler Çalıştırılıyor")
    success, output = run_command(
        ["pytest", "tests/test_critical_fixes.py", "-v", "--tb=short"],
        "Tüm critical fix testleri",
        allow_fail=True
    )
    
    if success:
        print_success("[OK] TÜM TESTLER BAŞARILI!")
        
        # Test özeti çıkar
        if "passed" in output.lower():
            print("\n" + "="*70)
            print("TEST ÖZETİ:")
            for line in output.split('\n'):
                if 'passed' in line.lower() or 'failed' in line.lower():
                    print(f"  {line.strip()}")
            print("="*70)
        
        return True
    else:
        print_error("[X] BAZI TESTLER BAŞARISIZ")
        return False

def generate_report(results: dict):
    """Deployment raporu oluştur"""
    print_header("DEPLOYMENT RAPORU")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
======================================================================
                    DEPLOYMENT RAPORU
                    {timestamp}
======================================================================

ADIMLAR:
  1. ChromaDB WHERE Filter:  {"[OK] BASARILI" if results.get('step1') else "[X] BASARISIZ"}
  2. Circuit Breaker:         {"[OK] BASARILI" if results.get('step2') else "[X] BASARISIZ"}
  3. Alembic Migration:       {"[OK] BASARILI" if results.get('step3') else "[X] BASARISIZ"}
  4. Integration Tests:       {"[OK] BASARILI" if results.get('integration') else "[X] BASARISIZ"}

GENEL DURUM: {"[OK] BASARILI" if all(results.values()) else "[!] KISMEN BASARISIZ"}

SONRAKI ADIMLAR:
"""
    
    if all(results.values()):
        report += """
  [OK] Tum duzeltmeler basariyla uygulandi
  [OK] Tum testler gecti
  
  Şimdi yapılması gerekenler:
  1. Staging environment'ta test edin
  2. 7 gün monitoring yapın
  3. Production'a deploy edin
  
  Detaylı rapor: docs/UYGULAMA_RAPORU_FINAL.md
"""
    else:
        report += """
  [!] Bazi adimlar basarisiz oldu
  
  Kontrol edilmesi gerekenler:
  1. Hata loglarını inceleyin
  2. Başarısız testleri debug edin
  3. Gerekirse geri dönüş yapın
  
  Geri dönüş:
  - ChromaDB: cp -r data/chroma_db.backup data/chroma_db
  - Database: cp data/app.db.backup data/app.db
"""
    
    report += f"""
======================================================================

Detayli loglar: logs/deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log
"""
    
    print(report)
    
    # Raporu dosyaya yaz
    report_path = Path(f"logs/deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report, encoding='utf-8')
    print_success(f"Rapor kaydedildi: {report_path}")

def main():
    """Ana deployment fonksiyonu"""
    print_header("KRİTİK HATALARIN OTOMATIK DEPLOYMENT")
    print(f"Başlangıç Zamanı: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Sonuçları takip et
    results = {
        'step1': False,
        'step2': False,
        'step3': False,
        'integration': False
    }
    
    # Ön koşulları kontrol et
    if not check_prerequisites():
        print_error("Ön koşullar sağlanamadı, çıkılıyor!")
        sys.exit(1)
    
    print_success("Ön koşullar sağlandı, deployment başlıyor...\n")
    time.sleep(2)
    
    # Adım 1: ChromaDB
    try:
        results['step1'] = step1_chromadb_upgrade()
    except Exception as e:
        print_error(f"Adım 1 hata: {e}")
        results['step1'] = False
    
    time.sleep(1)
    
    # Adım 2: Circuit Breaker
    try:
        results['step2'] = step2_circuit_breaker()
    except Exception as e:
        print_error(f"Adım 2 hata: {e}")
        results['step2'] = False
    
    time.sleep(1)
    
    # Adım 3: Alembic
    try:
        results['step3'] = step3_alembic_migration()
    except Exception as e:
        print_error(f"Adım 3 hata: {e}")
        results['step3'] = False
    
    time.sleep(1)
    
    # Integration tests
    try:
        results['integration'] = run_integration_tests()
    except Exception as e:
        print_error(f"Integration tests hata: {e}")
        results['integration'] = False
    
    # Rapor oluştur
    generate_report(results)
    
    # Çıkış kodu
    if all(results.values()):
        print_success("\n[OK] DEPLOYMENT BASARILI!")
        sys.exit(0)
    else:
        print_error("\n[!] DEPLOYMENT KISMEN BASARISIZ")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\n\nDeployment iptal edildi (Ctrl+C)")
        sys.exit(130)
    except Exception as e:
        print_error(f"\n\nBeklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)