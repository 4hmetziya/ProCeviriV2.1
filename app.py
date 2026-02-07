# Project: ProCeviri AI Translation Tool
# Developer: Ahmet Ziya OĞUZ
# Date: 2026

import sys
import io
# Sistem Kodlamasını Zorla
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from flask import Flask, render_template, request, Response, send_file, url_for, redirect
import fitz  # PyMuPDF
import gc
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black
from pypdf import PdfWriter, PdfReader
from deep_translator import GoogleTranslator
# import google.generativeai as genai  # Gemini devre dışı
from groq import Groq  # Groq ana motor
import os
import io
import re
import sys
import time
import json
import unicodedata
from werkzeug.utils import secure_filename as werkzeug_secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- KRİTİK EKLEME: Sunucu nerede çalışırsa çalışsın fontu bulması için ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# İlerleme durumunu tutacak global sözlük (Basitlik için)
progress_status = {}

# --- GÜVENLİ DOSYA YÖNETİMİ ---
def secure_filename(filename):
    """
    Türkçe karakterleri ve boşlukları temizleyen güvenli dosya isimlendirme fonksiyonu.
    Örn: "Öğrenci Belgesi.pdf" -> "ogrenci_belgesi.pdf"
    """
    if not filename:
        return "unknown_file.pdf"
    
    # Werkzeug'ün secure_filename fonksiyonunu kullan
    safe_name = werkzeug_secure_filename(filename)
    
    # Türkçe karakterleri ASCII'ye çevir
    try:
        # Unicode normalization ve Türkçe karakter çevirisi
        name_part, ext_part = os.path.splitext(safe_name)
        
        # Türkçe karakterleri İngilizce karşılıklarına çevir
        turkish_chars = {
            'ç': 'c', 'Ç': 'C',
            'ğ': 'g', 'Ğ': 'G', 
            'ı': 'i', 'İ': 'I',
            'ö': 'o', 'Ö': 'O',
            'ş': 's', 'Ş': 'S',
            'ü': 'u', 'Ü': 'U'
        }
        
        # Karakter çevirisi
        for turkish, english in turkish_chars.items():
            name_part = name_part.replace(turkish, english)
        
        # Boşlukları alt çizgiye çevir
        name_part = re.sub(r'\s+', '_', name_part.strip())
        
        # Birden fazla alt çizgiyi tekilleştir
        name_part = re.sub(r'_+', '_', name_part)
        
        # Başlangıç ve sondaki alt çizgileri temizle
        name_part = name_part.strip('_')
        
        # Eğer isim boş kaldıysa varsayılan isim kullan
        if not name_part:
            name_part = "converted_file"
        
        # Uzantıyı geri ekle
        final_name = name_part + ext_part.lower() if ext_part else name_part + ".pdf"
        
        return final_name
        
    except Exception as e:
        # Hata durumunda timestamp ile benzersiz isim oluştur
        timestamp = int(time.time())
        return f"converted_file_{timestamp}.pdf"

# --- FONT YOLLARI GÜNCELLENDİ (Sadece yol eklendi, yapı bozulmadı) ---
FONTS = {
    "Regular": os.path.join(BASE_DIR, "tr_font_reg.ttf"), 
    "Bold": os.path.join(BASE_DIR, "tr_font_bold.ttf"),
    "Italic": os.path.join(BASE_DIR, "tr_font_italic.ttf"), 
    "BoldItalic": os.path.join(BASE_DIR, "tr_font_bi.ttf"),
    "Mono": os.path.join(BASE_DIR, "tr_font_mono.ttf"), 
    "Serif": os.path.join(BASE_DIR, "tr_font_serif.ttf"),
    "Light": os.path.join(BASE_DIR, "tr_font_light.ttf"), 
    "Black": os.path.join(BASE_DIR, "tr_font_black.ttf")
}

# Basit Prompt (Flash için - Hız öncelikli)
SIMPLE_PROMPT = "Sen bir çevirmensin. Verilen metni hedef dile çevir."

# Gelişmiş Prompt (Pro için - Teknik doğruluk öncelikli)
ADVANCED_PROMPT = """Sen teknik bir çevirmensin. ŞU KELİMELERİ ASLA ÇEVİRME: Git, Commit, Push, Pull, Merge, Branch, Repo, Repository, Clone, Fork, Checkout, PR, Pull Request, Staging, Pipeline. Kod bloklarını koru.cat, tar, head, tail, ls, mkdir, rm, chmod, chown, chgrp, pwd, wget, ssh, ftp, ping, whois.
Ayrıca chmod parametrelerini (u, g, o, a, +, -, =) asla değiştirme. 
'cat file.txt' gibi ifadeleri 'kedi dosya.txt' yapma!

For form headers like "Name (Given Name)", translate CONCISELY. Example: instead of "Name (Given Name)", just write "Name". Keep text SHORT to fit in small boxes."""

