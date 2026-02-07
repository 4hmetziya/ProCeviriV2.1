import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# app.py'deki mantığı test et
app_dir = os.path.dirname(os.path.abspath(__file__))
fonts_dir = os.path.join(app_dir, "fonts")

print("=" * 60)
print("FONT YOLU KONTROLÜ")
print("=" * 60)
print(f"app.py dizini: {app_dir}")
print(f"fonts klasörü: {fonts_dir}")
print(f"fonts klasörü var mı: {os.path.exists(fonts_dir)}")
print()

if os.path.exists(fonts_dir):
    print("Font dosyaları:")
    files = os.listdir(fonts_dir)
    for f in files:
        if f.endswith('.ttf'):
            full_path = os.path.join(fonts_dir, f)
            exists = os.path.exists(full_path)
            size = os.path.getsize(full_path) if exists else 0
            print(f"  [OK] {f}")
            print(f"     Yol: {full_path}")
            print(f"     Var mi: {exists}")
            print(f"     Boyut: {size:,} bytes")
            
            # Fontu yüklemeyi dene
            try:
                font_key = f"TestFont-{f.replace('.ttf', '')}"
                pdfmetrics.registerFont(TTFont(font_key, full_path))
                print(f"     [BASARILI] Font yuklendi!")
            except Exception as e:
                print(f"     [HATA] Yukleme hatasi: {e}")
            print()
else:
    print("[HATA] fonts klasoru bulunamadi!")
    print(f"   Olması gereken yol: {fonts_dir}")

print("=" * 60)
