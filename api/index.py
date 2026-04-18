from flask import Flask, request, jsonify, render_template_string
import time
from datetime import datetime
import urllib.request

app = Flask(__name__)

db = {"region": "UPLINK_STABLE", "coords": {"x": 0, "y": 0}, "avatars": []}
times = {}      
watchlist = {} 

HTML_CODE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>NOX_TACTICAL_V7.5</title>
    <style>
        :root { --p: #00ffff; --bg: #010103; --panel: #05050a; --font: 'Fira Code', monospace; }
        body { background: var(--bg); color: #a0c0c0; font-family: var(--font); margin: 0; padding: 15px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        
        header { border-bottom: 2px solid var(--p); background: rgba(0,255,255,0.02); padding: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        
        /* Layout Principal */
        .grid { display: grid; grid-template-columns: 1fr auto; grid-template-rows: 512px 1fr; gap: 15px; flex: 1; overflow: hidden; }

        .map-wrapper { grid-column: 1; grid-row: 1; border: 1px solid #222; background: #000; position: relative; width: 512px; height: 512px; }
        #map-bg { width: 100%; height: 100%; background-size: cover; position: absolute; opacity: 0.6; filter: brightness(0.5); }
        canvas { position: absolute; top:0; left:0; z-index: 10; cursor: crosshair; }

        /* Colonne de droite ÉTIRABLE */
        .right-panel { 
            grid-column: 2; grid-row: 1 / 3; 
            display: flex; flex-direction: column; gap: 15px; 
            overflow: hidden; 
            min-width: 250px; max-width: 800px;
            width: 350px; /* Largeur par défaut */
            resize: horizontal; 
            direction: rtl; /* Place la poignée de redimensionnement à gauche */
            border-left: 2px solid #222;
            padding-left: 10px;
        }
        .right-panel > * { direction: ltr; } /* Remet le texte dans le bon sens */

        .list { flex: 1; background: var(--panel); border: 1px solid #111; padding: 15px; overflow-y: auto; border-left: 2px solid var(--p); }
        
        .card { background: rgba(255,255,255,0.01); border: 1px solid #1a1a1a; padding: 10px; margin-bottom: 5px; cursor: pointer; position: relative; }
        .card:hover { border-color: var(--p); background: rgba(0,255,255,0.05); }
        .card.selected { border-left: 4px solid var(--p); background: rgba(0,255,255,0.1); }
        
        .quick-add { position: absolute; right: 10px; top: 10px; background: #ff00ff; color: #000; border: none; padding: 2px 8px; font-weight: bold; font-size: 10px; cursor: pointer; }
        
        .watchlist-panel { grid-column: 1; grid-row: 2; background: #05080a; border: 1px solid #1a2025; border-top: 2px solid #ff00ff; padding: 10px; display: flex; flex-direction: column; overflow: hidden; }
        
        .w-table { width: 100%; border-collapse: collapse; font-size: 10px; table-layout: fixed; }
        .w-table th { text-align: left; color: #ff00ff; border-bottom: 1px solid #222; padding: 5px; font-size: 9px; }
        .w-table td { padding: 5px; border-bottom: 1px solid #111; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .inspector { background: #000; border: 1px solid #222; padding: 15px; min-height: 120px; border-top: 2px solid var(--p); display: flex; }
        #i-img { width: 80px; height: 80px; border: 1px solid #333; margin-right: 15px; flex-shrink: 0; }
        
        .timer-badge { color: var(--p); font-size: 10px; background: rgba(0,255,255,0.1); padding: 2px 5px; border-radius: 3px; }
        input { background: #000; border: 1px solid #333; color: var(--p); padding: 5px; font-family: inherit; width: 120px; }

        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-thumb { background: #333; }
        ::-webkit-scrollbar-thumb:hover { background: var(--p); }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ NOX_TACTICAL_V7.5 ]</div>
        <div id="sim-status" style="font-size: 10px; opacity: 0.5;">UPLINK_READY</div>
    </header>

    <div class="grid">
        <div class="map-wrapper"><div id="map-bg"></div><canvas id="cv" width="512" height="512"></canvas></div>
        
        <div class="right-panel">
            <div class="inspector">
                <div id="inspect-ui" style="display:none; width:100%; overflow:hidden;">
                    <img id="i-img" src="">
                    <div style="display:inline-block; vertical-align:top;">
                        <div id="i-name" style="font-weight:bold; color:#fff; font-size:16px; margin-bottom:5px; white-space:nowrap;">---</div>
                        <div id="i-time" style="font-size:11px; color:var(--p); margin-bottom:10px;">---</div>
                        <button id="i-btn" style="padding:4px 12px; background:var(--p); border:none; cursor:pointer; font-weight:bold; font-size:10px;">PROFIL</button>
                    </div>
                </div>
                <div id="inspect-none" style="text-align:center; width:100%; opacity:0.2; font-size:10px; margin-top:35px;">TARGET_SCANNER_IDLE</div>
            </div>
            <div class="list" id="feed"></div>
        </div>

        <div class="watchlist-panel">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div style="font-size:10px; color:#ff00ff; font-weight:bold;">// DATA_LOGS</div>
                <div>
                    <input type="text" id="watch-uuid" placeholder="UUID...">
                    <button onclick="addWatchManual()" style="background:#ff00ff; border:none; padding:5px 10px; font-size:10px; cursor:pointer; font-weight:bold;">TRACK</button>
                </div>
            </div>
            <div style="overflow-y:auto; flex:1;">
                <table class="w-table">
                    <colgroup>
                        <col style="width: 40%;">
                        <col style="width: 15%;">
                        <col style="width: 15%;">
                        <col style="width: 15%;">
                        <col style="width: 15%;">
                    </colgroup>
                    <thead>
                        <tr><th>AGENT / UUID</th><th>STATUS</th><th>ARRIVE</th><th>DEPART</th><th>DEL</th></tr>
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
            return Math.floor(diff/60) + "m " + (diff % 60) + "s";
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
                        document.getElementById('i-time').innerText = "SESSION: " + formatDuration(av.start_time);
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
                                  <small style="font-size:9px; opacity:0.3">${av.key}</small>
                                  <button class="quick-add" onclick="addToWatch('${av.key}', '${av.name}')">+ LOG</button>`;
                feed.appendChild(card);
            });

            const wBody = document.getElementById('watch-list-body');
            wBody.innerHTML = "";
            Object.keys(d.watchlist).forEach(uuid => {
                const info = d.watchlist[uuid];
                const row = document.createElement('tr');
                let c = info.online ? "#00ff00" : "#ff4444";
                row.innerHTML = `<td><b>${info.name || 'Unknown'}</b><br><small style="font-size:8px;opacity:0.3">${uuid}</small></td>
                                 <td style="color:${c}; font-weight:bold;">${info.online ? 'ON' : 'OFF'}</td>
                                 <td style="color:#aaa">${info.arr || '--:--'}</td>
                                 <td style="color:#aaa">${info.dep || '--:--'}</td>
                                 <td><button onclick="removeWatch('${uuid}')" style="background:none; border:1px solid #411; color:#f44; cursor:pointer;">X</button></td>`;
                wBody.appendChild(row);
            });
        }

        setInterval(fetchData, 2000);
        draw();
    </script>
</body>
</html>
"""

# ... LE RESTE DU CODE PYTHON (API) EST LE MÊME QUE LA V7.4 ...
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
            for w_uid in list(watchlist.keys()):
                try:
                    url = f"http://world.secondlife.com/resident/{w_uid}"
                    with urllib.request.urlopen(url, timeout=1) as f:
                        content = f.read().decode('utf-8').lower()
                        is_on = "online" in content and "offline" not in content
                        if w_uid in uids_present: is_on = True
                        if is_on and not watchlist[w_uid]["online"]:
                            watchlist[w_uid]["arr"] = dt_now
                        elif not is_on and watchlist[w_uid]["online"]:
                            watchlist[w_uid]["dep"] = dt_now
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
