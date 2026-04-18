from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "SECRET_NOX_99"

# Base de données temporaire
users_db = {
    "admin": {"pw": "1234", "region": "EN_ATTENTE", "coords": {"x":0, "y":0}, "avatars": []}
}

# Interface HTML simple et robuste
HTML_DASH = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { background: #020205; color: #0ff; font-family: sans-serif; text-align: center; }
        .radar { border: 1px solid #0ff; width: 512px; height: 512px; margin: 20px auto; position: relative; background: #000; }
        .dot { position: absolute; width: 10px; height: 10px; background: #f0f; border-radius: 50%; box-shadow: 0 0 10px #f0f; }
        header { border-bottom: 1px solid #333; padding: 10px; }
    </style>
</head>
<body onload="update()">
    <header> NOX//RADAR - REGION: <span id="reg">...</span> </header>
    <div class="radar" id="radar"></div>
    <div id="list"></div>
    <script>
        async function update() {
            try {
                const r = await fetch('/api_get');
                const d = await r.json();
                document.getElementById('reg').innerText = d.region;
                const radar = document.getElementById('radar');
                radar.innerHTML = d.avatars.map(av => `<div class="dot" style="left:${av.x*2}px; bottom:${av.y*2}px;"></div>`).join('');
                document.getElementById('list').innerHTML = d.avatars.map(av => `<div>${av.name}</div>`).join('');
            } catch(e) {}
        }
        setInterval(update, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(HTML_DASH)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('u', '').lower()
        p = request.form.get('p', '')
        if u in users_db and users_db[u]['pw'] == p:
            session['user'] = u
            return redirect(url_for('home'))
    return '<body style="background:#000;color:#0ff;"><form method="POST">ID: <input name="u"><br>PW: <input type="password" name="p"><br><button>GO</button></form></body>'

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api_get')
def api_get():
    if 'user' not in session: return jsonify({}), 401
    return jsonify(users_db.get(session['user'], {}))

@app.route('/api', methods=['POST'])
@app.route('/api/', methods=['POST'])
def api_post():
    data = request.get_json(silent=True) or {}
    op_id = data.get("operator_id", "").lower()
    if op_id in users_db:
        users_db[op_id].update({
            'region': data.get('region', 'UNK'),
            'coords': data.get('grid_coords', {'x':0, 'y':0}),
            'avatars': data.get('avatars', [])
        })
        return "OK", 200
    return "NOT_FOUND", 404
