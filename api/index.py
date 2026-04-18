from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = "NOX_ZETA_MULTIUSER_2026"

# Simulation de base de données multi-utilisateurs
# Structure : {"username": {"pw": "...", "region": "...", "coords": {}, "avatars": [], "history": {}}}
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "OFFLINE", 
        "coords": {"x":0, "y":0}, 
        "avatars": [],
        "history": {}
    }
}

# --- INTERFACE HTML (Identique à la précédente avec support multi-user) ---
INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --red: #ff3131; --bg: #020205; --panel: rgba(10, 10, 20, 0.95); --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { height: 55px; border-bottom: 1px solid var(--border); background: var(--panel); display: flex; justify-content: space-between; align-items: center; padding: 0 20px; flex-shrink: 0; z-index: 10; }
        .logo { font-family: 'Orbitron'; font-weight: 700; color: var(--cyan); letter-spacing: 2px; }
        .main-container { display: flex; flex: 1; overflow: hidden; width: 100%; }
        .column { height: 100%; overflow: hidden; display: flex; flex-direction: column; background: var(--panel); min-width: 200px; }
        .resizer { width: 4px; cursor: col-resize; background: var(--border); transition: 0.2s; flex-shrink: 0; }
        .resizer:hover { background: var(--cyan); box-shadow: 0 0 10px var(--cyan); }
        .col-header { padding: 15px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 11px; color: var(--magenta); background: rgba(0,0,0,0.4); text-transform: uppercase; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 12px; scrollbar-width: thin; }
        .item { background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .item.watched { border-left: 3px solid var(--red); background: rgba(255, 49, 49, 0.08); }
        .name { color: var(--cyan); font-weight: 600; font-size: 15px; text-decoration: none; }
        .item.watched .name { color: var(--red); }
        .details { font-size: 10px; color: #777; font-family: monospace; margin-top: 4px; }
        .log-box { font-size: 10px; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 5px; }
        .log-in { color: #00ffaa; } .log-out { color: #ff5555; }
        .action-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); font-family: 'Orbitron'; font-size: 14px; width: 28px; height: 28px; cursor: pointer; }
        .map-wrapper { width: 100%; display: flex; justify-content: center; align-items: center; padding: 20px; box-sizing: border-box; }
        .map-frame { position: relative; width: 512px; height: 512px; border: 1px solid var(--cyan); background: #000; }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.45; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
    </style>
</head>
<body onload="initApp()">
    <header>
        <div class="logo">NOX//ZETA <span style="font-size:10px; color:#555">USER: {{ session['user'] }}</span></div>
        <div style="font-family:monospace; font-size:12px; color:var(--cyan);">SIM: <span id="reg-name">OFFLINE</span></div>
        <a href="/logout" style="color:var(--red); text-decoration:none; font-family:'Orbitron'; font-size:11px; border:1px solid var(--red); padding:5px 10px;">LOGOUT</a>
    </header>

    <div class="main-container">
        <div class="column" style="width: 45%;">
            <div class="col-header">Tactical_Radar</div>
            <div class="scroll-area map-wrapper">
                <div class="map-frame"><div id="map-bg"></div><canvas id="radar-canvas" width="512" height="512"></canvas></div>
            </div>
        </div>
        <div class="resizer"></div>
        <div class="column" style="width: 25%;">
            <div class="col-header">Live_Scanner [<span id="count">0</span>]</div>
            <div id="scan-list" class="scroll-area"></div>
        </div>
        <div class="resizer"></div>
        <div class="column" style="width: 30%;">
            <div class="col-header" style="color:var(--red)">Watchlist_Logs</div>
            <div id="watch-list" class="scroll-area"></div>
        </div>
    </div>

    <script>
        let watchlist = JSON.parse(localStorage.getItem('nox_watchlist_' + "{{ session['user'] }}")) || [];

        function toggleWatch(name) {
            if (watchlist.includes(name)) watchlist = watchlist.filter(n => n !== name);
            else watchlist.push(name);
            localStorage.setItem('nox_watchlist_' + "{{ session['user'] }}", JSON.stringify(watchlist));
            updateUI();
        }

        async function updateUI() {
            try {
                const res = await fetch('/api_data');
                const data = await res.json();
                document.getElementById('reg-name').innerText = data.region;
                document.getElementById('count').innerText = data.avatars.length;
                if(data.coords) document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;

                document.getElementById('scan-list').innerHTML = data.avatars.map(av => {
                    const isWatched = watchlist.includes(av.name);
                    return `<div class="item ${isWatched ? 'watched' : ''}">
                        <div class="name-box"><span class="name">${av.name}</span><div class="details">POS: ${Math.round(av.x)}, ${Math.round(av.y)}</div></div>
                        <button class="action-btn" onclick="toggleWatch('${av.name}')">${isWatched ? '-' : '+'}</button>
                    </div>`;
                }).join('');

                document.getElementById('watch-list').innerHTML = watchlist.map(name => {
                    const hist = data.history[name] || {in: "---", out: "---"};
                    return `<div class="item watched">
                        <div class="name-box">
                            <a href="https://my.secondlife.com/${name.replace(/ /g, '.')}" target="_blank" class="name">${name}</a>
                            <div class="log-box"><span class="log-in">▲ IN: ${hist.in}</span><br><span class="log-out">▼ OUT: ${hist.out}</span></div>
                        </div>
                        <button class="action-btn" onclick="toggleWatch('${name}')" style="color:var(--red); border-color:var(--red)">✖</button>
                    </div>`;
                }).join('');

                const ctx = document.getElementById('radar-canvas').getContext('2d');
                ctx.clearRect(0, 0, 512, 512);
                data.avatars.forEach(av => {
                    const isWatched = watchlist.includes(av.name);
                    ctx.fillStyle = isWatched ? "#ff3131" : "#00ffff";
                    ctx.beginPath(); ctx.arc(av.x * 2, 512 - (av.y * 2), isWatched ? 8 : 4.5, 0, Math.PI * 2); ctx.fill();
                });
            } catch(e) {}
        }

        function initApp() {
            const resizers = document.querySelectorAll('.resizer');
            resizers.forEach(r => {
                r.addEventListener('mousedown', e => {
                    let prev = r.previousElementSibling, next = r.nextElementSibling, startX = e.pageX, startW = prev.offsetWidth;
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

# --- ROUTES ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        user = data.get("operator_id", "").lower()
        if user in users_db:
            now = datetime.now().strftime("%H:%M:%S")
            new_avs = data.get('avatars', [])
            names = [a['name'] for a in new_avs]
            hist = users_db[user]["history"]
            for n in names:
                if n not in hist or not hist[n].get('active'): hist[n] = {'in': now, 'out': '---', 'active': True}
            for n, s in hist.items():
                if s.get('active') and n not in names: s['out'] = now; s['active'] = False
            users_db[user].update({'region': data.get('region'), 'coords': data.get('grid_coords'), 'avatars': new_avs})
            return "OK", 200
        return "USER_NOT_FOUND", 404

    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(INTERFACE_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        u, p = request.form.get('u').lower(), request.form.get('p')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('index'))
        error = "Identifiants invalides"
    return f"""<body style="background:#020205; color:#0ff; font-family:'Orbitron'; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;"><form method="POST" style="border:1px solid #0ff; padding:40px; background:rgba(0,255,255,0.05); text-align:center;"><h2>NOX_AUTH</h2><p style="color:red; font-size:10px;">{error}</p><input name="u" placeholder="UTILISATEUR" required style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:10px; display:block; width:220px;"><input type="password" name="p" placeholder="MOT DE PASSE" required style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:20px; display:block; width:220px;"><button type="submit" style="background:#0ff; border:none; padding:10px; width:100%; font-weight:bold; cursor:pointer;">CONNEXION</button><br><br><a href="/register" style="color:#555; font-size:10px; text-decoration:none;">CRÉER UN COMPTE</a></form></body>"""

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, p = request.form.get('u').lower(), request.form.get('p')
        if u not in users_db:
            users_db[u] = {"pw": p, "region": "OFFLINE", "coords": {"x":0, "y":0}, "avatars": [], "history": {}}
            return redirect(url_for('login'))
    return """<body style="background:#020205; color:#0ff; font-family:'Orbitron'; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;"><form method="POST" style="border:1px solid #0ff; padding:40px; background:rgba(0,255,255,0.05); text-align:center;"><h2>NOX_REGISTER</h2><input name="u" placeholder="CHOISIR NOM" required style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:10px; display:block; width:220px;"><input type="password" name="p" placeholder="CHOISIR PASS" required style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:20px; display:block; width:220px;"><button type="submit" style="background:#0ff; border:none; padding:10px; width:100%; font-weight:bold; cursor:pointer;">CRÉER COMPTE</button></form></body>"""

@app.route('/api_data')
def api_data():
    return jsonify(users_db.get(session.get('user'), {}))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
