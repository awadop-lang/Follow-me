from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)
# Stockage en mémoire (se vide si inactif, parfait pour du live)
db = {
    "region": None,
    "coords": {"x": 0, "y": 0},
    "avatars": [] # Liste des avatars actifs détectés
}

HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CORE MONITOR V2 - GLOBAL VIEW</title>
    <style>
        /* Design System - Dark & Neon */
        :root {
            --bg-dark: #080808;
            --bg-panel: #141414;
            --primary: #00ff41; /* Vert Néon */
            --primary-dim: #004411;
            --accent: #ff0000; /* Rouge Alerte */
            --text-main: #e0e0e0;
            --text-muted: #888;
            --font-main: 'SF Mono', 'Roboto Mono', 'Courier New', monospace;
        }

        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: var(--font-main);
            margin: 0; padding: 20px;
            display: flex; flex-direction: column; height: 100vh;
            overflow: hidden;
        }

        /* En-tête */
        header {
            display: flex; justify-content: space-between; align-items: center;
            padding-bottom: 15px; border-bottom: 1px solid var(--primary-dim);
            margin-bottom: 20px;
        }
        h1 { margin: 0; font-size: 18px; letter-spacing: 2px; color: var(--primary); text-shadow: 0 0 10px var(--primary); }
        #region-info { font-size: 14px; color: var(--text-main); }
        #status { font-size: 12px; color: var(--text-muted); }

        /* Grille Principale (PC) */
        .main-grid {
            display: grid;
            grid-template-columns: 2fr 1fr; /* 2/3 Carte, 1/3 Liste */
            gap: 20px; flex: 1; height: calc(100% - 70px);
        }

        /* --- Zone Carte (GAUCHE) --- */
        .map-zone {
            background-color: var(--bg-panel);
            border: 1px solid var(--primary-dim);
            border-radius: 8px;
            padding: 10px;
            display: flex; justify-content: center; align-items: center;
            overflow: hidden;
            position: relative;
        }
        .map-viewer {
            position: relative; width: 512px; height: 512px; /* Carte plus grande */
            border: 2px solid var(--primary);
            background-color: black;
            background-size: cover;
            box-shadow: 0 0 20px rgba(0,255,0,0.1);
        }
        canvas { position: absolute; top:0; left:0; width: 100%; height: 100%; }

        /* --- Zone Liste (DROITE) --- */
        .list-zone {
            background-color: var(--bg-panel);
            border: 1px solid var(--primary-dim);
            border-radius: 8px;
            padding: 15px;
            overflow-y: auto;
            scrollbar-width: thin; scrollbar-color: var(--primary-dim) var(--bg-panel);
        }
        .list-zone h2 { font-size: 14px; color: var(--primary); margin-top: 0; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px; }

        /* Structure de ligne d'avatar PRO */
        .av-row {
            display: grid;
            grid-template-columns: 20px 1fr 100px 50px;
            gap: 10px; align-items: center;
            padding: 10px 5px;
            border-bottom: 1px solid rgba(0,255,0,0.05);
            font-size: 12px;
        }
        .av-row:hover { background-color: rgba(0,255,0,0.02); }
        .av-row:last-child { border-bottom: none; }

        /* Cellules */
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--primary); box-shadow: 0 0 5px var(--primary); }
        .name-cell { color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: bold; font-size: 13px; }
        .pos-cell { color: var(--primary); text-align: right; }
        .time-cell { color: var(--text-muted); text-align: right; }

    </style>
</head>
<body>
    <header>
        <h1>[CORE_MONITOR::GLOBAL_VIEW]</h1>
        <div id="region-info">REGION: <span style="color:white" id="reg-name">---</span> (<span id="reg-coords">0,0</span>)</div>
        <div id="status">CONNECTE | SCANNING...</div>
    </header>
    
    <div class="main-grid">
        <div class="map-zone">
            <div class="map-viewer" id="map-bg">
                <canvas id="map-canvas" width="512" height="512"></canvas>
            </div>
        </div>

        <div class="list-zone">
            <h2>AGENTS ACTIFS SUR SIM</h2>
            <div id="list-container">
                </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('map-canvas');
        const ctx = canvas.getContext('2d');
        const listContainer = document.getElementById('list-container');
        const mapBg = document.getElementById('map-bg');

        // Fonction pour formater le temps
        function formatTime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            return `${h}h ${m}m`;
        }

        async function updateMonitor() {
            try {
                const response = await fetch('/api');
                const data = await response.json();
                
                // 1. Mise à jour des infos globales
                if(data.region) {
                    document.getElementById('reg-name').innerText = data.region.toUpperCase();
                    document.getElementById('reg-coords').innerText = `${data.coords.x},${data.coords.y}`;
                    const mapUrl = `https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg`;
                    mapBg.style.backgroundImage = `url('${mapUrl}')`;
                }

                document.getElementById('status').innerText = `CONNECTE | ${data.avatars.length} AVATAR(S) DETECTE(S)`;

                // 2. Nettoyage de la carte et de la liste
                ctx.clearRect(0, 0, 512, 512);
                listContainer.innerHTML = "";

                if (data.avatars.length === 0) {
                    listContainer.innerHTML = "<div style='color:#444;text-align:center;margin-top:20px;'>Aucun agent détecté</div>";
                }

                // 3. Traitement de chaque avatar
                data.avatars.forEach(av => {
                    // --- Carte (Canvas) ---
                    // On convertit les coordonnées SL (256x256) vers le canvas (512x512)
                    const x = av.x * 2;
                    const y = 512 - (av.y * 2);

                    // Dessin du point rouge (Cœur brillant)
                    ctx.shadowBlur = 15;
                    ctx.shadowColor = "red";
                    ctx.fillStyle = "#ff0000";
                    ctx.beginPath(); ctx.arc(x, y, 7, 0, Math.PI * 2); ctx.fill();

                    // Nom de l'avatar sur la carte
                    ctx.shadowBlur = 0;
                    ctx.fillStyle = "white";
                    ctx.font = "bold 11px Arial";
                    ctx.fillText(av.name, x + 10, y + 3);

                    // --- Liste (HTML) ---
                    const row = document.createElement('div');
                    row.className = 'av-row';
                    
                    // Calcul du temps de connexion
                    const currentTime = Math.floor(Date.now() / 1000);
                    const timeOnSim = currentTime - av.start_time;

                    row.innerHTML = `
                        <div><span class="status-dot"></span></div>
                        <div class="name-cell">${av.name}</div>
                        <div class="pos-cell">${Math.floor(av.x)}, ${Math.floor(av.y)}</div>
                        <div class="time-cell">${formatTime(timeOnSim)}</div>
                    `;
                    listContainer.appendChild(row);
                });

            } catch (err) { console.log("OPS ERR...", err); }
        }
        setInterval(updateMonitor, 2000); // Mise à jour toutes les 2 secondes
    </script>
</body>
</html>
