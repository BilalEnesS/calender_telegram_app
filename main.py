import os
import json
import datetime
import asyncio
import logging
from dotenv import load_dotenv

from langchain.agents import initialize_agent, Tool
from langchain.llms import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Environment variables'ları yükle
load_dotenv()


# Environment variables'dan değerleri al
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GOOGLE_EMAIL = os.getenv('GOOGLE_EMAIL')
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Istanbul')

# Gerekli environment variables'ları kontrol et
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable bulunamadı!")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable bulunamadı!")
if not GOOGLE_EMAIL:
    raise ValueError("GOOGLE_EMAIL environment variable bulunamadı!")

SCOPES = ['https://www.googleapis.com/auth/calendar.events']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Tarih hesaplama fonksiyonu
def calculate_date_from_text(date_text: str) -> str:
    """
    Doğal dil tarih ifadelerini gerçek tarihe çevirir
    """
    today = datetime.datetime.now()
    
    # Gün isimlerini Türkçe'den İngilizce'ye çevir
    day_mapping = {
        'pazartesi': 'monday',
        'salı': 'tuesday', 
        'çarşamba': 'wednesday',
        'perşembe': 'thursday',
        'cuma': 'friday',
        'cumartesi': 'saturday',
        'pazar': 'sunday'
    }
    
    date_text_lower = date_text.lower()
    
    if 'yarın' in date_text_lower:
        return (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    for tr_day, en_day in day_mapping.items():
        if tr_day in date_text_lower:
            # Hedef günün hafta içindeki pozisyonunu bul (0=Pazartesi, 6=Pazar)
            target_day_num = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(en_day)
            current_day_num = today.weekday()  # 0=Pazartesi, 6=Pazar
            
            # Kaç gün sonra olduğunu hesapla
            days_ahead = target_day_num - current_day_num
            if days_ahead <= 0:  # Eğer bugün veya geçmiş bir günse, gelecek haftaya al
                days_ahead += 7
            
            return (today + datetime.timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    
    # Eğer hiçbir gün belirtilmemişse bugünü döndür
    return today.strftime("%Y-%m-%d")

# Google Calendar API servisini al
def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Render'da base64'ten credentials yükle
            if os.getenv('GOOGLE_CREDENTIALS_BASE64'):
                import base64
                credentials_content = base64.b64decode(os.getenv('GOOGLE_CREDENTIALS_BASE64')).decode('utf-8')
                flow = InstalledAppFlow.from_client_secrets_file(
                    json.loads(credentials_content), SCOPES
                )
            else:
                # Local development için dosyadan yükle
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    service = build('calendar', 'v3', credentials=creds)
    return service

# Google Calendar'a etkinlik ekleyen fonksiyon
def add_event_to_calendar(date:str, start_time:str, end_time:str, title:str, details:str) -> str:
    try:
        service = get_calendar_service()

        start_datetime = datetime.datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end_datetime = datetime.datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")

        event = {
            'summary': title,
            'description': details,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': TIMEZONE,
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': TIMEZONE,
            },
        }
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return f"✅ Etkinlik başarıyla oluşturuldu!\n📅 Tarih: {date}\n⏰ Saat: {start_time}-{end_time}\n📝 Başlık: {title}\n🔗 Link: {created_event.get('htmlLink')}"
    except Exception as e:
        if "access_denied" in str(e).lower():
            return f"❌ Google Calendar erişim hatası!\n\n🔧 Çözüm için:\n1. Google Cloud Console'a gidin\n2. OAuth consent screen > Test users\n3. {os.environ.get('GOOGLE_EMAIL', 'email adresinizi')} ekleyin\n\n📋 Etkinlik detayları:\n📅 Tarih: {date}\n⏰ Saat: {start_time}-{end_time}\n📝 Başlık: {title}\n📄 Detay: {details}"
        else:
            return f"❌ Takvime eklerken hata oluştu: {e}"

# LangChain tool: doğal dilden parse edip takvime ekle
def calendar_tool_func(command: str) -> str:
    """
    Burada LangChain LLM'i kullanarak tarih, saat, başlık ve detay çıkaracağız.
    Prompt ile bu işi LLM'ye yaptıracağız.
    """

    llm = OpenAI(temperature=0)
    
    # Bugünün tarihini al
    today = datetime.datetime.now()
    current_date = today.strftime("%Y-%m-%d")
    current_day_name = today.strftime("%A")  # Monday, Tuesday, etc.

    prompt = f"""
Bugünün tarihi: {current_date} ({current_day_name})

Aşağıdaki doğal dil komutunu al ve JSON formatında çıkar.  
JSON şu formatta olmalı:  
{{
    "date": "YYYY-MM-DD",
    "start_time": "HH:MM",
    "end_time": "HH:MM",
    "title": "Etkinlik başlığı",
    "details": "Etkinlik detayları"
}}

Önemli kurallar:
- Eğer tarih belirtilmemişse, bugünün tarihini ({current_date}) kullan
- "yarın" = bugünden 1 gün sonra
- "pazartesi" = gelecek pazartesi (bugün pazartesi ise bugün)
- "salı" = gelecek salı (bugün salı ise bugün)
- "çarşamba" = gelecek çarşamba (bugün çarşamba ise bugün)
- "perşembe" = gelecek perşembe (bugün perşembe ise bugün)
- "cuma" = gelecek cuma (bugün cuma ise bugün)
- "cumartesi" = gelecek cumartesi (bugün cumartesi ise bugün)
- "pazar" = gelecek pazar (bugün pazar ise bugün)
- Eğer sadece başlangıç saati belirtilmişse, 1 saatlik etkinlik varsay (örn: 8:30 -> 8:30-9:30)
- "sabah" = 09:00, "öğle" = 12:00, "akşam" = 18:00 olarak varsay
- Saat formatı 24 saat olmalı (HH:MM)

Komut: '''{command}'''
"""

    response = llm.predict(prompt)

    try:
        data = json.loads(response)
    except Exception as e:
        return f"JSON parse hatası: {e}\nModel cevabı: {response}"

    # Zaman bilgilerini al
    date = data.get("date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    title = data.get("title")
    details = data.get("details", "")

    # Eğer LLM tarihi doğru hesaplayamadıysa, manuel olarak hesapla
    if not date or date == "YYYY-MM-DD":
        date = calculate_date_from_text(command)
    
    # Saat düzeltmeleri
    if start_time and not end_time:
        # Sadece başlangıç saati varsa, 1 saatlik etkinlik yap
        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour = (start_hour + 1) % 24
        end_time = f"{end_hour:02d}:{start_minute:02d}"
    
    # Genel zaman ifadelerini düzelt
    if start_time == "09:00" and "sabah" in command.lower():
        start_time = "09:00"
        end_time = "10:00"
    elif start_time == "12:00" and "öğle" in command.lower():
        start_time = "12:00"
        end_time = "13:00"
    elif start_time == "18:00" and "akşam" in command.lower():
        start_time = "18:00"
        end_time = "19:00"

    # Debug bilgisi
    debug_info = f"📅 Hesaplanan tarih: {date}\n⏰ Saat: {start_time}-{end_time}\n📝 Başlık: {title}\n📄 Detay: {details}\n\n"
    
    # Takvime ekle
    try:
        result = add_event_to_calendar(date, start_time, end_time, title, details)
        return debug_info + result
    except Exception as e:
        return debug_info + f"Takvime eklerken hata oluştu: {e}"

# LangChain Tool objesi
calendar_tool = Tool(
    name="CalendarTool",
    func=calendar_tool_func,
    description="Kullanıcının doğal dil komutlarından Google Calendar'a etkinlik ekler. Örnek: 'Yarın 15:00-17:00 arası toplantı planla' veya 'Bugün 14:00'de doktor randevusu'"
)

# LangChain Agent oluştur
llm = OpenAI(temperature=0)
agent = initialize_agent(
    [calendar_tool], 
    llm, 
    agent="zero-shot-react-description", 
    verbose=False, 
    handle_parsing_errors=True,
    max_iterations=3,
    agent_kwargs={
        "system_message": "Sen bir takvim asistanısın. Kullanıcının doğal dil komutlarını alıp Google Calendar'a etkinlik eklersin. Her zaman CalendarTool'u kullan."
    }
)

# Telegram mesajlarını işle
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    await update.message.chat.send_action(action="typing")

    try:
        # Daha geniş anahtar kelime kontrolü
        calendar_keywords = [
            'planla', 'ekle', 'randevu', 'toplantı', 'etkinlik', 'saat', 'tarih',
            'pazartesi', 'salı', 'çarşamba', 'perşembe', 'cuma', 'cumartesi', 'pazar',
            'bugün', 'yarın', 'sabah', 'öğle', 'akşam', 'gece', 'görüşme', 'meeting',
            'doktor', 'iş', 'firma', 'şirket', 'mülakat', 'interview'
        ]
        
        if any(keyword in user_text.lower() for keyword in calendar_keywords):
            result = agent.run(user_text)
        else:
            result = "Takvimine etkinlik eklemek için şu şekilde yazabilirsin:\n- 'Yarın 15:00-17:00 arası toplantı planla'\n- 'Bugün 14:00'de doktor randevusu ekle'\n- 'Pazartesi 10:00'da iş görüşmesi'"
    except Exception as e:
        result = f"Bir hata oluştu: {e}\n\nLütfen şu formatta yazmayı dene:\n'Yarın 15:00-17:00 arası toplantı planla'"

    await update.message.reply_text(result)

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Merhaba! Takvimine etkinlik eklemek için doğal dilde komut yazabilirsin.\n"
        "Örnek: 'Yarın 15:00-17:00 arası OpenCV temelleri dersi planla.'"
    )

def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot çalışıyor...")
    
    # Render için webhook kullanımı (opsiyonel)
    # Eğer webhook kullanmak isterseniz:
    # app.run_webhook(
    #     listen="0.0.0.0",
    #     port=int(os.environ.get("PORT", 8080)),
    #     webhook_url="https://your-app-name.onrender.com"
    # )
    
    # Şimdilik polling kullanıyoruz
    app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Bot durduruldu.")
    except Exception as e:
        print(f"Hata: {e}")
