from flask import Flask, request, jsonify, render_template_string
import time
import urllib.request

app = Flask(__name__)

# --- BASE DE DONNÉES ---
db = {"region": "UPLINK_SEARCHING", "coords": {"x": 0, "y": 0}, "avatars": []}
times = {}      # {uuid: timestamp_entree}
watchlist = {}  # {uuid: {"online": bool, "start": timestamp}}

# --- INTERFACE VISUELLE ---
HTML_CODE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>NOX_TACTICAL_V6.7</title>
    <style>
        :root { --p: #00ffff; --bg: #010103; --panel: #05050a; --font: 'Fira Code', monospace; }
        body { background: var(--bg); color: #a0c0c0; font-family: var(--font); margin: 0; padding: 15px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { border-bottom: 2px solid var(--p); background: rgba(0,255,255,0.02); padding: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .grid { display: grid; grid-template-columns: 512px 1fr 300px; grid-template-rows: 1fr 220px; gap: 15px; flex: 1; overflow: hidden; }
        .map-wrapper { grid-row: 1 / 3; width: 512px; height: 512px; border: 1px solid #222; background: #000; position: relative; }
        #map-bg { width: 100%; height: 100%; background-size: cover; position: absolute; opacity: 0.7; filter: brightness(0.6); }
        canvas { position: absolute; top:0; left:0; z-index: 10; }
        .list { grid-row: 1 / 3; background: var(--panel); border: 1px solid #111; padding: 15px; overflow-y: auto; border-left: 2px solid var(--p); }
        .card { background: rgba(255,255,255,0.01); border: 1px solid #1a1a1a; padding: 10px; margin-bottom: 8px; cursor: pointer; }
        .card:hover { border-color: var(--p); background: rgba(0,255,255,0.05); }
        .inspector { background: #000; border: 1px solid #222; border-top: 2px solid var(--p); padding: 10px; }
        #i-img { width: 100%; aspect-ratio: 1; object-fit: cover; border: 1px solid #333; margin-bottom: 10px; display: none; }
        .watchlist-panel { background: #05080a; border: 1px solid #1a2025; border-top: 2px solid #ff00ff; padding: 10px; display: flex; flex-direction: column; }
        .watch-input-group { display: flex; gap: 5px; margin-bottom: 10px; }
        input { background: #000; border: 1px solid #333; color: var(--p); padding: 5px; flex: 1; font-family: inherit; font-size: 11px; outline: none; }
        .add-btn { background: #ff00ff; color: #000; border: none; padding: 5px 10px; cursor: pointer; font-weight: bold; }
        .watch-item { font-size: 10px; padding: 6px; border-bottom: 1px solid #111; display: flex; justify-content: space-between; align-items: center; }
        .dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ TACTICAL_MONITOR_V6.7 ]</div>
        <div id="sim-status" style="font-size: 10px; opacity: 0.5;">UPLINK_READY</div>
    </header>

    <div class="grid">
        <div class="map-wrapper"><div id="map-bg"></div><canvas id="cv" width="512" height="512"></canvas></div>
        <div class="list" id="feed"></div>
        <div class="inspector">
            <div id="inspect-ui" style="display:none;">
                <img id="i-img" src="" onload="this.style.display='block'">
                <div id="i-name" style="font-weight:bold; color:#fff; font-size:14px;">---</div>
                <div id="i-time" style="font-size:11px; color:var(--p); margin: 5px 0;">---</div>
                <button id="i-btn" style="width:100%; padding:8px; background:var(--p); border:none; cursor:pointer; font-weight:bold; margin-top:5px;">OPEN PROFILE</button>
            </div>
        </div>
        <div class="watchlist-panel">
            <div style="font-size:10px; color:#ff00ff; margin-bottom:8px; font-weight:bold;">// GLOBAL_WATCHLIST</div>
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
            if(uuid.length < 30) return;
            await fetch('/watch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({uuid}) });
            document.getElementById('watch-uuid').value = "";
        }

        function showInspect(av) {
            selectedKey = av.key;
            document.getElementById('inspect-ui').style.display = 'block';
            document.getElementById('i-name').innerText = av.name.toUpperCase();
            document.getElementById('i-img').src = `https://my-secondlife-p01.s3.amazonaws.com/users/${av.key.replace(/-/g, '_')}/thumb_sl_image.png`;
            const n = av.name.toLowerCase().split(' ');
            const p = (n[1] === 'resident') ? n[0] : n.join('.');
            document.getElementById('i-btn').onclick = () => window.open(`https://my.secondlife.com/${p}`, '_blank');
        }

        async function update() {
            try {
                const r = await fetch('/api');
                const d = await r.json();
                document.getElementById('sim-status').innerText = "REGION: " + d.region;
                document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
                
                ctx.clearRect(0,0,512,512);
                const feed = document.getElementById('feed'); feed.innerHTML = "";
                
                d.avatars.forEach((av, i) => {
                    const color = colors[i % colors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);
                    const timeS = Math.floor(Date.now()/1000 - av.start_time);
                    if(selectedKey === av.key) document.getElementById('i-time').innerText = "ACTIVE: " + Math.floor(timeS/60) + "m " + (timeS%60) + "s";
                    ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x,y,6,0,7); ctx.stroke();
                    const card = document.createElement('div');
                    card.className = "card"; card.onclick = () => showInspect(av);
                    card.innerHTML = `<b style="color:${color}">${av.name}</b><br><small>${Math.floor(timeS/60)}m</small>`;
                    feed.appendChild(card);
                });

                const wList = document.getElementById('watch-list'); wList.innerHTML = "";
                Object.keys(d.watchlist).forEach(uuid => {
                    const info = d.watchlist[uuid];
                    const item = document.createElement('div');
                    item.className = "watch-item";
                    let status = "OFFLINE"; let c = "#444";
                    if(info.online) { 
                        status = "ONLINE (" + Math.floor((Date.now()/1000 - info.start)/60) + "m)";
                        c = "#00ff00";
                    }
                    item.innerHTML = `<span><i class="dot" style="background:${c}"></i>${uuid.substring(0,8)}</span><span style="color:${c}">${status}</span>`;
                    wList.appendChild(item);
                });
            } catch(e){}
        }
        setInterval(update, 3000);
    </script>
</body>
</html>
"""

# --- LOGIQUE SERVEUR ---
@app.route('/api', methods=['GET', 'POST'])
def handle():
    global db, times, watchlist
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True)
            if not data: return "OK", 200
            db["region"] = data.get("region", "UNK")
            db["coords"] = data.get("grid_coords", {"x":0, "y":0})
            now = time.time()
            incoming = data.get("avatars", [])
            active_list = []
            uids_present = [av.get("key") for av in incoming]
            
            # Gestion temps d'activité local
            for uid in list(times.keys()):
                if uid not in uids_present: del times[uid]

            for av in incoming:
                uid = av.get("key")
                if uid:
                    if uid not in times: times[uid] = now
                    av["start_time"] = times[uid]
                    active_list.append(av)
            db["avatars"] = active_list

            # Check Global Watchlist status
            for w_uid in list(watchlist.keys()):
                try:
                    url = f"http://world.secondlife.com/resident/{w_uid}"
                    with urllib.request.urlopen(url, timeout=1) as f:
                        is_on = "online" in f.read().decode('utf-8').lower()
                        if is_on and not watchlist[w_uid]["online"]:
                            watchlist[w_uid]["start"] = now
                        watchlist[w_uid]["online"] = is_on
                except: pass
            return "OK", 200
        except: return "ERR", 500
    return jsonify({**db, "watchlist": watchlist})

@app.route('/watch', methods=['POST'])
def add_watch():
    data = request.get_json(silent=True)
    uid = data.get("uuid")
    if uid and uid not in watchlist:
        watchlist[uid] = {"online": False, "start": 0}
    return "OK"

@app.route('/')
def home(): return render_template_string(HTML_CODE)
