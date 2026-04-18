from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "NOX_ZETA_ULTIMATE_STABLE_2026"

# Simulation de base de données (Note: se réinitialise à chaque déploiement Vercel)
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "WAITING_FOR_UPLINK...", 
        "coords": {"x":0, "y":0}, 
        "avatars": [],
        "watchlist": ["Linden Lab", "Example Resident"] # Ajoute tes noms à surveiller ici
    }
}

# --- INTERFACE CYBERPUNK COMPLETE AVEC TOUTES LES FONCTIONNALITÉS ---
INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>NOX // ZETA CORE</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --red: #ff3131; --bg: #020205; --panel: rgba(10, 10, 20, 0.9); --border: rgba(0, 255, 255, 0.2); }
        
        body { background: var(--bg); color: #e0e0e0; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; }
        
        /* Header */
        header { height: 60px; border-bottom: 1px solid var(--border); background: var(--panel); display: flex; justify-content: space-between; align-items: center; padding: 0 25px; box-shadow: 0 0 20px rgba(0,255,255,0.1); z-index: 100; position: relative; }
        .logo { font-family: 'Orbitron'; font-weight: 700; color: var(--cyan); letter-spacing: 4px; font-size: 1.2rem; }
        .status-bar { font-size: 12px; color: #555; font-family: 'Orbitron'; }
        .status-online { color: var(--cyan); text-shadow: 0 0 5px var(--cyan); }

        /* Layout */
        .container { display: flex; height: calc(100vh - 60px); }
        
        /* Map Section */
        .map-section { flex: 1; background: radial-gradient(circle, #0d0d1a 0%, #020205 100%); display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; }
        .map-frame { position: relative; width: 512px; height: 512px; border: 2px solid var(--border); box-shadow: 0 0 40px rgba(0,0,0,0.5); }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.5; background-size: cover; background-color: #000; }
        canvas { position: absolute; top: 0; left: 0; z-index: 10; pointer-events: none; }
        
        /* Sidebar Section */
        .sidebar { width: 380px; border-left: 1px solid var(--border); background: var(--panel); display: flex; flex-direction: column; backdrop-filter: blur(10px); }
        .sidebar-title { padding: 20px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 13px; color: var(--magenta); letter-spacing: 2px; display: flex; justify-content: space-between; }
        
        /* Feed / Watchlist */
        #avatar-list { flex: 1; overflow-y: auto; padding: 15px; scrollbar-width: thin; scrollbar-color: var(--cyan) transparent; }
        .card { background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 15px; margin-bottom: 10px; border-radius: 2px; transition: 0.2s; position: relative; overflow: hidden; }
        .card:hover { border-color: var(--cyan); background: rgba(0,255,255,0.05); transform: translateX(-5px); }
        
        /* Watchlist Warning */
        .card.watched { border-left: 4px solid var(--red); background: rgba(255, 49, 49, 0.08); border-color: rgba(255, 49, 49, 0.3); }
        .card.watched .name { color: var(--red) !important; text-shadow: 0 0 10px rgba(255, 49, 49, 0.5); }

        .name { color: var(--cyan); font-weight: 700; font-size: 16px; text-decoration: none; display: block; margin-bottom: 5px; transition: 0.3s; }
        .details { font-family: monospace; font-size: 11px; color: #888; text-transform: uppercase; }
        .profile-btn { margin-top: 10px; display: inline-block; font-size: 10px; color: var(--magenta); text-decoration: none; border: 1px solid var(--magenta); padding: 3px 8px; transition: 0.3s; font-family: 'Orbitron'; }
        .profile-btn:hover { background: var(--magenta); color: white; box-shadow: 0 0 10px var(--magenta); }

        .logout { text-decoration: none; color: #444; font-size: 10px; border: 1px solid #444; padding: 5px 10px; font-family: 'Orbitron'; transition: 0.3s; }
        .logout:hover { color: var(--red); border-color: var(--red); }
    </style>
</head>
<body onload="init()">
    <header>
        <div class="logo">NOX // ZETA <span style="font-size:10px; opacity:0.5;">v2.0.4</span></div>
        <div class="status-bar">SIM: <span id="region-name" class="status-online">CONNECTING...</span></div>
        <a href="/logout" class="logout">TERMINATE_SESSION</a>
    </header>

    <div class="container">
        <div class="map-section">
            <div class="map-frame">
                <div id="map-bg"></div>
                <canvas id="radar-canvas" width="512" height="512"></canvas>
            </div>
            <p style="font-family:'Orbitron'; font-size:9px; color:var(--cyan); margin-top:15px; opacity:0.4;">SATELLITE_UPLINK_ACTIVE // 512m_SCAN_RADIUS</p>
        </div>

        <div class="sidebar">
            <div class="sidebar-title">
                <span>SIGNALS_DETECTED</span>
                <span id="counter" style="color:var(--cyan)">00</span>
            </div>
            <div id="avatar-list"></div>
        </div>
    </div>

    <script>
        async function refresh() {
            try {
                const res = await fetch('/api_data');
                const data = await res.json();
                const watchlist = data.watchlist || [];
                
                // Header & Counter
                document.getElementById('region-name').innerText = data.region.toUpperCase();
                document.getElementById('counter').innerText = data.avatars.length.toString().padStart(2, '0');

                // Map Update
                if(data.coords) {
                    const gridX = data.coords.x;
                    const gridY = data.coords.y;
                    document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${gridX}-${gridY}-objects.jpg')`;
                }

                // Sidebar Feed
                const list = document.getElementById('avatar-list');
                list.innerHTML = data.avatars.map(av => {
                    const isWatched = watchlist.includes(av.name);
                    const slName = av.name.replace(/ /g, '.');
                    const profileUrl = `https://my.secondlife.com/en-US/auth/login?to=https://my.secondlife.com/${slName}`;
                    
                    return `
                        <div class="card ${isWatched ? 'watched' : ''}">
                            <a href="${profileUrl}" target="_blank" class="name">${isWatched ? '⚠️ ' : ''}${av.name.toUpperCase()}</a>
                            <div class="details">Pos: ${Math.round(av.x)} / ${Math.round(av.y)} / 0</div>
                            <a href="${profileUrl}" target="_blank" class="profile-btn">View Profile</a>
                        </div>
                    `;
                }).join('');

                // Canvas Radar
                const canvas = document.getElementById('radar-canvas');
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, 512, 512);

                data.avatars.forEach(av => {
                    const isWatched = watchlist.includes(av.name);
                    ctx.beginPath();
                    ctx.arc(av.x * 2, 512 - (av.y * 2), isWatched ? 8 : 5, 0, Math.PI * 2);
                    ctx.fillStyle = isWatched ? "#ff3131" : "#00ffff";
                    ctx.shadowBlur = isWatched ? 20 : 10;
                    ctx.shadowColor = isWatched ? "#ff3131" : "#00ffff";
                    ctx.fill();
                    
                    if(isWatched) {
                        ctx.strokeStyle = "white";
                        ctx.lineWidth = 2;
                        ctx.stroke();
                    }
                });

            } catch(e) { console.log("Sync lost..."); }
        }

        function init() {
            refresh();
            setInterval(refresh, 3000);
        }
    </script>
</body>
</html>
"""

# --- ROUTES LOGIQUE ---

@app.route('/', methods=['GET', 'POST'])
def index():
    # Reception des données POST de Second Life
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        op_id = data.get("operator_id", "").lower()
        if op_id in users_db:
            users_db[op_id].update({
                'region': data.get('region', 'UNK'),
                'coords': data.get('grid_coords', {'x':0, 'y':0}),
                'avatars': data.get('avatars', [])
            })
            return "SIGNAL_OK", 200
        return "ACCESS_DENIED", 403

    # Affichage de l'interface GET
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
    return """<body style="background:#020205; color:#0ff; font-family:'Orbitron'; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;"><form method="POST" style="border:1px solid #0ff; padding:40px; background:rgba(0,255,255,0.05); text-align:center; box-shadow: 0 0 20px rgba(0,255,255,0.2);"><h2 style="letter-spacing:5px; margin-bottom:30px;">NOX_SYSTEM_AUTH</h2><input name="u" placeholder="OPERATOR_ID" style="background:transparent; border:1px solid #0ff; color:white; padding:12px; margin-bottom:15px; display:block; width:250px; font-family:'Rajdhani';"><input type="password" name="p" placeholder="SECURITY_KEY" style="background:transparent; border:1px solid #0ff; color:white; padding:12px; margin-bottom:25px; display:block; width:250px; font-family:'Rajdhani';"><button type="submit" style="background:#0ff; border:none; padding:12px; width:100%; font-weight:bold; cursor:pointer; font-family:'Orbitron'; letter-spacing:2px;">INITIATE_LINK</button></form></body>"""

@app.route('/api_data')
def api_data():
    if 'user' not in session: return jsonify({}), 401
    return jsonify(users_db.get(session.get('user', ''), {}))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
