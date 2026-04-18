from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time
from datetime import datetime
import urllib.request

app = Flask(__name__)
app.secret_key = "NOX_ULTRA_SECRET_ZONE_X"

# --- STRUCTURE DE DONNÉES ---
# users_db stocke : { "username": {"pw": "...", "is_admin": False, "watchlist": {}, "times": {}, "last_region": "..."} }
users_db = {
    "admin": {"pw": "root", "is_admin": True, "watchlist": {}, "times": {}, "last_region": "SYSTEM_CORE", "last_coords": {"x":0, "y":0}, "avatars": []}
}

# --- TEMPLATES HTML ---

LOGIN_REGISTER_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>NOX_NEXUS_AUTH</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body { background: #020205; color: #00ffff; font-family: 'Orbitron'; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .box { border: 1px solid #00ffff; padding: 30px; background: rgba(0,255,255,0.05); text-align: center; width: 300px; }
        input { background: transparent; border: 1px solid #00ffff; color: #fff; padding: 10px; margin: 10px 0; width: 100%; box-sizing: border-box; outline: none; }
        button { background: #00ffff; border: none; color: #000; padding: 10px; width: 100%; font-family: 'Orbitron'; font-weight: bold; cursor: pointer; margin-top: 10px; }
        .toggle { font-size: 10px; margin-top: 15px; cursor: pointer; color: #ff00ff; text-decoration: underline; }
        .error { color: #ff00ff; font-size: 10px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h2 id="title">ACCESS_GATE</h2>
        <form id="authForm" method="POST">
            <input type="text" name="username" placeholder="OPERATOR_ID" required>
            <input type="password" name="password" placeholder="SECURE_KEY" required>
            <input type="hidden" name="action" id="actionField" value="login">
            <button type="submit" id="btnLabel">INITIALIZE_LINK</button>
        </form>
        <div class="toggle" id="toggleAuth" onclick="toggle()">CREATE_NEW_OPERATOR_IDENTITY</div>
        {% if error %}<div class="error">{{error}}</div>{% endif %}
    </div>
    <script>
        function toggle() {
            const isLogin = document.getElementById('actionField').value === 'login';
            document.getElementById('actionField').value = isLogin ? 'register' : 'login';
            document.getElementById('title').innerText = isLogin ? 'NEW_IDENTITY' : 'ACCESS_GATE';
            document.getElementById('btnLabel').innerText = isLogin ? 'REGISTER_OPERATOR' : 'INITIALIZE_LINK';
            document.getElementById('toggleAuth').innerText = isLogin ? 'BACK_TO_LOGIN' : 'CREATE_NEW_OPERATOR_IDENTITY';
        }
    </script>
</body>
</html>
"""

# --- ROUTES AUTH & ADMIN ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')
        user = request.form.get('username').lower()
        pw = request.form.get('password')

        if action == 'register':
            if user in users_db:
                return render_template_string(LOGIN_REGISTER_HTML, error="ID_ALREADY_EXISTS")
            users_db[user] = {"pw": pw, "is_admin": False, "watchlist": {}, "times": {}, "last_region": "NONE", "last_coords": {"x":0, "y":0}, "avatars": []}
            session['logged_in'] = True; session['user'] = user
            return redirect(url_for('home'))
        
        else: # Login
            if user in users_db and users_db[user]["pw"] == pw:
                session['logged_in'] = True; session['user'] = user
                return redirect(url_for('home'))
            return render_template_string(LOGIN_REGISTER_HTML, error="ACCESS_DENIED")
            
    return render_template_string(LOGIN_REGISTER_HTML)

@app.route('/admin')
def admin_panel():
    if not session.get('logged_in') or not users_db[session['user']]['is_admin']:
        return "ACCESS_FORBIDDEN", 403
    
    user_list = "".join([f"<li>{u} (Admin: {data['is_admin']}) - <a href='/admin/del/{u}' style='color:red;'>DELETE</a></li>" for u, data in users_db.items()])
    return f"""
    <body style="background:#000; color:#00ffff; font-family:monospace; padding:50px;">
        <h1>[ ADMIN_CORE_INTERFACE ]</h1>
        <ul>{user_list}</ul>
        <br><a href="/" style="color:#ff00ff;"><< BACK_TO_OS</a>
    </body>
    """

@app.route('/admin/del/<username>')
def delete_user(username):
    if session.get('logged_in') and users_db[session['user']]['is_admin']:
        if username != "admin": del users_db[username]
    return redirect(url_for('admin_panel'))

# --- LOGIQUE API (SÉPARÉE PAR UTILISATEUR) ---

@app.route('/api', methods=['GET', 'POST'])
def handle():
    now = time.time()
    
    # POST : L'objet SL doit envoyer l'ID de l'utilisateur dans le JSON pour savoir qui mettre à jour
    if request.method == 'POST':
        data = request.get_json(silent=True)
        target_user = data.get("operator_id", "").lower()
        
        if target_user in users_db:
            u_data = users_db[target_user]
            u_data["last_region"] = data.get("region", "UNK")
            u_data["last_coords"] = data.get("grid_coords", {"x":0, "y":0})
            
            incoming = data.get("avatars", [])
            uids_present = [av.get("key") for av in incoming]
            
            # Nettoyage des timers
            for uid in list(u_data["times"].keys()):
                if uid not in uids_present: del u_data["times"][uid]
            
            active_list = []
            for av in incoming:
                uid = av.get("key")
                if uid not in u_data["times"]: u_data["times"][uid] = now
                av["start_time"] = u_data["times"][uid]
                active_list.append(av)
            
            u_data["avatars"] = active_list
            # Logique Watchlist simplifiée ici (même principe que V8.1)
            return "OK", 200
        return "OPERATOR_NOT_FOUND", 404

    # GET : Récupère uniquement les données de l'utilisateur connecté
    if not session.get('logged_in'): return "Unauthorized", 401
    
    user = session['user']
    u_data = users_db[user]
    return jsonify({
        "region": u_data["last_region"],
        "coords": u_data["last_coords"],
        "avatars": u_data["avatars"],
        "watchlist": u_data["watchlist"],
        "is_admin": u_data["is_admin"]
    })

# --- Reste du code (routes /watch, /logout, etc) ---
# Note : Pour que l'objet SL sache à quel utilisateur envoyer les données, 
# il faudra ajouter le nom de l'utilisateur dans la description de l'objet SL
# ou dans le script LSL (ex: operator_id = "admin").
