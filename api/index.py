from flask import Flask, request, jsonify, render_template_string
import time
import requests

app = Flask(__name__)

db = {
    "region": "TACTICAL_NET_ACTIVE...",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
times = {}
watchlist = {} # Stocke {uuid: {"start": timestamp, "status": bool}}

HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TACTICAL_HUD // NOX_V6.2</title>
    <style>
        :root { --p: #00ffff; --bg: #010103; --panel: #05050a; --font: 'Fira Code', monospace; }
        body { background: var(--bg); color: #a0c0c0; font-family: var(--font); margin: 0; padding: 15px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { border-bottom: 2px solid var(--p); background: rgba(0,255,255,0.02); padding: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; }
        
        .grid { display: grid; grid-template-columns: 512px 1fr 300px; grid-template-rows: 1fr 250px; gap: 15px; flex: 1; overflow: hidden; }

        /* Colonnes Standard */
        .map-wrapper { grid-row: 1 / 3; width: 512px; height: 512px; border: 1px solid #222; background: #000; position: relative; }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.7; filter: brightness(0.6); }
        canvas { position: absolute; top:0; left:0; z-index: 10; }
        
        .list { grid-row: 1 / 3; background: var(--panel); border: 1px solid #111; padding: 15px; overflow-y: auto; border-left: 2px solid var(--p); }
        .card { background: rgba(255,255,255,0.01); border: 1px solid #1a1a1a; padding: 10px; margin-bottom: 8px; cursor: pointer; }

        /* Inspecteur */
        .inspector { background: #000; border: 1px solid #222; border-top: 2px solid var(--p); display: flex; flex-direction: column; }
        
        /* Watchlist (Bas Droite) */
        .watchlist-panel { background: #05080a; border: 1px solid #1a2025; border-top: 2px solid #ff00ff; padding: 10px; display: flex; flex-direction: column; }
        .watch-input-group { display: flex; gap: 5px; margin-bottom: 10px; }
        input { background: #000; border: 1px solid #333; color: var(--p); padding: 5px; flex: 1; font-family: inherit; font-size: 11px; }
        .add-btn { background: #ff00ff; color: #000; border: none; padding: 5px 10px; cursor: pointer; font-weight: bold; }
        
        .watch-item { font-size: 11px; padding: 5px; border-bottom: 1px solid #111; display: flex; justify-content: space-between; align-items: center; }
        .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 5px; }
        .online { background: #00ff00; box-shadow: 0 0 5px #00ff00; }
        .offline { background: #ff0000; opacity: 0.3; }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ TACTICAL_MONITOR_V6.2 ]</div>
    </header>

    <div class="grid">
        <div class="map-wrapper"><div id="map-bg"></div><canvas id="cv" width="512" height="512"></canvas></div>
        
        <div class="list" id="feed"></div>

        <div class="inspector">
            <div id="inspect-ui" style="display:none; padding:10px;">
                <img id="i-img" src="" style="width:100%; aspect-ratio:1; object-fit:cover; margin-bottom:10px;">
                <div style="font-size:12px; color:#fff; font-weight:bold;" id="i-name">---</div>
                <div style="font-size:10px; color:var(--p)" id="i-time">---</div>
                <button id="i-btn" style="width:100%; margin-top:10px; padding:8px; cursor:pointer;">PROFIL WEB</button>
            </div>
        </div>

        <div class="watchlist-panel">
            <div style="font-size:10px; color:#ff00ff; margin-bottom:8px; letter-spacing:1px;">// GLOBAL_WATCHLIST</div>
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
            const uuid = document.getElementById('watch-uuid').value;
            if(uuid.length < 32) return;
            await fetch('/watch', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({uuid})
            });
            document.getElementById('watch-uuid').value = "";
        }

        function showInspect(av) {
            selectedKey = av.key;
            document.getElementById('inspect-ui').style.display = 'block';
            document.getElementById('i-name').innerText = av.name.toUpperCase();
            document.getElementById('i-img').src = `https://my-secondlife-p01.s3.amazonaws.com/users/${av.key.replace(/-/g, '_')}/thumb_sl_image.png`;
            
            const urlName = av.name.toLowerCase().replace(/ /g, '.');
            document.getElementById('i-btn').onclick = () => window.open(`https://my.secondlife.com/${urlName.replace('.resident','')}`, '_blank');
        }

        async function update() {
            try {
                const r = await fetch('/api');
                const d = await r.json();
                
                // Update Map & Local Avatars
                document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
                ctx.clearRect(0,0,512,512);
                const feed = document.getElementById('feed'); feed.innerHTML = "";
                
                d.avatars.forEach((av, i) => {
                    const color = colors[i % colors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);
                    const timeS = Math.floor(Date.now()/1000 - av.start_time);
                    if(selectedKey === av.key) document.getElementById('i-time').innerText = Math.floor(timeS/60) + "m " + (timeS%60) + "s";
                    
                    ctx.strokeStyle = color; ctx.beginPath(); ctx.arc(x,y,6,0,7); ctx.stroke();
                    const card = document.createElement('div');
                    card.className = "card"; card.onclick = () => showInspect(av);
                    card.innerHTML = `<b style="color:${color}">${av.name}</b><br><small>${Math.floor(timeS/60)}m</small>`;
                    feed.appendChild(card);
                });

                // Update Watchlist UI
                const wList = document.getElementById('watch-list');
                wList.innerHTML = "";
                Object.keys(d.watchlist).forEach(uuid => {
                    const info = d.watchlist[uuid];
                    const item = document.createElement('div');
                    item.className = "watch-item";
                    const timeStr = info.online ? Math.floor((Date.now()/1000 - info.start)/60) + "m" : "OFFLINE";
                    item.innerHTML = `
                        <span><span class="dot ${info.online ? 'online' : 'offline'}"></span>${uuid.substring(0,8)}</span>
                        <span style="color:${info.online ? '#00ff00' : '#444'}">${timeStr}</span>
                    `;
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
    global db, times, watchlist
    if request.method == 'POST':
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
        
        # Background check watchlist status
        for uuid in list(watchlist.keys()):
            # Appel API Second Life pour le statut online
            try:
                # Utilisation d'un service public de tracking SL ou simulation ici
                # Pour un vrai tracking, on utilise souvent l'URL de profil my.sl
                is_on = "online" in requests.get(f"http://world.secondlife.com/resident/{uuid}").text.lower()
                if is_on and not watchlist[uuid]["online"]:
                    watchlist[uuid]["start"] = time.time()
                watchlist[uuid]["online"] = is_on
            except: pass

        return "OK", 200
    
    # On renvoie tout au HUD
    return jsonify({**db, "watchlist": watchlist})

@app.route('/watch', methods=['POST'])
def add_watch():
    uuid = request.json.get("uuid")
    if uuid and uuid not in watchlist:
        watchlist[uuid] = {"online": False, "start": time.time()}
    return "OK"

@app.route('/')
def home(): return render_template_string(HTML_CODE)
