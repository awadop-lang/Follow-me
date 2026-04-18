from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

# Base de données stable (stockage temporaire en mémoire vive)
db = {
    "region": "NET_SEARCHING...",
    "coords": {"x": 0, "y": 0},
    "avatars": [] # Liste des avatars actifs détectés
}
# Dictionnaire pour le suivi du temps (UUID: timestamp)
times = {}

# Palette de couleurs Cyberpunk Néon (Cyan dominate, Magenta accent)
# Ces couleurs seront attribuées aléatoirement aux avatars
AGENT_COLORS = [
    "#00ffff", # Cyan Électrique
    "#ff00ff", # Magenta Néon
    "#00ff9f", # Vert Matrice
    "#7f00ff", # Violet Profond
    "#ffff00", # Jaune Canari
    "#ff3f00", # Orange Brûlé
    "#007fff"  # Bleu Azur
]

# --- INTERFACE NEON CYBER CORE V4.1 (PC OPTIMIZED) ---
HTML_CODE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>NEON_MONITOR // CORE_V4.1 // CYAN_PROTOCOL</title>
    <style>
        :root {
            --bg: #010103; /* Noir/Bleu très profond */
            --panel: #050509; /* Panneau sombre bleu */
            --p: #00ffff; /* Cyan Néon Principal */
            --p-dim: #004444; /* Cyan éteint */
            --accent: #ff00ff; /* Magenta Néon Accent */
            --text: #c0e0e0; /* Texte bleu très clair */
            --font: 'SF Mono', 'Fira Code', 'Roboto Mono', monospace;
        }

        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: var(--font);
            margin: 0; padding: 20px;
            display: flex; flex-direction: column; height: 100vh;
            overflow: hidden;
            background-image: 
                radial-gradient(var(--panel) 1px, transparent 1px),
                linear-gradient(rgba(0, 255, 255, 0.03) 1px, transparent 1px);
            background-size: 20px 20px, 100px 100px; /* Grille de fond complexe */
            box-shadow: inset 0 0 100px rgba(0, 255, 255, 0.05); /* Halo global */
        }

        /* En-tête Cyber Néon */
        header {
            display: flex; justify-content: space-between; align-items: center;
            padding-bottom: 10px; border-bottom: 2px solid var(--p-dim);
            margin-bottom: 20px;
            position: relative;
        }
        header::after { /* Effet de lueur sous la bordure */
            content: ''; position: absolute; bottom: -2px; left: 0; width: 100%; height: 2px;
            background: var(--p); box-shadow: 0 0 15px var(--p);
        }
        h1 { margin: 0; font-size: 18px; letter-spacing: 4px; color: var(--p); text-shadow: 0 0 10px var(--p); text-transform: uppercase; }
        .sys-info { font-size: 12px; color: var(--text); border: 1px solid var(--p-dim); padding: 5px 15px; border-radius: 3px; background: rgba(0,0,0,0.5); box-shadow: 0 0 5px rgba(0,255,255,0.1); }

        /* Grille Principale */
        .main-grid {
            display: grid;
            grid-template-columns: 520px 1fr; /* Largeur fixe pour la carte */
            gap: 25px; flex: 1; height: calc(100% - 80px);
        }

        /* Zone Carte (Gauche) */
        .map-outer {
            display: flex; flex-direction: column; gap: 10px;
        }
        .map-container {
            width: 512px; height: 512px;
            border: 2px solid var(--p-dim);
            background-color: #000;
            position: relative;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.1);
            overflow: hidden;
            transition: border-color 0.3s;
        }
        .map-container:hover { border-color: var(--p); box-shadow: 0 0 30px rgba(0, 255, 255, 0.2); }
        
        #map-bg {
            width: 100%; height: 100%;
            background-repeat: no-repeat;
            background-size: 100% 100%; /* Ratio Forcé */
            background-position: center;
            position: absolute; top:0; left:0;
            filter: saturate(0.7) brightness(0.8); /* Ambiance plus sombre */
        }
        canvas { position: absolute; top:0; left:0; z-index: 5; }

        /* Effet Scanline & Glitch */
        .overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.15) 50%), 
                        linear-gradient(90deg, rgba(0, 255, 255, 0.02), rgba(255, 0, 255, 0.01), rgba(0, 255, 255, 0.02));
            background-size: 100% 4px, 4px 100%; pointer-events: none; z-index: 10;
            opacity: 0.6;
        }

        /* Liste des Agents (Droite) */
        .list-container {
            background: var(--panel);
            border: 1px solid var(--p-dim);
            border-radius: 4px;
            padding: 20px;
            overflow-y: auto;
            position: relative;
            box-shadow: inset 0 0 20px rgba(0, 255, 255, 0.03);
        }
        .list-header {
            font-size: 11px; color: var(--p);
            font-weight: bold; padding-bottom: 10px;
            border-bottom: 1px solid var(--p-dim);
            margin-bottom: 15px;
            text-transform: uppercase; letter-spacing: 2px;
            text-shadow: 0 0 5px var(--p);
        }

        /* Ligne d'avatar PRO */
        .av-row {
            display: grid;
            grid-template-columns: 20px 1fr 100px 70px; /* Colonnes fixes */
            gap: 10px; align-items: center;
            padding: 12px 5px;
            border-bottom: 1px solid rgba(0, 255, 255, 0.05);
            font-size: 13px;
            transition: background 0.2s;
            position: relative;
        }
        .av-row:hover { background: rgba(0, 255, 255, 0.03); cursor: pointer; }
        .av-row::before { /* Ligne technique verticale */
            content: ''; position: absolute; left: 0; top: 10%; width: 2px; height: 80%; background: var(--p-dim);
        }
        .av-row:hover::before { background: var(--p); box-shadow: 0 0 5px var(--p); }

        /* Cellules */
        .c-stat { display: flex; justify-content: center; }
        .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--p); box-shadow: 0 0 8px var(--p); animation: pulse 2s infinite; }
        .c-name { color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: bold; font-size: 13px; text-transform: uppercase; }
        .c-pos { color: var(--p); text-align: right; letter-spacing: 1px; font-weight: bold; }
        .c-time { color: var(--text); text-align: right; opacity: 0.8; }

        /* Barre de progression du temps (CYAN) */
        .progress-box { grid-column: 2 / -1; margin-top: 5px; }
        .progress-bg { width: 100%; height: 3px; background: #080810; border-radius: 1px; overflow: hidden; border: 1px solid #111; }
        .progress-fill { height: 100%; width: 0%; transition: width 1s; box-shadow: 0 0 10px currentColor; }

        /* Animations */
        @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }
        @keyframes glitch-text { 0% { text-shadow: 0 0 8px var(--p); } 1% { text-shadow: 2px 0 var(--accent), -2px 0 var(--p); } 2% { text-shadow: 0 0 8px var(--p); } 100% { text-shadow: 0 0 8px var(--p); } }

    </style>
