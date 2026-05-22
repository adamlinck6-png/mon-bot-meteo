import requests
import time
import threading
import os
import datetime  # Ajouté pour la gestion de l'heure
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CONFIGURATION ---
TOKEN_TELEGRAM = "8720086632:AAHdZD6x5aL4fWB0h7dfIZ8P_6En4EN5rFg"
CHAT_ID_TELEGRAM = "7518104464"

# Coordonnées GPS exactes de Danne-et-Quatre-Vents !
LATITUDE = "48.7667"
LONGITUDE = "7.2833"

# Variable globale pour le suivi de ton IP internet
VOTRE_IP_PUBLIQUE = "AUTO"

# --- MINI SERVEUR WEB (POUR RENDER) ---
class WebServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Bot Meteo, Cyber et Reseaux operationnel !")

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

# --- RAPPORT MATIN ---
def obtenir_bulletin_matin():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&daily=weather_code,temperature_2m_max&timezone=Europe%2FParis"
    try:
        data = requests.get(url, timeout=5).json()
        code = data["daily"]["weather_code"][0]
        temp_max = data["daily"]["temperature_2m_max"][0]
        
        etat = "avec un ciel mitigé"
        if code == 0: etat = "sous un grand soleil"
        elif code in [1, 2]: etat = "avec quelques passages nuageux"
        elif code >= 60: etat = "avec de la pluie probable"
            
        return f"☀️ **Bonjour de Danne !**\n\nPrévisions du jour : {etat}. Température max prévue : {temp_max}°C. Passe une excellente journée ! 🚀"
    except:
        return "Impossible de récupérer la météo du matin."

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
            if service["name"] == "YouTube" and service["status"] != "AVAILABLE":
                alertes.append("🔴 **YouTube rencontre des perturbations mondiales !**")
    except:
        print("Impossible de joindre le statut de YouTube")
    return alertes

# --- 2. DÉTECTEUR MÉTÉO ACTUELLE (CONSOLE) ---
def obtenir_meteo():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current_weather=true"
    try:
        reponse = requests.get(url, timeout=5).json()
        return reponse["current_weather"]["temperature"], reponse["current_weather"]["windspeed"]
    except:
        return "N/A", "N/A"

# --- 3. DÉTECTEUR MÉTÉO CRITIQUE (TELEGRAM) ---
def verifier_meteo():
    alertes = []
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current=weather_code,wind_speed_10m"
    try:
        reponse = requests.get(url, timeout=5).json()
        actuel = reponse.get("current", {})
        code_meteo = actuel.get("weather_code", 0)
        vent = actuel.get("wind_speed_10m", 0)
        if code_meteo in [95, 96, 99]:
            alertes.append("⚡ **ALERTE ORAGE à Danne :** Impacts de foudre détectés !")
        elif code_meteo in [63, 65, 81, 82]:
            alertes.append("🌧️ **ALERTE PLUIE à Danne :** Forte averse en cours !")
        if vent >= 70:
            alertes.append(f"💨 **ALERTE TEMPÊTE à Danne :** Rafales de vent ({vent} km/h) !")
    except:
        pass
    return alertes

# --- 4. DETECTEUR DE FAILLES DE SÉCURITÉ ---
def verifier_failles_cyber():
    alertes = []
    for os_name in ["linux", "ios", "windows"]:
        try:
            url = f"https://cve.circl.lu/api/search/{os_name}"
            reponse = requests.get(url, timeout=5).json()
            if isinstance(reponse, list) and len(reponse) > 0:
                derniere_cve = reponse[0]
                alertes.append(f"🛡️ **VEILLE CYBER - {os_name.upper()}**\n🪲 Faille : `{derniere_cve.get('id')}`\n📝 {derniere_cve.get('summary')[:150]}...")
        except:
            pass
    return alertes

# --- VERSION AMÉLIORÉE (PLUS TOLÉRANTE) ---
def verifier_coupure_maison():
    global VOTRE_IP_PUBLIQUE
    
    if VOTRE_IP_PUBLIQUE == "AUTO":
        try:
            VOTRE_IP_PUBLIQUE = requests.get("https://api.ipify.org", timeout=10).text
        except:
            return [] # On ne peut même pas trouver l'IP, on attend le prochain cycle

    # On fait 3 essais avec plus de temps (7 secondes au lieu de 4)
    for essai in range(3):
        try:
            requests.get(f"http://{VOTRE_IP_PUBLIQUE}", timeout=7)
            return [] # La box a répondu, tout est OK !
        except:
            time.sleep(3) # On attend 3 secondes avant de ré-essayer
            
    # Si après 3 essais on n'a toujours rien, ALORS c'est une vraie panne
    return ["🔌 **ALERTE COUPURE à Danne :** Ta box ne répond plus après 3 tentatives. Vérifie ton courant ou ta connexion ! ⚠️"]

# --- BOUCLE PRINCIPALE ---
def boucle_du_bot():
    print("🤖 Boucle globale démarrée...")
    date_derniere_alerte = None # On mémorise le jour, c'est plus fiable
    
    while True:
        # On force le fuseau horaire de la France (UTC+2)
        paris_tz = datetime.timezone(datetime.timedelta(hours=2))
        maintenant = datetime.datetime.now(paris_tz)
        
        heure_actuelle = maintenant.hour
        date_actuelle = maintenant.date()
        
        # Rapport du matin à 8h (heure française garantie)
        if heure_actuelle == 8 and date_derniere_alerte != date_actuelle:
            envoyer_alerte_telegram(obtenir_bulletin_matin())
            date_derniere_alerte = date_actuelle # Marqué comme envoyé pour aujourd'hui
            
        try:
            # Exécute tous les checks (Réseaux, Météo, Cyber, Box)
            for alerte in verifier_pannes() + verifier_meteo() + verifier_failles_cyber() + verifier_coupure_maison():
                envoyer_alerte_telegram(alerte)
        except Exception as e:
            print(f"Erreur boucle : {e}")
            
        time.sleep(600)

if __name__ == "__main__":
    threading.Thread(target=boucle_du_bot, daemon=True).start()
    lancer_serveur_web()