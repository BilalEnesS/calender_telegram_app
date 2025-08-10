# 📅 Telegram Calendar Bot

Bu bot, doğal dil komutlarıyla Google Calendar'a etkinlik eklemenizi sağlar.

## 🚀 Özellikler

- ✅ Doğal dil komutlarıyla etkinlik ekleme
- ✅ Akıllı tarih hesaplama (yarın, pazartesi, vb.)
- ✅ Google Calendar entegrasyonu
- ✅ OpenAI GPT ile gelişmiş anlama
- ✅ Türkçe dil desteği

## 📋 Gereksinimler

- Python 3.8+
- OpenAI API Key
- Telegram Bot Token
- Google Calendar API Credentials

## 🛠️ Kurulum

### 1. Paketleri Yükleyin

```bash
pip install -r requirements.txt
```

### 2. Environment Variables Ayarlayın

`.env` dosyası oluşturun:

```env
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_TOKEN=your_telegram_bot_token_here
GOOGLE_EMAIL=your_google_email_here
TIMEZONE=Europe/Istanbul
```

### 3. Google Calendar API Kurulumu

1. [Google Cloud Console](https://console.cloud.google.com/)'a gidin
2. Yeni proje oluşturun
3. Google Calendar API'yi etkinleştirin
4. OAuth 2.0 credentials oluşturun
5. `credentials.json` dosyasını indirin ve proje klasörüne koyun
6. OAuth consent screen'de test kullanıcısı olarak email adresinizi ekleyin

### 4. Bot'u Çalıştırın

```bash
python main.py
```

## 💬 Kullanım

Bot'a şu şekilde mesajlar gönderebilirsiniz:

- `"pazartesi sabah 8.30 iş görüşmesi"`
- `"yarın öğle toplantı"`
- `"bugün akşam 7'de doktor randevusu"`
- `"salı 15:00-17:00 arası mülakat"`

## 📁 Dosya Yapısı

```
instagram/
├── main.py                 # Ana bot kodu
├── requirements.txt        # Python paketleri
├── .env                   # Environment variables (oluşturmanız gerekiyor)
├── credentials.json       # Google API credentials (indirmeniz gerekiyor)
├── token.json            # Google OAuth token (otomatik oluşur)
├── env_example.txt       # Environment variables örneği
├── google_calendar_setup.md  # Google Calendar kurulum rehberi
└── README.md             # Bu dosya
```

## 🔧 Sorun Giderme

### Google Calendar Erişim Hatası
- Google Cloud Console'da test kullanıcısı eklediğinizden emin olun
- `credentials.json` dosyasının doğru konumda olduğunu kontrol edin

### Telegram Bot Hatası
- Bot token'ının doğru olduğunu kontrol edin
- Bot'u Telegram'da başlattığınızdan emin olun

### OpenAI API Hatası
- API key'in doğru olduğunu kontrol edin
- API kredinizin yeterli olduğundan emin olun

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.
