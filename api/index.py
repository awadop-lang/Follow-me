from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time
from datetime import datetime
import urllib.request

app = Flask(__name__)
app.secret_key = "NOX_SUPER_ENCRYPT_99" # Change ceci pour plus de sécurité

# --- BASE DE DONNÉES TEMPORAIRE (Se vide au redémarrage serveur) ---
# Format: { "username": { "pw": "...", "is_admin": bool, "watchlist": {}, "times": {}, "data": {...} } }
users_db = {
    "admin": {
        "pw": "1234", 
        "is_admin": True, 
        "watchlist": {}, 
        "times": {}, 
        "region": "OFFLINE", 
        "coords": {"x":0, "y":0}, 
        "avatars": []
    }
}

# --- STYLE CSS CYBERPUNK (Commun à toutes les pages) ---
COMMON_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400&family=Orbitron:wght@400;700&family=Rajdhani:wght@300;400;600&display=swap" rel="stylesheet">
<style>
    :root { --cyan: #00ffff; --magenta: #ff00ff; --bg: #020205; --panel: rgba(5, 7, 12, 0.98); --border: rgba(0, 255, 255, 0.15); }
    body { 
        background: var(--bg); color: #a5b5b5; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden;
        background-image: linear-gradient(rgba(18,16,16,0) 50%, rgba(0,0,0,0.1) 50%), linear-gradient(90deg, rgba(255,0,0,0.03), rgba(0,255,0,0.01), rgba(0,0,255,0.03));
        background-size: 100% 3px, 3px 100%;
    }
    .btn-cyber { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); font-family: 'Orbitron'; cursor: pointer; transition: 0.3s; padding: 10px; }
    .btn-cyber:hover { background: var(--cyan); color: #000; box-shadow: 0 0 15px var(--cyan); }
    input { background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; padding: 8px; font-family: 'Fira Code'; outline: none; }
    input:focus { border-color: var(--cyan); }
</style>
"""

# --- PAGE DE LOGIN ---
LOGIN_HTML = COMMON_STYLE + """
<div style="display: flex; align-items: center; justify-content: center; height: 100vh;">
    <div style="border: 1px solid var(--cyan); padding: 40px; background: var(--panel); text-align: center; width: 320px;">
        <h2 style="font-family:'Orbitron'; color:var(--cyan); letter-spacing:5px;">NOX_AUTH</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="OPERATOR_ID" style="width:100%; margin-bottom:10px;" required>
            <input type="password" name="password" placeholder="SECURE_KEY" style="width:100%; margin-bottom:20px;" required>
            <input type="hidden" name="action" value="login">
            <button type="submit" class="btn-cyber" style="width:100%;">INITIALIZE_LINK</button>
        </form>
        <div style="margin-top:20px; font-size:10px;">
            <a href="/register" style="color:var(--magenta); text-decoration:none;">CREATE_NEW_OPERATOR</a>
        </div>
        {% if error %}<div style="color:var(--magenta); font-size:11px; margin-top:10px;">[ ACCESS_DENIED ]</div>{% endif %}
    </div>
</div>
"""

# --- PAGE D'ACCUEIL (DASHBOARD V8.1) ---
DASHBOARD_HTML = COMMON_STYLE + """
<body onload="fetchData()">
    <header style="border: 1px solid var(--border); background: var(--panel); padding: 8px 20px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid var(--cyan);">
        <div>
            <span style="font-family: 'Orbitron'; font-size: 16px; font-weight: 700; letter-spacing: 4px; color: var(--cyan);">NOX//CORE</span>
            <span id="region-display" style="margin-left:20px; font-family: 'Rajdhani'; font-weight: 300; letter-spacing: 3px; color: #666;">SCANNING...</span>
        </div>
        <div style="display:flex; align-items:center; gap:20px; font-family:'Orbitron'; font-size:12px;">
            <div id="clock" style="color:var(--cyan);">00:00:00</div>
            {% if is_admin %}<a href="/admin" style="color:var(--magenta); text-decoration:none;">[ ADMIN ]</a>{% endif %}
            <a href="/logout" style="color:#ff4444; text-decoration:none;">[ TERMINATE ]</a>
        </div>
    </header>

    <div style="display: flex; height: calc(100vh - 70px); margin: 10px; border: 1px solid var(--border);">
        <div style="flex: 1; display: flex; flex-direction: column;">
            <div id="map-cont" style="width: 512px; height: 512px; margin: 10px; position: relative; border: 1px solid #1a1a1a;">
                <div id="map-bg" style="width:100%; height:100%; background-size:cover; position:absolute; opacity:0.4;"></div>
                <canvas id="cv" width="512" height="512" style="position:absolute; top:0; left:0;"></canvas>
            </div>
            <div style="flex:1; background:var(--panel); border-top:1px solid var(--border); padding:15px; overflow-y:auto;">
                <h3 style="font-family:'Orbitron'; color:var(--magenta); font-size:12px;">TARGET_PERSISTENCE</h3>
                <table style="width:100%; font-family:'Fira Code'; font-size:11px; text-align:left;">
                    <thead><tr style="color:var(--magenta);"><th>AGENT</th><th>STATUS</th><th>IN</th><th>OUT</th></tr></thead>
                    <tbody id="watch-list-body"></tbody>
                </table>
            </div>
        </div>
        <div id="right-panel" style="width: 350px; background: var(--panel); border-left: 1px solid var(--border); overflow-y:auto; padding:10px;">
             <div id="inspect-box" style="padding:10px; border-bottom:1px solid var(--border); margin-bottom:10px; display:none;">
                <img id="i-img" src="" style="width:60px; float:left; margin-right:10px; border:1px solid var(--cyan);">
                <div style="font-family:'Orbitron'; font-size:14px; color:#fff;" id="i-name">---</div>
                <div style="font-family:'Fira Code'; font-size:10px; color:var(--magenta);" id="i-pos">XY: 0,0</div>
             </div>
             <div id="feed"></div>
        </div>
    </div>

    <script>
        let selectedKey = null;
        async function fetchData() {
            const r = await fetch('/api');
            if (r.status === 401) window.location = '/login';
            const d = await r.json();
            document.getElementById('region-display').innerText = d.region;
            document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
            renderFeed(d.avatars);
            renderWatch(d.watchlist);
            drawMap(d.avatars);
        }

        function renderFeed(avatars) {
            const feed = document.getElementById('feed');
            feed.innerHTML = avatars.map(av => `
                <div onclick="selectAv('${av.key}', '${av.name}', ${av.x}, ${av.y})" style="padding:10px; border:1px solid #222; margin-bottom:5px; cursor:pointer; background:${selectedKey===av.key?'rgba(0,255,255,0.1)':'transparent'}">
                    <div style="font-family:'Orbitron'; font-size:12px; color:var(--cyan);">${av.name}</div>
                    <div style="font-size:9px;">POS: ${Math.round(av.x)}, ${Math.round(av.y)}</div>
                </div>
            `).join('');
        }

        function selectAv(key, name, x, y) {
            selectedKey = key;
            document.getElementById('inspect-box').style.display = 'block';
            document.getElementById('i-name').innerText = name;
            document.getElementById('i-pos').innerText = `XY: ${Math.round(x)}, ${Math.round(y)}`;
            document.getElementById('i-img').src = `https://my-secondlife-p01.s3.amazonaws.com/users/${key.replace(/-/g, '_')}/thumb_sl_image.png`;
        }

        function drawMap(avatars) {
            const ctx = document.getElementById('cv').getContext('2d');
            ctx.clearRect(0,0,512,512);
            avatars.forEach(av => {
                ctx.fillStyle = (selectedKey === av.key) ? "#ff00ff" : "#00ffff";
                ctx.beginPath();
                ctx.arc(av.x*2, 512-(av.y*2), 5, 0, Math.PI*2);
                ctx.fill();
            });
        }

        function renderWatch(w) {
            const b = document.getElementById('watch-list-body');
            b.innerHTML = Object.keys(w).map(id => `<tr><td>${w[id].name}</td><td>${w[id].online?'ON':'OFF'}</td><td>${w[id].arr_raw||'-'}</td><td>${w[id].dep_raw||'-'}</td></tr>`).join('');
        }

        setInterval(fetchData, 3000);
        setInterval(() => { document.getElementById('clock').innerText = new Date().toLocaleTimeString(); }, 1000);
    </script>
</body>
"""

# --- ROUTES FLASK ---

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    user_info = users_db.get(session['user'])
    return render_template_string(DASHBOARD_HTML, is_admin=user_info.get('is_admin', False))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u, p = request.form.get('username').lower(), request.form.get('password')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('home'))
        return render_template_string(LOGIN_HTML, error=True)
    return render_template_string(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u, p = request.form.get('username').lower(), request.form.get('password')
        if u not in users_db:
            users_db[u] = {"pw":p, "is_admin":False, "watchlist":{}, "times":{}, "region":"OFFLINE", "coords":{"x":0,"y":0}, "avatars":[]}
            session['user'] = u
            return redirect(url_for('home'))
    return render_template_string(LOGIN_HTML.replace("NOX_AUTH", "NOX_REGISTER").replace("login", "register"))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'user' not in session or not users_db[session['user']]['is_admin']: return "Forbidden", 403
    users_html = "".join([f"<li>{u}</li>" for u in users_db.keys()])
    return f"<h1>ADMIN</h1><ul>{users_html}</ul><a href='/'>Back</a>"

@app.route('/api', methods=['GET', 'POST'])
def api():
    if request.method == 'POST':
        data = request.get_json(silent=True)
        op_id = data.get("operator_id", "").lower()
        if op_id in users_db:
            u = users_db[op_id]
            u['region'] = data.get('region', 'UNK')
            u['coords'] = data.get('grid_coords', {'x':0, 'y':0})
            u['avatars'] = data.get('avatars', [])
            return "OK", 200
        return "USER_NOT_FOUND", 404
    
    if 'user' not in session: return jsonify({"error":"unauth"}), 401
    return jsonify(users_db[session['user']])

if __name__ == '__main__':
    app.run(debug=True)
