from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

# Stockage minimaliste
db = {"region": "READY", "coords": {"x": 0, "y": 0}, "avatars": []}
times = {}
watchlist = {}

@app.route('/api', methods=['GET', 'POST'])
def handle():
    global db, times
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True)
            if not data: return "Empty", 400
            
            db["region"] = data.get("region", "UNK")
            db["coords"] = data.get("grid_coords", {"x":0, "y":0})
            
            now = time.time()
            active_avs = []
            for av in data.get("avatars", []):
                uid = av.get("key")
                if uid:
                    if uid not in times: times[uid] = now
                    av["start_time"] = times[uid]
                    active_avs.append(av)
            db["avatars"] = active_avs
            return "OK", 200
        except Exception as e:
            return str(e), 500
    return jsonify({**db, "watchlist": watchlist})

@app.route('/watch', methods=['POST'])
def add_watch():
    data = request.get_json(silent=True)
    uid = data.get("uuid")
    if uid: watchlist[uid] = {"online": False, "start": time.time()}
    return "OK"

@app.route('/')
def home():
    return "<h1>RADAR_SERVER_ACTIVE</h1><p>V6.3.1 - Stable</p>"
