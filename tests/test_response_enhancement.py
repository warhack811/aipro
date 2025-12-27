"""
Response Enhancement System - Test Script
Tüm yeni formatlama özelliklerini test eder
"""

from app.services.response_processor import full_post_process, get_preset_config


def test_basic_markdown():
    """Temel Markdown formatlaması testi"""
    print("=" * 60)
    print("TEST 1: Temel Markdown Formatlaması")
    print("=" * 60)

    input_text = """
KURULUM ADIMLARI

Adım 1: Projeyi kur
İlk olarak projeyi indirin.

Adım 2: Bağımlılıkları yükle
pip install komutu ile paketleri yükleyin.
    """

    result = full_post_process(input_text)
    print("\n📥 GIRIŞ:")
    print(input_text)
    print("\n📤 ÇIKIŞ:")
    print(result)
    print("\n")


def test_code_enhancement():
    """Kod bloğu zenginleştirme testi"""
    print("=" * 60)
    print("TEST 2: Kod Bloğu Zenginleştirme")
    print("=" * 60)

    input_text = """
İşte bir örnek kod:

```
def hello_world():
    print("Merhaba Dünya!")
    return True
```

JavaScript örneği:

```
const greeting = () => {
    console.log("Hello!");
};
```
    """

    result = full_post_process(input_text)
    print("\n📥 GIRIŞ:")
    print(input_text)
    print("\n📤 ÇIKIŞ:")
    print(result)
    print("\n")


def test_emoji_callouts():
    """Emoji ve callout kutusu testi"""
    print("=" * 60)
    print("TEST 3: Emoji ve Callout Kutuları")
    print("=" * 60)

    input_text = """
İpucu: Bu çok önemli bir bilgi

Uyarı: Bu işlem geri alınamaz

Başarılı: İşlem tamamlandı

KURULUM

Bu adımları takip edin.
    """

    result = full_post_process(input_text)
    print("\n📥 GIRIŞ:")
    print(input_text)
    print("\n📤 ÇIKIŞ:")
    print(result)
    print("\n")


def test_list_formatting():
    """Liste formatlaması testi"""
    print("=" * 60)
    print("TEST 4: Liste Formatlaması")
    print("=" * 60)

    input_text = """
Yapılacaklar:

-Proje planı hazırla
-  Takım toplantısı yap
* Kod review
•Deployment

Numaralı liste:

1.İlk adım
2.  İkinci adım
3.Üçüncü adım
    """

    result = full_post_process(input_text)
    print("\n📥 GIRIŞ:")
    print(input_text)
    print("\n📤 ÇIKIŞ:")
    print(result)
    print("\n")


def test_turkish_rules():
    """Türkçe yazım kuralları testi"""
    print("=" * 60)
    print("TEST 5: Türkçe Yazım Kuralları")
    print("=" * 60)

    input_text = """
bu bir cümle.sonra başka bir cümle gelir.

değil mi ?

var mı ?

için mi kullanıyoruz .
    """

    result = full_post_process(input_text)
    print("\n📥 GIRIŞ:")
    print(input_text)
    print("\n📤 ÇIKIŞ:")
    print(result)
    print("\n")


def test_format_levels():
    """Format seviyeleri karşılaştırması"""
    print("=" * 60)
    print("TEST 6: Format Seviyeleri (Minimal vs Normal vs Rich)")
    print("=" * 60)

    input_text = """
KURULUM

İpucu: Dikkatli okuyun

```
print("Hello")
```

- Birinci madde
- İkinci madde
    """

    print("\n📥 ORIJINAL METİN:")
    print(input_text)

    print("\n--- MINIMAL FORMAT ---")
    minimal = full_post_process(input_text, get_preset_config("minimal"))
    print(minimal)

    print("\n--- NORMAL FORMAT ---")
    normal = full_post_process(input_text, get_preset_config("normal"))
    print(normal)

    print("\n--- RICH FORMAT ---")
    rich = full_post_process(input_text, get_preset_config("rich"))
    print(rich)

    print("\n")


def test_comprehensive():
    """Kapsamlı test - tüm özellikler birlikte"""
    print("=" * 60)
    print("TEST 7: Kapsamlı Test (Tüm Özellikler)")
    print("=" * 60)

    input_text = """
PYTHON WEB UYGULAMASI NASIL YAPILIR

KURULUM ADIMLARI

Adım 1: Gerekli paketleri yükleyin

```
pip install fastapi uvicorn
```

Adım 2: Ana dosyayı oluşturun

```
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Merhaba Dünya"}
```

ÖNEMLİ NOTLAR

İpucu: FastAPI otomatik dokümantasyon sağlar

Uyarı: Production için uvicorn worker sayısını artırın

YAPILACAKLAR LİSTESİ

- API endpoints tasarla
- Veritabanı modelleri oluştur
• Testleri yaz
-Deployment yap

SONUÇ

bu proje ile hızlı bir şekilde api geliştirebilirsiniz .değil mi ?
    """

    result = full_post_process(input_text)
    print("\n📥 GIRIŞ:")
    print(input_text)
    print("\n📤 ÇIKIŞ (RICH FORMAT):")
    print(result)
    print("\n")


if __name__ == "__main__":
    print("\n🚀 RESPONSE ENHANCEMENT SYSTEM - TEST SÜİTİ\n")

    try:
        test_basic_markdown()
        test_code_enhancement()
        test_emoji_callouts()
        test_list_formatting()
        test_turkish_rules()
        test_format_levels()
        test_comprehensive()

        print("=" * 60)
        print("✅ TÜM TESTLER TAMAMLANDI!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback

        traceback.print_exc()
