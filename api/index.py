from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = "NOX_ZETA_RENDER_2026"

# Base de données volatile
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "Initialisation...", 
        "coords": {"x":0, "y":0}, 
        "avatars": [],
        "history": {},
        "watchlist": [] # [{"name":str, "uuid":str, "online_sl":bool, "last_ping":float}]
    }
}

# --- Copie ici le bloc INTERFACE_HTML (le design cyberpunk que tu as validé) ---
# (Je raccourcis ici pour la lisibilité, garde bien tout le HTML/CSS précédent)
INTERFACE_HTML = """...""" 

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(INTERFACE_HTML)

@app.route('/update_radar', methods=['POST'])
def update_radar():
    data = request.get_json(silent=True) or {}
    user = data.get("op", "admin").lower()
    if user in users_db:
        now = datetime.now().strftime("%H:%M:%S")
        new_avs = data.get('avs', [])
        names = [a['name'] for a in new_avs]
        hist = users_db[user]["history"]
        
        # Logique In/Out
        for n in names:
            if n not in hist or not hist[n].get('active'):
                hist[n] = {'in': now, 'out': '--:--:--', 'active': True}
        for n, s in hist.items():
            if s.get('active') and n not in names:
                s['out'] = now; s['active'] = False
                
        users_db[user].update({
            'region': data.get('reg'),
            'coords': data.get('pos'),
            'avatars': new_avs
        })
        return "OK", 200
    return "ERR", 404

@app.route('/update_global', methods=['POST'])
def update_global():
    data = request.get_json(silent=True) or {}
    uuid, status = data.get('uuid'), data.get('status') == "1"
    for u in users_db:
        for agent in users_db[u]['watchlist']:
            if agent.get('uuid') == uuid:
                agent['online_sl'] = status
                agent['last_ping'] = time.time()
    return "OK", 200

@app.route('/get_watchlist')
def get_watchlist():
    op = request.args.get('op', 'admin').lower()
    return jsonify([a['uuid'] for a in users_db[op]['watchlist']])

@app.route('/api_data')
def api_data():
    user = session.get('user', 'admin')
    return jsonify(users_db.get(user, {}))

@app.route('/toggle_watch', methods=['POST'])
def toggle_watch():
    u = session.get('user', 'admin')
    data = request.get_json()
    name, uuid = data.get('name'), data.get('uuid')
    wl = users_db[u]['watchlist']
    exists = next((i for i in wl if i["uuid"] == uuid), None)
    if exists: wl.remove(exists)
    else: wl.append({"name": name, "uuid": uuid, "online_sl": True, "last_ping": time.time()})
    return jsonify({"status": "ok"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('u', '').lower(), request.form.get('p', '')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('index'))
    return '<form method="POST">USER: <input name="u"> PASS: <input type="password" name="p"><button>IN</button></form>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
