from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

db = {
    "region": "SYS_SEARCHING...",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
times = {}
# Palette de couleurs cyber pour différencier les noms
colors = ["#00f2ff", "#ffb000", "#00ff41", "#ff00ff", "#ffff00", "#0088ff", "#ff5500"]

HTML_CODE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>CYBER_MONITOR // CORE_V4</title>
    <style>
        :root { --bg: #030303; --panel: #0a0a0a; --p: #ffb000; --text: #e0e0e0; --font: 'SF Mono', monospace; }
        body { background-color: var(--bg); color: var(--text); font-family: var(--font); margin: 0; padding: 20px; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        
        header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; border-bottom: 2px solid #222; margin-bottom: 20px; }
        h1 { margin: 0; font-size: 18px; letter-spacing: 4px; color: var(--p); text-shadow: 0 0 10px var(--p); }

        .main-grid { display: grid; grid-template-columns: 512px 1fr; gap: 25px; flex: 1; height: calc(100% - 80px); }

        /* Carte */
        .map-box { width: 512px; height: 512px; border: 2px solid #222; background: #000; position: relative; overflow: hidden; }
        #map-bg { width: 100%; height: 100%; background-repeat: no-repeat; background-size: 100% 100%; position: absolute; }
        canvas { position: absolute; top:0; left:0; z-index: 5; }

        /* Liste */
        .list-box { background: var(--panel); border: 1px solid #222; border-radius: 4px; padding: 20px; overflow-y: auto; }
        .av-row { display: grid; grid-template-columns: 1fr 100px; gap: 10px; padding: 15px 0; border-bottom: 1px solid #1a1a1a; }
        
        .name-tag { font-weight: bold; font-size: 14px; text-transform: uppercase; margin-bottom: 5px; }
        
        /* Barre de progression du temps */
        .progress-bg { width: 100%; height: 4px; background: #111; border-radius: 2px; overflow: hidden; margin-top: 5px; }
        .progress-fill { height: 100%; width: 0%; transition: width 1s; box-shadow: 0 0 10px currentColor; }
        
        .info-cell { text-align: right; font-size: 11px; color: #666; }
    </style>
</head>
<body>
    <header>
        <h1>[CYBER_CORE // V4]</h1>
        <div style="font-size:12px;">REGION: <span id="r_name" style="color:var(--p)">---</span></div>
    </header>

    <div class="main-grid">
        <div class="map-box">
            <div id="map-bg"></div>
            <canvas id="cv" width="512" height="512"></canvas>
        </div>

        <div class="list-box" id="list">
            </div>
    </div>

    <script>
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const colors = ["#00f2ff", "#ffb000", "#00ff41", "#ff00ff", "#ffff00", "#0088ff", "#ff5500"];

        async function update() {
            try {
                const res = await fetch('/api');
                const data = await res.json();
                
                document.getElementById('r_name').innerText = data.region.toUpperCase();
                document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;

                ctx.clearRect(0,0,512,512);
                const list = document.getElementById('list');
                list.innerHTML = "";

                data.avatars.forEach((av, index) => {
                    const color = colors[index % colors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);

                    // Dessin Carte
                    ctx.strokeStyle = color; ctx.lineWidth = 2;
                    ctx.beginPath(); ctx.moveTo(x-12,y); ctx.lineTo(x+12,y); ctx.moveTo(x,y-12); ctx.lineTo(x,y+12); ctx.stroke();
                    
                    ctx.fillStyle = "white"; ctx.font = "bold 11px monospace";
                    ctx.shadowColor = "black"; ctx.shadowBlur = 4;
                    ctx.fillText(av.name.toUpperCase(), x + 15, y + 5);
                    ctx.shadowBlur = 0;

                    // Ligne Liste
                    const row = document.createElement('div');
                    row.className = "av-row";
                    
                    // Calcul temps (max 60 min pour la barre de progression)
                    const elapsed = Math.floor((Date.now()/1000 - av.start_time)/60);
                    const progress = Math.min(100, (elapsed / 60) * 100);

                    row.innerHTML = `
                        <div>
                            <div class="name-tag" style="color:${color}">${av.name}</div>
                            <div class="progress-bg">
                                <div class="progress-fill" style="width:${progress}%; background-color:${color}; color:${color}"></div>
                            </div>
                        </div>
                        <div class="info-cell">
                            <div style="color:white">${Math.floor(av.x)}, ${Math.floor(av.y)}</div>
                            <div>${elapsed} MIN</div>
                        </div>
                    `;
                    list.appendChild(row);
                });
            } catch(e) {}
        }
        setInterval(update, 2000);
    </script>
</body>
</html>
"""

@app.route('/api', methods=['GET', 'POST'])
def handle():
    global db, times
    if request.method == 'POST':
        data = request.json
        if not data: return "No Data", 400
        db["region"] = data.get("region", "UNKNOWN")
        db["coords"] = data.get("grid_coords", {"x":0, "y":0})
        incoming = data.get("avatars", [])
        active_list = []
        now = time.time()
        for av in incoming:
            uid = av.get("key")
            if uid:
                if uid not in times: times[uid] = now
                av["start_time"] = times[uid]
                active_list.append(av)
        db["avatars"] = active_list
        return "OK", 200
    return jsonify(db)

@app.route('/')
def home(): return render_template_string(HTML_CODE)
