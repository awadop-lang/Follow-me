import os
from flask import Flask, request, jsonify, render_template_string, session, redirect

app = Flask(__name__)
app.secret_key = "NOX_ZETA_STABLE_99"

# Base de données simplifiée
db = {"admin": {"pw": "1234", "reg": "---", "avs": [], "wl": []}}

@app.route('/')
def home():
    if 'u' not in session: return redirect('/login')
    return render_template_string("<h1>NOX//ZETA ACTIVE</h1><p>Region: {{reg}}</p>", reg=db["admin"]["reg"])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('u') == 'admin' and request.form.get('p') == '1234':
            session['u'] = 'admin'
            return redirect('/')
    return '<form method="POST">User: <input name="u"> Pass: <input name="p" type="password"><button>GO</button></form>'

@app.route('/update_radar', methods=['POST'])
def update_radar():
    data = request.get_json(silent=True) or {}
    db["admin"]["reg"] = data.get('reg', 'Unknown')
    db["admin"]["avs"] = data.get('avs', [])
    return "OK"

@app.route('/api_data')
def api_data():
    return jsonify(db["admin"])

if __name__ == "__main__":
    # Render impose l'écoute sur 0.0.0.0
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
