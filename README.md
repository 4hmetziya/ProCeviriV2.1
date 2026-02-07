# 🚀 ProÇeviri AI - V2.1 (Stable & Light Edition)

![Python](https://img.shields.io/badge/Python-3.14%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-red?style=for-the-badge&logo=flask&logoColor=white)
![Groq](https://img.shields.io/badge/AI-Groq_Llama3-orange?style=for-the-badge)
![Render](https://img.shields.io/badge/Deploy-Render_Ready-success?style=for-the-badge&logo=render&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

> **"Doküman yapısını bozmadan, teknik ve akademik PDF'leri yapay zeka gücüyle saniyeler içinde çevirin."**

---

### 🌟 Proje Hakkında
**ProÇeviri AI**, teknik ve akademik belgelerin mizanpajını koruyarak yüksek doğrulukla çeviri yapan **Groq AI (Llama 3)** tabanlı bir web uygulamasıdır. V2.1 sürümü, kısıtlı sunucu kaynaklarında (Render 512MB RAM) bile donma yapmadan büyük PDF'leri işleyebilmek için **"OCR-Free"** mimarisine geçirilmiş en kararlı sürümdür.

### 🚀 Öne Çıkan Özellikler
* ⚡ **Ultra-Hafif Altyapı:** Tesseract OCR veya Poppler gibi ağır bağımlılıklar kaldırılarak %100 taşınabilir yapıya geçildi.
* 🧠 **Hibrit Çeviri:** Hız için **Google Translate**, teknik derinlik için **Groq (Llama 3.3 70B)** motoru kullanılır.
* 🎨 **Kusursuz Mizanpaj:** Orijinal metinler akıllı maskeleme ile kapatılır ve çeviri tam aynı koordinatlara yazılır.
* 🛡️ **Teknik Koruma:** "Git, Commit, Push, Merge" gibi terimlerin bozulmasını engelleyen özel sözlük mekanizması mevcuttur.
* 📉 **RAM Optimizasyonu:** `gc.collect()` ve agresif bellek yönetimi ile düşük donanımlı sunucularda yüksek performans sağlar.

### 🛠️ Teknik Altyapı
* **Backend:** Python 3.14 & Flask
* **AI Engine:** Groq SDK & Deep-Translator
* **PDF İşleme:** PyMuPDF (fitz), ReportLab, PyPDF
* **Frontend:** Modern JavaScript (ES6+) & UI Odaklı Tasarım

### 💻 Kurulum ve Kullanım
1. **Depoyu Klonlayın:** `git clone https://github.com/4hmetziya/ProCeviriV2.1.git`
2. **Gerekli Kütüphaneleri Yükleyin:** `pip install -r requirements.txt`
3. **Uygulamayı Çalıştırın:** `python app.py`  
   *(Erişim: http://localhost:5000)*

> **Not:** AI modunu kullanmak için arayüzden kendi **Groq API Key**'inizi girmeniz gerekmektedir.

### 🌐 Render.com Deployment
Bu proje `Procfile` içerir ve bulut platformlarına anında yüklenmeye hazırdır:
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `gunicorn app:app`

### 👨‍💻 Geliştirici Bilgileri
**Ahmet Ziya OĞUZ** * **Üniversite:** Recep Tayyip Erdoğan Üniversitesi  
* **Bölüm:** Bilgisayar Mühendisliği (1. Sınıf)  
* **Proje Tarihi:** 2026

---

⚖️ **Lisans:** Bu proje **MIT Lisansı** ile korunmaktadır.
