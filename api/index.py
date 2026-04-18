from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)
# Initialisation propre de la base de données
db = {"region": "Inconnue", "coords": {"x": 0, "y": 0}, "avatars": []}
# Dictionnaire pour garder les temps de connexion en mémoire vive
start_times = {}

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>CORE MONITOR V2</title>
    <style>
        body { background: #080808; color: #00ff41; font-family: monospace; margin: 0; padding: 20px; display: flex; flex-direction: column; height: 100vh; }
        .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; flex: 1; }
        .map-box { background: #111; border: 1px solid #004411; display: flex; justify-content: center; align-items: center; position: relative; }
        .map-img { width: 512px; height: 512px; background-size: cover; position: relative; border: 2px solid #00ff41; }
        canvas { position: absolute; top:0; left:0; }
        .list-box { background: #111; border: 1px solid #004411; padding: 15px; overflow-y: auto; }
        .av-row { display: grid; grid-template-columns: 1fr 100px 80px; padding: 8px; border-bottom: 1px solid #002200; font-size: 12px; }
        h1 { color: #00ff41; text-shadow: 0 0 10px #00ff41; font-size: 18px; }
    </style>
</head>
<body>
    <h1>[CORE MONITOR :: GLOBAL VIEW] - REGION: <span id="rname">...</span></h1>
    <div class="grid">
        <div class="map-box">
            <div id="bg" class="map-img">
                <canvas id="cv" width="512" height="512"></canvas>
            </div>
        </div>
        <div class="list-box">
            <div style="color:#00ff41; margin-bottom:10px; font-weight:bold;">AGENTS ACTIFS</div>
            <div id="list"></div>
        </div>
    </div>
    <script>
        async function up() {
            try {
                const res = await fetch('/api');
                const d = await res.json();
                document.getElementById('rname').innerText = d.region.toUpperCase();
                document.getElementById('bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
                
                const ctx = document.getElementById('cv').getContext('2d');
                ctx.clearRect(0,0,512,512);
                const list = document.getElementById('list');
                list.innerHTML = "";

                d.avatars.forEach(a => {
                    const x = a.x * 2; const y = 512 - (a.y * 2);
                    ctx.fillStyle = "red"; ctx.shadowBlur = 10; ctx.shadowColor = "red";
                    ctx.beginPath(); ctx.arc(x, y, 6, 0, 7); ctx.fill();
                    ctx.fillStyle = "white"; ctx.shadowBlur = 0;
                    ctx.fillText(a.name, x + 10, y + 3);

                    const row = document.createElement('div');
                    row.className = "av-row";
                    const t = Math.floor((Date.now()/1000 - a.start)/60);
                    row.innerHTML = `<span>${a.name}</span><span style="color:#00ff41">${Math.floor(a.x)},${Math.floor(a.y)}</span><span>${t} min</span>`;
                    list.appendChild(row);
                });
            } catch(e) {}
        }
        setInterval(up, 2000);
    </script>
</body>
</html>
"""

@app.route('/api', methods=['GET', 'POST'])
def handle():
    global db, start_times
    if request.method == 'POST':
        data = request.json
        db["region"] = data.get("region", "Inconnue")
        db["coords"] = data.get("grid_coords", {"x":0, "y":0})
        active = data.get("avatars", [])
        
        current_active = []
        now = time.time()
        for av in active:
            uid = av["key"]
            if uid not in start_times:
                start_times[uid] = now
            av["start"] = start_times[uid]
            current_active.append(av)
        
        db["avatars"] = current_active
        return "OK"
    return jsonify(db)

@app.route('/')
def home():
    return render_template_string(HTML)
