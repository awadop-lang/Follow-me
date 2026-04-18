from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time
import urllib.request

app = Flask(__name__)
app.secret_key = "NOX_SECURE_TOKEN_2026" # Change-le pour tes sessions

# --- BASE DE DONNÉES EN MÉMOIRE ---
# Note: Sur Vercel (Gratuit), cette variable se vide si personne ne visite le site pendant 30min.
users_db = {
    "admin": {
        "pw": "1234", 
        "is_admin": True, 
        "watchlist": {}, 
        "times": {}, 
        "region": "SYSTEM_BOOT", 
        "coords": {"x":0, "y":0}, 
        "avatars": []
    }
}

# --- TEMPLATES HTML (Fusionnés et optimisés) ---

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400&family=Orbitron:wght@400;700&family=Rajdhani:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --bg: #020205; --panel: rgba(5, 7, 12, 0.98); --border: rgba(0, 255, 255, 0.15); }
        body { 
            background: var(--bg); color: #a5b5b5; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden;
            background-image: linear-gradient(rgba(18,16,16,0) 50%, rgba(0,0,0,0.1) 50%), linear-gradient(90deg, rgba(255,0,0,0.03), rgba(0,255,0,0.01), rgba(0,0,255,0.03));
            background-size: 100% 3px, 3px 100%;
        }
        .btn-cyber { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); font-family: 'Orbitron'; cursor: pointer; transition: 0.3s; padding: 10px; text-decoration: none; display: inline-block; font-size: 12px; }
        .btn-cyber:hover { background: var(--cyan); color: #000; box-shadow: 0 0 15px var(--cyan); }
        input, select { background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #fff; padding: 8px; font-family: 'Fira Code'; outline: none; }
        .card { background: rgba(255, 255, 255, 0.01); border: 1px solid var(--border); padding: 10px; margin-bottom: 5px; cursor: pointer; }
        .card:hover { border-color: var(--cyan); background: rgba(0,255,255,0.05); }
        .selected { border-left: 3px solid var(--cyan); background: rgba(0,255,255,0.1) !important; }
    </style>
    <title>NOX_TACTICAL_OS</title>
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>
"""

LOGIN_HTML = """
{% extends "base" %}
{% block content %}
<div style="display: flex; align-items: center; justify-content: center; height: 100vh;">
    <div style="border: 1px solid var(--cyan); padding: 40px; background: var(--panel); text-align: center; width: 320px;">
        <h2 style="font-family:'Orbitron'; color:var(--cyan); letter-spacing:5px;">NOX_AUTH</h2>
        <form method="POST">
            <input type="text" name="username" placeholder="OPERATOR_ID" style="width:100%; margin-bottom:10px;" required>
            <input type="password" name="password" placeholder="SECURE_KEY" style="width:100%; margin-bottom:20px;" required>
            <button type="submit" class="btn-cyber" style="width:100%;">INITIALIZE_LINK</button>
        </form>
        <div style="margin-top:20px; font-size:10px;">
            <a href="/register" style="color:var(--magenta); text-decoration:none;">> CREATE_NEW_IDENTITY</a>
        </div>
        {% if error %}<div style="color:var(--magenta); font-size:11px; margin-top:15px;">[ ACCESS_DENIED ]</div>{% endif %}
    </div>
</div>
{% endblock %}
"""

DASHBOARD_HTML = """
{% extends "base" %}
{% block content %}
<header style="border-bottom: 1px solid var(--border); background: var(--panel); padding: 10px 25px; display: flex; justify-content: space-between; align-items: center;">
    <div>
        <span style="font-family: 'Orbitron'; font-size: 18px; font-weight: 700; color: var(--cyan); letter-spacing: 3px;">NOX//OS</span>
        <span id="reg-name" style="margin-left:20px; color:#fff; font-weight:300;">SCANNING...</span>
    </div>
    <div style="display:flex; align-items:center; gap:20px;">
        <div id="clock" style="font-family:'Fira Code'; color:var(--cyan);">00:00:00</div>
        {% if is_admin %}<a href="/admin" class="btn-cyber" style="border-color:var(--magenta); color:var(--magenta);">ADMIN</a>{% endif %}
        <a href="/logout" class="btn-cyber" style="border-color:#ff4444; color:#ff4444;">LOGOUT</a>
    </div>
</header>

<div style="display: flex; height: calc(100vh - 65px);">
    <div style="flex: 1; display: flex; flex-direction: column; border-right: 1px solid var(--border);">
        <div style="position: relative; width: 512px; height: 512px; margin: 15px; background: #000; border: 1px solid #1a1a1a;">
            <div id="map-img" style="width:100%; height:100%; background-size:cover; opacity:0.4; position:absolute;"></div>
            <canvas id="map-canvas" width="512" height="512" style="position:absolute; top:0; left:0; z-index:5;"></canvas>
        </div>
        <div style="flex: 1; padding: 15px; background: rgba(0,0,0,0.3); overflow-y: auto;">
            <h4 style="font-family:'Orbitron'; color:var(--magenta); margin:0 0 10px 0; font-size:12px;">LOGS_PERSISTANCE</h4>
            <table style="width:100%; font-family:'Fira Code'; font-size:11px; text-align:left;">
                <thead style="color:var(--magenta);"><tr><th>AGENT</th><th>STATUS</th><th>ARR</th><th>DEP</th></tr></thead>
                <tbody id="w-list"></tbody>
            </table>
        </div>
    </div>

    <div style="width: 380px; background: var(--panel); display: flex; flex-direction: column;">
        <div id="inspector" style="padding:15px; border-bottom:1px solid var(--border); min-height:100px; display:none;">
            <img id="ins-img" src="" style="width:70px; height:70px; float:left; margin-right:15px; border:1px solid var(--cyan);">
            <div id="ins-name" style="font-family:'Orbitron'; color:#fff; font-size:16px;">---</div>
            <div id="ins-pos" style="font-family:'Fira Code'; color:var(--magenta); font-size:11px; margin-top:5px;">POS: 0, 0</div>
            <button id="ins-btn" class="btn-cyber" style="padding:3px 8px; font-size:9px; margin-top:8px;">PROFILE</button>
        </div>
        <div id="feed" style="flex:1; overflow-y:auto; padding:10px;"></div>
    </div>
</div>

<script>
    let selectedID = null;
    let lastData = null;

    async function update() {
        try {
            const r = await fetch('/api');
            if(r.status === 401) window.location = '/login';
            const d = await r.json();
            lastData = d;
            
            document.getElementById('reg-name').innerText = d.region.toUpperCase();
            document.getElementById('map-img').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
            
            // Render Feed
            const feed = document.getElementById('feed');
            feed.innerHTML = d.avatars.map(av => `
                <div class="card ${selectedID === av.key ? 'selected' : ''}" onclick="inspect('${av.key}', '${av.name}', ${av.x}, ${av.y})">
                    <div style="font-family:'Orbitron'; color:var(--cyan); font-size:13px;">${av.name}</div>
                    <div style="font-size:10px;">COORD: ${Math.round(av.x)}, ${Math.round(av.y)}</div>
                </div>
            `).join('');

            draw();
        } catch(e) {}
    }

    function inspect(key, name, x, y) {
        selectedID = key;
        document.getElementById('inspector').style.display = 'block';
        document.getElementById('ins-name').innerText = name.toUpperCase();
        document.getElementById('ins-pos').innerText = `COORD: ${Math.round(x)} / ${Math.round(y)}`;
        document.getElementById('ins-img').src = `https://my-secondlife-p01.s3.amazonaws.com/users/${key.replace(/-/g, '_')}/thumb_sl_image.png`;
        update();
    }

    function draw() {
        const canvas = document.getElementById('map-canvas');
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0,0,512,512);
        if(!lastData) return;
        lastData.avatars.forEach(av => {
            ctx.fillStyle = (selectedID === av.key) ? "#ff00ff" : "#00ffff";
            ctx.shadowBlur = 10; ctx.shadowColor = ctx.fillStyle;
            ctx.beginPath();
            ctx.arc(av.x * 2, 512 - (av.y * 2), 5, 0, Math.PI*2);
            ctx.fill();
        });
    }

    setInterval(update, 3000);
    setInterval(() => { document.getElementById('clock').innerText = new Date().toLocaleTimeString(); }, 1000);
</script>
{% endblock %}
"""

# --- LOGIQUE FLASK ---

@app.route('/base') # Template parent
def base_tpl(): return render_template_string(BASE_LAYOUT)

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    u = users_db.get(session['user'])
    return render_template_string(DASHBOARD_HTML, is_admin=u.get('is_admin', False))

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
        if u and p and u not in users_db:
            users_db[u] = {"pw":p, "is_admin":False, "watchlist":{}, "times":{}, "region":"OFFLINE", "coords":{"x":0,"y":0}, "avatars":[]}
            session['user'] = u
            return redirect(url_for('home'))
    return render_template_string(LOGIN_HTML.replace("NOX_AUTH", "NOX_REGISTER"))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'user' not in session or not users_db[session['user']]['is_admin']: return "Accès interdit", 403
    users_list = "".join([f"<li style='margin-bottom:10px;'>{u} <a href='/del/{u}' style='color:red;'>[SUPPRIMER]</a></li>" for u in users_db.keys()])
    return f"<body style='background:#000;color:#00ffff;padding:50px;'><h1>ADMIN_CORE</h1><ul>{users_list}</ul><br><a href='/' style='color:#fff;'>RETOUR</a></body>"

@app.route('/del/<name>')
def delete_u(name):
    if session.get('user') == 'admin' and name != 'admin':
        if name in users_db: del users_db[name]
    return redirect(url_for('admin'))

@app.route('/api', methods=['GET', 'POST'])
def api():
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if not data: return "No JSON", 400
        op_id = data.get("operator_id", "").lower()
        if op_id in users_db:
            u = users_db[op_id]
            u['region'] = data.get('region', 'UNK')
            u['coords'] = data.get('grid_coords', {'x':0, 'y':0})
            u['avatars'] = data.get('avatars', [])
            return "OK", 200
        return "USER_NOT_FOUND", 404
    
    # GET : Lecture pour le Dashboard
    if 'user' not in session: return jsonify({"error":"unauth"}), 401
    return jsonify(users_db[session['user']])

# Gestion de l'héritage Jinja pour Vercel
@app.context_processor
def inject_base():
    return {'base': render_template_string(BASE_LAYOUT)}

if __name__ == '__main__':
    app.run(debug=True)
