from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_ZETA_HARD_V164"

# Note: Sur Vercel, pour une persistance REELLE après 24h, il faut une DB (Supabase/Redis).
# Mais ce code optimise la survie pendant la session.
db = {
    "admin": {
        "pw": "1234",
        "region": "OFFLINE",
        "coords": {"x": 0, "y": 0},
        "avatars": [],
        "watchlist": [] # Liste d'objets : {"name":str, "uuid":str, "online_sl":bool, "last_ping":float}
    }
}

INTERFACE_HTML = """
<script>
    async function updateUI() {
        const res = await fetch('/api_data');
        const data = await res.json();
        
        // Affichage Map
        if (data.coords && data.coords.x > 0) {
            document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;
        }

        // Watchlist Persistante
        document.getElementById('watch-list').innerHTML = data.watchlist.map(w => {
            const isLocal = data.avatars.find(a => a.uuid === w.uuid);
            
            // LOGIQUE DE PERSISTANCE : On considère Online si le dernier ping date de moins de 2 minutes
            // car le dataserver de SL peut être lent.
            const now = Math.floor(Date.now() / 1000);
            const isOnlineSL = w.online_sl && (now - w.last_ping < 120);
            
            let statusClass = "st-off", statusText = "OFFLINE";
            if (isLocal) { statusClass = "st-local"; statusText = "SUR RADAR"; }
            else if (isOnlineSL) { statusClass = "st-grid"; statusText = "ONLINE (GRID)"; }

            return `
            <div class="item" style="border-left: 3px solid ${isLocal?'#0f0':'#f31'}">
                <button class="action-btn" onclick="toggleWatch('${w.name}')" style="border-color:#f31;color:#f31">&times;</button>
                <span class="name">${w.name}</span>
                <div><span class="status-badge ${statusClass}">${statusText}</span></div>
            </div>`;
        }).join('');
        
        // ... (Reste du JS identique)
    }
</script>
"""

@app.route('/update_global_status', methods=['POST'])
def update_global():
    data = request.get_json(silent=True) or {}
    uuid = data.get('uuid')
    status = (data.get('status') == "1")
    
    for u in db:
        for agent in db[u]['watchlist']:
            if agent['uuid'] == uuid:
                agent['online_sl'] = status
                agent['last_ping'] = time.time() # On enregistre le moment précis du ping
    return "OK", 200

@app.route('/toggle_watch', methods=['POST'])
def toggle_watch():
    u = session.get('user', 'admin')
    data = request.get_json()
    name, uuid = data.get('name'), data.get('uuid')
    wl = db[u]['watchlist']
    
    # Vérification par UUID (plus sûr que le nom)
    exists = next((i for i in wl if i["uuid"] == uuid or i["name"] == name), None)
    
    if exists:
        wl.remove(exists)
    else:
        # Initialisation avec last_ping au moment de l'ajout
        wl.append({
            "name": name, 
            "uuid": uuid, 
            "online_sl": True, 
            "last_ping": time.time()
        })
    return jsonify({"status": "ok"})

# ... (Routes update_radar / api_data / login identiques à v1.6.3)
