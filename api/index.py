from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

db = {
    "region": "SYS_SCANNING...",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
times = {}

# --- INTERFACE TACTIQUE V5.6 (FIX PHOTO + DURATION) ---
HTML_CODE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>TACTICAL_HUD // NOX_V5.6</title>
    <style>
        :root { --p: #00ffff; --bg: #010103; --panel: #05050a; --font: 'Fira Code', monospace; }
        body { background: var(--bg); color: #a0c0c0; font-family: var(--font); margin: 0; padding: 15px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { border-bottom: 2px solid var(--p); background: rgba(0,255,255,0.02); padding: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
        
        .grid { display: grid; grid-template-columns: 512px 1fr 300px; gap: 15px; flex: 1; overflow: hidden; }

        /* Carte */
        .map-wrapper { width: 512px; height: 512px; border: 1px solid #222; background: #000; position: relative; overflow: hidden; }
        #map-bg { width: 100%; height: 100%; background-size: 100% 100%; position: absolute; opacity: 0.8; filter: brightness(0.6); }
        canvas { position: absolute; top:0; left:0; z-index: 10; }
        
        /* Liste Agents */
        .list { background: var(--panel); border: 1px solid #111; padding: 10px; overflow-y: auto; border-left: 2px solid var(--p); }
        .card { background: rgba(255,255,255,0.01); border: 1px solid #1a1a1a; padding: 12px; margin-bottom: 8px; cursor: pointer; transition: 0.2s; }
        .card:hover { background: rgba(0,255,255,0.1); border-color: var(--p); }

        /* Colonne Inspecteur */
        .inspector { background: #000; border: 1px solid #222; display: flex; flex-direction: column; border-top: 2px solid var(--p); }
        .inspect-header { padding: 10px; font-size: 10px; color: var(--p); background: rgba(0,255,255,0.05); text-align: center; letter-spacing: 2px; }
        
        .inspect-photo-area { width: 100%; aspect-ratio: 1; background: #0a0a0a; border-bottom: 1px solid #222; display: flex; align-items: center; justify-content: center; overflow: hidden; }
        #i-img { width: 100%; height: 100%; object-fit: cover; display: none; }
        .placeholder { font-size: 10px; opacity: 0.3; text-align: center; }

        .inspect-details { padding: 15px; flex: 1; overflow-y: auto; }
        .label { font-size: 9px; color: var(--p); opacity: 0.6; margin-top: 12px; text-transform: uppercase; }
        .val { font-size: 13px; color: #fff; font-weight: bold; margin-bottom: 4px; }

        .btn { width: 100%; padding: 12px; background: var(--p); color: #000; border: none; font-family: inherit; font-weight: bold; cursor: pointer; margin-top: 20px; display: none; }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ TACTICAL_HUD_V5.6 ]</div>
        <div id="sim-info" style="font-size: 10px;">SIGNAL_ACTIVE</div>
    </header>

    <div class="grid">
        <div class="map-wrapper">
            <div id="map-bg"></div>
            <canvas id="cv" width="512" height="512"></canvas>
        </div>

        <div class="list" id="feed"></div>

        <div class="inspector">
            <div class="inspect-header">// TARGET_INVESTIGATION</div>
            <div class="inspect-photo-area">
                <img id="i-img" src="" onerror="this.src='https://world.secondlife.com/static/img/avatars/default_avatar.png'">
                <div id="i-wait" class="placeholder">SELECT_TARGET</div>
            </div>
            <div class="inspect-details">
                <div class="label">Agent Name</div>
                <div id="i-name" class="val">---</div>
                
                <div class="label">Presence Duration</div>
                <div id="i-time" class="val" style="color: var(--p);">00m 00s</div>

                <div class="label">Position Data</div>
                <div id="i-pos" class="val">---</div>
                
                <div class="label">UUID</div>
                <div id="i-key" class="val" style="font-size:10px; color:#666;">---</div>

                <button id="i-btn" class="btn">VIEW WEB PROFILE</button>
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
            const sec = Math.floor(s%60);
            return `${m}m ${sec}s`;
        }

        function showProfile(av) {
            selectedKey = av.key;
            const img = document.getElementById('i-img');
            const wait = document.getElementById('i-wait');
            const btn = document.getElementById('i-btn');
            
            // Correction de l'URL de la photo (Fallback sur world.secondlife)
            img.src = `https://my-secondlife-p01.s3.amazonaws.com/users/${av.key.replace(/-/g, '_')}/thumb_sl_image.png`;
            img.style.display = 'block';
            wait.style.display = 'none';

            document.getElementById('i-name').innerText = av.name.toUpperCase();
            document.getElementById('i-key').innerText = av.key;
            document.getElementById('i-pos').innerText = `${Math.floor(av.x)}, ${Math.floor(av.y)}`;
            
            btn.style.display = 'block';
            btn.onclick = () => window.open(`https://my.secondlife.com/${av.name.replace(/ /g, '.')}`, '_blank');
        }

        async function update() {
            try {
                const r = await fetch('/api');
                const d = await r.json();
                
                document.getElementById('sim-info').innerText = `REGION: ${d.region.toUpperCase()} [${d.coords.x},${d.coords.y}]`;
                document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
                
                ctx.clearRect(0,0,512,512);
                const feed = document.getElementById('feed');
                feed.innerHTML = "";

                d.avatars.forEach((av, i) => {
                    const color = colors[i % colors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);
                    const duration = Math.floor(Date.now()/1000 - av.start_time);

                    // Mise à jour de l'inspecteur en temps réel si l'agent est sélectionné
                    if(selectedKey === av.key) {
                        document.getElementById('i-time').innerText = fmtTime(duration);
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

                    // Draw dot
                    ctx.strokeStyle = color; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(x,y,6,0,7); ctx.stroke(); 
                    ctx.fillStyle = "white"; ctx.beginPath(); ctx.arc(x,y,1.5,0,7); ctx.fill(); 

                    // List Card
                    const card = document.createElement('div');
                    card.className = "card";
                    card.onclick = () => showProfile(av);
                    card.innerHTML = `<b style="color:${color}">${av.name}</b><br><span style="font-size:9px; opacity:0.5;">DURATION: ${fmtTime(duration)}</span>`;
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
