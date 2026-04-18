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
    <title>NOX_TACTICAL_V7.7</title>
    <style>
        :root { --p: #00ffff; --bg: #010103; --panel: #05050a; --font: 'Fira Code', monospace; }
        body { background: var(--bg); color: #a0c0c0; font-family: var(--font); margin: 0; padding: 15px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        
        header { border-bottom: 2px solid var(--p); background: rgba(0,255,255,0.02); padding: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
        
        /* Layout */
        .main-container { display: flex; flex: 1; overflow: hidden; border: 1px solid #222; background: #000; }

        /* Zone Gauche */
        .left-zone { display: flex; flex-direction: column; flex: 1; min-width: 512px; overflow: hidden; }
        .map-wrapper { width: 512px; height: 512px; background: #000; position: relative; flex-shrink: 0; border-right: 1px solid #222; }
        #map-bg { width: 100%; height: 100%; background-size: cover; position: absolute; opacity: 0.6; filter: brightness(0.4); }
        canvas { position: absolute; top:0; left:0; z-index: 10; cursor: crosshair; }

        .watchlist-panel { flex: 1; background: #05080a; border-top: 2px solid #ff00ff; padding: 10px; display: flex; flex-direction: column; overflow: hidden; }

        /* Resizer (Poignée) */
        .resizer { width: 12px; background: #0a0a0f; cursor: col-resize; transition: background 0.2s; z-index: 100; border-left: 1px solid #222; border-right: 1px solid #222; display: flex; align-items: center; justify-content: center; }
        .resizer:hover { background: #1a1a25; border-color: var(--p); }
        .resizer::after { content: "⋮"; color: #444; font-size: 18px; }

        /* Zone Droite (Extensible) */
        .right-zone { 
            width: 400px; 
            min-width: 150px; 
            max-width: 90vw; /* Permet d'occuper presque tout l'écran */
            display: flex; 
            flex-direction: column; 
            background: var(--bg); 
            overflow: hidden; 
        }
        
        .inspector { background: #000; border-bottom: 1px solid #222; padding: 15px; min-height: 110px; flex-shrink: 0; display: flex; }
        #i-img { width: 70px; height: 70px; border: 1px solid #333; margin-right: 15px; }
        
        /* Liste avec Slider (Scrollbar) */
        .list { 
            flex: 1; 
            background: var(--panel); 
            padding: 10px; 
            overflow-y: auto; /* Active le scroll si ça déborde */
            scrollbar-width: thin; /* Pour Firefox */
            scrollbar-color: var(--p) #000;
        }
        
        /* Style du Slider (Webkit) */
        .list::-webkit-scrollbar { width: 6px; }
        .list::-webkit-scrollbar-track { background: #000; }
        .list::-webkit-scrollbar-thumb { background: #222; border-radius: 10px; border: 1px solid #111; }
        .list::-webkit-scrollbar-thumb:hover { background: var(--p); }

        .card { background: rgba(255,255,255,0.01); border: 1px solid #1a1a1a; padding: 12px; margin-bottom: 6px; cursor: pointer; position: relative; transition: 0.2s; }
        .card:hover { border-color: #444; background: rgba(255,255,255,0.03); }
        .card.selected { border-left: 4px solid var(--p); background: rgba(0,255,255,0.08); border-color: var(--p); }
        
        .quick-add { position: absolute; right: 10px; top: 12px; background: #ff00ff; color: #000; border: none; padding: 3px 8px; font-weight: bold; font-size: 9px; cursor: pointer; border-radius: 2px; }
        
        .w-table { width: 100%; border-collapse: collapse; font-size: 10px; }
        .w-table th { text-align: left; color: #ff00ff; border-bottom: 1px solid #222; padding: 5px; opacity: 0.7; }
        .w-table td { padding: 6px 5px; border-bottom: 1px solid #111; }
        
        .timer-badge { color: var(--p); font-size: 10px; background: rgba(0,255,255,0.1); padding: 2px 6px; border-radius: 2px; border: 1px solid rgba(0,255,255,0.2); }
        input { background: #000; border: 1px solid #333; color: var(--p); padding: 6px; width: 140px; font-family: inherit; font-size: 11px; }
        button.add-manual { background: #ff00ff; border: none; color: #000; padding: 6px 12px; font-weight: bold; font-size: 11px; cursor: pointer; }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ NOX_CORE_V7.7 ]</div>
        <div id="sim-status" style="font-size: 10px; opacity: 0.4; font-family: monospace;">SYSTEM_OPERATIONAL</div>
    </header>

    <div class="main-container">
        <div class="left-zone">
            <div class="map-wrapper"><div id="map-bg"></div><canvas id="cv" width="512" height="512"></canvas></div>
            <div class="watchlist-panel">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <span style="font-size:10px; color:#ff00ff; font-weight:bold; letter-spacing:1px;">// TARGET_HISTORY</span>
                    <div>
                        <input type="text" id="watch-uuid" placeholder="PASTE_UUID_HERE">
                        <button class="add-manual" onclick="addWatchManual()">TRACK_TARGET</button>
                    </div>
                </div>
                <div style="overflow-y:auto; flex:1;" class="list">
                    <table class="w-table">
                        <thead><tr><th>IDENTIFIER</th><th>STATUS</th><th>IN</th><th>OUT</th><th>ACTION</th></tr></thead>
                        <tbody id="watch-list-body"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="resizer" id="dragMe"></div>

        <div class="right-zone" id="rightSide">
            <div class="inspector">
                <div id="inspect-ui" style="display:none; width:100%;">
                    <img id="i-img" src="">
                    <div style="display:inline-block; vertical-align:top;">
                        <div id="i-name" style="font-weight:bold; color:#fff; font-size:16px; margin-bottom:4px;">---</div>
                        <div id="i-time" style="font-size:11px; color:var(--p); margin-bottom:8px; font-family:monospace;">---</div>
                        <button id="i-btn" style="padding:5px 15px; background:var(--p); border:none; cursor:pointer; font-size:10px; font-weight:bold; color:#000;">OPEN_PROFILE</button>
                    </div>
                </div>
                <div id="inspect-none" style="text-align:center; width:100%; opacity:0.2; font-size:10px; margin-top:30px; letter-spacing:2px;">SCANNING...</div>
            </div>
            <div class="list" id="feed">
                </div>
        </div>
    </div>

    <script>
        // --- LOGIQUE RESIZE (AMÉLIORÉE) ---
        const resizer = document.getElementById('dragMe');
        const rightSide = document.getElementById('rightSide');
        let isResizing = false;

        resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            document.body.style.cursor = 'col-resize';
            resizer.style.background = 'var(--p)';
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            const newWidth = window.innerWidth - e.clientX;
            // Limites de sécurité
            if (newWidth > 150 && newWidth < (window.innerWidth - 550)) {
                rightSide.style.width = `${newWidth}px`;
            }
        });

        document.addEventListener('mouseup', () => {
            if(isResizing) {
                isResizing = false;
                document.body.style.cursor = 'default';
                resizer.style.background = '#0a0a0f';
            }
        });

        // --- DATA & RADAR ---
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const colors = ["#00ffff", "#ff00ff", "#00ff9f", "#ffff00", "#ff4444"];
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
                pulseVal += 0.12;
                lastData.avatars.forEach((av, i) => {
                    const color = colors[i % colors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);
                    if (selectedKey === av.key) {
                        const s = 10 + Math.sin(pulseVal) * 5;
                        ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(x,y, s, 0, Math.PI*2); ctx.stroke();
                        ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x,y, 4, 0, Math.PI*2); ctx.fill();
                        document.getElementById('i-time').innerText = "LIVE_SESSION: " + formatDuration(av.start_time);
                    } else {
                        ctx.globalAlpha = selectedKey ? 0.2 : 0.9;
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
            document.getElementById('sim-status').innerText = "LOC: " + d.region.toUpperCase();
            document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
            
            const feed = document.getElementById('feed');
            const scrollPos = feed.scrollTop; // Garde la position du scroll
            feed.innerHTML = "";
            d.avatars.forEach((av, i) => {
                const card = document.createElement('div');
                card.className = "card" + (selectedKey === av.key ? " selected" : "");
                card.onclick = (e) => { if(e.target.tagName !== 'BUTTON') showInspect(av); };
                card.innerHTML = `<b style="color:${colors[i%colors.length]}">${av.name}</b> 
                                  <span class="timer-badge">${formatDuration(av.start_time)}</span><br>
                                  <small style="opacity:0.2; font-size:9px;">${av.key}</small>
                                  <button class="quick-add" onclick="addToWatch('${av.key}', '${av.name}')">LOG</button>`;
                feed.appendChild(card);
            });
            feed.scrollTop = scrollPos;

            const wBody = document.getElementById('watch-list-body');
            wBody.innerHTML = "";
            Object.keys(d.watchlist).forEach(uuid => {
                const info = d.watchlist[uuid];
                const row = document.createElement('tr');
                let c = info.online ? "#00ff00" : "#ff4444";
                row.innerHTML = `<td><b>${info.name || '---'}</b><br><small style="opacity:0.2">${uuid}</small></td>
                                 <td style="color:${c}; font-weight:bold;">${info.online ? 'ONLINE' : 'OFFLINE'}</td>
                                 <td style="color:#888">${info.arr || '--:--'}</td>
                                 <td style="color:#888">${info.dep || '--:--'}</td>
                                 <td><button onclick="removeWatch('${uuid}')" style="background:none; border:1px solid #411; color:#f44; cursor:pointer; padding:2px 6px;">DEL</button></td>`;
                wBody.appendChild(row);
            });
        }
        setInterval(fetchData, 2000);
        draw();
    </script>
</body>
</html>
"""

# ... (Partie API Python identique aux versions précédentes) ...
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
