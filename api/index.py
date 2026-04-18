from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import datetime
import pytz # Librairie pour la gestion des fuseaux horaires

app = Flask(__name__)
app.secret_key = "NOX_ZETA_TIMEZONE_V8"

# Base de données multi-utilisateurs
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "OFFLINE", 
        "coords": {"x":0, "y":0}, 
        "avatars": [],
        "history": {},
        "watchlist": [],
        "tz": "UTC" # Timezone par défaut
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

        .time-selector { background: transparent; border: 1px solid var(--border); color: var(--cyan); font-family: 'Rajdhani'; font-size: 12px; padding: 5px; cursor: pointer; border-radius: 3px; }
        .time-selector option { background: #020205; color: white; }

        .main-container { display: flex; flex: 1; overflow: hidden; width: 100%; }
        .column { height: 100%; overflow: hidden; display: flex; flex-direction: column; background: var(--panel); min-width: 200px; }
        .resizer { width: 4px; cursor: col-resize; background: var(--border); transition: 0.2s; flex-shrink: 0; }
        .resizer:hover { background: var(--cyan); }

        .col-header { padding: 15px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 11px; color: var(--magenta); background: rgba(0,0,0,0.5); text-transform: uppercase; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 12px; scrollbar-width: thin; }

        .item { background: rgba(255,255,255,0.02); border: 1px solid var(--border); padding: 15px; margin-bottom: 12px; position: relative; }
        .item.watched { border-left: 4px solid var(--red); background: rgba(255, 49, 49, 0.05); }
        .name-row { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
        .name { color: var(--cyan); font-weight: 700; font-size: 16px; text-decoration: none; font-family: 'Orbitron'; }
        .item.watched .name { color: var(--red); }
        .profile-link { color: #555; text-decoration: none; font-size: 12px; margin-left: 8px; transition: 0.2s; }
        .profile-link:hover { color: var(--cyan); }

        .log-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 5px; }
        .time-badge { background: rgba(0,0,0,0.5); padding: 6px; border-radius: 3px; border: 1px solid rgba(255,255,255,0.1); }
        .time-label { font-size: 9px; text-transform: uppercase; color: #888; display: block; margin-bottom: 2px; }
        .time-value { font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; }
        .val-in { color: var(--green); } .val-out { color: var(--red); }

        .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 5px; }
        .online { background: var(--green); box-shadow: 0 0 8px var(--green); }
        .offline { background: #444; }

        .action-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); font-family: 'Orbitron'; font-size: 14px; width: 30px; height: 30px; cursor: pointer; transition: 0.2s; }
        .action-btn:hover { background: var(--cyan); color: #000; }

        .map-frame { position: relative; width: 512px; height: 512px; border: 1px solid var(--cyan); background: #000; }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.4; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
    </style>
</head>
<body onload="initApp()">
    <header>
        <div class="logo">NOX//ZETA SYSTEM</div>
        <div style="display:flex; align-items:center; gap:15px;">
            <select id="tz-select" class="time-selector" onchange="changeTZ()">
                <option value="UTC">UTC (Standard)</option>
                <option value="Europe/Paris">CET (Paris/Brussels)</option>
                <option value="America/Los_Angeles">SLT (Second Life Time)</option>
            </select>
            <div style="font-family:monospace; font-size:12px; color:var(--cyan);">[ {{ session['user'].upper() }} ]</div>
        </div>
        <a href="/logout" style="color:var(--red); text-decoration:none; font-family:'Orbitron'; font-size:11px; border:1px solid var(--red); padding:5px 10px;">LOGOUT</a>
    </header>

    <div class="main-container">
        <div class="column" style="width: 40%;">
            <div class="col-header">Tactical_Radar</div>
            <div class="scroll-area" style="display:flex; justify-content:center; align-items:center;">
                <div class="map-frame"><div id="map-bg"></div><canvas id="radar-canvas" width="512" height="512"></canvas></div>
            </div>
        </div>
        <div class="resizer"></div>
        <div class="column" style="width: 25%;">
            <div class="col-header">Live_Scanner [<span id="count">0</span>]</div>
            <div id="scan-list" class="scroll-area"></div>
        </div>
        <div class="resizer"></div>
        <div class="column" style="width: 35%;">
            <div class="col-header" style="color:var(--red)">Watchlist_Logs</div>
            <div id="watch-list" class="scroll-area"></div>
        </div>
    </div>

    <script>
        async function changeTZ() {
            const tz = document.getElementById('tz-select').value;
            await fetch('/set_tz', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({tz: tz})
            });
            updateUI();
        }

        async function toggleWatch(name) {
            await fetch('/toggle_watch', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name})
            });
            updateUI();
        }

        async function updateUI() {
            try {
                const res = await fetch('/api_data');
                const data = await res.json();
                const watchlist = data.watchlist || [];
                document.getElementById('tz-select').value = data.tz || 'UTC';

                document.getElementById('count').innerText = data.avatars.length;
                if(data.coords) document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;

                document.getElementById('scan-list').innerHTML = data.avatars.map(av => {
                    const isWatched = watchlist.includes(av.name);
                    return `<div class="item ${isWatched ? 'watched' : ''}">
                        <div class="name-box">
                            <span class="name" style="font-size:14px;">${av.name}</span>
                            <a href="https://my.secondlife.com/${av.name.replace(/ /g, '.')}" target="_blank" class="profile-link">🔗</a>
                        </div>
                        <button class="action-btn" onclick="toggleWatch('${av.name}')">${isWatched ? '-' : '+'}</button>
                    </div>`;
                }).join('');

                document.getElementById('watch-list').innerHTML = watchlist.map(name => {
                    const hist = data.history[name] || {in: "--:--", out: "--:--"};
                    const isOnline = data.avatars.find(a => a.name === name);
                    return `<div class="item watched">
                        <div class="name-row">
                            <div><span class="status-dot ${isOnline ? 'online' : 'offline'}"></span><span class="name">${name}</span></div>
                            <button class="action-btn" onclick="toggleWatch('${name}')" style="color:var(--red); border-color:var(--red); width:24px; height:24px; font-size:10px;">✖</button>
                        </div>
                        <div class="log-grid">
                            <div class="time-badge"><span class="time-label">In</span><span class="time-value val-in">${hist.in}</span></div>
                            <div class="time-badge"><span class="time-label">Out</span><span class="time-value val-out">${hist.out}</span></div>
                        </div>
                    </div>`;
                }).join('');

                const ctx = document.getElementById('radar-canvas').getContext('2d');
                ctx.clearRect(0, 0, 512, 512);
                data.avatars.forEach(av => {
                    ctx.fillStyle = watchlist.includes(av.name) ? "#ff3131" : "#00ffff";
                    ctx.beginPath(); ctx.arc(av.x * 2, 512 - (av.y * 2), watchlist.includes(av.name) ? 8 : 4.5, 0, Math.PI * 2); ctx.fill();
                });
            } catch(e) {}
        }

        function initApp() {
            const resizers = document.querySelectorAll('.resizer');
            resizers.forEach(r => {
                r.addEventListener('mousedown', e => {
                    let prev = r.previousElementSibling, startX = e.pageX, startW = prev.offsetWidth;
                    const drag = e => { prev.style.width = (startW + (e.pageX - startX)) + 'px'; };
                    const stop = () => window.removeEventListener('mousemove', drag);
                    window.addEventListener('mousemove', drag); window.addEventListener('mouseup', stop);
                });
            });
            setInterval(updateUI, 3000); updateUI();
        }
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
            tz = pytz.timezone(users_db[user].get('tz', 'UTC'))
            now = datetime.now(tz).strftime("%H:%M:%S")
            new_avs = data.get('avatars', [])
            names = [a['name'] for a in new_avs]
            hist = users_db[user]["history"]
            for n in names:
                if n not in hist or not hist[n].get('active'): hist[n] = {'in': now, 'out': '--:--:--', 'active': True}
            for n, s in hist.items():
                if s.get('active') and n not in names: s['out'] = now; s['active'] = False
            users_db[user].update({'region': data.get('region'), 'coords': data.get('grid_coords'), 'avatars': new_avs})
            return "OK", 200
        return "NOT_FOUND", 404
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(INTERFACE_HTML)

