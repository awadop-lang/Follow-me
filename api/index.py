from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

# Base de données stable (stockage temporaire en mémoire vive)
db = {
    "region": "SEARCHING_SIGNAL...",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
# Dictionnaire pour le suivi du temps (UUID: timestamp)
times = {}

# --- INTERFACE CYBER CORE V3.2 (PC OPTIMIZED) ---
HTML_CODE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>CYBER_MONITOR // CORE_READOUT_V3.2</title>
    <style>
        :root {
            --bg: #030303;
            --panel: #0a0a0a;
            --p: #ffb000; /* Ambre Cyber */
            --p-dim: #332200;
            --alert: #ff0000;
            --text: #e0e0e0;
            --font: 'SF Mono', 'Fira Code', 'Roboto Mono', monospace;
        }

        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: var(--font);
            margin: 0; padding: 20px;
            display: flex; flex-direction: column; height: 100vh;
            overflow: hidden;
            background-image: radial-gradient(#111 1px, transparent 1px);
            background-size: 25px 25px;
        }

        /* En-tête */
        header {
            display: flex; justify-content: space-between; align-items: center;
            padding-bottom: 10px; border-bottom: 2px solid var(--p-dim);
            margin-bottom: 20px;
        }
        h1 { margin: 0; font-size: 18px; letter-spacing: 4px; color: var(--p); text-shadow: 0 0 10px var(--p); }
        .sys-info { font-size: 12px; color: var(--p); border: 1px solid var(--p-dim); padding: 5px 15px; border-radius: 3px; background: #000; }

        /* Grille Principale */
        .main-grid {
            display: grid;
            grid-template-columns: 520px 1fr; /* Largeur fixe pour la carte */
            gap: 25px; flex: 1; height: calc(100% - 80px);
        }

        /* Cadre de la Carte (Correction Ratio) */
        .map-container {
            width: 512px; height: 512px;
            border: 2px solid var(--p);
            background-color: #000;
            position: relative;
            box-shadow: 0 0 20px rgba(255, 176, 0, 0.1);
            overflow: hidden;
        }
        #map-bg {
            width: 100%; height: 100%;
            background-repeat: no-repeat;
            background-size: 100% 100%; /* Force l'image à remplir le carré */
            background-position: center;
            position: absolute; top:0; left:0;
        }
        canvas { position: absolute; top:0; left:0; z-index: 5; }

        /* Liste des Agents (Droite) */
        .list-container {
            background: var(--panel);
            border: 1px solid var(--p-dim);
            border-radius: 5px;
            padding: 20px;
            overflow-y: auto;
        }
        .list-header {
            display: grid;
            grid-template-columns: 30px 1fr 100px 80px;
            font-size: 11px; color: var(--p);
            font-weight: bold; padding-bottom: 10px;
            border-bottom: 1px solid var(--p-dim);
            margin-bottom: 15px;
            text-transform: uppercase;
        }

        /* Ligne d'avatar */
        .av-row {
            display: grid;
            grid-template-columns: 30px 1fr 100px 80px;
            gap: 10px; align-items: center;
            padding: 12px 5px;
            border-bottom: 1px solid #1a1a1a;
            font-size: 13px;
            transition: 0.2s;
        }
        .av-row:hover { background: rgba(255, 176, 0, 0.05); }
        .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--p); box-shadow: 0 0 10px var(--p); }
        .name { font-weight: bold; color: #fff; text-transform: uppercase; }
        .coord { color: var(--p); font-family: monospace; font-size: 12px; text-align: right; }
        .time { color: #888; text-align: right; font-size: 12px; }

        /* Effet Scanline */
        .scanlines {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%), 
                        linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
            background-size: 100% 3px, 3px 100%; pointer-events: none; z-index: 10;
        }
    </style>
</head>
<body>
    <header>
        <h1>[CYBER_CORE // SIM_MONITOR]</h1>
        <div class="sys-info">REGION: <span id="r_name">---</span> // COORDS: <span id="r_coords">0,0</span></div>
    </header>

    <div class="main-grid">
        <div class="map-container">
            <div id="map-bg"></div>
            <div class="scanlines"></div>
            <canvas id="cv" width="512" height="512"></canvas>
        </div>

        <div class="list-container">
            <div class="list-header">
                <span>ST</span><span>AGENT_IDENT</span><span style="text-align:right">POS_XY</span><span style="text-align:right">DURAT</span>
            </div>
            <div id="list-rows"></div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');

        async function update() {
            try {
                const res = await fetch('/api');
                const data = await res.json();
                
                // Update Infos
                document.getElementById('r_name').innerText = data.region.toUpperCase();
                document.getElementById('r_coords').innerText = `${data.coords.x},${data.coords.y}`;
                
                // Update Map Background
                const mapUrl = `https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg`;
                document.getElementById('map-bg').style.backgroundImage = `url('${mapUrl}')`;

                // Update Canvas & List
                ctx.clearRect(0,0,512,512);
                const list = document.getElementById('list-rows');
                list.innerHTML = "";

                data.avatars.forEach(av => {
                    const x = av.x * 2;
                    const y = 512 - (av.y * 2);

                    // Dessin Target (Croix de visée)
                    ctx.strokeStyle = "red"; ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(x-12, y); ctx.lineTo(x+12, y);
                    ctx.moveTo(x, y-12); ctx.lineTo(x, y+12);
                    ctx.stroke();
                    
                    // Point central
                    ctx.fillStyle = "white"; ctx.beginPath(); ctx.arc(x,y,3,0,7); ctx.fill();

                    // Nom sur carte
                    ctx.fillStyle = "white"; ctx.font = "bold 12px monospace";
                    ctx.shadowColor = "black"; ctx.shadowBlur = 4;
                    ctx.fillText(av.name.toUpperCase(), x + 15, y + 5);
                    ctx.shadowBlur = 0;

                    // Ajout Liste
                    const row = document.createElement('div');
                    row.className = "av-row";
                    const elapsed = Math.floor((Date.now()/1000 - av.start_time)/60);
                    row.innerHTML = `
                        <div class="dot"></div>
                        <div class="name">${av.name}</div>
                        <div class="coord">${Math.floor(av.x)}, ${Math.floor(av.y)}</div>
                        <div class="time">${elapsed} MIN</div>
                    `;
                    list.appendChild(row);
                });
            } catch(e) { console.log("DATA_STREAM_ERROR"); }
        }
        setInterval(update, 2000);
    </script>
</body>
</html>
"""

@app.route('/api', methods=['GET', 'POST'])
def handle():
    global db, times
    if request.method == 'POST':
        try:
            data = request.json
            if not data: return "No Data", 400
            
            db["region"] = data.get("region", "UNKNOWN")
            db["coords"] = data.get("grid_coords", {"x":0, "y":0})
            
            incoming = data.get("avatars", [])
            active_list = []
            now = time.time()
            
            for av in incoming:
                uid = av.get("key")
                if uid:
                    if uid not in times:
                        times[uid] = now
                    av["start_time"] = times[uid]
                    active_list.append(av)
            
            db["avatars"] = active_list
            return "OK", 200
        except: return "ERROR", 500
            
    return jsonify(db)

@app.route('/')
def home():
    return render_template_string(HTML_CODE)
