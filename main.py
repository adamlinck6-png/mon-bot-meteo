import requests
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIGURATION ---
TOKEN_TELEGRAM = "8720086632:AAHdZD6x5aL4fWB0h7dfIZ8P_6En4EN5rFg"
CHAT_ID_TELEGRAM = "7518104464"  # <--- Mets tes chiffres ici !

LATITUDE = "48.76"
LONGITUDE = "7.25"

# --- MINI SERVEUR WEB POUR FAIRE PLAISIR À RENDER ---
class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot Meteo en ligne !")

def lancer_serveur_web():
    # Render donne automatiquement un port dans les variables d'environnement, sinon on prend 8080
    import os
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), WebServerHandler)
    print(f"🌍 Serveur web de secours active sur le port {port}")
    server.serve_forever()

# --- FONCTIONS DU BOT MÉTÉO ---
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
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erreur d'envoi Telegram : {e}")

def boucle_du_bot():
    print("🤖 Bot Météo autonome activé dans son coin...")
    while True:
        try:
            temp, vent = obtenir_meteo()
            print(f"Vérification : Il fait {temp}°C et le vent souffle à {vent} km/h.")
            
            message_alerte = f"⚠️ ALERTE MÉTÉO ! ⚠️\n\nIl fait actuellement {temp}°C.\nLe vent souffle à {vent} km/h."
            
            if vent > 15 or temp < 10:
                message_alerte += "\n\nPrépare la veste, ça caille ou ça souffle !"
                envoyer_alerte_telegram(message_alerte)
                print("📨 Alerte envoyée sur Telegram !")
                
        except Exception as e:
            print(f"Erreur bot : {e}")
            
        print("💤 Pause d'une heure...")
        time.sleep(3600)

# --- LANCEMENT REUSSIT ---
if __name__ == "__main__":
    # 1. On lance le serveur web dans un fil secondaire pour occuper Render
    thread_web = threading.Thread(target=lancer_serveur_web, daemon=True)
    thread_web.start()
    
    # 2. On lance le vrai bot météo dans le programme principal
    boucle_du_bot()