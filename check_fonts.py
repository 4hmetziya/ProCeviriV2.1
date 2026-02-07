import os

# app.py'deki mantığı test et
app_dir = os.path.dirname(os.path.abspath('app.py'))
print("=" * 60)
print("FONT YOLU KONTROLÜ")
print("=" * 60)
print(f"app.py dizini: {app_dir}")
print()

# Font dosyalarını kontrol et
font_files = ['tr_font_reg.ttf', 'tr_font_bold.ttf', 'tr_font_italic.ttf', 'tr_font_bi.ttf']

print("Font dosyaları kontrolü:")
print("-" * 60)

for filename in font_files:
    # Proje kökünde (eski çalışan versiyon)
    path_kok = os.path.join(app_dir, filename)
    
    # fonts/ klasöründe (yeni versiyon - çalışmadı)
    path_fonts = os.path.join(app_dir, "fonts", filename)
    
    print(f"\n{filename}:")
    print(f"  Proje kokunde: {os.path.exists(path_kok)}")
    if os.path.exists(path_kok):
        print(f"    [OK] Yol: {path_kok}")
    else:
        print(f"    [HATA] Yol: {path_kok}")
    
    print(f"  fonts/ klasorunde: {os.path.exists(path_fonts)}")
    if os.path.exists(path_fonts):
        print(f"    [OK] Yol: {path_fonts}")
    else:
        print(f"    [HATA] Yol: {path_fonts}")

print("\n" + "=" * 60)
print("KOD KONTROLÜ")
print("=" * 60)

# app.py dosyasını oku ve kontrol et
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
    # fonts_dir kullanımı var mı?
    if 'fonts_dir' in content:
        print("[UYARI] Kodda 'fonts_dir' kullanimi bulundu!")
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'fonts_dir' in line:
                print(f"  Satir {i}: {line.strip()}")
    else:
        print("[OK] Kodda 'fonts_dir' kullanimi YOK - Proje kokunde ariyor")
    
    # os.path.join(app_dir, "fonts") kullanımı var mı?
    if 'os.path.join(app_dir, "fonts")' in content or "os.path.join(app_dir, 'fonts')" in content:
        print("[UYARI] Kodda fonts/ klasoru kullanimi bulundu!")
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'fonts' in line and 'join' in line:
                print(f"  Satir {i}: {line.strip()}")
    else:
        print("[OK] Kodda fonts/ klasoru kullanimi YOK - Proje kokunde ariyor")
    
    # os.path.join(app_dir, filename) kullanımı var mı? (doğru versiyon)
    if 'os.path.join(app_dir, filename)' in content:
        print("[OK] Kodda 'os.path.join(app_dir, filename)' kullanimi VAR - Proje kokunde ariyor")
    else:
        print("[UYARI] Kodda 'os.path.join(app_dir, filename)' kullanimi bulunamadi!")

print("=" * 60)
