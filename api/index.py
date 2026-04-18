from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_FORCE_REBOOT_2026"

# Simulation de base de données
users_db = {
    "admin": {"pw": "1234", "is_admin": True, "region": "SYSTEM_START", "coords": {"x":0, "y":0}, "avatars": []}
}

# Style Cyberpunk Unifié
STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;400&display=swap" rel="stylesheet">
<style>
    body { background: #020205; color: #00ffff; font-family: 'Rajdhani', sans-serif; margin: 0; text-align: center; }
    .box { border: 1px solid #00ffff; padding: 30px; margin-top: 100px; display: inline-block; background: rgba(0,255,255,0.05); }
    input { background: transparent; border: 1px solid #00ffff; color: #fff; padding: 10px; margin: 10px; font-family: monospace; }
    button { background: #00ffff; border: none; padding: 10px 20px; font-family: 'Orbitron'; cursor: pointer; font-weight: bold; }
    h1 { font-family: 'Orbitron'; letter-spacing: 5px; }
</style>
"""

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    u = users_db[session['user']]
    return f"{STYLE}<h1>SYSTEM_ONLINE</h1><p>OPERATOR: {session['user']}</p><p>REGION: {u['region']}</p><a href='/logout' style='color:magenta'>LOGOUT</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username').lower()
        p = request.form.get('password')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('home'))
        return "ERREUR_ACCES"
    return f"{STYLE}<div class='box'><h1>NOX_LOGIN</h1><form method='POST'><input name='username' placeholder='ID'><br><input type='password' name='password' placeholder='KEY'><br><button type='submit'>ENTER</button></form></div>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api', methods=['GET', 'POST'])
def api():
    if request.method == 'POST':
        data = request.get_json(silent=True)
        if not data: return "NO_DATA", 400
        op_id = data.get("operator_id", "").lower()
        if op_id in users_db:
            users_db[op_id]['region'] = data.get('region', 'UNK')
            users_db[op_id]['coords'] = data.get('grid_coords', {'x':0, 'y':0})
            users_db[op_id]['avatars'] = data.get('avatars', [])
            return "OK"
        return "USER_NOT_FOUND", 404
    
    if 'user' not in session: return jsonify({"error": "unauth"}), 401
    return jsonify(users_db[session['user']])

# Pour Vercel
app.debug = True
