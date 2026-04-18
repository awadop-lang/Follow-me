from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "NOX_ZETA_ULTIMATE_2026"

# Base de données étendue
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "INITIALIZING...", 
        "coords": {"x":0, "y":0}, 
        "avatars": [],
        "watchlist": ["Linden Lab", "Example Resident"] # Ajoute les noms à surveiller ici
    }
}

INTERFACE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;600&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --red: #ff3333; --bg: #020205; --panel: rgba(5, 7, 12, 0.95); --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #a5b5b5; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; }
        
        header { border-bottom: 1px solid var(--border); background: var(--panel); padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-family: 'Orbitron'; color: var(--cyan); letter-spacing: 3px; }
        
        .main { display: flex; height: calc(100vh - 60px); }
        
        .map-area { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; background: radial-gradient(circle, #0a0a15 0%, #020205 100%); }
        #map-container { position: relative; width: 512px; height: 512px; border: 1px solid var(--cyan); }
        #map-img { width: 100%; height: 100%; position: absolute; opacity: 0.4; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
        
        .sidebar { width: 350px; border-left: 1px solid var(--border); background: var(--panel); display: flex; flex-direction: column; }
        .sidebar-header { padding: 15px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 12px; color: var(--magenta); }
        #feed { flex: 1; overflow-y: auto; padding: 10px; }
        
        /* Style des cartes avatars */
        .av-card { background: rgba(255,255,255,0.02); border: 1px solid var(--border); padding: 12px; margin-bottom: 8px; position: relative; }
        .av-card.watched { border-left: 4px solid var(--red); background: rgba(255, 51, 51, 0.1); }
        .av-name { color: var(--cyan); font-weight: 600; font-size: 15px; text-decoration: none; display: block; }
        .av-card.watched .av-name { color: var(--red); }
        .av-name:hover { text-shadow: 0 0 10px var(--cyan); }
        
        .av-pos { font-size: 11px; font-family: monospace; opacity: 0.6; margin-top: 4px; }
        .profile-link { font-size: 10px; color: var(--magenta); text-decoration: none; text-transform: uppercase; margin-top: 5px; display: inline-block; }
        
        .btn-logout { color: var(--magenta); border: 1px solid var(--magenta); padding: 5px 12px; text-decoration: none; font-family: 'Orbitron'; font-size: 10px; }
    </style>
</head>
<body onload="startUpdates()">
    <header>
        <div class="logo">NOX//ZETA <span id="reg-display" style="color:#555; font-size:12px; margin-left:15px;"></span></div>
        <a href="/logout" class="btn-logout">DISCONNECT</a>
    </header>

    <div class="main">
        <div class="map-area">
            <div id="map-container">
                <div id="map-img"></div>
                <canvas id="map-canvas" width="512" height="512"></canvas>
            </div>
        </div>
        
        <div class="sidebar">
            <div class="sidebar-header">SIGNAL_ANALYSIS // <span id="count">0</span> DETECTED</div>
            <div id="feed"></div>
        </div>
    </div>

    <script>
        async function update() {
            try {
                const r = await fetch('/api_data');
                const d = await r.json();
                const watchlist = d.watchlist || [];
                
                document.getElementById('reg-display').innerText = "> " + d.region.toUpperCase();
                document.getElementById('count').innerText = d.avatars.length;
                
                if(d.coords) {
                    const mapUrl = `https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg`;
                    document.getElementById('map-img').style.backgroundImage = `url('${mapUrl}')`;
                }

                const feed = document.getElementById('feed');
                feed.innerHTML = d.avatars.map(av => {
                    const isWatched = watchlist.includes(av.name);
                    const profileUrl = `https://my.secondlife.com/en-US/auth/login?to=https://my.secondlife.com/${av.name.replace(/ /g, '.')}`;
                    
                    return `
                        <div class="av-card ${isWatched ? 'watched' : ''}">
                            <a href="${profileUrl}" target="_blank" class="av-name">${isWatched ? '⚠️ ' : ''}${av.name}</a>
                            <div class="av-pos">POS: ${Math.round(av.x)}, ${Math.round(av.y)}</div>
                            <a href="${profileUrl}" target="_blank" class="profile-link">View SL Profile</a>
                        </div>
                    `;
                }).join('');

                const ctx = document.getElementById('map-canvas').getContext('2d');
                ctx.clearRect(0, 0, 512, 512);
                d.avatars.forEach(av => {
                    const isWatched = watchlist.includes(av.name);
                    ctx.fillStyle = isWatched ? "#ff3333" : "#00ffff";
                    ctx.shadowBlur = isWatched ? 15 : 8;
                    ctx.shadowColor = ctx.fillStyle;
                    ctx.beginPath();
                    ctx.arc(av.x * 2, 512 - (av.y * 2), isWatched ? 7 : 4, 0, Math.PI * 2);
                    ctx.fill();
                });
            } catch(e) {}
        }

        function startUpdates() {
            update();
            setInterval(update, 3000);
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def main():
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
    return """<body style="background:#020205; color:#0ff; font-family:'Orbitron'; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;"><form method="POST" style="border:1px solid #0ff; padding:30px; background:rgba(0,255,255,0.05); text-align:center;"><h2>NOX_AUTH</h2><input name="u" placeholder="ID" style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:10px; display:block; width:200px;"><input type="password" name="p" placeholder="KEY" style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:20px; display:block; width:200px;"><button type="submit" style="background:#0ff; border:none; padding:10px; width:100%; font-weight:bold; cursor:pointer;">ACCESS</button></form></body>"""

@app.route('/api_data')
def api_data():
    if 'user' not in session: return jsonify({}), 401
    return jsonify(users_db.get(session.get('user', ''), {}))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