@app.route('/set_tz', methods=['POST'])
def set_tz():
    if 'user' not in session: return "Unauthorized", 401
    users_db[session['user']]['tz'] = request.json.get('tz', 'UTC')
    return jsonify({"status": "ok"})

@app.route('/toggle_watch', methods=['POST'])
def toggle_watch():
    if 'user' not in session: return "Unauthorized", 401
    name = request.json.get('name')
    u = session['user']
    if name in users_db[u]['watchlist']: users_db[u]['watchlist'].remove(name)
    else: users_db[u]['watchlist'].append(name)
    return jsonify({"status": "ok"})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('u', '').lower(), request.form.get('p', '')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('index'))
    return """<body style="background:#020205; color:#0ff; font-family:'Orbitron'; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;"><form method="POST" style="border:1px solid #0ff; padding:40px; background:rgba(0,255,255,0.05); text-align:center;"><h2>NOX_AUTH</h2><input name="u" placeholder="USER" required style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:10px; display:block; width:220px;"><input type="password" name="p" placeholder="PASS" required style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:20px; display:block; width:220px;"><button type="submit" style="background:#0ff; border:none; padding:10px; width:100%; font-weight:bold; cursor:pointer;">LOGIN</button><br><br><a href="/register" style="color:#555; font-size:10px; text-decoration:none;">CREATE ACCOUNT</a></form></body>"""

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, p = request.form.get('u', '').lower(), request.form.get('p', '')
        if u not in users_db:
            users_db[u] = {"pw": p, "region": "OFFLINE", "coords": {"x":0, "y":0}, "avatars": [], "history": {}, "watchlist": [], "tz": "UTC"}
            return redirect(url_for('login'))
    return """<body style="background:#020205; color:#0ff; font-family:'Orbitron'; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;"><form method="POST" style="border:1px solid #0ff; padding:40px; background:rgba(0,255,255,0.05); text-align:center;"><h2>NOX_REGISTER</h2><input name="u" placeholder="NAME" required style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:10px; display:block; width:220px;"><input type="password" name="p" placeholder="PASS" required style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:20px; display:block; width:220px;"><button type="submit" style="background:#0ff; border:none; padding:10px; width:100%; font-weight:bold; cursor:pointer;">REGISTER</button></form></body>"""

@app.route('/api_data')
def api_data():
    return jsonify(users_db.get(session.get('user'), {}))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
