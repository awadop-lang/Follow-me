from flask import Flask, request, jsonify, render_template_string
import time
from datetime import datetime
import urllib.request

app = Flask(__name__)

# Stockage des données
db = {"region": "UPLINK_STABLE", "coords": {"x": 0, "y": 0}, "avatars": []}
times = {}      
watchlist = {} # {uuid: {"name": str, "online": bool, "arr": str, "dep": str}}

HTML_CODE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>NOX_TACTICAL_V7.4</title>
    <style>
        :root { --p: #00ffff; --bg: #010103; --panel: #05050a; --font: 'Fira Code', monospace; }
        body { background: var(--bg); color: #a0c0c0; font-family: var(--font); margin: 0; padding: 15px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { border-bottom: 2px solid var(--p); background: rgba(0,255,255,0.02); padding: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .grid { display: grid; grid-template-columns: 512px 1fr; grid-template-rows: 512px 1fr; gap: 15px; flex: 1; overflow: hidden; }
        .map-wrapper { grid-column: 1; grid-row: 1; border: 1px solid #222; background: #000; position: relative; }
        #map-bg { width: 100%; height: 100%; background-size: cover; position: absolute; opacity: 0.6; filter: brightness(0.5); }
        canvas { position: absolute; top:0; left:0; z-index: 10; cursor: crosshair; }
        .right-panel { grid-column: 2; grid-row: 1 / 3; display: flex; flex-direction: column; gap: 15px; overflow: hidden; }
        .list { flex: 1; background: var(--panel); border: 1px solid #111; padding: 15px; overflow-y: auto; border-left: 2px solid var(--p); }
        .card { background: rgba(255,255,255,0.01); border: 1px solid #1a1a1a; padding: 10px; margin-bottom: 5px; cursor: pointer; position: relative; }
        .card:hover { border-color: var(--p); background: rgba(0,255,255,0.05); }
        .card.selected { border-left: 4px solid var(--p); background: rgba(0,255,255,0.1); }
        .quick-add { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); background: #ff00ff; color: #000; border: none; padding: 2px 8px; font-weight: bold; font-size: 10px; cursor: pointer; border-radius: 2px; }
        .watchlist-panel { grid-column: 1; grid-row: 2; background: #05080a; border: 1px solid #1a2025; border-top: 2px solid #ff00ff; padding: 10px; display: flex; flex-direction: column; }
        .w-table { width: 100%; border-collapse: collapse; font-size: 10px; }
        .w-table th { text-align: left; color: #ff00ff; border-bottom: 1px solid #222; padding: 5px; font-size: 9px; }
        .w-table td { padding: 5px; border-bottom: 1px solid #111; white-space: nowrap; }
        .del-btn { color: #ff4444; cursor: pointer; border: 1px solid #411; padding: 1px 6px; font-size: 10px; }
        .inspector { background: #000; border: 1px solid #222; padding: 15px; min-height: 120px; border-top: 2px solid var(--p); display: flex; }
        #i-img { width: 90px; height: 90px; border: 1px solid #333; margin-right: 15px; }
        .timer-badge { color: var(--p); font-size: 10px; background: rgba(0,255,255,0.1); padding: 2px 5px; border-radius: 3px; }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ NOX_LOGGER_V7.4 ]</div>
        <div id="sim-status" style="font-size: 10px; opacity: 0.5;">UPLINK_STABLE</div>
    </header>

    <div class="grid">
        <div class="map-wrapper"><div id="map-bg"></div><canvas id="cv" width="512" height="512"></canvas></div>
        <div class="right-panel">
            <div class="inspector">
                <div id="inspect-ui" style="display:none; width:100%;">
                    <img id="i-img" src="">
                    <div style="display:inline-block; vertical-align:top;">
                        <div id="i-name" style="font-weight:bold; color:#fff; font-size:18px; margin-bottom:5px;">---</div>
                        <div id="i-time" style="font-size:11px; color:var(--p); margin-bottom:10px;">---</div>
                        <button id="i-btn" style="padding:5px 20px; background:var(--p); border:none; cursor:pointer; font-weight:bold; font-size:11px; color:#000;">PROFILE</button>
                    </div>
                </div>
                <div id="inspect-none" style="text-align:center; width:100%; opacity:0.2; font-size:10px; margin-top:35px;">MONITORING_ACTIVE</div>
            </div>
            <div class="list" id="feed"></div>
        </div>

        <div class="watchlist-panel">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div style="font-size:10px; color:#ff00ff; font-weight:bold;">// LOGS_WATCHLIST</div>
                <div>
                    <input type="text" id="watch-uuid" style="background:#000; border:1px solid #333; color:var(--p); padding:3px; font-size:10px;" placeholder="UUID...">
                    <button onclick="addWatchManual()" style="background:#ff00ff; border:none; padding:3px 10px; font-size:10px; cursor:pointer;">ADD</button>
                </div>
            </div>
            <div style="overflow-y:auto; flex:1;">
                <table class="w-table">
                    <thead>
                        <tr><th>AGENT</th><th>STATUS</th><th>ARRIVE (UTC)</th><th>DEPART (UTC)</th><th>X</th></tr>
                    </thead>
                    <tbody id="watch-list-body"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const colors = ["#00ffff", "#ff00ff", "#00ff9f", "#ffff00"];
        let selectedKey = null;
        let lastData = null;
        let pulseVal = 0;

        function formatDuration(start) {
            const diff = Math.floor(Date.now()/1000 - start);
            const m = Math.floor(diff/60);
            const s = diff % 60;
            return m + "m " + s + "s";
        }

        async function addToWatch(uuid, name) {
            await fetch('/watch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({uuid, name}) });
            fetchData();
        }

        async function addWatchManual() {
            const uuid = document.getElementById('watch-uuid').value.trim();
            if(uuid.length < 30) return;
            await addToWatch(uuid, "");
            document.getElementById('watch-uuid').value = "";
        }

        async function removeWatch(uuid) {
            await fetch('/unwatch', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({uuid}) });
            fetchData();
        }

        function showInspect(av) {
            selectedKey = av.key;
            document.getElementById('inspect-none').style.display = 'none';
            document.getElementById('inspect-ui').style.display = 'block';
            document.getElementById('i-name').innerText = av.name.toUpperCase();
            document.getElementById('i-img').src = `https://my-secondlife-p01.s3.amazonaws.com/users/${av.key.replace(/-/g, '_')}/thumb_sl_image.png`;
            const n = av.name.toLowerCase().split(' ');
            const p = (n[1] === 'resident') ? n[0] : n.join('.');
            document.getElementById('i-btn').onclick = () => window.open(`https://my.secondlife.com/${p}`, '_blank');
        }

        function draw() {
            if (lastData) {
                ctx.clearRect(0,0,512,512);
                pulseVal += 0.15;
                lastData.avatars.forEach((av, i) => {
                    const color = colors[i % colors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);
                    if (selectedKey === av.key) {
                        const s = 8 + Math.sin(pulseVal) * 4;
                        ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(x,y, s, 0, Math.PI*2); ctx.stroke();
                        ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x,y, 4, 0, Math.PI*2); ctx.fill();
                        document.getElementById('i-time').innerText = "PRESENCE: " + formatDuration(av.start_time);
                    } else {
                        ctx.globalAlpha = selectedKey ? 0.2 : 0.8;
                        ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x,y, 5, 0, Math.PI*2); ctx.fill();
                        ctx.globalAlpha = 1.0;
                    }
                });
            }
            requestAnimationFrame(draw);
        }

        async function fetchData() {
            try {
                const r = await fetch('/api');
                const d = await r.json();
                lastData = d;
                renderUI(d);
            } catch(e){}
        }

        function renderUI(d) {
            document.getElementById('sim-status').innerText = "REGION: " + d.region;
            document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
            
            const feed = document.getElementById('feed');
            feed.innerHTML = "";
            d.avatars.forEach((av, i) => {
                const card = document.createElement('div');
                card.className = "card" + (selectedKey === av.key ? " selected" : "");
                card.onclick = (e) => { if(e.target.tagName !== 'BUTTON') showInspect(av); };
                card.innerHTML = `<b style="color:${colors[i%colors.length]}">${av.name}</b> 
                                  <span class="timer-badge">${formatDuration(av.start_time)}</span><br>
                                  <small style="opacity:0.5">Online Now</small>
                                  <button class="quick-add" onclick="addToWatch('${av.key}', '${av.name}')">+ TRACK</button>`;
                feed.appendChild(card);
            });

            const wBody = document.getElementById('watch-list-body');
            wBody.innerHTML = "";
            Object.keys(d.watchlist).forEach(uuid => {
                const info = d.watchlist[uuid];
                const row = document.createElement('tr');
                let c = info.online ? "#00ff00" : "#ff4444";
                row.innerHTML = `<td><b>${info.name || 'Unknown'}</b></td>
                                 <td style="color:${c}; font-weight:bold;">${info.online ? 'ONLINE' : 'OFFLINE'}</td>
                                 <td style="color:#aaa">${info.arr || '--:--'}</td>
                                 <td style="color:#aaa">${info.dep || '--:--'}</td>
                                 <td><span class="del-btn" onclick="removeWatch('${uuid}')">X</span></td>`;
                wBody.appendChild(row);
            });
        }

        setInterval(fetchData, 2000);
        draw();
    </script>
</body>
</html>
"""

@app.route('/api', methods=['GET', 'POST'])
def handle():
    global db, times, watchlist
    now = time.time()
    dt_now = datetime.now().strftime("%H:%M:%S")
    
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True)
            if not data: return "OK", 200
            db["region"] = data.get("region", "UNK")
            db["coords"] = data.get("grid_coords", {"x":0, "y":0})
            incoming = data.get("avatars", [])
            uids_present = [av.get("key") for av in incoming]
            
            # Nettoyage présence locale
            for uid in list(times.keys()):
                if uid not in uids_present: del times[uid]
            
            active_list = []
            for av in incoming:
                uid = av.get("key")
                if uid:
                    if uid not in times: times[uid] = now
                    av["start_time"] = times[uid]
                    active_list.append(av)
                    if uid in watchlist: watchlist[uid]["name"] = av.get("name", "Unknown")
            db["avatars"] = active_list
            
            # Update Watchlist Log
            for w_uid in list(watchlist.keys()):
                try:
                    url = f"http://world.secondlife.com/resident/{w_uid}"
                    with urllib.request.urlopen(url, timeout=1) as f:
                        content = f.read().decode('utf-8').lower()
                        is_on = "online" in content and "offline" not in content
                        if w_uid in uids_present: is_on = True
                        
                        # Détection changement de statut pour log
                        if is_on and not watchlist[w_uid]["online"]:
                            watchlist[w_uid]["arr"] = dt_now # Arrivée
                        elif not is_on and watchlist[w_uid]["online"]:
                            watchlist[w_uid]["dep"] = dt_now # Départ
                            
                        watchlist[w_uid]["online"] = is_on
                except: pass
            return "OK", 200
        except: return "ERR", 500
    return jsonify({**db, "watchlist": watchlist})

@app.route('/watch', methods=['POST'])
def add_watch():
    data = request.get_json(silent=True)
    uid = data.get("uuid"); name = data.get("name", "")
    if uid and uid not in watchlist:
        watchlist[uid] = {"name": name, "online": False, "arr": "", "dep": ""}
    return "OK"

@app.route('/unwatch', methods=['POST'])
def unwatch():
    data = request.get_json(silent=True)
    uid = data.get("uuid")
    if uid in watchlist: del watchlist[uid]
    return "OK"

@app.route('/')
def home(): return render_template_string(HTML_CODE)
