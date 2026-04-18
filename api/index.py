from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

# Base de données temporaire
db = {
    "region": "SECURE_STREAM_ACTIVE...",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
times = {}

# --- INTERFACE TACTIQUE NOX V5.3 (FINAL) ---
HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TACTICAL_HUD // NOX_V5.3</title>
    <style>
        :root { 
            --p: #00ffff; 
            --bg: #010103; 
            --panel: #05050a; 
            --font: 'Fira Code', 'Courier New', monospace; 
        }
        body { 
            background: var(--bg); color: #a0c0c0; font-family: var(--font); 
            margin: 0; padding: 15px; height: 100vh; overflow: hidden; 
            display: flex; flex-direction: column; 
        }
        
        header { 
            border-bottom: 2px solid var(--p); 
            background: rgba(0,255,255,0.02); 
            padding: 10px; margin-bottom: 15px; 
            display: flex; justify-content: space-between; align-items: center; 
        }

        .grid { display: grid; grid-template-columns: 512px 1fr; gap: 20px; flex: 1; overflow: hidden; }

        /* --- BLOC CARTE --- */
        .map-wrapper { 
            width: 512px; height: 512px; 
            border: 1px solid #222; background: #000; 
            position: relative; overflow: hidden; 
            box-shadow: 0 0 20px rgba(0,255,255,0.05);
        }
        #map-bg { 
            width: 100%; height: 100%; 
            background-size: 100% 100%; 
            position: absolute; opacity: 0.8; filter: brightness(0.7) saturate(0.8); 
        }
        canvas { position: absolute; top:0; left:0; z-index: 10; }
        
        .scan-line { 
            position: absolute; width: 100%; height: 1px; 
            background: var(--p); z-index: 11; 
            animation: scan 6s linear infinite; opacity: 0.3; 
        }
        @keyframes scan { from { top: 0; } to { top: 100%; } }
        
        /* --- BLOC LISTE --- */
        .list { 
            background: var(--panel); border: 1px solid #111; 
            padding: 15px; overflow-y: auto; border-left: 2px solid var(--p); 
        }
        
        .card { 
            background: rgba(255,255,255,0.01); border: 1px solid #1a1a1a; 
            padding: 12px; margin-bottom: 10px; border-radius: 2px; 
            cursor: pointer; transition: all 0.2s ease; position: relative;
        }
        .card:hover { 
            background: rgba(0,255,255,0.08); border-color: var(--p); 
            transform: translateX(8px); box-shadow: -5px 0 15px rgba(0,255,255,0.15);
        }
        .card:active { transform: scale(0.98); }
        
        .card-header { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 5px; }
        .bar-bg { width: 100%; height: 2px; background: #111; margin-top: 8px; }
        .bar-fill { height: 100%; transition: width 1s; box-shadow: 0 0 8px currentColor; }
        .card-footer { font-size: 9px; margin-top: 6px; opacity: 0.4; letter-spacing: 1px; }

        /* Scrollbar Cyber */
        .list::-webkit-scrollbar { width: 4px; }
        .list::-webkit-scrollbar-track { background: #000; }
        .list::-webkit-scrollbar-thumb { background: var(--p); }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ TACTICAL_MONITOR_V5.3 ]</div>
        <div id="status" style="font-size: 10px; opacity: 0.6;">MODE: INTERACTIVE_PROFILING // ENCRYPTED</div>
    </header>

    <div class="grid">
        <div class="map-wrapper">
            <div id="map-bg"></div>
            <div class="scan-line"></div>
            <canvas id="cv" width="512" height="512"></canvas>
        </div>
        <div class="list" id="feed">
            </div>
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
                
                // Update Map
                document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
                
                ctx.clearRect(0,0,512,512);
                const feed = document.getElementById('feed');
                feed.innerHTML = "";

                if (d.avatars.length === 0) {
                    feed.innerHTML = "<div style='text-align:center; opacity:0.2; margin-top:50px;'>NO_SIGNALS_DETECTED</div>";
                }

                d.avatars.forEach((av, i) => {
                    const color = colors[i % colors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);

                    // --- Logique Trails Persistants ---
                    if(!trails[av.key]) trails[av.key] = [];
                    let lastP = trails[av.key][trails[av.key].length - 1];
                    if(!lastP || Math.abs(lastP.x - x) > 1 || Math.abs(lastP.y - y) > 1) {
                        trails[av.key].push({x, y});
                    }
                    if(trails[av.key].length > 600) trails[av.key].shift();

                    // Dessin Trajectoire
                    ctx.beginPath(); ctx.strokeStyle = color; ctx.globalAlpha = 0.4; ctx.lineWidth = 1;
                    trails[av.key].forEach((p, idx) => { if(idx==0) ctx.moveTo(p.x,p.y); else ctx.lineTo(p.x,p.y); });
                    ctx.stroke(); ctx.globalAlpha = 1.0;

                    // Dessin Target Précision
                    ctx.strokeStyle = color; ctx.lineWidth = 1; 
                    ctx.beginPath(); ctx.arc(x,y,6,0,7); ctx.stroke(); 
                    ctx.fillStyle = "white"; ctx.beginPath(); ctx.arc(x,y,1.5,0,7); ctx.fill(); 
                    
                    ctx.fillStyle = "white"; ctx.font = "bold 10px monospace"; 
                    ctx.shadowColor = "black"; ctx.shadowBlur = 3;
                    ctx.fillText(av.name.toUpperCase(), x+10, y+4);
                    ctx.shadowBlur = 0;

                    // Création de la Carte Interactive
                    const timeS = Math.floor(Date.now()/1000 - av.start_time);
                    const pct = Math.min(100, (timeS / 3600) * 100);
                    const card = document.createElement('div');
                    card.className = "card";
                    
                    // Action au clic : Profil SL
                    card.onclick = () => {
                        window.open(`secondlife:///app/agent/${av.key}/about`, '_self');
                    };

                    card.innerHTML = `
                        <div class="card-header">
                            <b style="color:${color}">${av.name}</b>
                            <span style="opacity:0.7">${Math.floor(av.x)}, ${Math.floor(av.y)}</span>
                        </div>
                        <div class="bar-bg"><div class="bar-fill" style="width:${pct}%; background:${color}; color:${color}"></div></div>
                        <div class="card-footer">
                            U_TIME: ${Math.floor(timeS/60)}M ${timeS%60}S | ID: ${av.key.substring(0,8)}...
                        </div>
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
