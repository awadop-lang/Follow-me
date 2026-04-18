from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

# Base de données en mémoire
db = {
    "region": "SYS_CONNECTING...",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
times = {}

# --- INTERFACE TACTIQUE NOX V5.1 ---
HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TACTICAL_HUD // NOX_V5</title>
    <style>
        :root { --p: #00ffff; --bg: #020205; --panel: #05050a; --font: 'Courier New', monospace; }
        body { background: var(--bg); color: #a0c0c0; font-family: var(--font); margin: 0; padding: 15px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { border: 1px solid var(--p); background: rgba(0,255,255,0.05); padding: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 0 10px rgba(0,255,255,0.1); }
        .grid { display: grid; grid-template-columns: 512px 1fr; gap: 20px; flex: 1; }
        .map-wrapper { width: 512px; height: 512px; border: 1px solid var(--p); background: #000; position: relative; overflow: hidden; }
        #map-bg { width: 100%; height: 100%; background-size: 100% 100%; position: absolute; opacity: 0.7; }
        canvas { position: absolute; top:0; left:0; z-index: 10; }
        .scan-line { position: absolute; width: 100%; height: 2px; background: var(--p); z-index: 11; animation: scan 4s linear infinite; box-shadow: 0 0 10px var(--p); opacity: 0.5; }
        @keyframes scan { from { top: 0; } to { top: 100%; } }
        .list { background: var(--panel); border: 1px solid #111; padding: 15px; overflow-y: auto; border-left: 4px solid var(--p); }
        .card { background: rgba(255,255,255,0.02); border: 1px solid #1a1a1a; padding: 12px; margin-bottom: 10px; border-radius: 2px; }
        .bar-bg { width: 100%; height: 4px; background: #000; margin-top: 8px; border-radius: 2px; }
        .bar-fill { height: 100%; transition: width 1s; box-shadow: 0 0 8px currentColor; }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 18px; font-weight: bold; letter-spacing: 3px; color: var(--p);">[ TACTICAL_MONITOR_V5 ]</div>
        <div id="status" style="font-size: 12px;">SIGNAL: ACTIVE</div>
    </header>
    <div class="grid">
        <div class="map-wrapper">
            <div id="map-bg"></div>
            <div class="scan-line"></div>
            <canvas id="cv" width="512" height="512"></canvas>
        </div>
        <div class="list" id="feed"></div>
    </div>
    <script>
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const colors = ["#00ffff", "#ff00ff", "#00ff9f", "#ffff00", "#ff3f00", "#007fff"];
        let trails = {}; // Historique des positions

        async function update() {
            try {
                const r = await fetch('/api');
                const d = await r.json();
                document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
                
                ctx.clearRect(0,0,512,512);
                const feed = document.getElementById('feed');
                feed.innerHTML = "";

                d.avatars.forEach((av, i) => {
                    const color = colors[i % colors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);

                    // Historique pour trajectoire
                    if(!trails[av.key]) trails[av.key] = [];
                    trails[av.key].push({x, y});
                    if(trails[av.key].length > 15) trails[av.key].shift();

                    // Dessin Trajectoire
                    ctx.beginPath(); ctx.strokeStyle = color; ctx.globalAlpha = 0.4; ctx.lineWidth = 1;
                    trails[av.key].forEach((p, idx) => { if(idx==0) ctx.moveTo(p.x,p.y); else ctx.lineTo(p.x,p.y); });
                    ctx.stroke(); ctx.globalAlpha = 1.0;

                    // Dessin Target
                    ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x,y,10,0,7); ctx.stroke();
                    ctx.fillStyle = "white"; ctx.font = "bold 11px monospace"; ctx.fillText(av.name.toUpperCase(), x+15, y+5);

                    // HTML Card
                    const timeS = Math.floor(Date.now()/1000 - av.start_time);
                    const pct = Math.min(100, (timeS / 1800) * 100);
                    const card = document.createElement('div');
                    card.className = "card";
                    card.innerHTML = `
                        <div style="display:flex; justify-content:space-between; font-size:12px;">
                            <b style="color:${color}">${av.name}</b>
                            <span>${Math.floor(av.x)}, ${Math.floor(av.y)}</span>
                        </div>
                        <div class="bar-bg"><div class="bar-fill" style="width:${pct}%; background:${color}; color:${color}"></div></div>
                        <div style="font-size:10px; margin-top:5px; opacity:0.5;">DURATION: ${Math.floor(timeS/60)}m ${timeS%60}s</div>
                    `;
                    feed.appendChild(card);
                });
            } catch(e){}
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
        try:
            data = request.json
            if not data: return "No Data", 400
            db["region"] = data.get("region", "UNK")
            db["coords"] = data.get("grid_coords", {"x":0, "y":0})
            active = []
            now = time.time()
            for av in data.get("avatars", []):
                uid = av.get("key")
                if uid:
                    if uid not in times: times[uid] = now
                    av["start_time"] = times[uid]
                    active.append(av)
            db["avatars"] = active
            return "OK", 200
        except: return "ERR", 500
    return jsonify(db)

@app.route('/')
def home(): return render_template_string(HTML_CODE)
