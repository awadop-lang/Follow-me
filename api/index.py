from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

# Base de données ultra-stable (mémoire vive)
db = {
    "region": "SYS_INITIALISATION...",
    "coords": {"x": 0, "y": 0},
    "avatars": [] # Liste des avatars actifs détectés
}
# Dictionnaire pour garder les temps de connexion (UUID: timestamp)
times = {}

# --- L'interface CYBER PRO MIS A JOUR ---
CYBER_HTML_V3_1 = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CYBER_MONITOR // CORE_READOUT_V3.1</title>
    <style>
        /* Palette de couleurs Cyberpunk Ambre */
        :root {
            --bg: #050505; /* Noir profond */
            --bg-p: #0a0a0a; /* Panneau noir */
            --p: #ffb000; /* Ambre Classique */
            --p-d: #332200; /* Ambre éteint */
            --a: #ff0000; /* Rouge Cible */
            --txt: #e0e0e0;
            --font: 'SF Mono', 'Fira Code', 'Roboto Mono', monospace;
        }

        body {
            background-color: var(--bg);
            color: var(--txt);
            font-family: var(--font);
            margin: 0; padding: 15px;
            display: flex; flex-direction: column; height: 100vh;
            overflow: hidden;
            background-image: radial-gradient(#111 1px, transparent 1px);
            background-size: 20px 20px; /* Grille de fond subtile */
        }

        /* --- En-tête Cyber --- */
        header {
            display: flex; justify-content: space-between; align-items: center;
            padding-bottom: 10px; border-bottom: 2px solid var(--p-d);
            margin-bottom: 15px;
            position: relative;
        }
        h1 { margin: 0; font-size: 16px; letter-spacing: 3px; color: var(--p); text-shadow: 0 0 8px var(--p); }
        #region-info { font-size: 12px; color: var(--txt); background: #111; padding: 2px 8px; border-radius: 4px; border: 1px solid #222; }
        #status { font-size: 11px; opacity: 0.7; }

        /* --- Grille Principale --- */
        .grid {
            display: grid;
            grid-template-columns: 1.6fr 1.1fr; /* Carte/Liste équilibré */
            gap: 15px; flex: 1; height: calc(100% - 60px);
        }

        /* --- Zone Carte --- */
        .panel-map {
            background-color: var(--bg-p);
            border: 1px solid var(--p-d);
            border-radius: 4px;
            display: flex; justify-content: center; align-items: center;
            overflow: hidden;
            position: relative;
            box-shadow: inset 0 0 15px rgba(255,176,0,0.03);
        }
        .map-frame {
            position: relative; width: 512px; height: 512px;
            border: 2px solid var(--p);
            background-color: black;
            background-size: cover;
            background-position: center;
            /* Effet de scanline subtil */
            background-image: linear-gradient(0deg, rgba(0,0,0,0.1) 50%, rgba(255,255,255,0.01) 50%);
            background-size: 100% 4px;
        }
        canvas { position: absolute; top:0; left:0; width: 100%; height: 100%; filter: drop-shadow(0 0 5px rgba(255,0,0,0.8)); }

        /* --- Zone Liste --- */
        .panel-list {
            background-color: var(--bg-p);
            border: 1px solid var(--p-d);
            border-radius: 4px;
            padding: 15px;
            overflow-y: auto;
            scrollbar-width: thin; scrollbar-color: var(--p-d) var(--bg-p);
        }
        .list-header { font-size: 11px; color: var(--p); font-weight: bold; padding-bottom: 10px; border-bottom: 1px solid var(--p-d); margin-bottom: 10px; letter-spacing: 1px; }

        /* --- Ligne d'avatar PRO --- */
        .av-row {
            display: grid;
            grid-template-columns: 20px 1fr 100px 7
