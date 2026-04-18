from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

db = {
    "region": "SECURE_STREAM_ACTIVE...",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
times = {}

# --- INTERFACE TACTIQUE NOX V5.4 (WEB PROFILES) ---
HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TACTICAL_HUD // NOX_V5.4</title>
    <style>
        :root { --p: #00ffff; --bg: #010103; --panel: #05050a; --font: 'Fira Code', monospace; }
        body { background: var(--bg); color: #a0c0c0; font-family: var(--font); margin: 0; padding: 15px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { border-bottom: 2px solid var(--p); background: rgba(0,255,255,0.02); padding: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
        
        /* Grille : Carte | Liste | Inspecteur */
        .grid { display: grid; grid-template-columns: 512px 1fr 280px; gap: 15px; flex: 1; overflow: hidden; }

        .map-wrapper { width: 512px; height: 512px; border: 1px solid #222; background: #000; position: relative; overflow: hidden; }
        #map-bg { width: 100%; height: 100%; background-size: 100% 100%; position: absolute; opacity: 0.8; filter: brightness(0.7); }
        canvas { position: absolute; top:0; left:0; z-index: 10; }
        
        .list { background: var(--panel); border: 1px solid #111; padding: 10px; overflow-y: auto; border-left: 2px solid var(--p); }
        
        /* Panel Inspecteur (Nouveau) */
        .inspector { background: #000; border: 1px solid #222; padding: 15px; text-align: center; display: flex; flex-direction: column; gap: 10px; border-top: 2px solid var(--p); }
        .inspect-img { width: 100%; aspect-ratio: 1; border: 1px solid var(--p); background: #111; background-size: cover; background-position: center; }
        .inspect-data { text-align: left; font-size: 11px; margin-top: 10px; line-height: 1.6; }

        .card { 
            background: rgba(255,255,255,0.01); border: 1px solid #1a1a1a; 
            padding: 10px; margin-bottom: 8px; cursor: pointer; transition: 0.2s;
        }
        .card:hover { background: rgba(0,255,255,0.08); border-color: var(--p); transform: translateX(5px); }
        
        .bar-bg { width: 100%; height: 2px; background: #111; margin-top: 6px; }
        .bar-fill { height: 100%; transition: width 1s; }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ TACTICAL_MONITOR_V5.4 ]</div>
        <div id="status" style="font-size: 10px; opacity: 0.6;">MODE: WEB_INSPECTOR_ACTIVE</div>
    </header>

    <div class="grid">
        <div class="map-wrapper">
            <div id="map-bg"></div>
            <canvas id="cv" width="512" height="512"></canvas>
        </div>

        <div class="list" id="feed"></div>

        <div class="inspector" id="inspector">
            <div style="font-size: 10px; color: var(--p); letter-spacing: 2px;">// AGENT_DOSSIER</div>
            <div id="i-img" class="inspect-img" style="background-image: url('https://world.secondlife.com/images/logo.jpg');"></div>
            <div id="i-name" style="font-weight:bold; color:#fff; font-size:14px;">NO_SELECTION</div>
            <div id="i-data" class="inspect-data">Sélectionnez un agent pour obtenir les données de profil...</div>
            <button id="i-link" style="background:var(--p); border:none; color:#000; padding:5px; font-family:monospace; font-weight:bold; cursor:pointer; display:none;">OPEN WEB PROFILE</button>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const colors = ["#00ffff", "#ff00ff", "#00ff9f", "#ffff00", "#ff3f00", "#007fff"];
        let trails = {}; 

        // Fonction pour inspecter un agent
        function inspect(key, name) {
            document.getElementById('i-name').innerText = name.toUpperCase();
            document.getElementById('i-img').style.backgroundImage = `url('https://my-secondlife-p01.s3.amazonaws.com/users/${key.replace(/-/g, '_')}/thumb_sl_image.png'), url('https://world.secondlife.com/static/img/avatars/default_avatar.png')`;
            document.getElementById('i-data').innerHTML = `
                UUID: <span style="color:var(--p)">${key}</span><br>
                STATUS: ACTIVE_TARGET<br>
                LINK: <a href="https://world.secondlife.com/resident/${key}" target="_blank" style="color:var(--p)">WEB_PAGE</a>
            `;
            const btn = document.getElementById('i-link');
            btn.style.display = 'block';
            btn.onclick = () => window.open(`https://my.secondlife.com/${name.replace(/ /g, '.')}`, '_blank');
        }

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

                    if(!trails[av.key]) trails[av.key] = [];
                    let lastP = trails[av.key][trails[av.key].length - 1];
                    if(!lastP || Math.abs(lastP.x - x) > 1 || Math.abs(lastP.y - y) > 1) trails[av.key].push({x, y});
                    if(trails[av.key].length > 400) trails[av.key].shift();

                    ctx.beginPath(); ctx.strokeStyle = color; ctx.globalAlpha = 0.4; ctx.lineWidth = 1;
                    trails[av.key].forEach((p, idx) => { if(idx==0) ctx.moveTo(p.x,p.y); else ctx.lineTo(p.x,p.y); });
                    ctx.stroke(); ctx.globalAlpha = 1.0;

                    ctx.strokeStyle = color; ctx.lineWidth = 1; 
                    ctx.beginPath(); ctx.arc(x,y,6,0,7); ctx.stroke(); 
                    ctx.fillStyle = "white"; ctx.beginPath(); ctx.arc(x,y,1.5,0,7); ctx.fill(); 
                    ctx.fillText(av.name.toUpperCase(), x+10, y+4);

                    const timeS = Math.floor(Date.now()/1000 - av.start_time);
                    const card = document.createElement('div');
                    card.className = "card";
                    card.onclick = () => inspect(av.key, av.name); // CLIC POUR INSPECTER
                    card.innerHTML = `
                        <div style="display:flex; justify-content:space-between; font-size:11px;">
                            <b style="color:${color}">${av.name}</b>
                            <span>${Math.floor(av.x)}, ${Math.floor(av.y)}</span>
                        </div>
                        <div class="bar-bg"><div class="bar-fill" style="width:30%; background:${color}; color:${color}"></div></div>
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
