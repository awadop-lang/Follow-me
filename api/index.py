from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_ZETA_FIX_404_V16"

# Simulation de base de données
users_db = {
    "admin": {
        "pw": "1234",
        "avatars": [],    # Présence locale
        "watchlist": [],  # [{"name": "...", "uuid": "...", "online_sl": False}]
        "history": {},
        "coords": {"x":0, "y":0}
    }
}

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(INTERFACE_HTML, user_name=session['user'])

# --- ROUTE CRITIQUE : RECEPTION RADAR ---
@app.route('/update_radar', methods=['POST'])
def update_radar():
    data = request.get_json(silent=True) or {}
    user = data.get("operator_id", "admin").lower()
    if user in users_db:
        users_db[user]['avatars'] = data.get('avatars', [])
        users_db[user]['coords'] = data.get('grid_coords', {"x":0, "y":0})
        users_db[user]['region'] = data.get('region', 'Unknown')
        return "OK", 200
    return "User Not Found", 404

# --- ROUTE CRITIQUE : STATUS GLOBAL ---
@app.route('/update_global_status', methods=['POST'])
def update_global():
    data = request.get_json(silent=True) or {}
    uuid = data.get('uuid')
    status = data.get('status') == "1"
    # On met à jour le statut dans toutes les watchlists qui contiennent cet UUID
    for u in users_db:
        for agent in users_db[u]['watchlist']:
            if agent.get('uuid') == uuid:
                agent['online_sl'] = status
    return "OK", 200

# --- ROUTE CRITIQUE : LISTE UUID POUR LSL ---
@app.route('/get_watchlist_uuids')
def get_watchlist_uuids():
    user = request.args.get('operator_id', 'admin').lower()
    if user in users_db:
        uuids = [a['uuid'] for a in users_db[user]['watchlist'] if a.get('uuid')]
        return jsonify(uuids)
    return jsonify([])

@app.route('/api_data')
def api_data():
    u = session.get('user', 'admin')
    return jsonify(users_db.get(u, {}))

@app.route('/toggle_watch', methods=['POST'])
def toggle_watch():
    if 'user' not in session: return "Auth Error", 401
    data = request.get_json()
    u = session['user']
    name, uuid = data.get('name'), data.get('uuid')
    
    wl = users_db[u]['watchlist']
    exists = next((item for item in wl if item["name"] == name), None)
    
    if exists:
        users_db[u]['watchlist'].remove(exists)
    else:
        users_db[u]['watchlist'].append({"name": name, "uuid": uuid, "online_sl": True})
    return jsonify({"status": "ok"})

# --- INTERFACE HTML (Simplifiée pour la démo) ---
INTERFACE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>NOX//ZETA v1.6.1</title>
    <style>
        body { background: #020205; color: #0ff; font-family: 'Orbitron', sans-serif; }
        .st-radar { color: #0f0; border: 1px solid #0f0; padding: 2px; } /* En ligne ici */
        .st-grid { color: #ff0; border: 1px solid #ff0; padding: 2px; }  /* En ligne ailleurs */
        .st-off { color: #666; border: 1px solid #666; padding: 2px; }   /* Déconnecté */
        .item { border-bottom: 1px solid #222; padding: 10px; }
    </style>
</head>
<body onload="setInterval(refresh, 2000)">
    <h1>TACTICAL MONITORING</h1>
    <div id="main"></div>
    <script>
        async function refresh() {
            const r = await fetch('/api_data');
            const d = await r.json();
            let html = "<h3>WATCHLIST PERSISTANTE</h3>";
            d.watchlist.forEach(w => {
                const isLocal = d.avatars.find(a => a.uuid === w.uuid);
                let status = w.online_sl ? "st-grid" : "st-off";
                let txt = w.online_sl ? "SL ONLINE" : "OFFLINE";
                if(isLocal) { status = "st-radar"; txt = "LOCAL"; }
                
                html += `<div class='item'>${w.name} <span class='${status}'>${txt}</span></div>`;
            });
            document.getElementById('main').innerHTML = html;
        }
    </script>
</body>
</html>
"""

# Ajouter ici les routes /login et /logout (identiques aux précédentes)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('u', '').lower()
        if u in users_db:
            session['user'] = u
            return redirect(url_for('index'))
    return '<form method="POST"><input name="u"><button>LOGIN</button></form>'

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))
