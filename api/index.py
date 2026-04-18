from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "NOX_STABLE_KEY_2026"

# Simulation de base de données
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "EN_ATTENTE_DE_SIGNAL", 
        "coords": {"x":0, "y":0}, 
        "avatars": []
    }
}

# Interface Radar
DASH_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>NOX CORE</title>
    <style>
        body { background: #050505; color: #0ff; font-family: monospace; text-align: center; }
        .radar { border: 2px solid #0ff; width: 400px; height: 400px; margin: 20px auto; position: relative; background: #000; }
        .dot { position: absolute; width: 8px; height: 8px; background: #f0f; border-radius: 50%; transform: translate(-50%, 50%); }
    </style>
</head>
<body onload="setInterval(update, 3000)">
    <h1>NOX//RADAR_CORE</h1>
    <p>REGION: <span id="reg">---</span></p>
    <div class="radar" id="radar"></div>
    <div id="list"></div>
    <script>
        async function update() {
            const r = await fetch('/api_data');
            const d = await r.json();
            if(d.region) {
                document.getElementById('reg').innerText = d.region;
                document.getElementById('radar').innerHTML = d.avatars.map(av => `<div class="dot" style="left:${(av.x/256)*400}px; top:${400-((av.y/256)*400)}px;"></div>`).join('');
                document.getElementById('list').innerHTML = d.avatars.map(av => `<div>${av.name}</div>`).join('');
            }
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
        return "USER_NOT_FOUND", 404

    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(DASH_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('u', '').lower()
        p = request.form.get('p', '')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('main'))
    return '<body style="background:#000;color:#0ff;"><form method="POST">ID: <input name="u"><br>PW: <input type="password" name="p"><br><button>LOGIN</button></form></body>'

@app.route('/api_data')
def api_data():
    if 'user' not in session: return jsonify({}), 401
    return jsonify(users_db.get(session['user'], {}))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
