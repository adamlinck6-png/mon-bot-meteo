import requests
import time

# --- CONFIGURATION ---
TOKEN_TELEGRAM = "8720086632:AAHdZD6x5aL4fWB0h7dfIZ8P_6En4EN5rFg"
# METS TON VRAI ID À LA PLACE DU TEXTE CI-DESSOUS
CHAT_ID_TELEGRAM = "7518104464" 

LATITUDE = "48.76"
LONGITUDE = "7.25"

def obtenir_meteo():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current_weather=true"
    reponse = requests.get(url).json()
    temperature = reponse["current_weather"]["temperature"]
    vitesse_vent = reponse["current_weather"]["windspeed"]
    return temperature, vitesse_vent

def envoyer_alerte_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN_TELEGRAM}/sendMessage"
    payload = {
        "chat_id": CHAT_ID_TELEGRAM,
        "text": message
    }
    requests.post(url, json=payload)

print("🤖 Bot Météo en ligne et autonome activé...")

while True:
    try:
        temp, vent = obtenir_meteo()
        print(f"Vérification : Il fait {temp}°C et le vent souffle à {vent} km/h.")
        
        message_alerte = f"⚠️ ALERTE MÉTÉO ! ⚠️\n\nIl fait actuellement {temp}°C.\nLe vent souffle à {vent} km/h."
        
        # Le bot t'alerte s'il fait moins de 10°C ou s'il y a plus de 15km/h de vent
        if vent > 15 or temp < 10:
            message_alerte += "\n\nPrépare la veste, ça caille ou ça souffle !"
            envoyer_alerte_telegram(message_alerte)
            print("📨 Alerte envoyée sur Telegram !")
            
    except Exception as e:
        print(f"Erreur : {e}")
        
    print("💤 Pause d'une heure...")
    time.sleep(3600)