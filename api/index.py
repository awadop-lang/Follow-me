from flask import Flask, request, jsonify, render_template_string
import time
import urllib.request

app = Flask(__name__)

# Base de données persistante (durant la session Vercel)
db = {"region": "AWAITING_UPLINK", "coords": {"x": 0, "y": 0}, "avatars": []}
times = {}      # Mémoire des arrivées : {uuid: timestamp}
watchlist = {}  # {uuid: {"online": bool, "start": timestamp}}

@app.route('/api', methods=['GET', 'POST'])
def handle():
    global db, times, watchlist
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True)
            if not data: return "OK", 200
            
            db["region"] = data.get("region", "UNK")
            db["coords"] = data.get("grid_coords", {"x":0, "y":0})
            
            now = time.time()
            incoming_avatars = data.get("avatars", [])
            active_list = []
            
            # 1. Gérer le temps d'activité des avatars LOCAUX
            current_uuids = [av.get("key") for av in incoming_avatars]
            
            # Nettoyer 'times' pour les gens partis
            for uid in list(times.keys()):
                if uid not in current_uuids:
                    del times[uid]

            for av in incoming_avatars:
                uid = av.get("key")
                if uid:
                    if uid not in times:
                        times[uid] = now  # On marque l'heure d'arrivée
                    av["start_time"] = times[uid]
                    active_list.append(av)
            
            db["avatars"] = active_list

            # 2. Gérer le statut de la WATCHLIST (Global)
            for w_uid in list(watchlist.keys()):
                try:
                    # On vérifie sur le web de SL (Léger et sûr)
                    url = f"http://world.secondlife.com/resident/{w_uid}"
                    with urllib.request.urlopen(url, timeout=1) as f:
                        content = f.read().decode('utf-8').lower()
                        is_now_online = "online" in content
                        
                        # Si l'état change vers ONLINE, on démarre le chrono
                        if is_now_online and not watchlist[w_uid]["online"]:
                            watchlist[w_uid]["start"] = now
                        
                        watchlist[w_uid]["online"] = is_now_online
                except: pass

            return "OK", 200
        except: return "ERR", 500
        
    return jsonify({**db, "watchlist": watchlist})

@app.route('/watch', methods=['POST'])
def add_watch():
    data = request.get_json(silent=True)
    uid = data.get("uuid")
    if uid and uid not in watchlist:
        watchlist[uid] = {"online": False, "start": 0}
    return "OK"

@app.route('/')
def home():
    # Ici tu peux remettre ton HTML_CODE de la V6.5, 
    # assure-toi juste de modifier la partie JS de la watchlist (voir ci-dessous)
    return render_template_string(HTML_CODE)
