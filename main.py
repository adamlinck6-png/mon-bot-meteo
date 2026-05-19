import requests
import time
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIGURATION ---
TOKEN_TELEGRAM = "8720086632:AAHdZD6x5aL4fWB0h7dfIZ8P_6En4EN5rFg"
CHAT_ID_TELEGRAM = "7518104464"

# Coordonnées GPS exactes de Danne-et-Quatre-Vents !
LATITUDE = "48.7667"
LONGITUDE = "7.2833"

# --- MINI SERVEUR WEB (POUR RENDER) ---
class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot Meteo et Reseaux operationnel !")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

def lancer_serveur_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), WebServerHandler)
    print(f"🌍 Serveur web actif sur le port {port}")
    server.serve_forever()

# --- FONCTION ENVOI TELEGRAM ---
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

# --- 1. DETECTEUR DE PANNES RÉSEAUX ---
def verifier_pannes():
    alertes = []

    # Check Discord
    try:
        url_discord = "https://discordstatus.com/api/v2/summary.json"
        data_discord = requests.get(url_discord, timeout=5).json()
        statut_discord = data_discord["status"]["description"]
        if "All Systems Operational" not in statut_discord:
            alertes.append(f"🔴 **Discord est en panne !**\nStatut : {statut_discord}")
    except:
        print("Impossible de joindre le statut de Discord")

    # Check YouTube
    try:
        url_youtube = "https://www.google.com/appsstatus/dashboard/summary.json"
        data_youtube = requests.get(url_youtube, timeout=5).json()
        for service in data_youtube.get("services", []):
            if service["name"] == "YouTube":
                if service["status"] != "AVAILABLE":
                    alertes.append("🔴 **YouTube rencontre des perturbations mondiales !**")
    except:
        print("Impossible de joindre le statut de YouTube")

    # Check des autres réseaux
    autres_sites = {
        "Instagram": "https://www.instagram.com",
        "Twitter/X": "https://twitter.com",
        "Twitch": "https://www.twitch.tv"
    }

    for nom_site, url in autres_sites.items():
        try:
            reponse = requests.get(url, timeout=5)
            if reponse.status_code >= 400:
                alertes.append(f"⚠️ **{nom_site} semble rencontrer un problème !** (Code : {reponse.status_code})")
        except:
            alertes.append(f"🚨 **Alerte Critique : {nom_site} est totalement inaccessible !**")

    return alertes

# --- 2. DÉTECTEUR MÉTÉO ACTUELLE (CONSOLE) ---
def obtenir_meteo():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current_weather=true"
    try:
        reponse = requests.get(url, timeout=5).json()
        temperature = reponse["current_weather"]["temperature"]
        vitesse_vent = reponse["current_weather"]["windspeed"]
        return temperature, vitesse_vent
    except:
        return "N/A", "N/A"

# --- 3. DÉTECTEUR MÉTÉO CRITIQUE (TELEGRAM) ---
def verifier_meteo():
    alertes = []
    # L'URL utilise maintenant tes variables globales configurées en haut !
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current=weather_code,wind_speed_10m"
    
    try:
        reponse = requests.get(url, timeout=5).json()
        actuel = reponse.get("current", {})
        code_meteo = actuel.get("weather_code", 0)
        vent = actuel.get("wind_speed_10m", 0)
        
        # Orages
        if code_meteo in [95, 96, 99]:
            alertes.append("⚡ **ALERTE ORAGE à Danne :** Attention, de l'orage et des impacts de foudre sont détectés !")
        # Pluies fortes
        elif code_meteo in [63, 65, 81, 82]:
            alertes.append("🌧️ **ALERTE PLUIE à Danne :** Une forte averse ou une pluie battante est en cours !")
        # Tempête
        if vent >= 70:
            alertes.append(f"💨 **ALERTE TEMPÊTE à Danne :** Grosses rafales de vent détectées ({vent} km/h) !")
            
    except Exception as e:
        print(f"Erreur lors du check météo : {e}")
        
    return alertes

# --- BOUCLE PRINCIPALE ---
def boucle_du_bot():
    print("🤖 Boucle globale démarrée (Réseaux Sociaux + Météo de Danne)...")
    
    while True:
        try:
            # 1. Stats dans la console
            temp, vent = obtenir_meteo()
            print(f"📊 Météo actuelle : {temp}°C | Vent : {vent} km/h")
            
            # 2. Check Réseaux Sociaux
            print("🔍 Vérification des réseaux sociaux...")
            pannes = verifier_pannes()
            for alerte in pannes:
                envoyer_alerte_telegram(alerte)
                
            # 3. Check Météo d'Extrême
            print("🔍 Vérification des alertes météo...")
            alertes_meteo = verifier_meteo()
            for alerte in alertes_meteo:
                envoyer_alerte_telegram(alerte)
                
        except Exception as e:
            print(f"❌ Erreur dans la boucle : {e}")
            
        print("💤 Pause de 10 minutes avant le prochain contrôle...")
        time.sleep(600)

if __name__ == "__main__":
    thread_bot = threading.Thread(target=boucle_du_bot, daemon=True)
    thread_bot.start()
    
    lancer_serveur_web()