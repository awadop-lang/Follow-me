from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)
# Structure de données avancée
db = {
    "avatars": {},   # Stockage par UUID {key: {name, pos, last_seen, start_time, total_time_sim}}
    "last_update": 0 # Timestamp global
}

HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RADAR CORE - OPS STATUS</title>
    <style>
        :root { --main-bg: #030303; --hud-green: #00ff41; --hud-blue: #0088ff; --text-dim: #004411; }
        body { background: var(--main-bg); color: var(--hud-green); font-family: 'Courier New', monospace; margin: 0; padding: 10px; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
        
        /* Header style HUD */
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--hud-green); padding-bottom: 5px; margin-bottom: 10px; }
        h1 { margin: 0; font-size: 16px; letter-spacing: 5px; text-shadow: 0 0 5px var(--hud-green); }
        #clock { font-size: 12px; }

        /* Conteneur principal */
        .ops-grid { display: flex; flex-direction: column; height: calc(100vh - 50px); gap: 10px; }
        
        /* Zone Radar (Centrée) */
        .radar-zone { flex: 1; position: relative; display: flex; justify-content: center; align-items: center; background: rgba(0,20,0,0.1); border: 1px solid var(--text-dim); border-radius: 4px; }
        canvas { background: black; border: 2px solid var(--hud-green); border-radius: 50%; box-shadow: 0 0 15px rgba(0,255,0,0.2); }
        .grid-circle { position: absolute; border: 1px solid var(--text-dim); border-radius: 50%; }
        
        /* Zone Liste des Noms (En bas) */
        .list-zone { height: 150px; border-top: 1px solid var(--hud-green); background: rgba(0,5,0,0.5); padding: 5px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--hud-green) var(--main-bg); }
        
        /* Structure de ligne d'avatar */
        .avatar-row { display: grid; grid-template-columns: 15px 150px 1fr 60px; gap: 5px; align-items: center; font-size: 11px; margin-bottom: 4px; padding-bottom: 2px; border-bottom: 1px solid #001100; }
        .avatar-row:hover { background: rgba(0,255,0,0.05); }
        
        /* Icones de statut */
        .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
        .dot-sim { background-color: var(--hud-green); box-shadow: 0 0 5px var(--hud-green); }
        .dot-off { background-color: #aa0000; }
        .dot-else { background-color: var(--hud-blue); box-shadow: 0 0 5px var(--hud-blue); }

        .name-cell { color: white; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: bold; }
        .time-cell { text-align: right; color: var(--hud-green); }
        .time-cell-else { text-align: right; color: var(--hud-blue); }

        /* Barre de temps de connexion */
        .time-bar-bg { width: 100%; height: 6px; background: #001100; border-radius: 3px; position: relative; overflow: hidden; border: 1px solid #002200; }
        .time-bar-fill-sim { height: 100%; background: var(--hud-green); border-radius: 3px; }
        .time-bar-fill-else { height: 100%; background: var(--hud-blue); border-radius: 3px; }

    </style>
</head>
<body>
    <div class="header">
        <h1>[RADAR CORE - OPSHUD]</h1>
        <div id="clock">00:00:00</div>
    </div>
    
    <div class="ops-grid">
        <div class="radar-zone">
            <div class="grid-circle" style="width: 100px; height: 100px;"></div>
            <div class="grid-circle" style="width: 200px; height: 200px;"></div>
            <canvas id="radar" width="256" height="256"></canvas>
        </div>
        
        <div class="list-zone" id="avatar-list">
            </div>
    </div>

    <script>
        // Gestion de l'horloge
        function updateClock() {
            const now = new Date();
            document.getElementById('clock').innerText = now.toLocaleTimeString('fr-FR');
        }
        setInterval(updateClock, 1000);

        const canvas = document.getElementById('radar');
        const ctx = canvas.getContext('2d');
        const listDiv = document.getElementById('avatar-list');

        // Fonction pour formater le temps
        function formatTime(seconds) {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }

        async function updateData() {
            try {
                const response = await fetch('/api');
                const data = await response.json();
                
                // Dessiner Radar
                ctx.clearRect(0, 0, 256, 256);
                ctx.strokeStyle = "#004411";
                ctx.beginPath(); ctx.moveTo(128,0); ctx.lineTo(128,256); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(0,128); ctx.lineTo(256,128); ctx.stroke();

                // Préparer Liste
                listDiv.innerHTML = "";
                
                data.forEach(av => {
                    // Calcul du temps écoulé
                    const currentTime = Math.floor(Date.now() / 1000);
                    const timeOnSim = currentTime - av.start_time;
                    const maxTimeRef = 3600 * 4; // Référence de 4h pour la barre (ajustable)
                    const fillSimPercent = Math.min(100, (timeOnSim / maxTimeRef) * 100);

                    // Créer la ligne de l'avatar
                    const row = document.createElement('div');
                    row.className = 'avatar-row';
                    
                    // Déterminer le statut
                    let statusClass = "dot-else";
                    let fillClass = "time-bar-fill-else";
                    let timeClass = "time-cell-else";
                    let statutTexte = "ELSEWHERE";

                    if (av.is_on_sim) {
                        statusClass = "dot-sim";
                        fillClass = "time-bar-fill-sim";
                        timeClass = "time-cell";
                        statutTexte = "LOCAL SIM";
                        
                        // Dessiner sur Radar
                        const x = av.x;
                        const y = 256 - av.y;
                        ctx.fillStyle = "#ff0000";
                        ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.fill();
                        
                        ctx.fillStyle = "white"; ctx.font = "8px 'Courier New'";
                        ctx.fillText(av.name.toUpperCase(), x + 7, y + 2);
                    }

                    row.innerHTML = `
                        <div><span class="status-dot ${statusClass}"></span></div>
                        <div class="name-cell">${av.name.toUpperCase()}</div>
                        <div class="time-bar-bg">
                            <div class="${fillClass}" style="width: ${fillSimPercent}%"></div>
                        </div>
                        <div class="${timeClass}">${formatTime(timeOnSim)}</div>
                    `;
                    listDiv.appendChild(row);
                });

            } catch (err) { console.log("OPS ERR..."); }
        }
        setInterval(updateData, 2000);
    </script>
</body>
</html>
"""

@app.route('/api', methods=['GET', 'POST'])
def handle_api():
    if request.method == 'POST':
        # Données reçues de Second Life (uniquement les avatars LOCAUX)
        local_avatars_data = request.json
        current_time = Math.floor(time.time())
        
        # Marquer tout le monde comme temporairement absent de la sim
        for key in db["avatars"]:
            db["avatars"][key]["is_on_sim"] = False

        # Mettre à jour les données des avatars locaux
        for av in local_avatars_data:
            uuid = av["key"]
            name = av["name"]
            
            if uuid not in db["avatars"]:
                # Nouvel avatar détecté !
                db["avatars"][uuid] = {
                    "name": name,
                    "x": av["x"], "y": av["y"],
                    "start_time": current_time,
                    "is_on_sim": True
                }
            else:
                # Mise à jour des coordonnées
                db["avatars"][uuid].update({
                    "x": av["x"], "y": av["y"],
                    "is_on_sim": True
                })

        # Vercel est "serverless", il n'a pas de mémoire persistante.
        # Ce tracker est parfait pour du direct, mais il "oublie" les avatars 
        # quand ils partent si l'application s'endort.
        
        return "OK", 200
        
    # GET : Renvoyer tous les avatars suivis
    # (Pour cet hébergement gratuit, on ne renvoie que ceux ACTUELLEMENT sur la sim)
    current_avatars = []
    for key, data in db["avatars"].items():
        if data["is_on_sim"]:
            current_avatars.append(data)
            
    return jsonify(current_avatars)

@app.route('/')
def home():
    return render_template_string(HTML)

# Petite astuce Python pour Vercel
import math as Math
