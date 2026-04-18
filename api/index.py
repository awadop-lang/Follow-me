from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_ZETA_MAX_COMPLEX_2026"

# Base de données avec horodatage
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "WAITING_FOR_UPLINK...", 
        "coords": {"x":0, "y":0}, 
        "avatars": [],
        "last_update": 0,
        "watchlist": ["Linden Lab"]
    }
}

INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --red: #ff3131; --bg: #020205; --panel: rgba(10, 10, 20, 0.9); --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; }
        
        header { height: 60px; border-bottom: 1px solid var(--border); background: var(--panel); display: flex; justify-content: space-between; align-items: center; padding: 0 25px; box-shadow: 0 0 20px rgba(0,255,255,0.1); z-index: 100; position: relative; }
        .logo { font-family: 'Orbitron'; font-weight: 700; color: var(--cyan); letter-spacing: 4px; }

        .container { display: flex; height: calc(100vh - 60px); }
        
        /* Map Section */
        .map-section { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; background: radial-gradient(circle, #0d0d1a 0%, #020205 100%); }
        .map-frame { position: relative; width: 512px; height: 512px; border: 2px solid var(--border); }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.5; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 10; pointer-events: none; }
        
        /* Sidebar Section */
        .sidebar { width: 400px; border-left: 1px solid var(--border); background: var(--panel); display: flex; flex-direction: column; }
        .sidebar-title { padding: 20px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 13px; color: var(--magenta); display: flex; justify-content: space-between; }
        
        #avatar-list { flex: 1; overflow-y: auto; padding: 15px; }
        
        /* Avatar Card Evolution */
        .card { background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 15px; margin-bottom: 12px; position: relative; transition: 0.3s; }
        .card:hover { border-color: var(--cyan); background: rgba(0,255,255,0.08); transform: scale(1.02); }
        .card.watched { border-left: 5px solid var(--red); background: rgba(255, 49, 49, 0.1); }
        
        .name-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .name { color: var(--cyan); font-weight: 700; font-size: 17px; text-decoration: none; }
        .card.watched .name { color: var(--red); }
        
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; font-family: monospace; font-size: 10px; color: #888; }
        .stat-item { border-left: 1px solid #333; padding-left: 5px; }
        
        .profile-btn { margin-top: 12px; display: block; text-align: center; font-size: 10px; color: var(--cyan); text-decoration: none; border: 1px solid var(--cyan); padding: 5px; font-family: 'Orbitron'; transition: 0.3s; }
        .profile-btn:hover { background: var(--cyan); color: black; }

        .logout { text-decoration: none; color: var(--red); font-size: 10px; border: 1px solid var(--red); padding: 5px 10px; font-family: 'Orbitron'; }
    </style>
</head>
<body onload="init()">
    <header>
        <div class="logo">NOX // ZETA SYSTEM</div>
        <div style="font-family:'Orbitron'; font-size:12px;">SIM: <span id="region-name" style="color:var(--cyan)">SCANNING...</span></div>
        <a href="/logout" class="logout">EXIT</a>
    </header>

    <div class="container">
        <div class="map-section">
            <div class="map-frame">
                <div id="map-bg"></div>
                <canvas id="radar-canvas" width="512" height="512"></canvas>
            </div>
            <div id="tech-data" style="margin-top:15px; font-family:monospace; font-size:10px; color:#444;"></div>
        </div>

        <div class="sidebar">
            <div class="sidebar-title">TARGETS_IN_RANGE <span id="counter" style="color:var(--cyan)">0</span></div>
            <div id="avatar-list"></div>
        </div>
    </div>

    <script>
        async function refresh() {
            try {
                const res = await fetch('/api_data');
                const data = await res.json();
                const watchlist = data.watchlist || [];
                
                document.getElementById('region-name').innerText = data.region.toUpperCase();
                document.getElementById('counter').innerText = data.avatars.length;

                if(data.coords) {
                    document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;
                }

                const list = document.getElementById('avatar-list');
                list.innerHTML = data.avatars.map(av => {
                    const isWatched = watchlist.includes(av.name);
                    const slName = av.name.replace(/ /g, '.');
                    const profileUrl = `https://my.secondlife.com/${slName}`;
                    
                    return `
                        <div class="card ${isWatched ? 'watched' : ''}">
                            <div class="name-row">
                                <a href="${profileUrl}" target="_blank" class="name">${isWatched ? '!! ' : ''}${av.name}</a>
                                <span style="font-size:9px; color:${isWatched ? 'var(--red)' : '#555'}">${isWatched ? 'PRIORITY' : 'SCAN'}</span>
                            </div>
                            <div class="stats-grid">
                                <div class="stat-item">COORD_X: ${Math.round(av.x)}</div>
                                <div class="stat-item">COORD_Y: ${Math.round(av.y)}</div>
                                <div class="stat-item">SIGNAL: ACTIVE</div>
                                <div class="stat-item">TYPE: AVATAR</div>
                            </div>
                            <a href="${profileUrl}" target="_blank" class="profile-btn">OPEN_DATA_PROFILE</a>
                        </div>
                    `;
                }).join('');

                const canvas = document.getElementById('radar-canvas');
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, 512, 512);

                data.avatars.forEach(av => {
                    const isWatched = watchlist.includes(av.name);
                    ctx.beginPath();
                    ctx.arc(av.x * 2, 512 - (av.y * 2), isWatched ? 10 : 5, 0, Math.PI * 2);
                    ctx.fillStyle = isWatched ? "rgba(255, 49, 49, 0.8)" : "rgba(0, 255, 255, 0.8)";
                    ctx.shadowBlur = 15;
                    ctx.shadowColor = ctx.fillStyle;
                    ctx.fill();
                    
                    if(isWatched) {
                        ctx.strokeStyle = "#fff";
                        ctx.setLineDash([2, 2]);
                        ctx.stroke();
                        ctx.setLineDash([]);
                    }
                });

            } catch(e) {}
        }

        function init() { refresh(); setInterval(refresh, 3000); }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        op_id = data.get("operator_id", "").lower()
        if op_id in users_db:
            users_db[op_id].update({
                'region': data.get('region', 'UNK'),
                'coords': data.get('grid_coords', {'x':0, 'y':0}),
                'avatars': data.get('avatars', []),
                'last_update': time.time()
            })
            return "OK", 200
        return "DENIED", 403

    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(INTERFACE_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('u', '').lower()
        p = request.form.get('p', '')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('index'))
    return """<body style="background:#020205; color:#0ff; font-family:'Orbitron'; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;"><form method="POST" style="border:1px solid #0ff; padding:40px; background:rgba(0,255,255,0.05); text-align:center;"><h2>NOX_AUTH</h2><input name="u" placeholder="ID" style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:10px; display:block; width:250px;"><input type="password" name="p" placeholder="KEY" style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:20px; display:block; width:250px;"><button type="submit" style="background:#0ff; border:none; padding:10px; width:100%; cursor:pointer; font-weight:bold;">ACCESS</button></form></body>"""

@app.route('/api_data')
def api_data():
    if 'user' not in session: return jsonify({}), 401
    return jsonify(users_db.get(session.get('user', ''), {}))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
