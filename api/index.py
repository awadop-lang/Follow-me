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

# --- INTERFACE TACTIQUE NOX V6.0 (INTEGRATED INSPECTOR) ---
HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TACTICAL_HUD // NOX_V6.0</title>
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

        /* Grille : Carte (512px) | Liste (Flexible) | Inspecteur (300px) */
        .grid { display: grid; grid-template-columns: 512px 1fr 300px; gap: 15px; flex: 1; overflow: hidden; }

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
            cursor: pointer; transition: all 0.2s ease;
        }
        .card:hover { 
            background: rgba(0,255,255,0.08); border-color: var(--p); 
            transform: translateX(5px);
        }
        
        .card-header { display: flex; justify-content: space-between; font-size: 11px; margin-bottom: 5px; }
        .bar-bg { width: 100%; height: 2px; background: #111; margin-top: 8px; }
        .bar-fill { height: 100%; transition: width 1s; }

        /* --- BLOC INSPECTEUR --- */
        .inspector { 
            background: #000; border: 1px solid #222; display: flex; flex-direction: column; 
            border-top: 2px solid var(--p); box-shadow: inset 0 0 20px rgba(0,255,255,0.05);
        }
        .inspect-header { padding: 10px; font-size: 10px; color: var(--p); background: rgba(0,255,255,0.05); text-align: center; letter-spacing: 2px; }
        
        .inspect-photo-frame { 
            width: 100%; aspect-ratio: 1; background: #0a0a0a; border-bottom: 1px solid #222;
            display: flex; align-items: center; justify-content: center; overflow: hidden; position: relative;
        }
        #i-img { width: 100%; height: 100%; object-fit: cover; display: none; z-index: 2; }
        .no-photo { font-size: 10px; opacity: 0.2; text-align: center; z-index: 1; }

        .inspect-content { padding: 15px; flex: 1; overflow-y: auto; }
        .i-label { font-size: 9px; color: var(--p); opacity: 0.6; margin-top: 12px; text-transform: uppercase; }
        .i-val { font-size: 13px; color: #fff; font-weight: bold; margin-bottom: 4px; word-break: break-all; }

        .btn-profile { 
            width: 100%; padding: 12px; background: var(--p); color: #000; 
            border: none; font-family: inherit; font-weight: bold; cursor: pointer;
            margin-top: 20px; text-transform: uppercase; display: none;
        }
        .btn-profile:hover { background: #fff; }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #000; }
        ::-webkit-scrollbar-thumb { background: var(--p); }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ TACTICAL_MONITOR_V6.0 ]</div>
        <div id="status" style="font-size: 10px; opacity: 0.6;">SIGNAL: STABLE // SCANNER_ACTIVE</div>
    </header>

    <div class="grid">
        <div class="map-wrapper">
            <div id="map-bg"></div>
            <div class="scan-line"></div>
            <canvas id="cv" width="512" height="512"></canvas>
        </div>

        <div class="list" id="feed"></div>

        <div class="inspector">
            <div class="inspect-header">// AGENT_DOSSIER</div>
            <div class="inspect-photo-frame">
                <img id="i-img" src="" onerror="this.style.display='none'">
                <div class="no-photo">AWAITING_SCAN...</div>
            </div>
            <div class="inspect-content">
                <div class="i-label">Identity</div>
                <div id="i-name" class="i-val">NOT_SELECTED</div>
                
                <div class="i-label">Duration</div>
                <div id="i-time" class="i-val" style="color:var(--p)">00m 00s</div>

                <div class="i-label">Position</div>
                <div id="i-pos" class="i-val">---</div>

                <div class="i-label">Global UID</div>
                <div id="i-key" class="i-val" style="font-size:10px; color:#444;">---</div>

                <button id="i-btn" class="btn-profile">Open Web Profile</button>
            </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const colors = ["#00ffff", "#ff00ff", "#00ff9f", "#ffff00", "#ff3f00", "#007fff"];
        let trails = {}; 
        let selectedKey = null;

        function fmtTime(s) {
            const m = Math.floor(s/60);
            return `${m}m ${Math.floor(s%60)}s`;
        }

        function inspectAgent(av) {
            selectedKey = av.key;
            const img = document.getElementById('i-img');
            const btn = document.getElementById('i-btn');
            
            // Photo Fix
            img.style.display = 'none';
            img.src = `https://my-secondlife-p01.s3.amazonaws.com/users/${av.key.replace(/-/g, '_')}/thumb_sl_image.png`;
            img.onload = () => img.style.display = 'block';

            document.getElementById('i-name').innerText = av.name.toUpperCase();
            document.getElementById('i-key').innerText = av.key;
            
            btn.style.display = 'block';
            const urlName = av.name.toLowerCase().replace(/ /g, '.');
            btn.onclick = () => window.open(`https://my.secondlife.com/${urlName}`, '_blank');
        }

        async function update() {
            try {
                const r = await fetch('/api');
                const d = await r.json();
                
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
                    const timeS = Math.floor(Date.now()/1000 - av.start_time);

                    // Update Inspector in real-time
                    if(selectedKey === av.key) {
                        document.getElementById('i-time').innerText = fmtTime(timeS);
                        document.getElementById('i-pos').innerText = `${Math.floor(av.x)}, ${Math.floor(av.y)}`;
                    }

                    // Trails
                    if(!trails[av.key]) trails[av.key] = [];
                    let lp = trails[av.key][trails[av.key].length - 1];
                    if(!lp || Math.abs(lp.x - x) > 1 || Math.abs(lp.y - y) > 1) trails[av.key].push({x, y});
                    if(trails[av.key].length > 400) trails[av.key].shift();

                    ctx.beginPath(); ctx.strokeStyle = color; ctx.globalAlpha = 0.4; ctx.lineWidth = 1;
                    trails[av.key].forEach((p, idx) => { if(idx==0) ctx.moveTo(p.x,p.y); else ctx.lineTo(p.x,p.y); });
                    ctx.stroke(); ctx.globalAlpha = 1.0;

                    // Dot
                    ctx.strokeStyle = color; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(x,y,6,0,7); ctx.stroke(); 
                    ctx.fillStyle = "white"; ctx.beginPath(); ctx.arc(x,y,1.5,0,7); ctx.fill(); 

                    // List Card
                    const pct = Math.min(100, (timeS / 3600) * 100);
                    const card = document.createElement('div');
                    card.className = "card";
                    card.onclick = () => inspectAgent(av);
                    card.innerHTML = `
                        <div class="card-header">
                            <b style="color:${color}">${av.name}</b>
                            <span style="opacity:0.7">${Math.floor(av.x)}, ${Math.floor(av.y)}</span>
                        </div>
                        <div class="bar-bg"><div class="bar-fill" style="width:${pct}%; background:${color}; box-shadow:0 0 5px ${color}"></div></div>
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
