import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "NOX_ZETA_STABLE_2026")

# Base de données temporaire
db = {
    "admin": {
        "pw": "1234",
        "region": "Initialisation...",
        "coords": {"x": 0, "y": 0},
        "avatars": [],
        "history": {},
        "watchlist": [] # [{"name":str, "uuid":str, "online_sl":bool, "last_ping":float}]
    }
}

# --- Design Cyberpunk Minimaliste ---
HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NOX//ZETA v1.7.3</title>
    <style>
        body { background: #020205; color: #0ff; font-family: sans-serif; margin: 0; padding: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 350px; gap: 20px; }
        .map-box { border: 1px solid #0ff; height: 512px; width: 512px; position: relative; background: #000; }
        .item { background: rgba(0,255,255,0.05); border: 1px solid rgba(0,255,255,0.2); padding: 10px; margin-bottom: 10px; }
        .st-on { color: #0f0; } .st-off { color: #f00; }
        button { cursor: pointer; background: transparent; border: 1px solid #0ff; color: #0ff; }
    </style>
</head>
<body onload="setInterval(refresh, 3000)">
    <h2>NOX//ZETA - <span id="reg-name">---</span></h2>
    <div class="grid">
        <div class="map-box">
            <div id="map-bg" style="width:100%; height:100%; opacity:0.5; background-size:cover;"></div>
        </div>
        <div>
            <h3>WATCHLIST</h3>
            <div id="w-list"></div>
            <hr>
            <h3>RADAR</h3>
            <div id="r-list"></div>
        </div>
    </div>
    <script>
        async function refresh() {
            const r = await fetch('/api_data');
            const d = await r.json();
            document.getElementById('reg-name').innerText = d.region;
            if(d.coords.x > 0) document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
            
            document.getElementById('r-list').innerHTML = d.avatars.map(a => `
                <div class="item">${a.name} <button onclick="toggle('${a.name}','${a.uuid}')">+</button></div>
            `).join('');

            document.getElementById('w-list').innerHTML = d.watchlist.map(w => {
                const isOn = d.avatars.find(a => a.uuid === w.uuid);
                return `<div class="item">${w.name} <span class="${isOn?'st-on':'st-off'}">${isOn?'[LOCAL]':'[GRID]'}</span> <button onclick="toggle('${w.name}','${w.uuid}')">x</button></div>`;
            }).join('');
        }
        async function toggle(n, u) { 
            await fetch('/toggle_watch', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:n, uuid:u})});
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    if 'user' not in session: return redirect('/login')
    return render_template_string(HTML_UI)

@app.route('/update_radar', methods=['POST'])
def update_radar():
    data = request.get_json(silent=True) or {}
    user = data.get("op", "admin").lower()
    if user in db:
        db[user].update({'region': data.get('reg'), 'coords': data.get('pos'), 'avatars': data.get('avs', [])})
        return "OK", 200
    return "ERR", 404

@app.route('/update_global', methods=['POST'])
def update_global():
    data = request.get_json(silent=True) or {}
    uuid, status = data.get('uuid'), data.get('status') == "1"
    for agent in db['admin']['watchlist']:
        if agent['uuid'] == uuid:
            agent['online_sl'] = status
            agent['last_ping'] = time.time()
    return "OK", 200

@app.route('/get_watchlist')
def get_watchlist():
    return jsonify([a['uuid'] for a in db['admin']['watchlist']])

@app.route('/api_data')
def api_data():
    return jsonify(db.get(session.get('user', 'admin'), {}))

@app.route('/toggle_watch', methods=['POST'])
def toggle_watch():
    u = session.get('user', 'admin')
    d = request.get_json()
    wl = db[u]['watchlist']
    exists = next((i for i in wl if i["uuid"] == d['uuid']), None)
    if exists: wl.remove(exists)
    else: wl.append({"name": d['name'], "uuid": d['uuid'], "online_sl": True, "last_ping": time.time()})
    return jsonify({"status": "ok"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('u', '').lower()
        if u in db: session['user'] = u; return redirect('/')
    return '<body style="background:#000;color:#0ff;"><form method="POST">USER: <input name="u"><button>IN</button></form></body>'

@app.route('/logout')
def logout(): session.clear(); return redirect('/')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
