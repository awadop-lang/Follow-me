from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_ZETA_PRO_V163"

db = {
    "admin": {
        "pw": "1234",
        "region": "OFFLINE",
        "coords": {"x": 0, "y": 0},
        "avatars": [],
        "watchlist": [], # [{"name":"", "uuid":"", "online_sl": False, "last_seen": 0}]
        "tz": "Europe/Paris"
    }
}

INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --red: #ff3131; --green: #00ffaa; --bg: #020205; --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { height: 60px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; padding: 0 20px; background: rgba(10,10,25,0.9); }
        .logo { font-family: 'Orbitron'; font-weight: 700; color: var(--cyan); letter-spacing: 2px; }
        .main-container { display: flex; flex: 1; overflow: hidden; }
        .column { height: 100%; display: flex; flex-direction: column; border-right: 1px solid var(--border); background: rgba(5,5,15,0.6); }
        .col-header { padding: 15px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 11px; color: var(--magenta); text-transform: uppercase; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 15px; }
        .item { background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 12px; margin-bottom: 10px; border-radius: 2px; }
        .name { color: var(--cyan); font-family: 'Orbitron'; font-size: 14px; cursor: pointer; }
        .status-badge { font-size: 9px; padding: 3px 6px; border-radius: 3px; font-weight: bold; margin-top: 8px; display: inline-block; border: 1px solid; }
        .st-local { color: var(--green); border-color: var(--green); background: rgba(0,255,170,0.1); }
        .st-grid { color: #f1c40f; border-color: #f1c40f; background: rgba(241,196,15,0.1); }
        .st-off { color: #555; border-color: #444; background: rgba(255,255,255,0.05); }
        .action-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); cursor: pointer; padding: 5px 10px; font-family: 'Orbitron'; }
        .map-frame { width: 512px; height: 512px; position: relative; border: 1px solid var(--cyan); background: #000; box-shadow: 0 0 20px rgba(0,255,255,0.1); }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.5; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
        .tz-select { background: #000; color: var(--cyan); border: 1px solid var(--border); font-family: 'Rajdhani'; font-size: 12px; padding: 4px; }
    </style>
</head>
<body onload="initApp()">
    <header>
        <div class="logo">NOX//ZETA v1.6.3</div>
        <div style="display:flex; align-items:center; gap:15px;">
            <select id="tz-select" class="tz-select" onchange="updateUI()"></select>
            <div style="font-family:'JetBrains Mono'; color:var(--cyan); font-size:12px;">OP: {{ user_name.upper() }}</div>
        </div>
        <a href="/logout" style="color:var(--red); text-decoration:none; font-family:'Orbitron'; font-size:11px;">[ LOGOUT ]</a>
    </header>

    <div class="main-container">
        <div class="column" style="width: 40%; align-items:center; justify-content:center; background: #000;">
            <div class="map-frame"><div id="map-bg"></div><canvas id="radar-canvas" width="512" height="512"></canvas></div>
        </div>
        <div class="column" style="width: 30%;">
            <div class="col-header">Tactical Scanner</div>
            <div id="scan-list" class="scroll-area"></div>
        </div>
        <div class="column" style="width: 30%;">
            <div class="col-header" style="color:var(--red)">Watchlist Tracker</div>
            <div id="watch-list" class="scroll-area"></div>
        </div>
    </div>

    <script>
        let selectedAgent = null;

        function initApp() {
            const tzS = document.getElementById('tz-select');
            Intl.supportedValuesOf('timeZone').forEach(tz => {
                const opt = document.createElement('option'); opt.value = tz; opt.innerText = tz;
                if(tz === "Europe/Paris") opt.selected = true;
                tzS.appendChild(opt);
            });
            setInterval(updateUI, 2000); 
            updateUI();
        }

        async function updateUI() {
            const res = await fetch('/api_data');
            const data = await res.json();
            if (!data.watchlist) return;

            // Update Map
            if (data.coords && data.coords.x > 0) {
                document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;
            }

            // Scanner Local
            document.getElementById('scan-list').innerHTML = data.avatars.map(av => `
                <div class="item">
                    <button class="action-btn" onclick="toggleWatch('${av.name}', '${av.uuid}')">+</button>
                    <span class="name" onclick="selectedAgent='${av.name}'">${av.name}</span>
                    <div style="font-size:10px; color:#555; margin-top:5px;">POS: ${Math.round(av.x)}, ${Math.round(av.y)}</div>
                </div>`).join('');

            // Watchlist Global
            document.getElementById('watch-list').innerHTML = data.watchlist.map(w => {
                const isLocal = data.avatars.find(a => a.uuid === w.uuid);
                // Si l'info date de plus de 30 secondes, on considère offline
                const isOnlineSL = w.online_sl && (Date.now()/1000 - w.last_seen < 30);
                
                let statusClass = "st-off", statusText = "OFFLINE";
                if (isLocal) { statusClass = "st-local"; statusText = "SUR RADAR"; }
                else if (isOnlineSL) { statusClass = "st-grid"; statusText = "EN LIGNE (GRID)"; }

                return `
                <div class="item" style="border-left: 3px solid ${isLocal ? 'var(--green)' : 'var(--red)'}">
                    <button class="action-btn" onclick="toggleWatch('${w.name}')" style="border-color:var(--red); color:var(--red)">&times;</button>
                    <span class="name">${w.name}</span>
                    <div><span class="status-badge ${statusClass}">${statusText}</span></div>
                </div>`;
            }).join('');

            // Radar
            const ctx = document.getElementById('radar-canvas').getContext('2d');
            ctx.clearRect(0, 0, 512, 512);
            data.avatars.forEach(av => {
                ctx.fillStyle = data.watchlist.some(w => w.uuid === av.uuid) ? "#ff3131" : "#00ffff";
                ctx.beginPath(); ctx.arc(av.x * 2, 512 - (av.y * 2), 7, 0, Math.PI * 2); ctx.fill();
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
    </script>
</body>
</html>
"""

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
            'coords': data.get('grid_coords', {"x":0, "y":0}),
            'region': data.get('region', 'Unknown')
        })
        return "OK", 200
    return "Err", 404

@app.route('/update_global_status', methods=['POST'])
def update_global():
    data = request.get_json(silent=True) or {}
    uuid, status = data.get('uuid'), data.get('status') == "1"
    for u in db:
        for agent in db[u]['watchlist']:
            if agent.get('uuid') == uuid:
                agent['online_sl'] = status
                agent['last_seen'] = time.time() # Timestamp de sécurité
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
    else: wl.append({"name": name, "uuid": uuid, "online_sl": False, "last_seen": 0})
    return jsonify({"status": "ok"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('u', '').lower()
        if u in db: session['user'] = u; return redirect(url_for('index'))
    return '<body style="background:#000; color:#0ff; display:flex; justify-content:center; align-items:center; height:100vh;"><form method="POST">USER: <input name="u"><button>LOGIN</button></form></body>'

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))
