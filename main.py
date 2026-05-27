import requests
import time
import threading
import os
import datetime  # Ajouté pour la gestion de l'heure
import imaplib
import email
from email.header import decode_header
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
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current=weather_code,wind_speed_10m,temperature_2m"
    try:
        reponse = requests.get(url, timeout=5).json()
        actuel = reponse.get("current", {})
        code_meteo = actuel.get("weather_code", 0)
        vent = actuel.get("wind_speed_10m", 0)
        temperature = actuel.get("temperature_2m", None)
        
        if code_meteo in [95, 96, 99]:
            alertes.append("⚡ **ALERTE ORAGE à Danne :** Impacts de foudre détectés !")
        elif code_meteo in [63, 65, 81, 82]:
            alertes.append("🌧️ **ALERTE PLUIE à Danne :** Forte averse en cours !")
        if vent >= 70:
            alertes.append(f"💨 **ALERTE TEMPÊTE à Danne :** Rafales de vent ({vent} km/h) !")
            
        return alertes, temperature
    except:
        return alertes, None

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

# --- 5. DÉTECTEUR DE FUITES DE DONNÉES (DARK WEB) ---
def verifier_fuites_email(email_a_surveiller):
    alertes = []
    url = f"https://leakcheck.io/api/public?check={email_a_surveiller}"
    try:
        reponse = requests.get(url, timeout=5).json()
        if reponse.get("success") and reponse.get("sources"):
            sources = reponse.get("sources", [])
            nombre_fuites = len(sources)
            dernières_sources = ", ".join(sources[:3])
            
            alertes.append(
                f"⚠️ **ALERTE CYBER - FUITE DE DONNÉES DETECTÉE !**\n\n"
                f"Ton adresse `{email_a_surveiller}` apparaît dans **{nombre_fuites}** fuites de données sur le web.\n"
                f"📦 **Dernières sources connues :** {dernières_sources}\n\n"
                f"💡 *Conseil : Si tu utilises le même mot de passe partout, change-le d'urgence !*"
            )
    except Exception as e:
        print(f"Erreur lors du check de fuite de données : {e}")
    return alertes

# --- 6. GUETTEUR D'E-MAILS DE SÉCURITÉ (IMAP) ---
def verifier_emails_securite(votre_email, mot_de_passe_app):
    alertes = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(votre_email, mot_de_passe_app)
        mail.select("inbox")

        mots_cles = ['security', 'connexion', 'password', 'code', 'securite', 'reinitialisation', 'suspect']
        status, messages = mail.search(None, 'UNSEEN')
        
        if status == "OK":
            liste_ids = messages[0].split()
            for mail_id in liste_ids[-5:]:
                status, data = mail.fetch(mail_id, '(RFC822)')
                if status != "OK":
                    continue
                
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                sujet, encoding = decode_header(msg["Subject"])[0]
                if isinstance(sujet, bytes):
                    sujet = sujet.decode(encoding if encoding else 'utf-8', errors='ignore')
                
                sujet_lower = sujet.lower()
                
                if any(mc in sujet_lower for mc in mots_cles):
                    expediteur, encoding = decode_header(msg["From"])[0]
                    if isinstance(expediteur, bytes):
                        expediteur = expediteur.decode(encoding if encoding else 'utf-8', errors='ignore')
                        
                    alertes.append(
                        f"🔔 **GUETTEUR EMAIL - ALERTE SÉCURITÉ COMPTE !**\n\n"
                        f"📧 **De :** {expediteur}\n"
                        f"📌 **Sujet :** {sujet}\n"
                        f"⚠️ *Un tiers essaie peut-être de forcer l'un de tes comptes (Discord, Google, Epic...), vérifie tes mails d'urgence !*"
                    )
        mail.logout()
    except Exception as e:
        print(f"Erreur guetteur IMAP : {e}")
        
    return alertes

# --- BOUCLE PRINCIPALE ---
def boucle_du_bot():
    print("🤖 Boucle globale démarrée...")
    date_derniere_alerte = None # Mémorise le jour pour le bulletin du matin
    date_alerte_chaleur = None  # Mémorise le jour pour l'alerte chaleur (anti-spam)
    
    # 📝 CONFIGURATION CYBER
    EMAIL_A_PROTEGER = "addm5196@gmail.com" 
    # ⚠️ TON MOT DE PASSE D'APPLICATION À 16 CARACTÈRES COPIÉ-COLLÉ ICI :
    MDP_APP_GMAIL = "kcxrplkogjfjygxh" 
    
    while True:
        # On force le fuseau horaire de la France (UTC+2)
        paris_tz = datetime.timezone(datetime.timedelta(hours=2))
        maintenant = datetime.datetime.now(paris_tz)
        
        heure_actuelle = maintenant.hour
        date_actuelle = maintenant.date()
        
        # ⏰ Rapport du matin et check cyber-fuites à 7h00 pile !
        if heure_actuelle == 7 and date_derniere_alerte != date_actuelle:
            envoyer_alerte_telegram(obtenir_bulletin_matin())
            
            alertes_cyber_fuites = verifier_fuites_email(EMAIL_A_PROTEGER)
            for alerte in alertes_cyber_fuites:
                envoyer_alerte_telegram(alerte)
                
            date_derniere_alerte = date_actuelle
            
        try:
            # On récupère les alertes météo de base et la température en temps réel
            alertes_meteo, temp_actuelle = verifier_meteo()
            
            # 🔥 Détecteur d'excès de chaleur (Seuil : 24°C)
            if temp_actuelle and temp_actuelle >= 24.0 and date_alerte_chaleur != date_actuelle:
                alertes_meteo.append(f"🔥 **ALERTE CHALEUR à Danne :** La barre des 24°C a été franchie ! Il fait actuellement {temp_actuelle}°C. ☀️")
                date_alerte_chaleur = date_actuelle
            
            # 📬 Check des e-mails de sécurité en temps réel
            alertes_emails = verifier_emails_securite(EMAIL_A_PROTEGER, MDP_APP_GMAIL)
            
            # Exécute tous les checks restants (Pannes + Météo + Cyber CVE + Mails de sécu)
            toutes_les_alertes = verifier_pannes() + alertes_meteo + verifier_failles_cyber() + alertes_emails
            
            for alerte in toutes_les_alertes:
                envoyer_alerte_telegram(alerte)
        except Exception as e:
            print(f"Erreur boucle : {e}")
            
        time.sleep(600)

if __name__ == "__main__":
    threading.Thread(target=boucle_du_bot, daemon=True).start()
    lancer_serveur_web()