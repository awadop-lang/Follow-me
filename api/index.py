from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)
# Structure de données stable pour le live-tracking
db = {
    "region": None,
    "coords": {"x": 0, "y": 0},
    "avatars": [] # Liste des avatars actifs détectés
}

# --- Design System : Cyberpunk Console ---
CYBER_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CYBER_MONITOR // CORE_READOUT_V3</title>
    <style>
        /* Palette de couleurs Cyberpunk (Ambre / Noir / Rouge Alerte) */
        :root {
            --bg-deep: #030303; /* Noir presque pur */
            --bg-panel: #0a0a0a; /* Noir panneau */
            --primary: #ffb000; /* Ambre Classique */
            --primary-dim: #553300; /* Ambre éteint */
            --accent: #ff0033; /* Rouge Alerte Cyber */
            --text-main: #e0e0e0;
            --font-cyber: 'Fira Code', 'Roboto Mono', 'Courier New', monospace;
            --border-tech: 1px solid #222;
        }

        body {
            background-color: var(--bg-deep);
            color: var(--text-main);
            font-family: var(--font-cyber);
            margin: 0; padding: 15px;
            display: flex; flex-direction: column; height: 100vh;
            overflow: hidden;
            background-image: radial-gradient(#111 1px, transparent 1px);
            background-size: 30px 30px; /* Grille de fond subtile */
        }

        /* --- En-tête Cyber --- */
        header {
            display: flex; justify-content: space-between; align-items: center;
            padding-bottom: 10px; border-bottom: 2px solid var(--primary-dim);
            margin-bottom: 15px;
            position: relative;
        }
        header::after { /* Effet de glitch subtil sur la bordure */
            content: ''; position: absolute; bottom: -2px; left: 0; width: 100%; height: 2px;
            background: var(--primary); animation: glitch-band 4s infinite; opacity: 0.3;
        }
        h1 { margin: 0; font-size: 16px; letter-spacing: 3px; color: var(--primary); text-shadow: 0 0 8px var(--primary); font-weight: bold; }
        #region-info { font-size: 12px; color: var(--text-main); background: #111; padding: 2px 8px; border-radius: 4px; border: var(--border-tech); }
        #status-glitch { font-size: 11px; color: var(--text-main); opacity: 0.7; }

        /* --- Grille Principale Cyber --- */
        .cyber-grid {
            display: grid;
            grid-template-columns: 1.8fr 1fr; /* Carte plus grande */
            gap: 15px; flex: 1; height: calc(100% - 60px);
        }

        /* --- Zone Carte Cyber (GAUCHE) --- */
        .map-zone {
            background-color: var(--bg-panel);
            border: 2px solid var(--primary-dim);
            border-radius: 4px;
            padding: 5px;
            display: flex; justify-content: center; align-items: center;
            overflow: hidden;
            position: relative;
            box-shadow: inset 0 0 15px rgba(255,176,0,0.05);
        }
        /* Bordures techniques biseautées */
        .map-zone::before, .map-zone::after {
            content: ''; position: absolute; width: 10px; height: 10px; border: 2px solid var(--primary);
        }
        .map-zone::before { top: -2px; left: -2px; border-right: none; border-bottom: none; }
        .map-zone::after { bottom: -2px; right: -2px; border-left: none; border-top: none; }

        .map-viewer {
            position: relative; width: 512px; height: 512px;
            border: 1px solid var(--primary);
            background-color: black;
            background-size: cover;
            background-position: center;
            /* Effet de scanline persistant */
            background-image: linear-gradient(0deg, rgba(0,0,0,0.1) 50%, rgba(255,255,255,0.02) 50%);
            background-size: 100% 4px;
        }
        canvas { position: absolute; top:0; left:0; width: 100%; height: 100%; filter: drop-shadow(0 0 5px rgba(255,0,0,0.8)); }

        /* --- Zone Liste Cyber (DROITE) --- */
        .list-zone {
            background-color: var(--bg-panel);
            border: 2px solid var(--primary-dim);
            border-radius: 4px;
            padding: 10px;
            overflow-y: auto;
            scrollbar-width: thin; scrollbar-color: var(--primary) var(--bg-panel);
        }
        .list-zone h2 { font-size: 12px; color: var(--primary); margin-top: 0; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 0 5px var(--primary); }

        /* Structure de ligne d'avatar CYBER */
        .av-row {
            display: grid;
            grid-template-columns: 15px 1fr 90px 60px;
            gap: 8px; align-items: center;
            padding: 8px 4px;
            border-bottom: 1px solid #1a1a1a;
            font-size: 11px;
            position: relative;
        }
        .av-row:hover { background-color: rgba(255,176,0,0.03); cursor: pointer; }
        .av-row::before { /* Ligne technique verticale */
            content: ''; position: absolute; left: 0; top: 10%; width: 2px; height: 80%; background: var(--primary-dim);
        }
        .av-row:hover::before { background: var(--primary); box-shadow: 0 0 5px var(--primary); }

        /* Cellules Cyber */
        .status-cell { display: flex; justify-content: center; }
        .status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--primary); box-shadow: 0 0 8px var(--primary); animation: pulse 2s infinite; }
        .name-cell { color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: bold; font-size: 12px; text-transform: uppercase; }
        .pos-cell { color: var(--primary); text-align: right; letter-spacing: 1px; }
        .time-cell { color: var(--text-main); text-align: right; opacity: 0.8; }

        /* --- Animations --- */
        @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }
        @keyframes glitch-band { 0% { transform: scaleX(1); } 5% { transform: scaleX(1.05) skewX(2deg); } 10% { transform: scaleX(1); } 100% { transform: scaleX(1); } }

    </style>