def restore_technical_terms(text):
    """
    Çeviri sonrasında bozulan teknik terimleri ve Linux komutlarını 
    orijinal hallerine (İngilizce/Teknik) geri döndürür.
    """
    if text is None:
        return None

    replacements = [
        # --- Git & GitHub Terimleri ---
        ("Çekme isteği", "Pull Request"),
        ("çekme talebi", "pull request"),
        ("Taahhüt", "Commit"),
        ("taahhüt", "commit"),
        ("işlemek", "commit"),
        ("Şube", "Branch"),
        ("şube", "branch"),
        ("Depo", "Repo"),
        ("Birleştirme", "Merge"),
        ("İtmek", "Push"),
        ("Çekmek", "Pull"),
        
        # --- Linux Komutları (Hayvan ve Zift Sorunu Çözümü) ---
        ("kedi", "cat"),
        ("Kedi", "cat"),
        ("katran", "tar"),
        ("Katran", "tar"),
        ("tura", "head"),
        ("Tura", "head"),
        ("kuyruk", "tail"),
        ("Kuyruk", "tail"),
        ("dizin", "directory"),
        ("Dizin", "directory"),
        ("pwd", "pwd"),
        ("ls", "ls"),
        ("mkdir", "mkdir"),
        ("rm", "rm"),
        ("cp", "cp"),
        ("mv", "mv"),
        ("ln", "ln"),
        ("more", "more"),
        ("less", "less"),
        ("wget", "wget"),
        ("ping", "ping"),
        ("whois", "whois"),
        ("ssh", "ssh"),
        ("ftp", "ftp"),
        
        # --- Fonksiyon Adı Korumaları ---
        ("calculate_factorial", "hesapla_faktöriyel"),
        ("hesapla faktöriyel", "hesapla_faktöriyel"),
        ("hesaplaFaktöriyel", "hesapla_faktöriyel"),
    ]

    for src, dst in replacements:
        text = text.replace(src, dst)
    
    # regex ile fonksiyon çağrılarını (örnekteki özel durum için) daha güvenli düzelt
    import re
    if "hesapla_faktöriyel" in text and "calculate_factorial" in text:
        text = re.sub(r'\bcalculate_factorial\b', 'hesapla_faktöriyel', text)
    
    # Tekrarlanan teknik komutları temizle (daha agresif regex)
    # Aradaki -> gibi işaretlere rağmen tekrarları yakalar
    text = re.sub(r'(.{7,})\s*[\W_]+\s*\1', r'\1', text, flags=re.IGNORECASE)
    
    # > veya -> işaretinden sonra gelen gereksiz kelime tekrarlarını temizle
    # Örn: "telnet > telnet" -> "telnet", "ssh -> ssh" -> "ssh"
    text = re.sub(r'(\b\w+\b)(?:\s*[-=]*>\s*\1)+', r'\1', text, flags=re.IGNORECASE)
    
    # SSH açıklamasındaki satır arası boşluğu kontrol et ve düzenle
    # 'bağlanır' kelimesinden sonra çok az boşluk varsa ekle
    if 'bağlanır' in text and 'ssh' in text.lower():
        # SSH açıklamalarında satır sonlarında boşluk eksikliğini düzelt
        text = re.sub(r'(bağlanır)(?=\s*[^\s])', r'\1 ', text)
    
    return text

def hex_to_rgb(color_int):
    """PDF renk kodunu (integer) ReportLab için 0-1 arası RGB değerine dönüştürür."""
    if not isinstance(color_int, int): return (0, 0, 0)
    r = ((color_int >> 16) & 255) / 255.0
    g = ((color_int >> 8) & 255) / 255.0
    b = (color_int & 255) / 255.0
    return (r, g, b)

def is_bilingual_pattern(text):
    """
    Kısa metinlerde çift dilli yapıyı tespit eder.
    Örn: 'Soyadı (Surname)', 'Adı (Name)', 'Tarih (Date)'
    """
    if len(text) >= 60:  # Sadece kısa metinler için geçerli
        return False
    
    # Parantez içinde İngilizce kelime tespiti
    import re
    bilingual_pattern = r'\b\w+\s*\(\s*[A-Za-z]+\s*\)'
    match = re.search(bilingual_pattern, text)
    
    if match:
        # Parantez içindeki kelimenin gerçekten İngilizce olup olmadığını kontrol et
        word_in_parentheses = match.group().strip('()').strip()
        # Eğer parantez içindeki kelime yaygın İngilizce kelimelerden biri ise
        common_english_words = ['name', 'surname', 'date', 'title', 'description', 'status', 'type', 'id', 'code', 'number', 'version']
        if word_in_parentheses.lower() in common_english_words:
            return True
    
    return False

