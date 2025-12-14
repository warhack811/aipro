"""
Placeholder Image Generator
============================

Forge API fail durumunda gösterilecek placeholder image'leri oluşturur.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Placeholder dizini
PLACEHOLDER_DIR = Path("data/images/placeholders")
PLACEHOLDER_DIR.mkdir(parents=True, exist_ok=True)

def create_placeholder(text: str, output_path: Path, color: str = '#2C3E50'):
    """
    Basit placeholder image oluştur.
    
    Args:
        text: Gösterilecek metin
        output_path: Kaydedilecek yol
        color: Arka plan rengi
    """
    # 512x512 görsel oluştur
    img = Image.new('RGB', (512, 512), color=color)
    draw = ImageDraw.Draw(img)
    
    # Font (default font kullan, arial bulunamazsa)
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except:
            font = ImageFont.load_default()
    
    # Metni ortala
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (512 - text_width) / 2
    y = (512 - text_height) / 2
    
    # Metni çiz
    draw.text((x, y), text, fill='white', font=font, align='center')
    
    # Kaydet
    img.save(output_path)
    print(f"✓ Oluşturuldu: {output_path}")

def main():
    """Tüm placeholder'ları oluştur"""
    print("Placeholder image'ler oluşturuluyor...")
    
    # Error placeholder
    create_placeholder(
        "Görsel Üretim Hatası\n\nLütfen daha sonra\ntekrar deneyin",
        PLACEHOLDER_DIR / "error.png",
        color='#C0392B'  # Kırmızı
    )
    
    # Timeout placeholder
    create_placeholder(
        "Zaman Aşımı\n\nİşlem çok uzun sürdü",
        PLACEHOLDER_DIR / "timeout.png",
        color='#E67E22'  # Turuncu
    )
    
    # Maintenance placeholder
    create_placeholder(
        "Servis Geçici Kapalı\n\nBakım yapılıyor",
        PLACEHOLDER_DIR / "maintenance.png",
        color='#7F8C8D'  # Gri
    )
    
    print("\n✓ Tüm placeholder'lar oluşturuldu!")
    print(f"Dizin: {PLACEHOLDER_DIR.absolute()}")

if __name__ == "__main__":
    main()