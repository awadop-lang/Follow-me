from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_ZETA_PERSISTENT_V15"

# Base de données (En production, ceci devrait être un vrai fichier ou une DB)
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "OFFLINE", 
        "coords": {"x":0, "y":0}, 
        "avatars": [],    # Ce que le scanner voit actuellement
        "history": {},    # Logs IN/OUT
        "watchlist": [],  # Liste persistante : [{"name": "Nom", "uuid": "id"}, ...]
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
        :root { --cyan: #00ffff; --magenta: #ff00ff; --red: #ff3131; --green: #00ffaa; --bg: #020205; --panel: rgba(12, 12, 25, 0.98); --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { height: 60px; border-bottom: 1px solid var(--border); background: var(--panel); display: flex; justify-content: space-between; align-items: center; padding: 0 20px; flex-shrink: 0; }
        .logo { font-family: 'Orbitron'; font-weight: 700; color: var(--cyan); letter-spacing: 2px; }
        .main-container { display: flex; flex: 1; overflow: hidden; }
        .column { height: 100%; display: flex; flex-direction: column; background: var(--panel); border-right: 1px solid var(--border); }
        .col-header { padding: 15px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 11px; color: var(--magenta); text-transform: uppercase; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 12px; }
        
        .item { background: rgba(255,255,255,0.02); border: 1px solid var(--border); padding: 12px; margin-bottom: 10px; transition: 0.3s; }
        .item.active-target { border: 1px solid var(--cyan); background: rgba(0,255,255,0.05); }
        .name { color: var(--cyan); font-weight: 700; font-size: 14px; font-family: 'Orbitron'; cursor: pointer; text-decoration: none; }
        .pos-label { font-family: 'JetBrains Mono'; font-size: 10px; color: #666; margin-top: 4px; }
        
        .status-badge { font-size: 9px; padding: 2px 6px; border-radius: 3px; margin-left: 5px; border: 1px solid; font-weight: bold; }
        .st-local { color: var(--green); border-color: var(--green); background: rgba(0,255,170,0.1); }
        .st-off { color: #ff3131; border-color: #ff3131; background: rgba(255,49,49,0.1); }

        .log-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin-top: 10px; }
        .time-badge { background: #000; padding: 5px; border-radius: 3px; border: 1px solid #222; }
        .time-label { font-size: 8px; color: #555; display: block; text-transform: uppercase; }
        .time-value { font-family: 'JetBrains Mono'; font-size: 11px; color: #aaa; }
        
        .action-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); cursor: pointer; width: 30px; height: 30px; font-family: 'Orbitron'; }
        .map-frame { width: 512px; height: 512px; position: relative; border: 1px solid var(--cyan); background: #000; }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.4; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
    </style>
</head>
<body onload="initApp()">
    <header>
        <div class="logo">NOX//ZETA v1.5 - PERSISTENT</div>
        <div style="font-family:'JetBrains Mono'; color:var(--cyan); font-size:12px;">OPERATOR: {{ user_name.upper() }}</div>
        <a href="/logout" style="color:var(--red); text-decoration:none; font-family:'Orbitron'; font-size:11px;">LOGOUT</a>
    </header>

    <div class="main-container">
        <div class="column" style="width: 40%; align-items:center; justify-content:center;">
            <div class="map-frame"><div id="map-bg"></div><canvas id="radar-canvas" width="512" height="512"></canvas></div>
        </div>
        <div class="column" style="width: 30%;">
            <div class="col-header">Scanner Local [<span id="count">0</span>]</div>
            <div id="scan-list" class="scroll-area"></div>
        </div>
        <div class="column" style="width: 30%;">
            <div class="col-header" style="color:var(--red)">Watchlist Persistante</div>
            <div id="watch-list" class="scroll-area"></div>
        </div>
    </div>

    <script>
        let selectedAgent = null;

        function formatTime(ts) {
            if (!ts || ts === "---") return "---";
            return new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(new Date(ts * 1000));
        }

        async function updateUI() {
            const res = await fetch('/api_data');
            const data = await res.json();
            const watchlist = data.watchlist || [];
            const avatars = data.avatars || [];

            document.getElementById('count').innerText = avatars.length;
            if(data.coords) document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;

            // Rendu SCANNER (uniquement ceux présents)
            document.getElementById('scan-list').innerHTML = avatars.map(av => `
                <div class="item ${selectedAgent === av.name ? 'active-target' : ''}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="name" onclick="selectedAgent='${av.name}'">${av.name}</span>
                        <button class="action-btn" onclick="toggleWatch('${av.name}', '${av.uuid}')">
                            ${watchlist.some(w => w.name === av.name) ? '✖' : '+'}
                        </button>
                    </div>
                    <div class="pos-label">COORD: ${Math.round(av.x)}, ${Math.round(av.y)} <span class="status-badge st-local">LOCAL</span></div>
                </div>`).join('');

            // Rendu WATCHLIST (Toujours affichée, même si OFFLINE)
            document.getElementById('watch-list').innerHTML = watchlist.map(w => {
                const isLocal = avatars.find(a => a.name === w.name);
                const hist = data.history[w.name] || {in: "---", out: "---"};
                
                return `
                <div class="item ${selectedAgent === w.name ? 'active-target' : ''}" style="border-left: 4px solid var(--red)">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span>
                            <span class="name" onclick="selectedAgent='${w.name}'">${w.name}</span>
                            ${isLocal ? '<span class="status-badge st-local">ON</span>' : '<span class="status-badge st-off">OFF</span>'}
                        </span>
                        <button onclick="toggleWatch('${w.name}')" style="color:var(--red); background:none; border:none; cursor:pointer; font-size:18px;">&times;</button>
                    </div>
                    <div class="log-grid">
                        <div class="time-badge"><span class="time-label">Entrée</span><span class="time-value">${formatTime(hist.in)}</span></div>
                        <div class="time-badge"><span class="time-label">Sortie</span><span class="time-value">${formatTime(hist.out)}</span></div>
                    </div>
                </div>`;
            }).join('');

            // Radar Canvas
            const ctx = document.getElementById('radar-canvas').getContext('2d');
            ctx.clearRect(0, 0, 512, 512);
            avatars.forEach(av => {
                const posX = av.x * 2; const posY = 512 - (av.y * 2);
                if (selectedAgent === av.name) {
                    ctx.strokeStyle = "#00ffff"; ctx.lineWidth = 2; ctx.beginPath();
                    ctx.arc(posX, posY, 12 + Math.sin(Date.now()/200)*4, 0, Math.PI*2); ctx.stroke();
                }
                ctx.fillStyle = watchlist.some(w => w.name === av.name) ? "#ff3131" : "#00ffff";
                ctx.beginPath(); ctx.arc(posX, posY, 6, 0, Math.PI * 2); ctx.fill();
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

        function initApp() { setInterval(updateUI, 1000); updateUI(); }
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
            
            # Gestion de l'historique IN/OUT
            hist = users_db[user].setdefault("history", {})
            for av in new_avs:
                n = av['name']
                if n not in hist or not hist[n].get('active'):
                    hist[n] = {'in': now_ts, 'out': "---", 'active': True}
            
            for n, s in list(hist.items()):
                if s.get('active') and n not in names:
                    s['out'] = now_ts
                    s['active'] = False
            
            users_db[user].update({
                'region': data.get('region'),
                'coords': data.get('grid_coords'),
                'avatars': new_avs
            })
            return "OK", 200
    
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(INTERFACE_HTML, user_name=session['user'])

@app.route('/toggle_watch', methods=['POST'])
def toggle_watch():
    if 'user' not in session: return "Auth Error", 401
    data = request.json
    name = data.get('name')
    uuid = data.get('uuid')
    u = session['user']
    
    # On cherche si l'agent est déjà dans la watchlist persistante
    existing = next((w for w in users_db[u]['watchlist'] if w['name'] == name), None)
    
    if existing:
        users_db[u]['watchlist'].remove(existing)
    else:
        users_db[u]['watchlist'].append({'name': name, 'uuid': uuid})
    
    return jsonify({"status": "ok"})

@app.route('/api_data')
def api_data():
    if 'user' not in session: return jsonify({})
    return jsonify(users_db.get(session['user'], {}))

# ... (Routes login/register/logout identiques) ...
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('u', '').lower(), request.form.get('p', '')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('index'))
    return """<body style="background:#020205; color:#0ff; font-family:'Orbitron'; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;"><form method="POST" style="border:1px solid #0ff; padding:40px; background:rgba(0,255,255,0.05); text-align:center;"><h2>NOX_AUTH</h2><input name="u" placeholder="USER" required style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:10px; display:block; width:220px;"><input type="password" name="p" placeholder="PASS" required style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:20px; display:block; width:220px;"><button type="submit" style="background:#0ff; border:none; padding:10px; width:100%; font-weight:bold; cursor:pointer;">LOGIN</button></form></body>"""

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('login'))