def is_atomic_math_or_keyword(text):
    """
    C/C++ benzeri kod satırlarını ve temel matematiksel ifadeleri
    Python tarafında yakalar. True → ÇEVİRME (atomik bırak),
    False → ÇEVİRİYE GİTSİN.
    """
    if text is None:
        return False

    text = text.strip()
    if not text:
        return False

    # // ile başlayan yorum satırları çevrilebilir → atomik DEĞİL
    if text.startswith("//"):
        return False

    # --- 1) KOD TESPİTİ (En öncelikli) ---

    # #include ile başlayan satırlar
    if text.startswith("#include"):
        return True

    # C/C++ anahtar kelimeleri ile başlayan ve ardından ; ( ) { } gibi yapılar gelen satırlar
    if re.match(r"^(int|void|char|float|double|struct|class|return)\b", text):
        if re.search(r"[;(){}]", text):
            return True

    # printf, scanf, std::, cout içeren fonksiyon çağrıları
    lowered = text.lower()
    if ("printf" in lowered) or ("scanf" in lowered) or ("std::" in text) or ("cout" in text):
        return True

    # --- Linux Komutları ---
    # text.lower().strip() kullanarak büyük/küçük harf hassasiyetini ortadan kaldır
    normalized_text = text.lower().strip()
    linux_commands = ["pwd", "ls", "mkdir", "rm", "cp", "mv", "ln", "cat", "more", "less", "head", "tail", "tar", "wget", "ping", "whois", "ssh", "ftp"]
    
    # Sadece komut本身 veya komut + parametre durumlarını yakala (örn: "ls", "ls -la")
    for cmd in linux_commands:
        # Sadece komut本身
        if normalized_text == cmd:
            return True
        # Komut + parametre (örn: "ls -la", "mkdir -p /home/user")
        if normalized_text.startswith(cmd + " "):
            return True

    # --- Dosya Yolu Koruması ---
    # / ile başlayan veya içeren, boşluk içermeyen dosya yollarını yakala
    # Örn: /home/user/file, ./script.sh, ../config/app.conf
    if re.search(r'^\/?[^\s]*\/[^\s]*$|^\.[^\s]*\/[^\s]*$|^\.\.[^\s]*\/[^\s]*$', text):
        return True

    # Satır sonunda ; olan ve içinde = geçen atama işlemleri
    if text.endswith(";") and "=" in text:
        return True

    # Sadece { veya } içeren satırlar
    if re.fullmatch(r"[{}]+", text):
        return True

    # --- 2) SAYISAL VERI KORUMASI ---
    # Sadece rakamlardan, tarihlerden veya noktalama işaretli sayılardan oluşuyorsa çevirme
    if len(text) < 60:  # Sadece kısa metinler için
        # Sadece rakamlar (123456789, 01.01.2005)
        if re.fullmatch(r'^[0-9./\-]+$', text):
            return True
        
        # Tarih formatları (01/01/2005, 2025-01-01)
        if re.fullmatch(r'^[0-9]{2,4}[./\-][0-9]{2}[./\-][0-9]{2,4}$', text):
            return True
        
        # Noktalı sayılar (2.83, 101101, 15.99)
        if re.fullmatch(r'^[0-9]*\.?[0-9]+$', text) and text.count('.') <= 1:
            return True

    # --- 3) REGEX İZİN/KOD BLOKLARI KORUMASI ---
    # Linux izinleri (drwxr-xr-x, -rw-r--r--)
    if re.fullmatch(r'^[-dclpsb]?[-rwxs]{9}$', text):
        return True
    
    # Belge doğrulama kodları (YOKTRE-123, NO-12345)
    if re.fullmatch(r'^[A-Z]{2,}-?[0-9]+$', text):
        return True
    
    # Teknik kod blokları (ERR-404, HTTP-200)
    if re.fullmatch(r'^[A-Z]{3,}-?[0-9]{3,}$', text):
        return True

    # --- 4) MATEMATİKSEL İFADE TESPİTİ ---
    # Eşittir (=) içeren ve görece kısa, boşluksuz denklemler (E=mc^2 vb.)
    if "=" in text and " " not in text and len(text) <= 30:
        has_letter = re.search(r"[A-Za-z]", text) is not None
        has_digit = re.search(r"\d", text) is not None
        if has_letter and has_digit:
            return True

    # --- 3) Diğer her şey çeviriye gitsin ---
    return False

def translate_content_hybrid(text, translator, api_key=None, target_lang="tr", translation_tone="general", use_ai=False, job_id=None):
    text = text.strip()
    if not text: return None
    if is_atomic_math_or_keyword(text): return text
    clean = text.replace(".", "").replace(")", "").replace("(", "").strip()
    if clean.isdigit(): return text
    if len(text) < 2 and text.isalpha(): return text

    # Çeviri Kararı: AI kapalı ise direkt Google Translate kullan
    if not use_ai:
        print("[MOD] Standart Çeviri Modu (AI Kapalı)")
        translated = translator.translate(text)
        if translated:
            translated = unicodedata.normalize('NFKC', translated)
        return translated

    # AI açık ise Groq motorunu kullan
    print("[MOD] Gelişmiş AI Çeviri Aktif (Groq/Llama)")
    if api_key:
        groq_success = False
        retry_count = 0
        
        while retry_count < 2 and not groq_success:
            try:
                # Groq Client oluştur
                client = Groq(api_key=api_key)
                print(f"[GROQ] Client oluşturuldu, çeviri başlatılıyor...")
                
                # Model Seçimi: llama-3.3-70b-versatile
                model_name = "llama-3.3-70b-versatile"
                print(f"[GROQ] {model_name} modeli kullanılıyor...")
                
                # Metni Hazırla: UTF-8 olarak normalize et
                normalized_text = unicodedata.normalize('NFKC', text)
                print(f"[GROQ] Metin hazırlandı: {normalized_text[:50]}...")
                
                # Karakter Kaçışlarını Engelle: Fazlalık tırnakları temizle
                clean_text = text.strip('"').strip("'")
                
                # Prompt Formatını Değiştir: Akademik terminoloji ve karakter sınırı ile
                original_length = len(clean_text)
                max_tokens = min(int(original_length * 1.5), 1024)  # Orijinalin 1.5 katını geçme
                
                # Akademik Sözlük Ekle
                academic_note = ""
                if translation_tone == "academic":
                    academic_note = "This is a transcript. Use academic terminology: Major = Major, Formal Education = Formal Education, Grade = Grade. "
                
                prompt = f"""{academic_note}Task: Translate the text below to {target_lang} line-by-line.
RULES:

Keep the exact number of lines.

Do NOT explain what the commands do.

Do NOT start with "Here is the translation" or "becomes:".

Do NOT translate technical commands (cp, mv, ls, echo, etc.).

EXAMPLES:

Input: File Commands • cp (-r, -R) text.txt • mv file1 file2

Output: Dosya Komutları • cp (-r, -R) text.txt • mv file1 file2

REAL INPUT TO TRANSLATE: '{clean_text}' """
                
                # Hız ve Güvenlik: Çok kısa bekleme
                time.sleep(0.1)  # Ücretsiz kota için
                
                # Mesaj Yapısını Basitleştir: Sadece user rolü
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=0.0  # AI'nın sadece çeviriye odaklanması
                )
                
                translated = response.choices[0].message.content.strip()
                print(f"[GROQ] Çeviri başarılı: {translated[:50]}...")
                
                # Strip ve Join İşlemi: Beklenmedik satır atlamalarını temizle
                translated = translated.strip()
                print(f"[GROQ] Satır temizleme: '{translated[:50]}...'")
                
                # Unicode karakterleri normalize et
                if translated:
                    translated = unicodedata.normalize('NFKC', translated)
                groq_success = True
                return translated
                
            except Exception as e:
                print(f'!!! KRİTİK GROQ HATASI: {e}')  # ZORUNLU HATA KAYDI
                print(f"Hata detayı: {type(e).__name__}, {e}")  # Detaylı hata yakalama
                retry_count += 1
                if retry_count < 2:
                    time.sleep(2)  # 2 saniye bekle ve tekrar dene
                else:
                    # İkinci deneme de başarısız oldu, fallback'e geç
                    if job_id and job_id in progress_status:
                        progress_status[job_id]['fallback_used'] = True
                        progress_status[job_id]['status_message'] = 'Groq hatası, Google Translate devreye girdi'
                    break
        
        # Fallback: Deep-Translator/Google
        try:
            print("[FALLBACK] Google Translate kullanılıyor...")
            translated = translator.translate(text)
            if translated:
                translated = unicodedata.normalize('NFKC', translated)
            return translated
        except Exception as e:
            print(f"[FALLBACK] Google Translate hatası: {e}")
            return text  # Son çare: orijinal metni döndür
    else:
        # API anahtarı yoksa doğrudan Google Translate kullan
        translated = translator.translate(text)
        if translated:
            translated = unicodedata.normalize('NFKC', translated)
        return translated

