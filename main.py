import requests
import time
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIGURATION ---
TOKEN_TELEGRAM = "8720086632:AAHdZD6x5aL4fWB0h7dfIZ8P_6En4EN5rFg"
CHAT_ID_TELEGRAM = "7518104464"  # <--- METS TES CHIFFRES ICI !

LATITUDE = "48.76"
LONGITUDE = "7.25"

# --- MINI SERVEUR WEB (RÉPOND AUX PINGS DE RENDER EN 1 MILLISECONDE) ---
class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot Meteo operationnel et isole !")

    # AJOUT ICI : Répondre aussi aux requêtes 'HEAD' pour éviter l'erreur 501
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

def lancer_serveur_web():
    # MODIFICATION ICI : On force le port 10000 par défaut si Render ne donne rien
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), WebServerHandler)
    print(f"🌍 Serveur web actif sur le port {port}")
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
        print(f"Erreur envoi Telegram : {e}")

def boucle_du_bot():
    print("🤖 Boucle du Bot Météo démarrée...")
    while True:
        try:
            temp, vent = obtenir_meteo()
            print(f"Vérification météo : {temp}°C, vent {vent} km/h.")
            
            # Seuil d'alerte : moins de 10°C OU plus de 15km/h de vent
            if vent > 15 or temp < 10:
                message_alerte = f"⚠️ ALERTE MÉTÉO ! ⚠️\n\nIl fait actuellement {temp}°C.\nLe vent souffle à {vent} km/h.\n\nPrépare la veste, ça caille ou ça souffle !"
                envoyer_alerte_telegram(message_alerte)
                print("📨 Alerte envoyée sur Telegram !")
                
        except Exception as e:
            print(f"Erreur dans la boucle météo : {e}")
            
        # Pause stricte de 1 heure (3600 secondes)
        print("💤 Pause de 1 heure avant la prochaine vérification...")
        time.sleep(3600)

if __name__ == "__main__":
    # 1. On lance la boucle du bot dans son propre Thread isolé
    # Comme ça, elle fait sa vie toutes les heures sans être dérangée
    thread_bot = threading.Thread(target=boucle_du_bot, daemon=True)
    thread_bot.start()
    
    # 2. Le programme principal fait tourner le serveur web pour répondre à Render
    lancer_serveur_web()