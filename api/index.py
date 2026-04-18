from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_ZETA_GLOBAL_STAY_V16"

users_db = {
    "admin": {
        "pw": "1234",
        "avatars": [],    # Présence locale (Radar)
        "watchlist": [],  # [{ "name": "...", "uuid": "...", "online_sl": False }]
        "history": {}
    }
}

# --- Logique de l'Interface ---
INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <style>
        :root { --cyan: #00ffff; --red: #ff3131; --green: #00ffaa; --bg: #020205; --panel: rgba(12,12,25,0.95); }
        body { background: var(--bg); color: #eee; font-family: 'Rajdhani', sans-serif; margin: 0; }
        .status-badge { font-size: 9px; padding: 2px 5px; border-radius: 3px; font-weight: bold; border: 1px solid; }
        
        /* Vert : Sur ton radar */
        .st-radar { color: var(--green); border-color: var(--green); background: rgba(0,255,170,0.1); }
        /* Jaune : Connecté à SL mais ailleurs */
        .st-grid { color: #f1c40f; border-color: #f1c40f; background: rgba(241,196,15,0.1); }
        /* Rouge : Déconnecté de SL */
        .st-off { color: #666; border-color: #666; background: rgba(255,255,255,0.05); }
        
        .item { background: rgba(255,255,255,0.02); border: 1px solid rgba(0,255,255,0.1); padding: 10px; margin-bottom: 8px; }
        .name { color: var(--cyan); font-family: 'Orbitron'; cursor: pointer; }
    </style>
</head>
<body>
    <div style="display:flex; height:100vh;">
        <div style="width:70%; border-right:1px solid #222; padding:20px;">
             <h3 style="color:var(--cyan)">TACTICAL RADAR</h3>
             <div id="radar-container">/* Carte ici */</div>
        </div>
        
        <div style="width:30%; padding:20px; background:var(--panel);">
            <h3 style="color:var(--red)">WATCHLIST GLOBALE</h3>
            <div id="watch-list"></div>
        </div>
    </div>

    <script>
        async function updateUI() {
            const res = await fetch('/api_data');
            const data = await res.json();
            const wl = data.watchlist || [];
            const local = data.avatars || []; // Agents vus par le scanner

            document.getElementById('watch-list').innerHTML = wl.map(w => {
                const isLocal = local.find(l => l.uuid === w.uuid);
                const isOnlineSL = w.online_sl; // Info venant du dataserver LSL
                
                let statusClass = "st-off";
                let statusText = "OFFLINE";

                if (isLocal) {
                    statusClass = "st-radar";
                    statusText = "SUR RADAR";
                } else if (isOnlineSL) {
                    statusClass = "st-grid";
                    statusText = "EN LIGNE (AUTRE REGION)";
                }

                return `
                <div class="item">
                    <span class="name">${w.name}</span>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                    <div style="font-size:10px; color:#555; margin-top:5px;">UUID: ${w.uuid}</div>
                </div>`;
            }).join('');
        }
        setInterval(updateUI, 2000);
    </script>
</body>
</html>
"""

@app.route('/api_data')
def api_data():
    return jsonify(users_db.get(session.get('user', 'admin'), {}))

@app.route('/update_global_status', methods=['POST'])
def update_global():
    # Cette route est appelée par le script LSL (dataserver)
    data = request.json
    uuid = data.get('uuid')
    is_online = (data.get('status') == "1")
    
    for user in users_db:
        for agent in users_db[user]['watchlist']:
            if agent['uuid'] == uuid:
                agent['online_sl'] = is_online # On met à jour le statut global
    return "OK"

# ... (reste du code Flask : /login, /toggle_watch etc)
