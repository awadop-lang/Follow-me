from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = "CLE_DE_SECOURS_99"

# Base de données temporaire
users_db = {
    "admin": {"pw": "1234", "region": "INITIALISATION", "coords": {"x":0, "y":0}, "avatars": []}
}

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return f"<h1>ACCES VALIDE</h1><p>Bienvenue {session['user']}</p><a href='/logout'>Sortir</a>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').lower()
        p = request.form.get('password', '')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('home'))
        return "ID_INCORRECT"
    return '<form method="POST">ID: <input name="username"><br>PW: <input type="password" name="password"><br><button>LOGIN</button></form>'

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
        return "USER_NOT_FOUND", 404
    if 'user' not in session: return jsonify({"error": "unauth"}), 401
    return jsonify(users_db.get(session.get('user', ''), {}))

# Indispensable pour Vercel
app.debug = True