</head>
<body>
    <header>
        <h1 style="animation: glitch-text 5s infinite;">[CYBER_CORE // NEON_PROTOCOL]</h1>
        <div class="sys-info">SYS: <span style="color:var(--p)" id="r_name">---</span> // NET_COORDS: <span id="r_coords">000,000</span></div>
    </header>

    <div class="main-grid">
        <div class="map-outer">
            <div class="map-container">
                <div id="map-bg"></div>
                <div class="overlay"></div>
                <canvas id="cv" width="512" height="512"></canvas>
            </div>
            <div style="font-size:10px; color:var(--p-dim); text-align:center;">// LIVE_MAP_FEED // RATIO_FORCED_1:1</div>
        </div>

        <div class="list-container">
            <div class="list-header">
                <span>ST</span><span>AGENT_IDENT</span><span style="text-align:right">POS_XY</span><span style="text-align:right">DURATION</span>
            </div>
            <div id="list-rows">
                </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const listRows = document.getElementById('list-rows');
        const mapBg = document.getElementById('map-bg');

        // Palette de couleurs Cyberpunk Néon pour différencier les noms sur la map
        const agentColors = ["#00ffff", "#ff00ff", "#00ff9f", "#7f00ff", "#ffff00", "#ff3f00", "#007fff"];

        function fmtTimeCyber(seconds) {
            const m = Math.floor(seconds / 60);
            const s = Math.floor(seconds % 60);
            return `${m.toString().padStart(2, '0')}M ${s.toString().padStart(2, '0')}S`;
        }

        async function updateMonitor() {
            try {
                const response = await fetch('/api');
                const data = await response.json();
                
                // 1. Infos globales
                if(data.region) {
                    document.getElementById('r_name').innerText = data.region.toUpperCase();
                    document.getElementById('r_coords').innerText = `${data.coords.x.toString().padStart(3, '0')},${data.coords.y.toString().padStart(3, '0')}`;
                    const mapUrl = `https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg`;
                    mapBg.style.backgroundImage = `url('${mapUrl}')`;
                }

                // 2. Nettoyage
                ctx.clearRect(0, 0, 512, 512);
                listRows.innerHTML = "";

                if (data.avatars.length === 0) {
                    listRows.innerHTML = "<div style='color:#333;text-align:center;margin-top:30px;font-size:11px;'>[ NO_TARGETS_IN_RANGE ]</div>";
                }

                // 3. Dessin et Liste
                data.avatars.forEach((av, index) => {
                    // Attribution d'une couleur unique basée sur l'index
                    const aColor = agentColors[index % agentColors.length];
                    
                    // --- Carte (Canvas) ---
                    // Conversion coords SL (256x256) vers Canvas (512x512)
                    const x = av.x * 2;
                    const y = 512 - (av.y * 2);

                    // Croix de ciblage technique (Couleur Néon de l'agent)
                    ctx.strokeStyle = aColor; ctx.lineWidth = 2; ctx.beginPath();
                    ctx.moveTo(x-12,y); ctx.lineTo(x+12,y); ctx.moveTo(x,y-12); ctx.lineTo(x,y+12); ctx.stroke();
                    
                    // Point central brillant (Blanc)
                    ctx.fillStyle = "white"; ctx.shadowBlur = 10; ctx.shadowColor = aColor;
                    ctx.beginPath(); ctx.arc(x,y,3,0, Math.PI * 2); ctx.fill();

                    // Nom sur carte (Blanc avec contour pour lisibilité)
                    ctx.shadowBlur = 0;
                    ctx.fillStyle = "white"; ctx.font = "bold 11px 'SF Mono', monospace";
                    ctx.strokeStyle = "black"; ctx.lineWidth = 2;
                    ctx.strokeText(av.name.toUpperCase(), x + 15, y + 4); // Contour
                    ctx.fillText(av.name.toUpperCase(), x + 15, y + 4); // Texte

                    // --- Liste (HTML PRO) ---
                    const row = document.createElement('div');
                    row.className = 'av-row';
                    
                    // Calcul temps de connexion
                    const currentTime = Math.floor(Date.now() / 1000);
                    const timeOnSim = currentTime - av.start_time;
                    
                    // Calcul progression (max 60 min = 100%)
                    const progressPercent = Math.min(100, (timeOnSim / 3600) * 100);

                    row.innerHTML = `
                        <div class="c-stat"><span class="dot"></span></div>
                        <div class="c-name">${av.name}</div>
                        <div class="c-pos">${Math.floor(av.x).toString().padStart(3, '0')}, ${Math.floor(av.y).toString().padStart(3, '0')}</div>
                        <div class="c-time">${fmtTimeCyber(timeOnSim)}</div>
                        <div class="progress-box">
                            <div class="progress-bg">
                                <div class="progress-fill" style="width:${progressPercent}%; background-color:${aColor}; color:${aColor}"></div>
                            </div>
                        </div>
                    `;
                    listRows.appendChild(row);
                });

            } catch (err) { console.log("DATA_STREAM_ERROR // NET_LOSS", err); }
        }
        setInterval(updateMonitor, 2000); // Mise à jour toutes les 2 secondes
    </script>
</body>
</html>
"""

@app.route('/api', methods=['GET', 'POST'])
def handle_api():
    global db, times
    if request.method == 'POST':
        try:
            data = request.json
            if not data: return "No Data", 400
            
            # Mise à jour des infos sim
            db["region"] = data.get("region", "UNKNOWN")
            db["coords"] = data.get("grid_coords", {"x":0, "y":0})
            
            # Gestion des avatars et du temps de connexion
            incoming = data.get("avatars", [])
            active_list = []
            now = time.time()
            
            for av in incoming:
                uid = av.get("key")
                if uid:
                    # Si c'est un nouvel avatar, on stocke son heure d'arrivée
                    if uid not in times:
                        times[uid] = now
                    # On lui associe son heure de début stockée
                    av["start_time"] = times[uid]
                    active_list.append(av)
            
            db["avatars"] = active_list
            return "OK", 200
        except Exception as e:
            print(f"Error: {e}")
            return str(e), 500
            
    # GET : Renvoyer la base de données actuelle
    return jsonify(db)

@app.route('/')
def home():
    return render_template_string(HTML_CODE)
