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
    url = f"https://api.open-meteo.