def translate_wrapper(text, translator, api_key=None, target_lang="tr", translation_tone="general", use_ai=False, job_id=None):
    """
    Ana çeviri fonksiyonunu çağırır ve sonucunu Terminator düzeltme fonksiyonundan geçirir.
    """
    
    # --- ÖZEL SÖZLÜK: Tablo başlıklarını zorla kısalt (SADECE İngilizce için) ---
    # SADECE hedef dil İngilizce ise bu zorlamayı yap
    if target_lang == 'en':
        forced_headers = {
            "Öğrenci No": "Student ID",
            "Ogrenci No": "Student ID",
            "T.C. Kimlik No": "TR ID",
            "TC Kimlik No": "TR ID",
            "Adı": "Name",
            "Soyadı": "Surname",
            "Doğum Tarihi": "Birth Date",
            "Baba Adı": "Father Name",
            "Ana Adı": "Mother Name",
            "Doğum Yeri": "Birth Place"
        }
        
        clean_search = text.replace(':', '').strip()
        for tr_key, en_val in forced_headers.items():
            if tr_key in clean_search and len(text) < 40:
                return en_val
    
    # --- AKILLI FİLTRELEME ---
    
    # 1. Bilingual (Çift Dilli) Tespiti
    if len(text) < 60 and is_bilingual_pattern(text):
        print(f"  [AKILLI] Bilingual tespit edildi, çeviri atlandı: {text[:50]}...")
        return text
    
    # 2. Mevcut kontrolleri devam et
    if is_atomic_math_or_keyword(text):
        return text
    
    final_translated_text = translate_content_hybrid(
        text,
        translator,
        api_key=api_key,
        target_lang=target_lang,
        translation_tone=translation_tone,
        use_ai=use_ai,
        job_id=job_id
    )
    if final_translated_text is None:
        return None
    return restore_technical_terms(final_translated_text)

def fit_text_to_box(c, text, font_name, max_width, start_size):
    # Hedef kutu genişliğini orijinal genişlik olarak kullan (toleranssız)
    adjusted_max_width = max_width
    size = start_size
    
    # Unicode karakterler için metni normalize et (NFC kullanarak karakter birleştirmesini sağla)
    try:
        normalized_text = unicodedata.normalize('NFC', text)
    except:
        normalized_text = text
    
    # Türkçe karakterler için genişlik hesaplaması
    try:
        text_width = pdfmetrics.stringWidth(normalized_text, font_name, size)
    except:
        # Hata durumunda orijinal metinle dene
        text_width = pdfmetrics.stringWidth(text, font_name, size)
        normalized_text = text
    
    # Font boyutunu 5.5pt'ye kadar küçültmesine izin ver (okunabilirlik öncelikli)
    # Başlıklar için özel minimum font boyutu
    special_headers = ["Student ID", "TR ID", "Name", "Surname", "Birth Date", "Father Name", "Mother Name", "Birth Place"]
    min_size = 5.0 if text in special_headers else 5.5
    
    while text_width > adjusted_max_width and size > min_size:
        size -= 0.5
        try:
            text_width = pdfmetrics.stringWidth(normalized_text, font_name, size)
        except:
            text_width = pdfmetrics.stringWidth(text, font_name, size)
    return size