</head>
<body>
    <header>
        <h1>[CYBER_MONITOR // CORE_READOUT_V3]</h1>
        <div id="region-info">SYS: <span style="color:var(--primary)" id="reg-name">---</span> (<span id="reg-coords">000,000</span>)</div>
        <div id="status-glitch">STATUS: <span style="color:var(--primary)">ACTIVE_SCAN</span> // NET_OK</div>
    </header>
    
    <div class="cyber-grid">
        <div class="map-zone">
            <div class="map-viewer" id="map-bg">
                <canvas id="map-canvas" width="512" height="512"></canvas>
            </div>
        </div>

        <div class="list-zone">
            <h2>AGENTS_DETECTED // LIVE_FEED</h2>
            <div id="list-container">
                </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('map-canvas');
        const ctx = canvas.getContext('2d');
        const listContainer = document.getElementById('list-container');
        const mapBg = document.getElementById('map-bg');

        // Fonction pour formater le temps (Cyber Style)
        function formatTimeCyber(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            return `${h.toString().padStart(2, '0')}H ${m.toString().padStart(2, '0')}M`;
        }

        async function updateCyberMonitor() {
            try {
                const response = await fetch('/api');
                const data = await response.json();
                
                // 1. Mise à jour des infos globales (Cyber Style)
                if(data.region) {
                    document.getElementById('reg-name').innerText = data.region.toUpperCase();
                    document.getElementById('reg-coords').innerText = `${data.coords.x.toString().padStart(3, '0')},${data.coords.y.toString().padStart(3, '0')}`;
                    const mapUrl = `https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg`;
                    mapBg.style.backgroundImage = `url('${mapUrl}')`;
                }

                document.getElementById('status-glitch').innerHTML = `STATUS: <span style="color:var(--primary)">ACTIVE_SCAN</span> // ${data.avatars.length} TARGETS`;

                // 2. Nettoyage Cyber
                ctx.clearRect(0, 0, 512, 512);
                listContainer.innerHTML = "";

                if (data.avatars.length === 0) {
                    listContainer.innerHTML = "<div style='color:#333;text-align:center;margin-top:30px;font-size:10px;'>[ NO_TARGETS_IN_RANGE ]</div>";
                }

                // 3. Traitement de chaque avatar (Cyber Style)
                data.avatars.forEach(av => {
                    // --- Carte (Canvas) ---
                    const x = av.x * 2;
                    const y = 512 - (av.y * 2);

                    // Dessin de la cible (Croix Cyber Rouge)
                    ctx.strokeStyle = "#ff0033"; // Rouge Alerte
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    // Croix horizontale
                    ctx.moveTo(x - 8, y); ctx.lineTo(x + 8, y);
                    // Croix verticale
                    ctx.moveTo(x, y - 8); ctx.lineTo(x, y + 8);
                    ctx.stroke();

                    // Point central brillant
                    ctx.fillStyle = "white"; ctx.shadowBlur = 10; ctx.shadowColor = "white";
                    ctx.beginPath(); ctx.arc(x, y, 3, 0, Math.PI * 2); ctx.fill();

                    // Nom de l'avatar sur la carte (Cyber style, tout majuscule)
                    ctx.shadowBlur = 0;
                    ctx.fillStyle = "white";
                    ctx.font = "bold 10px 'Fira Code', monospace";
                    ctx.fillText(av.name.toUpperCase(), x + 12, y + 3);

                    // --- Liste (HTML Cyber) ---
                    const row = document.createElement('div');
                    row.className = 'av-row';
                    row.title = `UUID: ${av.key}`; // Info bulle
                    
                    const currentTime = Math.floor(Date.now() / 1000);
                    const timeOnSim = currentTime - av.start_time;

                    row.innerHTML = `
                        <div class="status-cell"><span class="status-dot"></span></div>
                        <div class="name-cell">${av.name.toUpperCase()}</div>
                        <div class="pos-cell">${Math.floor(av.x).toString().padStart(3, '0')} // ${Math.floor(av.y).toString().padStart(3, '0')}</div>
                        <div class="time-cell">${formatTimeCyber(timeOnSim)}</div>
                    `;
                    listContainer.appendChild(row);
                });

            } catch (err) { console.log("CYBER_ERR // NETWORK_LOSS", err); }
        }
        setInterval(updateCyberMonitor, 2000);
    </script>
</body>
</html>
"""

# --- Routes Flask Classiques (Pas de changement) ---

@app.route('/api', methods=['GET', 'POST'])
def handle_api():
    if request.method == 'POST':
        local_avatars_data = request.json
        current_time = Math.floor(time.time())
        
        # Mettre à jour les données des avatars locaux
        current_active = []
        for av in local_avatars_data:
            uuid = av["key"]
            
            # Vérifier si on a déjà un temps de connexion pour cet UUID
            # (Vercel est stateless, on ne peut pas stocker proprement le temps de connexion 
            # de ceux qui partent et reviennent sans base de données).
            # On stocke le temps de connexion actuel s'il est inconnu.
            if "avatars" in db:
                 # Chercher si l'avatar est déjà dans la db locale (in-memory)
                 match = next((item for item in db["avatars"] if item["key"] == uuid), None)
                 if match:
                     av["start_time"] = match["start_time"]
                 else:
                     av["start_time"] = current_time
            else:
                 av["start_time"] = current_time
                 
            current_active.append(av)

        # Mise à jour complète de la DB in-memory
        db["region"] = request.json[0]["region"] if request.json else "Inconnue"
        # On assume que le script LSL envoie les grid_coords
        db["coords"] = request.json[0]["grid_coords"] if request.json else {"x": 0, "y": 0}
        db["avatars"] = current_active
        
        return "OK", 200
        
    return jsonify(db)

@app.route('/')
def home():
    return render_template_string(CYBER_HTML)

# Petite astuce Python pour Vercel
import math as Math
