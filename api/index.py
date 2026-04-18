from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_ZETA_STABLE_V162"

# Base de données temporaire (Mémoire vive)
# Note : Se réinitialise au déploiement Vercel
db = {
    "admin": {
        "pw": "1234",
        "region": "SEARCHING...",
        "coords": {"x": 128, "y": 128},
        "avatars": [],    # Présence locale (Radar)
        "watchlist": [],  # Persistance : [{"name": "...", "uuid": "...", "online_sl": False}]
        "history": {}
    }
}

# --- INTERFACE TACTIQUE ---
INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --red: #ff3131; --green: #00ffaa; --bg: #020205; --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { height: 50px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; padding: 0 20px; background: rgba(10,10,20,0.9); }
        .logo { font-family: 'Orbitron'; font-weight: 700; color: var(--cyan); letter-spacing: 2px; font-size: 14px; }
        .main-container { display: flex; flex: 1; overflow: hidden; }
        .column { height: 100%; display: flex; flex-direction: column; border-right: 1px solid var(--border); background: rgba(5,5,10,0.5); }
        .col-header { padding: 12px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 10px; color: var(--magenta); text-transform: uppercase; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 10px; }
        .item { background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 10px; margin-bottom: 8px; border-radius: 2px; }
        .name { color: var(--cyan); font-family: 'Orbitron'; font-size: 13px; cursor: pointer; }
        .status-badge { font-size: 9px; padding: 2px 5px; border-radius: 3px; font-weight: bold; margin-left: 8px; border: 1px solid; }
        .st-local { color: var(--green); border-color: var(--green); background: rgba(0,255,170,0.1); }
        .st-grid { color: #f1c40f; border-color: #f1c40f; background: rgba(241,196,15,0.1); }
        .st-off { color: #555; border-color: #444; }
        .action-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); cursor: pointer; float: right; }
        .map-frame { width: 512px; height: 512px; position: relative; border: 1px solid var(--cyan); background: #000; margin: auto; }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.4; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
    </style>
</head>
<body onload="initApp()">
    <header>
        <div class="logo">NOX//ZETA v1.6.2</div>
        <div style="font-size:11px; color:var(--cyan)">OP: {{ user_name.upper() }} // REGION: <span id="reg-name">---</span></div>
        <a href="/logout" style="color:var(--red); text-decoration:none; font-size:11px;">[ LOGOUT ]</a>
    </header>

    <div class="main-container">
        <div class="column" style="width: 40%; justify-content:center;">
            <div class="map-frame"><div id="map-bg"></div><canvas id="radar-canvas" width="512" height="512"></canvas></div>
        </div>
        <div class="column" style="width: 30%;">
            <div class="col-header">Scanner Local</div>
            <div id="scan-list" class="scroll-area"></div>
        </div>
        <div class="column" style="width: 30%;">
            <div class="col-header" style="color:var(--red)">Watchlist Global</div>
            <div id="watch-list" class="scroll-area"></div>
        </div>
    </div>

    <script>
        async function updateUI() {
            const res = await fetch('/api_data');
            const data = await res.json();
            if (!data.watchlist) return;

            document.getElementById('reg-name').innerText = data.region || "---";
            if(data.coords) document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;

            // Scanner Local
            document.getElementById('scan-list').innerHTML = data.avatars.map(av => `
                <div class="item">
                    <button class="action-btn" onclick="toggleWatch('${av.name}', '${av.uuid}')">+</button>
                    <span class="name">${av.name}</span>
                    <div style="font-size:9px; color:#555; margin-top:4px;">POS: ${Math.round(av.x)}, ${Math.round(av.y)}</div>
                </div>`).join('');

            // Watchlist Persistante
            document.getElementById('watch-list').innerHTML = data.watchlist.map(w => {
                const isLocal = data.avatars.find(a => a.uuid === w.uuid);
                const statusClass = isLocal ? 'st-local' : (w.online_sl ? 'st-grid' : 'st-off');
                const statusText = isLocal ? 'LOCAL' : (w.online_sl ? 'GRID ONLINE' : 'OFFLINE');
                return `
                <div class="item" style="border-left: 3px solid ${isLocal ? 'var(--green)' : 'var(--red)'}">
                    <button class="action-btn" onclick="toggleWatch('${w.name}')" style="border-color:var(--red); color:var(--red)">&times;</button>
                    <span class="name">${w.name}</span>
                    <div style="margin-top:5px;"><span class="status-badge ${statusClass}">${statusText}</span></div>
                </div>`;
            }).join('');

            // Radar
            const ctx = document.getElementById('radar-canvas').getContext('2d');
            ctx.clearRect(0, 0, 512, 512);
            data.avatars.forEach(av => {
                ctx.fillStyle = data.watchlist.some(w => w.uuid === av.uuid) ? "#ff3131" : "#00ffff";
                ctx.beginPath(); ctx.arc(av.x * 2, 512 - (av.y * 2), 6, 0, Math.PI * 2); ctx.fill();
            });
        }

        async function toggleWatch(name, uuid = "") {
            await fetch('/toggle_watch', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({name: name, uuid: uuid})
            });
            updateUI();
        }

        function initApp() { setInterval(updateUI, 2000); updateUI(); }
    </script>
</body>
</html>
"""

# --- ROUTES API ---

@app.route('/')
def index():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(INTERFACE_HTML, user_name=session['user'])

@app.route('/update_radar', methods=['POST'])
def update_radar():
    data = request.get_json(silent=True) or {}
    user = data.get("operator_id", "admin").lower()
    if user in db:
        db[user].update({
            'avatars': data.get('avatars', []),
            'region': data.get('region', 'Unknown'),
            'coords': data.get('grid_coords', {"x":128, "y":128})
        })
        return "OK", 200
    return "User Error", 404

@app.route('/update_global_status', methods=['POST'])
def update_global():
    data = request.get_json(silent=True) or {}
    uuid, status = data.get('uuid'), data.get('status') == "1"
    for u in db:
        for agent in db[u]['watchlist']:
            if agent.get('uuid') == uuid: agent['online_sl'] = status
    return "OK", 200

@app.route('/get_watchlist_uuids')
def get_watchlist_uuids():
    op = request.args.get('operator_id', 'admin').lower()
    return jsonify([a['uuid'] for a in db[op]['watchlist'] if a.get('uuid')])

@app.route('/api_data')
def api_data():
    return jsonify(db.get(session.get('user', 'admin'), {}))

@app.route('/toggle_watch', methods=['POST'])
def toggle_watch():
    u = session.get('user', 'admin')
    data = request.get_json()
    name, uuid = data.get('name'), data.get('uuid')
    wl = db[u]['watchlist']
    exists = next((i for i in wl if i["name"] == name), None)
    if exists: wl.remove(exists)
    else: wl.append({"name": name, "uuid": uuid, "online_sl": True})
    return jsonify({"status": "ok"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('u', '').lower()
        if u in db: session['user'] = u; return redirect(url_for('index'))
    return 'LOGIN: <form method="POST"><input name="u"><button>IN</button></form>'

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