def draw_wrapped_text(c, text, x, y, max_width, font_name, original_size, color):
    # GÜVENLİK PAYI: Metnin en sağa yapışıp kesilmesini önlemek için 
    # kutu genişliğinden 5 piksel çalıyoruz.
    safe_max_width = max_width - 5 
    if safe_max_width < 10: safe_max_width = max_width # Çok dar kutularda yapma
    
    # 1. Önce okunabilir bir boyutta (örn: 6.5pt) tek satıra sığıyor mu bak
    min_readable_size = 6.5
    try:
        # Genişliği hesapla (Hata olursa tahmini değer kullan)
        width_at_min = pdfmetrics.stringWidth(text, font_name, min_readable_size)
    except:
        width_at_min = len(text) * 3
    
    # Eğer minimum boyutta tek satıra sığıyorsa, normal sıkıştırma (fit_text_to_box) yap
    if width_at_min <= safe_max_width:
        final_size = fit_text_to_box(c, text, font_name, safe_max_width, original_size)
        c.setFont(font_name, final_size)
        r, g, b = hex_to_rgb(color)
        c.setFillColorRGB(r, g, b)
        c.drawString(x, y, text)
        return
    
    # 2. SIĞMIYORSA: Metni 2 satıra böl (Wrapping)
    words = text.split()
    if len(words) > 1:
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        
        wrap_size = 6.5 
        # Bölünen satırları da taşmasın diye gerekirse sıkıştır
        size1 = fit_text_to_box(c, line1, font_name, safe_max_width, wrap_size)
        size2 = fit_text_to_box(c, line2, font_name, safe_max_width, wrap_size)
        final_wrap_size = min(size1, size2, wrap_size) # İkisi de aynı boyda olsun
        
        c.setFont(font_name, final_wrap_size)
        r, g, b = hex_to_rgb(color)
        c.setFillColorRGB(r, g, b)
        
        # Dikey hizalama: Satırı yukarı ve aşağı kaydırarak ortala
        offset = final_wrap_size * 0.6
        c.drawString(x, y + offset, line1)  # Üst satır
        c.drawString(x, y - offset, line2)  # Alt satır
    else:
        # Tek kelimeyse... (Mevcut kod aynı kalsın)
        final_size = fit_text_to_box(c, text, font_name, safe_max_width, original_size)
        c.setFont(font_name, final_size)
        r, g, b = hex_to_rgb(color)
        c.setFillColorRGB(r, g, b)
        c.drawString(x, y, text)

def get_advanced_style(lines_spans, registered_fonts):
    sizes = []
    found_color = None
    detected_style = "Regular"
    for span in lines_spans:
        text = span.get("text", "").strip()
        if not text: continue
        sizes.append(span.get("size", 12))  # Default 12pt
        span_color = span.get("color", 0)
        if span_color > 0 and found_color is None: found_color = span_color
        flags = span.get("flags", 0)  # Default 0
        font_name_pdf = span.get("font", "Helvetica").lower()  # Default Helvetica
        if "mono" in font_name_pdf or "courier" in font_name_pdf: detected_style = "Mono"
        elif "serif" in font_name_pdf or "times" in font_name_pdf: detected_style = "Serif"
        elif "light" in font_name_pdf: detected_style = "Light"
        elif "black" in font_name_pdf: detected_style = "Black"
        if detected_style == "Regular":
            is_bold = flags & 16
            is_italic = flags & 2
            if is_bold and is_italic: detected_style = "BoldItalic"
            elif is_bold: detected_style = "Bold"
            elif is_italic: detected_style = "Italic"
    if detected_style not in registered_fonts:
        if detected_style == "Black" and "Bold" in registered_fonts: detected_style = "Bold"
        else: detected_style = "Regular"
    final_color = found_color if found_color is not None else 0
    final_size = sum(sizes) / len(sizes) if sizes else 10
    return detected_style, final_color, final_size

def draw_smart_text(c, text, x, y, max_width, font_name, font_size):
    """
    Metni akıllıca kelime kelime bölerek kutuya sığdırır.
    Türkçe karakterler için NFC normalizasyonu kullanır.
    Koordinat kontrolü ve font boyutu ayarı içerir.
    """
    if not text or not text.strip():
        return y
    
    # Türkçe karakterler için metni normalize et
    try:
        clean_text = unicodedata.normalize('NFC', text)
    except:
        clean_text = text
    
    # Koordinat Kontrolü: Font boyutunu dinamik ayarla
    current_font_size = font_size
    min_font_size = max(font_size - 3, 6)  # En fazla 3 punto küçült, minimum 6
    
    # Metin kutuya sığana kadar fontu küçült
    while current_font_size > min_font_size:
        test_width = pdfmetrics.stringWidth(clean_text, font_name, current_font_size)
        if test_width <= max_width:
            break
        current_font_size -= 1
    
    if current_font_size != font_size:
        print(f"[KOORDINAT] Font boyutu {font_size} -> {current_font_size} olarak ayarlandı")
    
    # Metni kelimelere böl
    words = clean_text.split()
    current_line = ""
    current_y = y
    line_height = current_font_size * 1.2  # Satır arası boşluk
    
    for word in words:
        # Eğer kelimeyi mevcut satıra ekleyebilirsek
        test_line = current_line + (" " if current_line else "") + word
        line_width = pdfmetrics.stringWidth(test_line, font_name, current_font_size)  # Dinamik font boyutunu kullan
        
        if line_width <= max_width:
            # Kelime satıra sığar, ekle
            current_line = test_line
        else:
            # Kelime satıra sığmaz, mevcut satırı yaz ve yeni satıra geç
            if current_line:
                try:
                    c.setFont(font_name, current_font_size)  # Dinamik font boyutunu ayarla
                    c.drawString(x, current_y, current_line)
                except Exception as e:
                    c.setFont(font_name, current_font_size)
                    c.drawString(x, current_y, str(current_line))
                current_y -= line_height
            
            # Eğer tek bir kelime bile max_width'dan büyükse, kelimeyi böl
            word_width = pdfmetrics.stringWidth(word, font_name, current_font_size)
            if word_width > max_width:
                # Kelimeyi karakter karakter böl
                for i, char in enumerate(word):
                    char_test = current_line + char
                    char_width = pdfmetrics.stringWidth(char_test, font_name, current_font_size)
                    if char_width <= max_width:
                        current_line += char
                    else:
                        if current_line:
                            try:
                                c.setFont(font_name, current_font_size)  # Dinamik font boyutunu ayarla
                                c.drawString(x, current_y, current_line)
                            except Exception as e:
                                c.setFont(font_name, current_font_size)
                                c.drawString(x, current_y, str(current_line))
                            current_y -= line_height
                        current_line = char
            else:
                current_line = word
    
    # Son satırı yaz
    if current_line:
        try:
            c.setFont(font_name, current_font_size)  # Dinamik font boyutunu ayarla
            c.drawString(x, current_y, current_line)
        except Exception as e:
            c.setFont(font_name, current_font_size)
            c.drawString(x, current_y, str(current_line))
        current_y -= line_height
    
    return current_y

