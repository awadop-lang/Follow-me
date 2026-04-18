from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_ZETA_V170_FINAL"

# Base de données volatile (se réinitialise au déploiement)
db = {
    "admin": {
        "pw": "1234",
        "region": "Initialisation...",
        "coords": {"x": 0, "y": 0},
        "avatars": [],
        "watchlist": [] # [{"name":str, "uuid":str, "online_sl":bool, "last_ping":float}]
    }
}

# --- HTML INTERFACE ---
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --red: #ff3131; --green: #00ffaa; --yellow: #f1c40f; --bg: #020205; --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Rajdhani', sans-serif; margin: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { height: 50px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; padding: 0 20px; background: #0a0a1a; }
        .main-container { display: flex; flex: 1; overflow: hidden; }
        .column { height: 100%; display: flex; flex-direction: column; border-right: 1px solid var(--border); background: rgba(0,0,0,0.4); }
        .col-header { padding: 12px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 10px; color: var(--cyan); text-transform: uppercase; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 10px; }
        .item { background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 10px; margin-bottom: 8px; border-radius: 4px; }
        .name { color: var(--cyan); font-family: 'Orbitron'; font-size: 13px; }
        .status-badge { font-size: 9px; padding: 2px 5px; border-radius: 3px; font-weight: bold; margin-top: 5px; display: inline-block; border: 1px solid; }
        .st-local { color: var(--green); border-color: var(--green); background: rgba(0,255,170,0.1); }
        .st-grid { color: var(--yellow); border-color: var(--yellow); background: rgba(241,196,15,0.1); }
        .st-off { color: #555; border-color: #444; }
        .action-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); cursor: pointer; float: right; padding: 2px 6px; }
        .map-frame { width: 512px; height: 512px; position: relative; border: 1px solid var(--cyan); background: #000; margin: auto; }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.5; background-size: cover; transition: background 0.5s; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
    </style>
</head>
<body onload="setInterval(updateUI, 2000)">
    <header>
        <div style="font-family:'Orbitron'; color:var(--cyan)">NOX//ZETA v1.7.0</div>
        <div style="font-size:12px; color:var(--green)">ZONE: <span id="reg-name">---</span></div>
        <a href="/logout" style="color:var(--red); text-decoration:none; font-size:11px;">[ LOGOUT ]</a>
    </header>

    <div class="main-container">
        <div class="column" style="width: 45%; justify-content:center; background:#000;">
            <div class="map-frame"><div id="map-bg"></div><canvas id="radar-canvas" width="512" height="512"></canvas></div>
        </div>
        <div class="column" style="width: 27%;">
            <div class="col-header">Proximité</div>
            <div id="scan-list" class="scroll-area"></div>
        </div>
        <div class="column" style="width: 28%;">
            <div class="col-header" style="color:var(--red)">Suivi Global (Persistent)</div>
            <div id="watch-list" class="scroll-area"></div>
        </div>
    </div>

    <script>
        async function updateUI() {
            try {
                const res = await fetch('/api_data');
                const data = await res.json();
                if (!data.watchlist) return;

                document.getElementById('reg-name').innerText = data.region || "DISCONNECTED";
                if(data.coords && data.coords.x > 0) {
                    const t = Math.floor(Date.now() / 30000); // Rafraîchit l'image si besoin
                    document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg?t=${t}')`;
                }

                document.getElementById('scan-list').innerHTML = data.avatars.map(av => `
                    <div class="item">
                        <button class="action-btn" onclick="toggleWatch('${av.name}', '${av.uuid}')">+</button>
                        <span class="name">${av.name}</span>
                    </div>`).join('');

                document.getElementById('watch-list').innerHTML = data.watchlist.map(w => {
                    const isLocal = data.avatars.find(a => a.uuid === w.uuid);
                    const now = Math.floor(Date.now() / 1000);
                    // L'agent reste ONLINE si le dernier ping date de moins de 45s
                    const isOnlineGrid = w.online_sl && (now - w.last_ping < 45);
                    
                    let stC = "st-off", stT = "HORS-LIGNE";
                    if (isLocal) { stC = "st-local"; stT = "SUR PLACE"; }
                    else if (isOnlineGrid) { stC = "st-grid"; stT = "DANS LA GRID"; }

                    return `<div class="item" style="border-left: 4px solid ${isLocal?'var(--green)':'var(--red)'}">
                        <button class="action-btn" onclick="
