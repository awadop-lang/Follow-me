import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "NOX_ZETA_2026_STABLE")

# Base de données en mémoire
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "Initialisation...", 
        "coords": {"x":0, "y":0}, 
        "avatars": [],
        "history": {},
        "watchlist": []
    }
}

INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@500;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --red: #ff3131; --green: #00ffaa; --bg: #020205; --panel: rgba(12, 12, 25, 0.98); --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { height: 55px; border-bottom: 1px solid var(--border); background: var(--panel); display: flex; justify-content: space-between; align-items: center; padding: 0 20px; flex-shrink: 0; }
        .logo { font-family: 'Orbitron'; font-weight: 700; color: var(--cyan); letter-spacing: 2px; }
        .main-container { display: flex; flex: 1; overflow: hidden; width: 100%; }
        .column { height: 100%; overflow: hidden; display: flex; flex-direction: column; background: var(--panel); min-width: 250px; border-right: 1px solid var(--border); }
        .col-header { padding: 15px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 11px; color: var(--magenta); background: rgba(0,0,0,0.5); text-transform: uppercase; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 12px; }
        .item { background: rgba(255,255,255,0.02); border: 1px solid var(--border); padding: 12px; margin-bottom: 10px; position: relative; }
        .item.watched { border-left: 4px solid var(--red); background: rgba(255, 49, 49, 0.05); }
        .name { color: var(--cyan); font-weight: 700; font-size: 15px; font-family: 'Orbitron'; text-decoration: none; }
        .log-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px; }
        .time-badge { background: rgba(0,0,0,0.5); padding: 5px; border-radius: 3px; border: 1px solid rgba(255,255,255,0.1); }
        .time-label { font-size: 8px; text-transform: uppercase; color: #888; display: block; }
        .time-value { font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; }
        .val-in { color: var(--green); } .val-out { color: var(--red); }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 5px; }
        .online { background: var(--green); box-shadow: 0 0 8px var(--green); }
        .offline { background: #444; }
        .map-frame { position: relative; width: 512px; height: 512px; border: 1px solid var(--cyan); background: #000; margin: auto; }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.4; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
        .action-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); font-family: 'Orbitron'; cursor: pointer; float: right; padding: 2px 8px; }
    </style>
</head>
<body onload="setInterval(updateUI, 3000)">
    <header>
        <div class="logo">NOX//ZETA SYSTEM</div>
        <div style="font-family:monospace; font-size:12px; color:var(--cyan);">[ <span id="reg-name">---</span> ]</div>
        <a href="/logout" style="color:var(--red); text-decoration:none; font-family:'Orbitron'; font-size:11px; border:1px solid var(--red); padding:5px 10px;">LOGOUT</a>
    </header>
    <div class="main-container">
        <div class="column" style="width: 45%;">
            <div class="col-header">Tactical_Radar</div>
            <div class="scroll-area"><div class="map-frame"><div id="map-bg"></div><canvas id="radar-canvas" width="512" height="512"></canvas></div></div>
        </div>
        <div class="column" style="width: 25%;">
            <div class="col-header">Live_Scanner</div>
            <div id="scan-list" class="scroll-area"></div>
        </div>
        <div class="column" style="width: 30%;">
            <div class="col-header" style="color:var(--red)">Priority_Watchlist</div>
            <div id="watch-list" class="scroll-area"></div>
        </div>
    </div>
    <script>
        async function updateUI() {
            try {
                const res = await fetch('/api_data');
                const data = await res.json();
                document.getElementById('reg-name').innerText = data.region;
                if(data.coords) document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;
                
                document.getElementById('scan-list').innerHTML = data.avatars.map(av => `
                    <div class="item">
                        <button class="action-btn" onclick="toggle('${av.name}','${av.uuid}')">+</button>
                        <span class="name">${av.name}</span>
                    </div>`).join('');

                document.getElementById('watch-list').innerHTML = data.watchlist.map(w => {
                    const h = data.history[w.name] || {in:"--", out:"--", active:false};
                    const isOn = data.avatars.find(a => a.uuid === w.uuid);
                    return `
                    <div class="item watched">
                        <span class="status-dot ${isOn?'online':'offline'}"></span>
                        <span class="name">${w.name}</span>
                        <button class="action-btn" onclick="toggle('${w.name}','${w.uuid}')" style="color:var(--red);border-color:var(--red)">X</button>
                        <div class="log-grid">
                            <div class="time-badge"><span class="time-label">IN</span><span class="time-value val-in">${h.in}</span></div>
                            <div class="time-badge"><span class="time-label">OUT</span><span class="time-value val-out">${h.out}</span></div>
                        </div>
                    </div>`;
                }).join('');

                const ctx = document.getElementById('radar-canvas').getContext('2d');
                ctx.clearRect(0, 0, 512, 512);
                data.avatars.forEach(av => {
                    ctx.fillStyle = data.watchlist.some(w => w.uuid === av.uuid) ? "#f00" : "#0ff";
                    ctx.beginPath(); ctx.arc(av.x*2, 512-(av.y*2), 6, 0, Math.PI*2); ctx.fill();
                });
            } catch(e) {}
        }
        async function toggle(n, u) { 
            await fetch('/toggle_watch', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:n, uuid:u})});
            updateUI(); 
        }
    </script>
</body>
</html>
"""

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
        for n in names:
            if n not in hist or not hist[n].get('active'):
                hist[n] = {'in': now, 'out': '--:--:--', 'active': True}
        for n, s in hist.items():
            if s.get('active') and n not in names:
                s['out'] = now; s['active'] = False
        users_db[user].update({'region': data.get('reg'), 'coords': data.get('pos'), 'avatars': new_avs})
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
    return jsonify(users_db.get(session.get('user', 'admin'), {}))

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
    return '<body style="background:#000;color:#0ff;display:flex;justify-content:center;align-items:center;height:100vh;"><form method="POST" style="border:1px solid #0ff;padding:20px;"><h2>NOX_LOGIN</h2><input name="u" placeholder="User"><br><input type="password" name="p" placeholder="Pass"><br><button>ENTER</button></form></body>'

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