def process_pdf_logic(input_path, output_path, api_key, job_id, source_lang, target_lang, translation_tone="general", use_ai=False, translator=None):
    # --- KESİN ÇÖZÜM: DEĞİŞKENLERİ EN BAŞTA TANIMLA ---
    target_font = "TrFont-Regular"  # Varsayılan font
    final_size = 10                # Varsayılan boyut
    safe_font = "TrFont-Regular"    # Emniyet fontu
    x = 50                         # Varsayılan koordinatlar
    y = 700
    # ------------------------------------------------
    
    registered_fonts = {}
    app_dir = os.path.dirname(os.path.abspath(__file__))
    # Fontlar proje kökünde (app.py ile aynı dizinde)
    for style, filename in FONTS.items():
        # --- DÜZELTME: BASE_DIR kullanılarak tam yol garantilendi ---
        path = filename 
        if os.path.exists(path):
            try:
                font_key = f"TrFont-{style}"
                pdfmetrics.registerFont(TTFont(font_key, path))
                registered_fonts[style] = font_key
            except Exception as e:
                print(f"⚠️ Font yükleme hatası [{style}]: {e}")
                pass
    
    # Fontlar yüklenemediyse uyarı ver ve Regular fontunu zorla yükle
    if not registered_fonts:
        print("⚠️ UYARI: Hiçbir font yüklenemedi! Türkçe karakterler düzgün görünmeyebilir.")
        regular_path = FONTS.get("Regular")
        if regular_path and os.path.exists(regular_path):
            try:
                pdfmetrics.registerFont(TTFont("TrFont-Regular", regular_path))
                registered_fonts["Regular"] = "TrFont-Regular"
                print("✅ Regular fontu zorla yüklendi!")
            except Exception as e:
                print(f"❌ Regular fontu yüklenemedi: {e}")
    
    default_font = registered_fonts.get("Regular", "Helvetica")
    
    # --- TRANSLATOR KONTROLÜ ---
    if translator is None:
        print("[HATA] Translator objesi None! Standart çeviri yapılamaz.")
        return
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    doc = fitz.open(input_path)
    total_pages = len(doc)
    
    # --- İŞLEME DÖNGÜSÜ ---
    for page_num, page in enumerate(doc):
        print(f'Sayfa {page_num + 1} işleniyor...')  # Detaylı log
        
        # --- SAYFA BAŞINDA BATCH LİSTESİNİ SIFIRLA ---
        if hasattr(translate_content_hybrid, '_page_texts'):
            translate_content_hybrid._page_texts = []
        if hasattr(translate_content_hybrid, '_original_coords'):
            translate_content_hybrid._original_coords = []
        
        progress_status[job_id] = {
            'current': page_num + 1,
            'total': total_pages,
            'status': f'{page_num + 1} / {total_pages} sayfa işleniyor...'
        }
        print(f"[DURUM] {progress_status[job_id]['status']}")
        
        c.setPageSize((page.rect.width, page.rect.height))
        blocks = page.get_text("dict")["blocks"]
        last_written_y = None  # Dinamik koordinat takibi için
        
        # --- ADIM 1: VERİYİ TOPLA (COLLECTION PHASE) ---
        page_data = []  # Bu sayfadaki tüm metin verileri
        
        for block in blocks:
            if "lines" not in block: continue
            
            # --- BLOK BAZLI FİLTRELEME ---
            # Watermark (filigran) bloklarını atla
            block_text = ""
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    block_text += span.get("text", "")
            
            if "Translated by ProCeviri" in block_text or "Dev: Ahmet Ziya OGUZ" in block_text:
                continue  # Bu bloğu atla, zaten sayfa sonunda ekleniyor
            
            for line in block.get("lines", []):
                # RENK BAZLI AYRIŞTIRMA: Aynı renkteki metinleri birleştir, farklı renkleri ayır
                # Turuncu başlık ve siyah maddeleri ayrı tutmak için
                
                spans = line.get("spans", [])
                if not spans: continue
                
                # Her span'i ayrı ayrı işle ama aynı renk olanları birleştir
                current_color = None
                current_text = ""
                current_size = None
                current_font = None
                current_origin = None
                current_flags = None
                
                for span in spans:
                    span_text = span.get("text", "")
                    if not span_text.strip():
                        continue
                        
                    span_color = span.get("color", 0)
                    span_size = span.get("size", 10)
                    span_font_raw = span.get("font", "Helvetica")
                    span_origin = span.get("origin", (0, 0))
                    span_flags = span.get("flags", 0)
                    
                    # İlk span veya renk farklı mı?
                    if current_color is None or span_color != current_color:
                        # Önceki grubu kaydet (varsa)
                        if current_text.strip():
                            style_name, color, size = get_advanced_style([{
                                "text": current_text,
                                "size": current_size,
                                "color": current_color,
                                "font": current_font_raw,
                                "flags": current_flags,
                                "origin": current_origin
                            }], registered_fonts)
                            target_font = registered_fonts.get(style_name, default_font)
                            
                            original_x = current_origin[0]
                            original_y = page.rect.height - current_origin[1]
                            line_width = fitz.Rect(line["bbox"]).width
                            
                            page_data.append({
                                'text': current_text.strip(),
                                'x': original_x,
                                'y': original_y,
                                'font': target_font,
                                'size': size,
                                'color': color,
                                'width': line_width
                            })
                        
                        # Yeni grubu başlat
                        current_color = span_color
                        current_size = span_size
                        current_font_raw = span_font_raw
                        current_origin = span_origin
                        current_flags = span_flags
                        current_text = span_text
                    else:
                        # Aynı renkse birleştir
                        current_text += span_text
                
                # Son grubu da kaydet
                if current_text.strip():
                    style_name, color, size = get_advanced_style([{
                        "text": current_text,
                        "size": current_size,
                        "color": current_color,
                        "font": current_font_raw,
                        "flags": current_flags,
                        "origin": current_origin
                    }], registered_fonts)
                    target_font = registered_fonts.get(style_name, default_font)
                    
                    original_x = current_origin[0]
                    original_y = page.rect.height - current_origin[1]
                    line_width = fitz.Rect(line["bbox"]).width
                    
                    page_data.append({
                        'text': current_text.strip(),
                        'x': original_x,
                        'y': original_y,
                        'font': target_font,
                        'size': size,
                        'color': color,
                        'width': line_width
                    })
        
        # --- ADIM 2: TOPLU İŞLE (PROCESSING PHASE) ---
        print(f"[İŞLEM] Sayfa {page_num + 1}: {len(page_data)} metin toplandı")
        
        # Metinleri 10'arlı gruplar halinde işle
        chunk_size = 10
        for i in range(0, len(page_data), chunk_size):
            chunk = page_data[i:i + chunk_size]
            
            # Grup metinlerini birleştir
            batch_text = "\n".join([item['text'] for item in chunk])
            print(f"[DEBUG] Gönderilen batch ({len(chunk)} satır): {repr(batch_text)}")
            
            # Toplu çeviri yap
            final_text = translate_wrapper(
                batch_text,
                translator,
                api_key=api_key,
                target_lang=target_lang,
                translation_tone=translation_tone,
                use_ai=use_ai,
                job_id=job_id
            )
            
            # --- EŞİTLEME MEKANİZMASI (Google Fallback YERİNE) ---
            translated_lines = final_text.split('\n') if final_text else []
            print(f"[DEBUG] Gelen çeviri ({len(translated_lines)} satır): {repr(final_text)}")
            
            # Eğer AI satırları birleştirdiyse (Eksik satır varsa)
            if len(translated_lines) < len(chunk):
                # Eksik kalan yerleri boşlukla doldur (Mizanpaj kaymasın diye)
                diff = len(chunk) - len(translated_lines)
                translated_lines.extend([""] * diff)
                print(f"[AI EŞİTLEME] {diff} boş satır eklendi. (AI satır birleştirdi)")
            
            # Eğer AI fazladan satır ürettiyse (Çok nadir)
            elif len(translated_lines) > len(chunk):
                # Fazlalığı son satıra ekle ve listeyi kes
                extra_text = " ".join(translated_lines[len(chunk)-1:])
                translated_lines = translated_lines[:len(chunk)-1]
                translated_lines.append(extra_text)
                print(f"[AI EŞİTLEME] Fazla satırlar son satırda birleştirildi.")
            
            # Her bir metni kendi koordinatına yaz
            for j, item in enumerate(chunk):
                if j < len(translated_lines):
                    translated_text = translated_lines[j]
                else:
                    translated_text = item['text']  # Çeviri yoksa orijinal metin
                
                try:
                    # Yeni metin sarma mantığı: Okunabilirlik öncelikli
                    draw_wrapped_text(c, translated_text, item['x'], item['y'], item['width'], item['font'], item['size'], item['color'])
                except Exception as e:
                    print(f"[HATA] Çizim hatası: {e}")
                    # Hata durumunda güvenli font ve küçük boyut kullan
                    safe_font = registered_fonts.get("Regular", default_font)
                    c.setFont(safe_font, 8)
                    c.drawString(item['x'], item['y'], str(translated_text))
        
        # Her sayfanın altına küçük, gri filigran (branding) ekle
        try:
            watermark_text = "Translated by ProCeviri AI | Dev: Ahmet Ziya OGUZ"
            watermark_font = "Helvetica-Oblique"
            watermark_size = 7
            c.setFont(watermark_font, watermark_size)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            text_width = pdfmetrics.stringWidth(watermark_text, watermark_font, watermark_size)
            x_center = (page.rect.width - text_width) / 2.0
            y_bottom = 15 # Changed from 12 to 15
            c.drawString(x_center, y_bottom, watermark_text)
        except:
            pass

        print(f'Sayfa {page_num + 1} tamamlandı.')  # Detaylı log
        
        # Akıllı bekleme: AI kullanımına göre bekleme
        if use_ai and total_pages > 5:
            time.sleep(1)  # AI modu için kısa bekleme
            print(f'  AI modu bekleme: 1 saniye ({total_pages} sayfa için)')
        elif use_ai:
            print(f'  AI modu hızlı: bekleme atlandı ({total_pages} sayfa için)')
        else:
            print(f'  Standart mod: bekleme yok ({total_pages} sayfa için)')
        
        c.showPage()
        
        # --- AGRESİF BELLEK YÖNETİMİ ---
        # Her sayfa sonunda belleği tamamen temizle
        gc.collect()
        
        # Büyük dosyalarda periyodik kontrol - her 5 sayfada bir
        if (page_num + 1) % 5 == 0:
            # PyMuPDF objesini kontrol et ve gerekirse yeniden oluştur
            try:
                # Bellek kullanımını kontrol et
                if hasattr(doc, '_doc') and doc._doc is not None:
                    # Dokümanı kapatıp yeniden açarak belleği boşalt
                    doc_path = doc.name if hasattr(doc, 'name') else input_path
                    doc.close()
                    gc.collect()
                    doc = fitz.open(doc_path)
                    print(f"  [BELLEK] Sayfa {page_num + 1}: Bellek temizlendi, doküman yeniden açıldı")
            except Exception as e:
                print(f"  [BELLEK] Bellek temizleme hatası: {e}")
                # Hata durumunda işlemeye devam et
                pass
    
    doc.close() # <--- Döngü biter bitmez orijinal PDF dosyasını bellekten at
    c.save()
    buffer.seek(0)
    
    # Temizlik ve Birleştirme
    progress_status[job_id]['status'] = 'Dosyalar birleştiriliyor...'
    print(f"[DURUM] {progress_status[job_id]['status']}")
    doc_clean = fitz.open(input_path)
    clean_buffer = io.BytesIO()
    for page in doc_clean:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block: continue
            for line in block["lines"]:
                page.add_redact_annot(line["bbox"], text=None, fill=False)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        gc.collect()
    doc_clean.save(clean_buffer)
    clean_buffer.seek(0)
    doc_clean.close()
    reader_clean = PdfReader(clean_buffer)
    reader_text = PdfReader(buffer)
    writer = PdfWriter()
    
    for i in range(len(reader_clean.pages)):
        page_clean = reader_clean.pages[i]
        if i < len(reader_text.pages):
            page_clean.merge_page(reader_text.pages[i])
        writer.add_page(page_clean)
        
    with open(output_path, "wb") as f:
        writer.write(f)
    
    # --- SON DURUM GÜNCELLEMESİ ---
    try:
        progress_status[job_id]['status'] = 'completed'
        progress_status[job_id]['download_url'] = f"/download/{os.path.basename(output_path)}"
        print(f"[DURUM] İşlem tamamlandı: {progress_status[job_id]['download_url']}")
    except Exception as e:
        print(f"[HATA] Durum güncelleme hatası: {e}")
        # Hata durumunda bile status'u completed yapmaya çalış
        try:
            progress_status[job_id]['status'] = 'completed'
            progress_status[job_id]['download_url'] = f"/download/{os.path.basename(output_path)}"
        except:
            pass


