from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

# Base de données ultra-stable
db = {
    "region": "Initialisation...",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
# Dictionnaire pour garder les temps de connexion (UUID: timestamp)
times = {}

# --- L'interface Cyber (HTML) ---
HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CYBER_MONITOR V3</title>
    <style>
        :root { --p: #ffb000; --bg: #050505; }
        body { background: var(--bg); color: #fff; font-family: monospace; margin: 0; padding: 15px; overflow: hidden; }
        header { border-bottom: 2px solid #332200; display: flex; justify-content: space-between; padding-bottom: 10px; margin-bottom: 15px; }
        .grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 15px; height: 85vh; }
        .panel { background: #0a0a0a; border: 1px solid #222; position: relative; padding: 10px; display: flex; justify-content: center; align-items: center; }
        .map-frame { position: relative; width: 512px; height: 512px; border: 1px solid var(--p); background-size: cover; }
        canvas { position: absolute; top:0; left:0; width:100%; height:100%; }
        .list { overflow-y: auto; padding: 10px; text-align: left; }
        .av-row { display: grid; grid-template-columns: 1fr 80px 80px; padding: 8px; border-bottom: 1px solid #111; font-size: 11px; }
        .p-text { color: var(--p); text-shadow: 0 0 5px var(--p); }
    </style>
</head>
<body>
    <header>
        <div class="p-text" style="font-weight:bold;">[ CYBER_MONITOR // CORE_V3 ]</div>
        <div>SYS: <span id="rn" class="p-text">---</span></div>
    </header>
    <div class="grid">
        <div class="panel">
            <div id="bg" class="map-frame">
                <canvas id="cv" width="512" height="512"></canvas>
            </div>
        </div>
        <div class="panel list" id="list">
            <div style="color:var(--p); margin-bottom:10px;">// LIVE_FEED_DETECTED</div>
        </div>
    </div>
    <script>
        async function refresh() {
            try {
                const r = await fetch('/api');
                const d = await r.json();
                document.getElementById('rn').innerText = d.region.toUpperCase();
                document.getElementById('bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
                
                const ctx = document.getElementById('cv').getContext('2d');
                ctx.clearRect(0,0,512,512);
                const list = document.getElementById('list');
                list.innerHTML = d.avatars.length ? "" : "NO TARGETS";

                d.avatars.forEach(a => {
                    const x = a.x * 2; const y = 512 - (a.y * 2);
                    ctx.strokeStyle = "red"; ctx.lineWidth = 2;
                    ctx.beginPath(); ctx.moveTo(x-10,y); ctx.lineTo(x+10,y); ctx.moveTo(x,y-10); ctx.lineTo(x,y+10); ctx.stroke();
                    ctx.fillStyle = "white"; ctx.font = "bold 12px monospace"; ctx.fillText(a.name.toUpperCase(), x+12, y+4);

                    const row = document.createElement('div');
                    row.className = "av-row";
                    const min = Math.floor((Date.now()/1000 - a.start)/60);
                    row.innerHTML = `<span style="color:white">${a.name}</span><span class="p-text">${Math.floor(a.x)},${Math.floor(a.y)}</span><span>${min} MIN</span>`;
                    list.appendChild(row);
                });
            } catch(e) {}
        }
        setInterval(refresh, 2000);
    </script>
</body>
</html>
"""

@app.route('/api', methods=['GET', 'POST'])
def handle():
    global db, times
    if request.method == 'POST':
        try:
            data = request.json
            if not data: return "No Data", 400
            
            # Mise à jour des infos sim
            db["region"] = data.get("region", "Unknown")
            db["coords"] = data.get("grid_coords", {"x":0, "y":0})
            
            # Gestion des avatars et du temps
            incoming = data.get("avatars", [])
            active_list = []
            now = time.time()
            
            for av in incoming:
                uid = av.get("key")
                if uid:
                    if uid not in times:
                        times[uid] = now
                    av["start"] = times[uid]
                    active_list.append(av)
            
            db["avatars"] = active_list
            return "OK", 200
        except Exception as e:
            print(f"Error: {e}")
            return str(e), 500
            
    return jsonify(db)

@app.route('/')
def home():
    return render_template_string(HTML_CODE)
