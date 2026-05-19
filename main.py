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
        "chat_id": 7518104464,
        "text": message
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erreur envoi Telegram : {e}")

def verifier_meteo():
    alertes = []
    
    # Remplace ici par tes coordonnées si besoin (ex: latitude=48.8566&longitude=2.3522 pour Paris)
    url = "https://api.open-meteo.com/v1/forecast?latitude=48.8566&longitude=2.3522&current=weather_code,wind_speed_10m"
    
    try:
        reponse = requests.get(url, timeout=5).json()
        actuel = reponse.get("current", {})
        
        code_meteo = actuel.get("weather_code", 0)
        vent = actuel.get("wind_speed_10m", 0)
        
        # Détection des orages (Codes WMO 95, 96, 99)
        if code_meteo in [95, 96, 99]:
            alertes.append("⚡ **ALERTE ORAGE :** Attention, de l'orage et des impacts de foudre sont détectés !")
            
        # Détection des pluies fortes / averses (Codes WMO 63, 65, 81, 82)
        elif code_meteo in [63, 65, 81, 82]:
            alertes.append("🌧️ **ALERTE PLUIE :** Une forte averse ou une pluie battante est en cours !")
            
        # Détection de tempête (Vent supérieur à 70 km/h)
        if vent >= 70:
            alertes.append(f"💨 **ALERTE TEMPÊTE :** Grosses rafales de vent détectées ({vent} km/h) !")
            
    except Exception as e:
        print(f"Erreur lors du check météo : {e}")
        
    return alertes

def boucle_du_bot():
    print("🤖 Boucle globale démarrée (Réseaux Sociaux + Météo d'Extrême)...")
    
    while True:
        try:
            # 1. Infos météo classiques dans la console (pas de spam Telegram)
            temp, vent = obtenir_meteo()
            print(f"📊 Météo actuelle : {temp}°C | Vent : {vent} km/h")
            
            # 2. SURVEILLANCE DES RÉSEAUX SOCIAUX
            print("🔍 Vérification des réseaux sociaux...")
            pannes = verifier_pannes()
            for alerte in pannes:
                envoyer_alerte_telegram(alerte)
                
            # 3. SURVEILLANCE DE LA MÉTÉO D'EXTRÊME (Orages, Tempêtes, Pluies fortes)
            print("🔍 Vérification des alertes météo critiques...")
            alertes_meteo = verifier_meteo()
            for alerte in alertes_meteo:
                envoyer_alerte_telegram(alerte)
                
        except Exception as e:
            print(f"❌ Erreur dans la boucle générale : {e}")
            
        # 4. On vérifie toutes les 10 minutes (600 secondes) pour être super réactif !
        print("💤 Pause de 10 minutes avant le prochain contrôle...")
        time.sleep(600)

if __name__ == "__main__":
    # 1. On lance la boucle du bot dans son propre Thread isolé
    # Comme ça, elle fait sa vie toutes les heures sans être dérangée
    thread_bot = threading.Thread(target=boucle_du_bot, daemon=True)
    thread_bot.start()
    
    # 2. Le programme principal fait tourner le serveur web pour répondre à Render
    lancer_serveur_web()