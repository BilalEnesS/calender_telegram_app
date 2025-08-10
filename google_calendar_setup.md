# Google Calendar API Kurulum Rehberi

## Hızlı Çözüm: Test Kullanıcısı Ekleme

1. [Google Cloud Console](https://console.cloud.google.com/)'a gidin
2. Projenizi seçin
3. Sol menüden "APIs & Services" > "OAuth consent screen" seçin
4. "Test users" bölümünde "Add Users" butonuna tıklayın
5. `ornekmail@gmail.com` email adresinizi ekleyin
6. "Save" butonuna tıklayın

## Alternatif Çözüm: Uygulamayı Doğrulama

Eğer uygulamanızı herkese açık hale getirmek istiyorsanız:

1. Google Cloud Console'da "OAuth consent screen" sayfasına gidin
2. "Publish app" butonuna tıklayın
3. Google'ın doğrulama sürecini bekleyin (birkaç gün sürebilir)

## Geçici Çözüm: Credentials Dosyasını Yeniden Oluşturma

Eğer credentials.json dosyanız yoksa veya güncel değilse:

1. Google Cloud Console'da "APIs & Services" > "Credentials" seçin
2. "Create Credentials" > "OAuth 2.0 Client IDs" seçin
3. Application type: "Desktop application" seçin
4. İndirilen JSON dosyasını `credentials.json` olarak kaydedin
5. Projenizin ana dizinine koyun

## Önemli Notlar

- Test kullanıcısı ekledikten sonra bot'u yeniden başlatın
- İlk çalıştırmada tarayıcıda Google hesabınızla giriş yapmanız gerekecek
- `token.json` dosyası otomatik olarak oluşturulacak
