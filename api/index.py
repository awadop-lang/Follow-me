from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "NOX_ZETA_FINAL_2026"

# Base de données (reset au déploiement)
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "INITIALIZING...", 
        "coords": {"x":0, "y":0}, 
        "avatars": []
    }
}

# --- L'INTERFACE CYBERPUNK COMPLÈTE ---
INTERFACE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;600&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --bg: #020205; --panel: rgba(5, 7, 12, 0.95); --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #a5b5b5; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; }
        
        header { border-bottom: 1px solid var(--border); background: var(--panel); padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 0 15px rgba(0,255,255,0.1); }
        .logo { font-family: 'Orbitron'; color: var(--cyan); letter-spacing: 3px; font-weight: 700; }
        
        .main { display: flex; height: calc(100vh - 60px); }
        
        /* Section Carte */
        .map-area { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; background: radial-gradient(circle, #0a0a15 0%, #020205 100%); }
        #map-container { position: relative; width: 512px; height: 512px; border: 1px solid var(--cyan); box-shadow: 0 0 30px rgba(0,255,255,0.05); }
        #map-img { width: 100%; height: 100%; position: absolute; opacity: 0.4; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
        
        /* Sidebar Droite */
        .sidebar { width: 350px; border-left: 1px solid var(--border); background: var(--panel); display: flex; flex-direction: column; }
        .sidebar-header { padding: 15px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 12px; color: var(--magenta); }
        #feed { flex: 1; overflow-y: auto; padding: 10px; }
        
        .av-card { background: rgba(255,255,255,0.02); border: 1px solid var(--border); padding: 12px; margin-bottom: 8px; transition: 0.3s; }
        .av-card:hover { border-color: var(--cyan); background: rgba(0,255,255,0.05); transform: translateX(-5px); }
        .av-name { color: var(--cyan); font-weight: 600; font-size: 14px; }
        .av-pos { font-size: 11px; font-family: monospace; opacity: 0.6; margin-top: 4px; }
        
        .btn-logout { color: var(--magenta); border: 1px solid var(--magenta); padding: 5px 12px; text-decoration: none; font-family: 'Orbitron'; font-size: 10px; transition: 0.3s; }
        .btn-logout:hover { background: var(--magenta); color: white; box-shadow: 0 0 10px var(--magenta); }
    </style>
</head>
<body onload="startUpdates()">
    <header>
        <div class="logo">NOX//CORE <span id="reg-display" style="color:#555; font-weight:300; margin-left:10px;"></span></div>
        <a href="/logout" class="btn-logout">DISCONNECT</a>
    </header>

    <div class="main">
        <div class="map-area">
            <div id="map-container">
                <div id="map-img"></div>
                <canvas id="map-canvas" width="512" height="512"></canvas>
            </div>
            <div style="margin-top:20px; font-family:'Orbitron'; font-size:10px; color:var(--cyan); opacity:0.5;">LIVE_GRID_FEED // STANDBY_MODE</div>
        </div>
        
        <div class="sidebar">
            <div class="sidebar-header">ACTIVE_SIGNALS [<span id="count">0</span>]</div>
            <div id="feed"></div>
        </div>
    </div>

    <script>
        async function update() {
            try {
                const r = await fetch('/api_data');
                const d = await r.json();
                
                // Update Infos
                document.getElementById('reg-display').innerText = "> " + d.region.toUpperCase();
                document.getElementById('count').innerText = d.avatars.length;
                
                // Update Map Background
                if(d.coords) {
                    const mapUrl = `https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg`;
                    document.getElementById('map-img').style.backgroundImage = `url('${mapUrl}')`;
                }

                // Update Feed
                const feed = document.getElementById('feed');
                feed.innerHTML = d.avatars.map(av => `
                    <div class="av-card">
                        <div class="av-name">${av.name}</div>
                        <div class="av-pos">X: ${Math.round(av.x)} | Y: ${Math.round(av.y)}</div>
                    </div>
                `).join('');

                // Draw Radar Dots
                const ctx = document.getElementById('map-canvas').getContext('2d');
                ctx.clearRect(0, 0, 512, 512);
                d.avatars.forEach(av => {
                    ctx.fillStyle = "#00ffff";
                    ctx.shadowBlur = 12;
                    ctx.shadowColor = "#00ffff";
                    ctx.beginPath();
                    // Conversion coords SL (0-256) vers Canvas (0-512)
                    ctx.arc(av.x * 2, 512 - (av.y * 2), 5, 0, Math.PI * 2);
                    ctx.fill();
                });
            } catch(e) { console.error("Sync Error"); }
        }

        function startUpdates() {
            update();
            setInterval(update, 3000);
        }
    </script>
</body>
</html>
"""

# --- ROUTES SERVEUR ---

@app.route('/', methods=['GET', 'POST'])
def main():
    # Traitement POST de Second Life
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        op_id = data.get("operator_id", "").lower()
        if op_id in users_db:
            users_db[op_id].update({
                'region': data.get('region', 'UNK'),
                'coords': data.get('grid_coords', {'x':0, 'y':0}),
                'avatars': data.get('avatars', [])
            })
            return "OK", 200
        return "DENIED", 403

    # Affichage GET pour l'utilisateur
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(INTERFACE_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('u', '').lower()
        p = request.form.get('p', '')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('main'))
    return """
    <body style="background:#020205; color:#0ff; font-family:'Orbitron'; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;">
        <form method="POST" style="border:1px solid #0ff; padding:30px; background:rgba(0,255,255,0.05); text-align:center;">
            <h2 style="letter-spacing:4px;">NOX_AUTH</h2>
            <input name="u" placeholder="ID" style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:10px; display:block; width:200px;">
            <input type="password" name="p" placeholder="KEY" style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:20px; display:block; width:200px;">
            <button type="submit" style="background:#0ff; border:none; padding:10px; width:100%; font-weight:bold; cursor:pointer;">ACCESS</button>
        </form>
    </body>
    """

@app.route('/api_data')
def api_data():
    if 'user' not in session: return jsonify({}), 401
    return jsonify(users_db.get(session.get('user', ''), {}))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
