@echo off
echo ========================================
echo ProCeviri V2.3 PDF Cevirici Sunucusu Baslatiliyor...
echo ========================================
echo.
echo Calisma Dizini: %CD%
echo.
cd /d "%~dp0"
echo Aktif Dizin: %CD%
echo.

echo [1/3] Python bagimliliklari kontrol ediliyor...
python -m pip install -r requirements.txt -q
echo.

echo [2/3] Groq AI ve Google Translate motorlari hazirlaniyor...
echo.

echo [3/3] Sunucu baslatiliyor...
echo.
echo NOT: AI kullanmak icin Groq API anahtari gereklidir!
echo Web arayuzu: http://localhost:5000
echo.
python app.py
echo.
echo Sunucu durduruldu.
pause
