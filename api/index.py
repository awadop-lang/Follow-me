from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

db = {
    "region": "SECURE_STREAM_ACTIVE...",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
times = {}

# --- INTERFACE TACTIQUE NOX V5.2 (TRAILS LONGUE DURÉE) ---
HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TACTICAL_HUD // NOX_V5.2</title>
    <style>
        :root { --p: #00ffff; --bg: #010103; --panel: #05050a; --font: 'Fira Code', monospace; }
        body { background: var(--bg); color: #a0c0c0; font-family: var(--font); margin: 0; padding: 15px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { border-bottom: 2px solid var(--p); background: rgba(0,255,255,0.02); padding: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
        .grid { display: grid; grid-template-columns: 512px 1fr; gap: 20px; flex: 1; }
        .map-wrapper { width: 512px; height: 512px; border: 1px solid #222; background: #000; position: relative; overflow: hidden; }
        #map-bg { width: 100%; height: 100%; background-size: 100% 100%; position: absolute; opacity: 0.8; filter: brightness(0.7); }
        canvas { position: absolute; top:0; left:0; z-index: 10; }
        .scan-line { position: absolute; width: 100%; height: 1px; background: var(--p); z-index: 11; animation: scan 6s linear infinite; opacity: 0.3; }
        @keyframes scan { from { top: 0; } to { top: 100%; } }
        .list { background: var(--panel); border: 1px solid #111; padding: 15px; overflow-y: auto; border-left: 2px solid var(--p); }
        .card { background: rgba(255,255,255,0.01); border: 1px solid #1a1a1a; padding: 10px; margin-bottom: 8px; border-radius: 2px; }
        .bar-bg { width: 100%; height: 2px; background: #111; margin-top: 6px; }
        .bar-fill { height: 100%; transition: width 1s; box-shadow: 0 0 5px currentColor; }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ TACTICAL_MONITOR_V5.2 ]</div>
        <div id="status" style="font-size: 10px; opacity: 0.6;">NET_STATUS: ENCRYPTED_LINK</div>
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
        const colors = ["#00ffff", "#ff00ff", "#00ff9f", "#ffff00", "#ff3f00", "#007fff", "#ff0066"];
        let trails = {}; 

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

                    // --- Logique de Trajectoire (Trails) ---
                    if(!trails[av.key]) trails[av.key] = [];
                    
                    // On n'ajoute un point que si l'avatar a bougé (économie de mémoire)
                    let lastP = trails[av.key][trails[av.key].length - 1];
                    if(!lastP || Math.abs(lastP.x - x) > 1 || Math.abs(lastP.y - y) > 1) {
                        trails[av.key].push({x, y});
                    }
                    
                    // Persistance augmentée : on garde 500 points (plusieurs minutes de trajet)
                    if(trails[av.key].length > 500) trails[av.key].shift();

                    // Dessin Trajectoire (Fine et Néon)
                    ctx.beginPath(); ctx.strokeStyle = color; ctx.globalAlpha = 0.5; ctx.lineWidth = 1;
                    trails[av.key].forEach((p, idx) => { if(idx==0) ctx.moveTo(p.x,p.y); else ctx.lineTo(p.x,p.y); });
                    ctx.stroke(); ctx.globalAlpha = 1.0;

                    // Dessin Target (DOT PLUS PETIT)
                    ctx.strokeStyle = color; ctx.lineWidth = 1; 
                    ctx.beginPath(); ctx.arc(x,y,6,0,7); ctx.stroke(); // Cercle extérieur fin
                    ctx.fillStyle = "white"; ctx.beginPath(); ctx.arc(x,y,1.5,0,7); ctx.fill(); // Dot minuscule
                    
                    ctx.fillStyle = "white"; ctx.font = "10px monospace"; 
                    ctx.shadowColor = "black"; ctx.shadowBlur = 3;
                    ctx.fillText(av.name.toUpperCase(), x+10, y+4);
                    ctx.shadowBlur = 0;

                    // HTML Card
                    const timeS = Math.floor(Date.now()/1000 - av.start_time);
                    const pct = Math.min(100, (timeS / 3600) * 100); // Progression sur 1 heure
                    const card = document.createElement('div');
                    card.className = "card";
                    card.innerHTML = `
                        <div style="display:flex; justify-content:space-between; font-size:11px;">
                            <b style="color:${color}">${av.name}</b>
                            <span style="opacity:0.7">${Math.floor(av.x)}, ${Math.floor(av.y)}</span>
                        </div>
                        <div class="bar-bg"><div class="bar-fill" style="width:${pct}%; background:${color}; color:${color}"></div></div>
                        <div style="font-size:9px; margin-top:4px; opacity:0.4;">U_TIME: ${Math.floor(timeS/60)}m ${timeS%60}s</div>
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
