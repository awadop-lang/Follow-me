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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NOX_TACTICAL_V7.9</title>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;500&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
    <style>
        :root { 
            --cyan: #00ffff; --magenta: #ff00ff; --bg: #050508; 
            --panel: rgba(10, 12, 18, 0.95); --border: rgba(0, 255, 255, 0.2);
        }

        * { box-sizing: border-box; }
        body { 
            background: var(--bg); 
            color: #c0d0d0; 
            font-family: 'Rajdhani', sans-serif; 
            margin: 0; padding: 15px; height: 100vh; overflow: hidden; 
            display: flex; flex-direction: column;
            background-image: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            background-size: 100% 2px, 3px 100%;
        }

        header { 
            border: 1px solid var(--border); background: var(--panel); 
            padding: 10px 20px; margin-bottom: 10px; 
            display: flex; justify-content: space-between; align-items: center;
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.1); flex-shrink: 0;
        }

        .main-container { display: flex; flex: 1; overflow: hidden; gap: 0; border: 1px solid var(--border); }

        /* GAUCHE */
        .left-zone { display: flex; flex-direction: column; flex: 1; min-width: 532px; overflow: hidden; background: rgba(0,0,0,0.4); }
        .map-wrapper { width: 512px; height: 512px; margin: 10px; background: #000; position: relative; flex-shrink: 0; border: 1px solid #222; }
        #map-bg { width: 100%; height: 100%; background-size: cover; position: absolute; opacity: 0.5; filter: contrast(1.2) brightness(0.6) grayscale(0.5); }
        canvas { position: absolute; top:0; left:0; z-index: 10; cursor: crosshair; }

        .watchlist-panel { flex: 1; background: var(--panel); border-top: 2px solid var(--magenta); padding: 15px; display: flex; flex-direction: column; overflow: hidden; }

        /* RESIZER */
        .resizer { 
            width: 10px; background: #0a0a10; cursor: col-resize; 
            transition: 0.3s; z-index: 100; border-left: 1px solid #222; border-right: 1px solid #222;
            display: flex; align-items: center; justify-content: center;
        }
        .resizer:hover { background: var(--cyan); box-shadow: 0 0 15px var(--cyan); }

        /* DROITE */
        .right-zone { width: 400px; min-width: 250px; max-width: 80vw; display: flex; flex-direction: column; background: var(--panel); overflow: hidden; }
        
        .inspector { 
            background: rgba(0,0,0,0.6); border-bottom: 1px solid var(--border); 
            padding: 15px; min-height: 110px; flex-shrink: 0; display: flex; 
        }
        #i-img { width: 80px; height: 80px; border: 1px solid var(--cyan); margin-right: 15px; }
        
        .list { 
            flex: 1; padding: 10px; overflow-y: auto; 
            scrollbar-width: thin; scrollbar-color: var(--cyan) transparent;
        }
        .list::-webkit-scrollbar { width: 4px; }
        .list::-webkit-scrollbar-thumb { background: var(--cyan); }

        .card { 
            background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255,255,255,0.05); 
            padding: 12px; margin-bottom: 8px; cursor: pointer; position: relative; 
            transition: all 0.2s; font-family: 'Fira Code', monospace;
        }
        .card:hover { border-color: var(--cyan); background: rgba(0, 255, 255, 0.05); }
        .card.selected { border-left: 4px solid var(--cyan); background: rgba(0, 255, 255, 0.1); border-color: var(--cyan); }
        
        .pos-badge { color: var(--magenta); font-size: 10px; background: rgba(255,0,255,0.1); padding: 1px 4px; border-radius: 2px; margin-left: 5px; }

        .w-table { width: 100%; border-collapse: collapse; font-family: 'Fira Code', monospace; font-size: 11px; }
        .w-table th { text-align: left; color: var(--magenta); padding: 8px; border-bottom: 1px solid rgba(255,0,255,0.2); }
        .w-table td { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }

        .timer-badge { color: var(--cyan); font-size: 11px; font-weight: bold; }
        input { background: #000; border: 1px solid var(--border); color: var(--cyan); padding: 8px; font-family: 'Fira Code'; font-size: 11px; outline: none; }
        button.action-btn { background: var(--magenta); border: none; color: #000; padding: 8px 15px; font-weight: bold; cursor: pointer; font-family: 'Rajdhani'; }
    </style>
</head>
<body>
    <header>
        <div>
            <span style="font-size: 20px; font-weight: 700; letter-spacing: 5px; color: var(--cyan); text-shadow: 0 0 10px var(--cyan);">NOX_TACTICAL //</span>
            <span id="region-display" style="font-size: 18px; color: #fff; font-weight: 300; letter-spacing: 2px;">SCANNING...</span>
        </div>
        <div id="sim-status" style="font-size: 12px; color: var(--magenta); font-family: 'Fira Code';">SYSTEM_ACTIVE</div>
    </header>

    <div class="main-container">
        <div class="left-zone">
            <div class="map-wrapper"><div id="map-bg"></div><canvas id="cv" width="512" height="512"></canvas></div>
            <div class="watchlist-panel">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                    <span style="font-size:14px; color:var(--magenta); font-weight:700; letter-spacing:2px;">[ TRACKER_LOGS ]</span>
                    <div>
                        <input type="text" id="watch-uuid" placeholder="TARGET_UUID">
                        <button class="action-btn" onclick="addWatchManual()">ADD_TRACK</button>
                    </div>
                </div>
                <div style="overflow-y:auto; flex:1;" class="list">
                    <table class="w-table">
                        <thead><tr><th>IDENTIFIANT</th><th>STATUS</th><th>IN</th><th>OUT</th><th>OPT</th></tr></thead>
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
                        <div id="i-name" style="font-weight:700; color:#fff; font-size:20px; margin-bottom:4px;">---</div>
                        <div id="i-pos" style="font-size:11px; color:var(--magenta); margin-bottom:4px; font-family:'Fira Code';">POS: --, --</div>
                        <div id="i-time" style="font-size:11px; color:var(--cyan); margin-bottom:8px; font-family:'Fira Code';">---</div>
                        <button id="i-btn" style="padding:4px 15px; background:var(--cyan); border:none; cursor:pointer; font-size:10px; font-weight:700; color:#000;">PROFILE</button>
                    </div>
                </div>
                <div id="inspect-none" style="text-align:center; width:100%; opacity:0.3; font-size:12px; margin-top:35px;">AWAITING_SCAN...</div>
            </div>
            <div class="list" id="feed"></div>
        </div>
    </div>

    <script>
        const resizer = document.getElementById('dragMe');
        const rightSide = document.getElementById('rightSide');
        let isResizing = false;

        resizer.addEventListener('mousedown', (e) => { isResizing = true; document.body.style.cursor = 'col-resize'; });
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            const newWidth = window.innerWidth - e.clientX;
            if (newWidth > 250 && newWidth < (window.innerWidth - 600)) { rightSide.style.width = `${newWidth}px`; }
        });
        document.addEventListener('mouseup', () => { isResizing = false; document.body.style.cursor = 'default'; });

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
            document.getElementById('i-pos').innerText = `COORD: ${Math.round(av.x)}, ${Math.round(av.y)}`;
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
                        ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(x,y, s, 0, Math.PI*2); ctx.stroke();
                        ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x,y, 4, 0, Math.PI*2); ctx.fill();
                        document.getElementById('i-time').innerText = "ONLINE: " + formatDuration(av.start_time);
                        document.getElementById('i-pos').innerText = `COORD: ${Math.round(av.x)}, ${Math.round(av.y)}`;
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
            document.getElementById('region-display').innerText = d.region.toUpperCase();
            document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
            
            const feed = document.getElementById('feed');
            const scrollPos = feed.scrollTop;
            feed.innerHTML = "";
            d.avatars.forEach((av, i) => {
                const card = document.createElement('div');
                card.className = "card" + (selectedKey === av.key ? " selected" : "");
                card.onclick = (e) => { if(e.target.tagName !== 'BUTTON') showInspect(av); };
                card.innerHTML = `<b style="color:${colors[i%colors.length]}">> ${av.name}</b> 
                                  <span class="pos-badge">${Math.round(av.x)},${Math.round(av.y)}</span>
                                  <br><span class="timer-badge">[${formatDuration(av.start_time)}]</span>
                                  <button class="quick-add" onclick="addToWatch('${av.key}', '${av.name}')">LOG</button>`;
                feed.appendChild(card);
            });
            feed.scrollTop = scrollPos;

            const wBody = document.getElementById('watch-list-body');
            wBody.innerHTML = "";
            Object.keys(d.watchlist).forEach(uuid => {
                const info = d.watchlist[uuid];
                const row = document.createElement('tr');
                let c = info.online ? "var(--cyan)" : "#444";
                row.innerHTML = `<td><b style="color:#fff">${info.name || '---'}</b></td>
                                 <td style="color:${c}; font-weight:bold;">${info.online ? 'ON' : 'OFF'}</td>
                                 <td>${info.arr || '--:--'}</td>
                                 <td>${info.dep || '--:--'}</td>
                                 <td><span style="color:var(--magenta); cursor:pointer;" onclick="removeWatch('${uuid}')">[X]</span></td>`;
                wBody.appendChild(row);
            });
        }
        setInterval(fetchData, 2000);
        draw();
    </script>
</body>
</html>
"""

# ... (Logique API Python reste identique à la V7.8) ...
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
