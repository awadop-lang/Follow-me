import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "NOX_ZETA_2026_STABLE")

# Base de données temporaire (se vide au redémarrage)
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "En attente...", 
        "coords": {"x":0, "y":0}, 
        "avatars": [],
        "history": {},
        "watchlist": []
    }
}

# --- Design Cyberpunk Intégré ---
INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>NOX//ZETA SYSTEM</title>
    <style>
        body { background: #020205; color: #0ff; font-family: sans-serif; margin: 0; padding: 20px; }
        .panel { border: 1px solid #0ff; padding: 15px; background: rgba(0,255,255,0.05); }
        h1 { color: #ff00ff; font-family: monospace; border-bottom: 2px solid #ff00ff; }
        .grid { display: grid; grid-template-columns: 1fr 300px; gap: 20px; }
        .radar-box { width: 512px; height: 512px; border: 1px solid #0ff; background: #000; position: relative; }
        .av-item { border-bottom: 1px solid rgba(0,255,255,0.2); padding: 5px; display: flex; justify-content: space-between; }
        .online { color: #0f0; font-weight: bold; }
        .offline { color: #f00; }
        button { background: transparent; border: 1px solid #0ff; color: #0ff; cursor: pointer; }
    </style>
</head>
<body onload="setInterval(update, 3000)">
    <h1>NOX//ZETA_TERMINAL_v1.7.5</h1>
    <div class="grid">
        <div class="panel">
            <h3>REGION: <span id="reg">---</span></h3>
            <div class="radar-box" id="map-container">
                <div id="map-bg" style="width:100%; height:100%; opacity:0.3; background-size:cover;"></div>
            </div>
        </div>
        <div class="panel">
            <h3>PRIORITY_WATCHLIST</h3>
            <div id="watchlist"></div>
            <hr>
            <h3>LOCAL_SCAN</h3>
            <div id="radarlist"></div>
        </div>
    </div>

    <script>
        async function update() {
            const res = await fetch('/api_data');
            const data = await res.json();
            document.getElementById('reg').innerText = data.region;
            
            if(data.coords.x > 0) {
                document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;
            }

            document.getElementById('radarlist').innerHTML = data.avatars.map(a => `
                <div class="av-item"><span>${a.name}</span> <button onclick="toggle('${a.name}','${a.uuid}')">+</button></div>
            `).join('');

            document.getElementById('watchlist').innerHTML = data.watchlist.map(w => {
                const isLocal = data.avatars.find(a => a.uuid === w.uuid);
                return `<div class="av-item">
                    <span class="${isLocal?'online':'offline'}">${isLocal?'[LOCAL]':'[GRID]'}</span>
                    <span>${w.name}</span>
                    <button onclick="toggle('${w.name}','${w.uuid}')">x</button>
                </div>`;
            }).join('');
        }

        async function toggle(n, u) {
            await fetch('/toggle_watch', {
