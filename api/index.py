import os
import time
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "NOX_ZETA_STABLE_2026")

# Base de données en mémoire
db = {
    "admin": {
        "pw": "1234",
        "region": "Initialisation...",
        "coords": {"x": 0, "y": 0},
        "avatars": [],
        "history": {},
        "watchlist": []
    }
}

@app.route('/')
def home():
    if 'user' not in session: return "NOX//ZETA ACTIVE - VEUILLEZ VOUS CONNECTER VIA LE SCRIPT SL"
    return "Connecté en tant que " + session['user']

@app.route('/api_data')
def api_data():
    return jsonify(db.get(session.get('user', 'admin'), {}))

# Route de test pour vérifier que Render fonctionne
@app.route('/ping')
def ping():
    return jsonify({"status": "online", "time": time.time()})

if __name__ == "__main__":
    # Render utilise la variable d'environnement PORT
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