@app.route('/')
def index():
    """Ana sayfa: Artık sunucudan hiçbir geçmiş verisi çekmiyor, sadece arayüzü yükler."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    """Dosya yükleme ve işlem başlatma mantığı."""
    if 'file' not in request.files: 
        return Response(json.dumps({"error": "Dosya seçilmedi!"}), status=400, mimetype="application/json")
    
    file = request.files['file']
    if file.filename == '': 
        return Response(json.dumps({"error": "Dosya adı boş!"}), status=400, mimetype="application/json")
    
    job_id = str(int(time.time()))
    api_key = request.form.get('api_key', '').strip() or None

    source_lang = request.form.get('source_lang', 'auto') or 'auto'
    target_lang = request.form.get('target_lang', 'tr') or 'tr'
    translation_tone = request.form.get('translation_tone', 'general') or 'general'
    use_ai = request.form.get('use_ai') in ['true', 'on', True]  # Switch verisini doğru Boolean'a çevir

    # Eski model_type kontrolünü kaldır (artık use_ai kullanılıyor)
    # if model_type == "pro" and not api_key:
    #     return Response(
    #         json.dumps({"error": "HATA: Pro modunu kullanmak için API Anahtarı şart!"}),
    #         status=400,
    #         mimetype="application/json"
    #     )
    
    # Güvenli dosya isimlendirme kullan
    safe_filename = secure_filename(file.filename)
    input_filename = f"input_{job_id}_{safe_filename}"
    filepath = os.path.join(UPLOAD_FOLDER, input_filename)
    file.save(filepath)
    
    # Çıktı dosyası için de güvenli isimlendirme kullan
    output_filename = f"CEVRILEN_{job_id}_{safe_filename}"
    output_path = os.path.join(UPLOAD_FOLDER, output_filename)
    
    # --- GOOGLE TRANSLATOR OLUŞTURMA ---
    translator = GoogleTranslator(source=source_lang or 'auto', target=target_lang or 'tr')
    print(f"[TRANSLATOR] GoogleTranslator oluşturuldu: {source_lang} → {target_lang}")
    
    # İlk durum güncellemesi - doğrudan doğru verilerle başlat
    progress_status[job_id] = {'current': 0, 'total': 0, 'status': 'İşlem sıraya alındı...'}
    print(f"[DURUM] Job {job_id} başlatıldı: {progress_status[job_id]['status']}")
    
    from threading import Thread
    thread = Thread(target=process_pdf_logic, args=(filepath, output_path, api_key, job_id, source_lang, target_lang, translation_tone, use_ai, translator))
    thread.start()
    
    return json.dumps({'job_id': job_id})

@app.route('/status/<job_id>')
def status(job_id):
    """Frontend'in anlık durum sorgulama kapısı."""
    return json.dumps(progress_status.get(job_id, {'status': 'unknown'}))

@app.route('/download/<filename>')
def download_file(filename):
    """Çevrilen PDF'i indirme kapısı."""
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    # Render'da çalışması için gerekli port yapılandırması
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

