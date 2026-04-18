from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)
db = {"avatars": {}, "region_name": "Sim Name"}

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>CORE MONITOR - MAP MODE</title>
    <style>
        body { background: #050505; color: #00ff41; font-family: monospace; margin: 0; padding: 10px; text-align: center; }
        .map-container { 
            position: relative; width: 256px; height: 256px; 
            margin: 20px auto; border: 2px solid #00ff41;
            background-size: cover;
        }
        canvas { position: absolute; top:0; left:0; }
        .list-zone { 
            width: 300px; margin: 20px auto; border-top: 1px solid #00ff41; 
            text-align: left; font-size: 12px;
        }
        .av-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #002200; }
        .bar-bg { width: 100px; height: 8px; background: #001100; border: 1px solid #004411; margin-left: 10px; }
        .bar-fill { height: 100%; background: #00ff41; width: 0%; transition: width 0.5s; }
    </style>
</head>
<body>
    <h1>SYSTEM MONITOR : <span id="reg-name">---</span></h1>
    
    <div class="map-container" id="map-bg">
        <canvas id="map-canvas" width="256" height="256"></canvas>
    </div>

    <div class="list-zone" id="list"></div>

    <script>
        async function update() {
            const r = await fetch('/api');
            const data = await r.json();
            const canvas = document.getElementById('map-canvas');
            const ctx = canvas.getContext('2d');
            const list = document.getElementById('list');
            
            // Mise à jour de l'image de fond (Map de la Sim)
            if(data.region) {
                document.getElementById('reg-name').innerText = data.region.toUpperCase();
                const mapUrl = `https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg`;
                document.getElementById('map-bg').style.backgroundImage = `url('${mapUrl}')`;
            }

            ctx.clearRect(0,0,256,256);
            list.innerHTML = "";

            data.avatars.forEach(av => {
                // Point sur la carte
                ctx.fillStyle = "red";
                ctx.shadowBlur = 10; ctx.shadowColor = "red";
                ctx.beginPath(); ctx.arc(av.x, 256-av.y, 5, 0, 7); ctx.fill();
                ctx.fillStyle = "white"; ctx.shadowBlur = 0;
                ctx.fillText(av.name, av.x + 8, 256-av.y);

                // Ligne dans la liste
                const row = document.createElement('div');
                row.className = "av-row";
                const timeSec = Math.floor(Date.now()/1000) - av.start;
                row.innerHTML = `<span>${av.name}</span>
                                <div style="display:flex; align-items:center;">
                                    <span>${Math.floor(timeSec/60)}m</span>
                                    <div class="bar-bg"><div class="bar-fill" style="width:${Math.min(100, timeSec/60)}%"></div></div>
                                </div>`;
                list.appendChild(row);
            });
        }
        setInterval(update, 2000);
    </script>
</body>
</html>
"""

@app.route('/api', methods=['GET', 'POST'])
def handle():
    if request.method == 'POST':
        raw = request.json
        db["region"] = raw.get("region")
        db["coords"] = raw.get("grid_coords")
        db["active"] = raw.get("avatars")
        # Logique simplifiée pour le stockage du temps
        for av in db["active"]:
            if av["key"] not in db["avatars"]:
                db["avatars"][av["key"]] = {"name": av["name"], "start": time.time()}
            db["avatars"][av["key"]].update(av)
        return "OK"
    
    # Envoyer les données au format attendu par le JS
    output = []
    if "active" in db:
        for av in db["active"]:
            if av["key"] in db["avatars"]:
                info = db["avatars"][av["key"]]
                output.append({
                    "name": info["name"], "x": info["x"], "y": info["y"], "start": info["start"]
                })
    return jsonify({"region": db.get("region"), "coords": db.get("coords"), "avatars": output})

@app.route('/')
def home(): return render_template_string(HTML)
