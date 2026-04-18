from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_PROTOCOL_DEEP_BLUE"

# Base de données (Se réinitialise au déploiement)
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "WAITING_DATA", 
        "coords": {"x":0, "y":0}, 
        "avatars": []
    }
}

# --- INTERFACE GRAPHIQUE ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;600&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --bg: #020205; --panel: rgba(5, 7, 12, 0.95); --border: rgba(0, 255, 255, 0.15); }
        body { background: var(--bg); color: #a5b5b5; font-family: 'Rajdhani', sans-serif; margin: 0; overflow: hidden; }
        header { border-bottom: 1px solid var(--border); background: var(--panel); padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; }
        .main { display: flex; height: calc(100vh - 60px); }
        .map-section { flex: 1; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        #map-cont { position: relative; width: 512px; height: 512px; background: #000; border: 1px solid var(--cyan); box-shadow: 0 0 20px rgba(0,255,255,0.1); }
        #map-img { width: 100%; height: 100%; background-size: cover; opacity: 0.4; position: absolute; }
        canvas { position: absolute; top: 0; left: 0; z-index: 10; }
        .sidebar { width: 300px; border-left: 1px solid var(--border); background: var(--panel); padding: 15px; overflow-y: auto; }
        .av-card { border: 1px solid var(--border); padding: 10px; margin-bottom: 8px; cursor: pointer; transition: 0.2s; }
        .av-card:hover { border-color: var(--cyan); background: rgba(0,255,255,0.05); }
        .btn-logout { color: var(--magenta); text-decoration: none; font-family: 'Orbitron'; font-size: 10px; border: 1px solid var(--magenta); padding: 5px 10px; }
    </style>
</head>
<body onload="refresh()">
    <header>
        <div style="font-family:'Orbitron'; color:var(--cyan); letter-spacing:2px;">NOX//CORE > <span id="reg-name" style="color:#fff;">...</span></div>
        <a href="/logout" class="btn-logout">TERMINATE_SESSION</a>
    </header>
    <div class="main">
        <div class="map-section">
            <div id="map-cont">
                <div id="map-img"></div>
                <canvas id="cv" width="512" height="512"></canvas>
            </div>
        </div>
        <div class="sidebar">
            <h3 style="font-family:'Orbitron'; font-size:12px; color:var(--magenta);">ACTIVE_SIGNALS</h3>
            <div id="feed"></div>
        </div>
    </div>
    <script>
        async function refresh() {
            try {
                const r = await fetch('/api');
                const d = await r.json();
                document.getElementById('reg-name').innerText = d.region;
                document.getElementById('map-img').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
                
                const feed = document.getElementById('feed');
                feed.innerHTML = d.avatars.map(av => `
                    <div class="av-card">
                        <div style="color:var(--cyan); font-weight:600;">${av.name}</div>
                        <div style="font-size:10px; opacity:0.7;">POS: ${Math.round(av.x)}, ${Math.round(av.y)}</div>
                    </div>
                `).join('');

                const ctx = document.getElementById('cv').getContext('2d');
                ctx.clearRect(0,0,512,512);
                d.avatars.forEach(av => {
                    ctx.fillStyle = "#00ffff";
                    ctx.shadowBlur = 10; ctx.shadowColor = "#00ffff";
                    ctx.beginPath(); ctx.arc(av.x*2, 512-(av.y*2), 5, 0, Math.PI*2); ctx.fill();
                });
            } catch(e) {}
        }
        setInterval(refresh, 3000);
    </script>
</body>
</html>
"""

# --- ROUTES ---

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(DASHBOARD_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').lower()
        p = request.form.get('password', '')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('home'))
        return "DENIED"
    return render_template_string('<body style="background:#020205;color:#0ff;display:flex;justify-content:center;align-items:center;height:100vh;font-family:Orbitron;"><form method="POST" style="border:1px solid #0ff;padding:20px;"><h2>AUTH_REQUIRED</h2><input name="username" placeholder="ID"><br><br><input type="password" name="password" placeholder="KEY"><br><br><button type="submit" style="width:100%">CONNECT</button></form></body>')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api', methods=['GET', 'POST'])
def api():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        op_id = data.get("operator_id", "").lower()
        if op_id in users_db:
            users_db[op_id].update({
                'region': data.get('region', 'UNK'),
                'coords': data.get('grid_coords', {'x':0, 'y':0}),
                'avatars': data.get('avatars', [])
            })
            return "OK"
        return "NOT_FOUND", 404
    if 'user' not in session: return jsonify({"error": "unauth"}), 401
    return jsonify(users_db.get(session.get('user', ''), {}))

app.debug = True
