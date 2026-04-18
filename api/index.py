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
            grid-template-columns: 20px 1fr 100px 70px; /* Colonnes fixes */
            gap: 10px; align-items: center;
            padding: 10px 5px;
            border-bottom: 1px solid rgba(255,176,0,0.05);
            font-size: 12px;
            position: relative;
            transition: background 0.2s;
        }
        .av-row:hover { background-color: rgba(255,176,0,0.03); }
        .av-row::before { content: ''; position: absolute; left: 0; top: 10%; width: 2px; height: 80%; background: var(--p-d); }
        .av-row:hover::before { background: var(--p); box-shadow: 0 0 5px var(--p); }

        /* Cellules */
        .c-stat { display: flex; justify-content: center; }
        .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--p); box-shadow: 0 0 8px var(--p); animation: pulse 2s infinite; }
        .c-name { color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: bold; font-size: 13px; text-transform: uppercase; }
        .c-pos { color: var(--p); text-align: right; letter-spacing: 1px; font-weight: bold; }
        .c-time { color: var(--txt); text-align: right; opacity: 0.8; }

        /* Animations */
        @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }

    </style>
</head>
<body>
    <header>
        <h1>[CYBER_MONITOR // CORE_READOUT]</h1>
        <div id="region-info">SYS: <span style="color:var(--p)" id="reg-name">---</span> (<span id="reg-coords">0,0</span>)</div>
        <div id="status">STATUS: <span style="color:var(--p)">LIVE_FEED</span> // OK</div>
    </header>
    
    <div class="grid">
        <div class="panel-map">
            <div class="map-frame" id="map-bg">
                <canvas id="map-canvas" width="512" height="512"></canvas>
            </div>
        </div>

        <div class="panel-list">
            <div class="list-header">// AGENTS_DETECTED // FEED</div>
            <div id="list-container">
                </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('map-canvas');
        const ctx = canvas.getContext('2d');
        const listC = document.getElementById('list-container');
        const mapBg = document.getElementById('map-bg');

        function fmtTimeCyber(seconds) {
            const m = Math.floor(seconds / 60);
            const s = Math.floor(seconds % 60);
            return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }

        async function updateMonitor() {
            try {
                const response = await fetch('/api');
                const data = await response.json();
                
                // 1. Infos globales
                if(data.region) {
                    document.getElementById('reg-name').innerText = data.region.toUpperCase();
                    document.getElementById('reg-coords').innerText = `${data.coords.x},${data.coords.y}`;
                    const mapUrl = `https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg`;
                    mapBg.style.backgroundImage = `url('${mapUrl}')`;
                }

                document.getElementById('status').innerHTML = `STATUS: <span style="color:var(--p)">LIVE_FEED</span> // ${data.avatars.length} TARGETS`;

                // 2. Nettoyage
                ctx.clearRect(0, 0, 512, 512);
                listC.innerHTML = "";

                if (data.avatars.length === 0) {
                    listC.innerHTML = "<div style='color:#333;text-align:center;margin-top:30px;font-size:10px;'>[ NO_TARGETS_IN_RANGE ]</div>";
                }

                // 3. Dessin et Liste
                data.avatars.forEach(av => {
                    // Carte (Canvas)
                    const x = av.x * 2; const y = 512 - (av.y * 2);
                    // Cible Rouge
                    ctx.strokeStyle = "#ff0000"; ctx.lineWidth = 2; ctx.beginPath();
                    ctx.moveTo(x-10,y); ctx.lineTo(x+10,y); ctx.moveTo(x,y-10); ctx.lineTo(x,y+10); ctx.stroke();
                    // Point central
                    ctx.fillStyle = "white"; ctx.beginPath(); ctx.arc(x,y,3,0,7); ctx.fill();
                    // Nom
                    ctx.fillStyle = "white"; ctx.font = "bold 11px 'SF Mono', monospace";
                    ctx.fillText(av.name.toUpperCase(), x+14, y+4);

                    // Liste (HTML PRO)
                    const row = document.createElement('div');
                    row.className = 'av-row';
                    const timeS = Math.floor(Date.now() / 1000) - av.start_time;

                    row.innerHTML = `
                        <div class="c-stat"><span class="dot"></span></div>
                        <div class="c-name">${av.name}</div>
                        <div class="c-pos">${Math.floor(av.x)}, ${Math.floor(av.y)}</div>
                        <div class="c-time">${fmtTimeCyber(timeS)}</div>
                    `;
                    listC.appendChild(row);
                });
            } catch (err) {}
        }
        setInterval(updateMonitor, 2000);
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
            
            # Mise à jour sim
            db["region"] = data.get("region", "Inconnue")
            db["coords"] = data.get("grid_coords", {"x":0, "y":0})
            
            # Gestion avatars et temps
            incoming = data.get("avatars", [])
            active_list = []
            now = time.time()
            
            for av in incoming:
                uid = av.get("key")
                if uid:
                    if uid not in times:
                        times[uid] = now # Nouvel avatar : on stocke l'heure de début
                    av["start_time"] = times[uid] # On lui associe son heure de début
                    active_list.append(av)
            
            db["avatars"] = active_list
            return "OK", 200
        except: return "Error", 500
            
    return jsonify(db)

@app.route('/')
def home():
    return render_template_string(CYBER_HTML_V3_1)
