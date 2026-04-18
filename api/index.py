from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_ZETA_GLOBAL_V13"

users_db = {
    "admin": {
        "pw": "1234", "region": "OFFLINE", "coords": {"x":0, "y":0}, 
        "avatars": [], "history": {}, "watchlist": [], "tz": "Europe/Paris"
    }
}

INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --red: #ff3131; --green: #00ffaa; --bg: #020205; --panel: rgba(12, 12, 25, 0.98); --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { height: 60px; border-bottom: 1px solid var(--border); background: var(--panel); display: flex; justify-content: space-between; align-items: center; padding: 0 20px; flex-shrink: 0; }
        .logo { font-family: 'Orbitron'; font-weight: 700; color: var(--cyan); letter-spacing: 2px; }
        .time-selector { background: #111; border: 1px solid var(--border); color: var(--cyan); font-family: 'Rajdhani'; padding: 5px; border-radius: 3px; font-size: 11px; }
        .main-container { display: flex; flex: 1; overflow: hidden; }
        .column { height: 100%; display: flex; flex-direction: column; background: var(--panel); border-right: 1px solid var(--border); }
        .col-header { padding: 15px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 11px; color: var(--magenta); text-transform: uppercase; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 12px; }
        
        .item { background: rgba(255,255,255,0.02); border: 1px solid var(--border); padding: 12px; margin-bottom: 10px; }
        .name { color: var(--cyan); font-weight: 700; font-size: 14px; font-family: 'Orbitron'; cursor: pointer; }
        .pos-label { font-family: 'JetBrains Mono'; font-size: 10px; color: #666; }
        
        /* Statuts */
        .status-badge { font-size: 9px; padding: 2px 5px; border-radius: 3px; margin-left: 5px; text-transform: uppercase; border: 1px solid; }
        .st-local { color: var(--green); border-color: var(--green); background: rgba(0,255,170,0.1); }
        .st-global { color: #f1c40f; border-color: #f1c40f; background: rgba(241,196,15,0.1); }
        .st-off { color: #555; border-color: #555; }

        .log-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-top: 8px; }
        .time-badge { background: #000; padding: 5px; border-radius: 3px; border: 1px solid #222; }
        .time-label { font-size: 8px; color: #555; display: block; }
        .time-value { font-family: 'JetBrains Mono'; font-size: 11px; color: #bbb; }
        
        .action-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); cursor: pointer; padding: 2px 8px; font-family: 'Orbitron'; font-size: 12px; }
        .map-frame { width: 512px; height: 512px; position: relative; border: 1px solid var(--cyan); }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.4; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
    </style>
</head>
<body onload="initApp()">
    <header>
        <div class="logo">NOX//ZETA v1.3 - GLOBAL TRACKER</div>
        <select id="tz-select" class="time-selector" onchange="updateUI()"></select>
        <a href="/logout" style="color:var(--red); text-decoration:none; font-family:'Orbitron'; font-size:11px;">LOGOUT</a>
    </header>

    <div class="main-container">
        <div class="column" style="width: 40%; align-items:center; justify-content:center;">
            <div class="map-frame"><div id="map-bg"></div><canvas id="radar-canvas" width="512" height="512"></canvas></div>
        </div>
        <div class="column" style="width: 25%;">
            <div class="col-header">Scanner [<span id="count">0</span>]</div>
            <div id="scan-list" class="scroll-area"></div>
        </div>
        <div class="column" style="width: 35%;">
            <div class="col-header" style="color:var(--red)">Watchlist Global</div>
            <div id="watch-list" class="scroll-area"></div>
        </div>
    </div>

    <script>
        let selectedAgent = null;
        const tzSelect = document.getElementById('tz-select');
        Intl.supportedValuesOf('timeZone').forEach(tz => {
            const opt = document.createElement('option'); opt.value = tz; opt.innerText = tz;
            if(tz === "Europe/Paris") opt.selected = true;
            tzSelect.appendChild(opt);
        });

        function formatTime(ts) {
            if (!ts || ts === "---") return "---";
            return new Intl.DateTimeFormat('fr-FR', {
                timeZone: tzSelect.value, hour: '2-digit', minute: '2-digit', second: '2-digit'
            }).format(new Date(ts * 1000));
        }

        async function updateUI() {
            const res = await fetch('/api_data');
            const data = await res.json();
            const watchlist = data.watchlist || [];
            const avatars = data.avatars || [];

            document.getElementById('count').innerText = avatars.length;
            if(data.coords) document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;

            // Scanner
            document.getElementById('scan-list').innerHTML = avatars.map(av => `
                <div class="item">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="name" onclick="selectedAgent='${av.name}'">${av.name}</span>
                        <button class="action-btn" onclick="toggleWatch('${av.name}')">${watchlist.find(w=>w.name===av.name)?'✖':'+'}</button>
                    </div>
                    <div class="pos-label">POS: ${Math.round(av.x)}, ${Math.round(av.y)} <span class="status-badge st-local">LOCAL</span></div>
                </div>`).join('');

            // Watchlist
            document.getElementById('watch-list').innerHTML = watchlist.map(w => {
                const hist = data.history[w.name] || {in: null, out: null};
                const isLocal = avatars.find(a => a.name === w.name);
                // Si pas local, on pourrait interroger un statut global ici
                const statusHtml = isLocal ? '<span class="status-badge st-local">SUR SITE</span>' : '<span class="status-badge st-off">HORS ZONE / SL</span>';
                
                return `
                <div class="item" style="border-left: 3px solid var(--red)">
                    <div style="display:flex; justify-content:space-between;">
                        <span><span class="name" onclick="selectedAgent='${w.name}'">${w.name}</span> ${statusHtml}</span>
                        <button onclick="toggleWatch('${w.name}')" style="color:var(--red); background:none; border:none; cursor:pointer;">✖</button>
                    </div>
                    <div class="log-grid">
                        <div class="time-badge"><span class="time-label">DERNIÈRE VUE</span><span class="time-value">${formatTime(hist.in)}</span></div>
                        <div class="time-badge"><span class="time-label">DÉCONNEXION</span><span class="time-value">${formatTime(hist.out)}</span></div>
                    </div>
                </div>`;
            }).join('');

            const ctx = document.getElementById('radar-canvas').getContext('2d');
            ctx.clearRect(0, 0, 512, 512);
            avatars.forEach(av => {
                const posX = av.x * 2; const posY = 512 - (av.y * 2);
                if (selectedAgent === av.name) {
                    ctx.strokeStyle = "#00ffff"; ctx.lineWidth = 2; ctx.beginPath();
                    ctx.arc(posX, posY, 12 + Math.sin(Date.now()/200)*4, 0, Math.PI*2); ctx.stroke();
                }
                ctx.fillStyle = watchlist.find(w=>w.name===av.name) ? "#ff3131" : "#00ffff";
                ctx.beginPath(); ctx.arc(posX, posY, 5, 0, Math.PI * 2); ctx.fill();
            });
        }

        async function toggleWatch(name) {
            await fetch('/toggle_watch', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:name}) });
            updateUI();
        }

        function initApp() { setInterval(updateUI, 2000); updateUI(); }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        user = data.get("operator_id", "").lower()
        if user in users_db:
            now_ts = time.time()
            new_avs = data.get('avatars', [])
            names = [a['name'] for a in new_avs]
            hist = users_db[user].setdefault("history", {})
            for n in names:
                if n not in hist or not hist[n].get('active'): hist[n] = {'in': now_ts, 'out': "---", 'active': True}
            for n, s in list(hist.items()):
                if s.get('active') and n not in names: s['out'] = now_ts; s['active'] = False
            users_db[user].update({'region': data.get('region'), 'coords': data.get('grid_coords'), 'avatars': new_avs})
            return "OK", 200
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(INTERFACE_HTML)

@app.route('/toggle_watch', methods=['POST'])
def toggle_watch():
    if 'user' not in session: return "Unauthorized", 401
    name = request.json.get('name')
    u = session['user']
    wl = users_db[u]['watchlist']
    if any(w['name'] == name for w in wl):
        users_db[u]['watchlist'] = [w for w in wl if w['name'] != name]
    else:
        users_db[u]['watchlist'].append({'name': name})
    return jsonify({"status": "ok"})

@app.route('/api_data')
def api_data():
    if 'user' not in session: return jsonify({})
    return jsonify(users_db.get(session['user'], {}))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('u', '').lower(), request.form.get('p', '')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('index'))
    return """<body style="background:#020205; color:#0ff; font-family:'Orbitron'; display:flex; justify-content:center; align-items:center; height:100vh;"><form method="POST" style="border:1px solid #0ff; padding:40px;"><h2>NOX_AUTH</h2><input name="u" placeholder="USER"><br><input type="password" name="p" placeholder="PASS"><br><button type="submit">LOGIN</button></form></body>"""

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))
