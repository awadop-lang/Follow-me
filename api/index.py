from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

db = {
    "region": "AWAITING_UPLINK",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
times = {}
watchlist = {} # Stockage des UUID ajoutés

HTML_CODE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>TACTICAL_HUD // NOX_V6.5</title>
    <style>
        :root { --p: #00ffff; --bg: #010103; --panel: #05050a; --font: 'Fira Code', monospace; }
        body { background: var(--bg); color: #a0c0c0; font-family: var(--font); margin: 0; padding: 15px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { border-bottom: 2px solid var(--p); background: rgba(0,255,255,0.02); padding: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .grid { display: grid; grid-template-columns: 512px 1fr 300px; grid-template-rows: 1fr 220px; gap: 15px; flex: 1; overflow: hidden; }
        
        .map-wrapper { grid-row: 1 / 3; width: 512px; height: 512px; border: 1px solid #222; background: #000; position: relative; overflow: hidden; }
        #map-bg { width: 100%; height: 100%; background-size: cover; position: absolute; opacity: 0.7; filter: brightness(0.6); }
        canvas { position: absolute; top:0; left:0; z-index: 10; }
        
        .list { grid-row: 1 / 3; background: var(--panel); border: 1px solid #111; padding: 15px; overflow-y: auto; border-left: 2px solid var(--p); }
        .card { background: rgba(255,255,255,0.01); border: 1px solid #1a1a1a; padding: 10px; margin-bottom: 8px; cursor: pointer; }
        .card:hover { background: rgba(0,255,255,0.1); border-color: var(--p); }
        
        .inspector { background: #000; border: 1px solid #222; border-top: 2px solid var(--p); padding: 10px; }
        #i-img { width: 100%; aspect-ratio: 1; object-fit: cover; border: 1px solid #333; margin-bottom: 10px; display: none; }
        
        .watchlist-panel { background: #05080a; border: 1px solid #1a2025; border-top: 2px solid #ff00ff; padding: 10px; display: flex; flex-direction: column; }
        .watch-input-group { display: flex; gap: 5px; margin-bottom: 10px; }
        input { background: #000; border: 1px solid #333; color: var(--p); padding: 5px; flex: 1; font-family: inherit; font-size: 11px; outline: none; }
        .add-btn { background: #ff00ff; color: #000; border: none; padding: 5px 10px; cursor: pointer; font-weight: bold; }
        
        .watch-item { font-size: 10px; padding: 6px; border-bottom: 1px solid #111; display: flex; justify-content: space-between; color: #ff00ff; font-family: 'Courier New', monospace; }
        .watch-item span { color: #555; }

        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-thumb { background: var(--p); }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ TACTICAL_MONITOR_V6.5 ]</div>
        <div id="sim-status" style="font-size: 10px; opacity: 0.5;">UPLINK_STABLE</div>
    </header>

    <div class="grid">
        <div class="map-wrapper"><div id="map-bg"></div><canvas id="cv" width="512" height="512"></canvas></div>
        <div class="list" id="feed"></div>
        
        <div class="inspector">
            <div id="inspect-ui" style="display:none;">
                <img id="i-img" src="" onload="this.style.display='block'">
                <div id="i-name" style="font-weight:bold; color:#fff;">---</div>
                <div id="i-time" style="font-size:11px; color:var(--p);">---</div>
                <button id="i-btn" style="width:100%; margin-top:10px; padding:8px; background:var(--p); border:none; cursor:pointer; font-weight:bold;">WEB PROFILE</button>
            </div>
        </div>

        <div class="watchlist-panel">
            <div style="font-size:10px; color:#ff00ff; margin-bottom:5px; font-weight:bold;">// GLOBAL_WATCHLIST</div>
            <div class="watch-input-group">
                <input type="text" id="watch-uuid" placeholder="Avatar UUID...">
                <button class="add-btn" onclick="addWatch()">ADD</button>
            </div>
            <div id="watch-list" style="overflow-y:auto; flex:1;"></div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const colors = ["#00ffff", "#ff00ff", "#00ff9f", "#ffff00"];
        let selectedKey = null;

        async function addWatch() {
            const uuid = document.getElementById('watch-uuid').value.trim();
            if(uuid.length < 32) return;
            await fetch('/watch', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({uuid})
            });
            document.getElementById('watch-uuid').value = "";
            update(); // Forcer la mise à jour visuelle
        }

        function showInspect(av) {
            selectedKey = av.key;
            document.getElementById('inspect-ui').style.display = 'block';
            document.getElementById('i-name').innerText = av.name.toUpperCase();
            document.getElementById('i-img').src = `https://my-secondlife-p01.s3.amazonaws.com/users/${av.key.replace(/-/g, '_')}/thumb_sl_image.png`;
            
            const urlName = av.name.toLowerCase().split(' ');
            const path = (urlName[1] === 'resident') ? urlName[0] : urlName.join('.');
            document.getElementById('i-btn').onclick = () => window.open(`https://my.secondlife.com/${path}`, '_blank');
        }

        async function update() {
            try {
                const r = await fetch('/api');
                const d = await r.json();
                
                document.getElementById('sim-status').innerText = "REGION: " + d.region;
                document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
                
                ctx.clearRect(0,0,512,512);
                const feed = document.getElementById('feed'); feed.innerHTML = "";
                
                // Agents locaux
                d.avatars.forEach((av, i) => {
                    const color = colors[i % colors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);
                    const timeS = Math.floor(Date.now()/1000 - av.start_time);
                    if(selectedKey === av.key) document.getElementById('i-time').innerText = Math.floor(timeS/60) + "m " + (timeS%60) + "s";
                    ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x,y,6,0,7); ctx.stroke();
                    const card = document.createElement('div');
                    card.className = "card"; card.onclick = () => showInspect(av);
                    card.innerHTML = `<b style="color:${color}">${av.name}</b><br><small>${Math.floor(timeS/60)}m active</small>`;
                    feed.appendChild(card);
                });

                // Watchlist (Affichage des UUID enregistrés)
                const wList = document.getElementById('watch-list');
                wList.innerHTML = "";
                Object.keys(d.watchlist).forEach(uuid => {
                    const item = document.createElement('div');
                    item.className = "watch-item";
                    item.innerHTML = `ID: ${uuid.substring(0,18)}... <span>[TRACKING]</span>`;
                    wList.appendChild(item);
                });

            } catch(e){}
        }
        setInterval(update, 3000);
    </script>
</body>
</html>
"""

@app.route('/api', methods=['GET', 'POST'])
def handle():
    global db, times
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True)
            if not data: return "OK", 200
            db["region"] = data.get("region", "UNK")
            db["coords"] = data.get("grid_coords", {"x":0, "y":0})
            now = time.time()
            active = []
            for av in data.get("avatars", []):
                uid = av.get("key")
                if uid:
                    if uid not in times: times[uid] = now
                    av["start_time"] = times[uid]
                    active.append(av)
            db["avatars"] = active
            return "OK", 200
        except: return "ERR", 500
    return jsonify({**db, "watchlist": watchlist})

@app.route('/watch', methods=['POST'])
def add_watch():
    data = request.get_json(silent=True)
    uid = data.get("uuid")
    if uid:
        watchlist[uid] = {"online": False, "start": time.time()}
    return "OK"

@app.route('/')
def home(): return render_template_string(HTML_CODE)
