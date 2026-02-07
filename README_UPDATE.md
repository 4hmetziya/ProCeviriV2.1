# ProCeviri V2.3 - Güncellemeler ve Değişiklikler

## 🚀 **Yeni Özellikler**

### **AI Motor Değişikliği**
- ❌ **Gemini AI** kaldırıldı
- ✅ **Groq AI (Llama 3.3-70b-versatile)** eklendi
- ✅ **Google Translate** fallback olarak korundu

### **Modern Arayüz**
- 🎨 **AI Toggle Switch**: Modern toggle ile AI kullanımı kontrol edilir
- 🎨 **Dinamik API Key**: AI açıkken görünür, kapalıyken gizli
- 🎨 **3 Çeviri Tonu**: Genel, Teknik/Akademik, Kod Odaklı
- 🎨 **Kalıcı Ayarlar**: Kullanıcı tercihleri localStorage'da saklanır

### **İşlem Kurtarma**
- 🔄 **Sayfa Yenileme Koruma**: F5 basıldığında ayarlar korunur
- 🔄 **Devam Eden İşlem**: Sayfa yenilenirse işlem otomatik devam eder
- 🔄 **Arayüz Devamlılığı**: Progress bar ve durum mesajları korunur

## 📋 **Kurulum**

### **Gereksinimler**
```bash
pip install -r requirements.txt
```

### **Başlatma**
```bash
# Windows
START_SERVER.bat

# Manuel
python app.py
```

### **API Anahtarı**
- Groq AI kullanmak için: https://console.groq.com/
- API anahtarını arayüzden girin veya localStorage'a kaydedin

## 🎯 **Kullanım**

### **Standart Mod (AI Kapalı)**
- Google Translate motorunu kullanır
- Hızlı ve güvenilir çeviri
- API anahtarı gerekmez

### **Gelişmiş Mod (AI Açık)**
- Groq AI (Llama 3.3) motorunu kullanır
- Daha yüksek kalitede çeviri
- Teknik terimleri daha iyi anlar
- API anahtarı gerekir

## 🔧 **Teknik İyileştirmeler**

### **Çeviri Kalitesi**
- 📝 **Karakter Sınırı**: Çeviri orijinal uzunluğu geçmez
- 📝 **Teknik Kelime Koruması**: Linux komutları korunur
- 📝 **Mizanpaj Koruma**: Alt satırlar engellenir
- 📝 **Kutu Sığdırma**: Metin PDF kutusuna tam sığar

### **Performans**
- ⚡ **Dinamik Token Limit**: Metin uzunluğuna göre ayarlanır
- ⚡ **Font Optimizasyonu**: Gerekirse font otomatik küçültülür
- ⚡ **Akıllı Önbellek**: Bellek yönetimi iyileştirildi

## 📁 **Dosya Yapısı**

```
ProCeviri_V2/
├── app.py                 # Ana uygulama
├── requirements.txt        # Python bağımlılıkları
├── START_SERVER.bat       # Windows başlatıcı
├── .gitignore            # Git ignore dosyası
├── templates/
│   └── index.html        # Web arayüzü
├── uploads/              # Geçici PDF dosyaları
└── fonts/               # PDF fontları
```

## 🌐 **Web Arayüzü**

- **Modern Tasarım**: Tailwind CSS ile şık arayüz
- **Dark Mode**: Koyu tema desteği
- **Responsive**: Mobil uyumlu
- **Gerçek Zamanlı**: Anlık durum takibi

## 🔐 **Güvenlik**

- **API Key Koruma**: Yerel olarak saklanır
- **Geçici Dosyalar**: Otomatik temizlenir
- **Hata Yönetimi**: Detaylı loglama

---

**ProCeviri V2.3** - Artık daha akıllı, daha hızlı ve daha güvenilir! 🚀
