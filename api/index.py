from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_ZETA_STAY_CONNECTED_V168"

db = {
    "admin": {
        "pw": "1234",
        "region": "Initialisation...",
        "coords": {"x": 0, "y": 0},
        "avatars": [],
        "watchlist": [] # {"name":str, "uuid":str, "online_sl":bool, "last_ping":float}
    }
}

INTERFACE_HTML = """
<script>
    async function updateUI() {
        const res = await fetch('/api_data');
        const data = await res.json();
        
        // ... (Code Map et Radar identique) ...

        document.getElementById('watch-list').innerHTML = data.watchlist.map(w => {
            const isLocal = data.avatars.find(a => a.uuid === w.uuid);
            const now = Math.floor(Date.now() / 1000);
            
            // LOGIQUE PERSISTANTE :
            // Si l'agent était Online, on lui accorde 30s de "grâce" même si le ping échoue
            // Cela couvre le temps de chargement entre deux régions.
            const isOnlineGrid = w.online_sl && (now - w.last_ping < 30);
            
            let stC = "st-off", stT = "OFFLINE";
            if (isLocal) { 
                stC = "st-local"; stT = "LOCAL (PORTÉE)"; 
            } else if (isOnlineGrid) { 
                stC = "st-grid"; stT = "TRANSIT / AUTRE REGION"; 
            }

            return `<div class="item" style="border-left: 4px solid ${isLocal?'#0f0':(isOnlineGrid?'#f1c40f':'#444')}">
                <button class="action-btn" onclick="toggleWatch('${w.name}', '${w.uuid}')">×</button>
                <span class="name">${w.name}</span><br>
                <span class="status-badge ${stC}">${stT}</span>
            </div>`;
        }).join('');
    }
</script>
"""

# Le reste des routes reste identique à la v1.6.7
