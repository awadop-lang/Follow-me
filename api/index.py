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
    <title>NOX_SHADOW_V8.1</title>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400&family=Orbitron:wght@400;700&family=Rajdhani:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root { 
            --cyan: #00ffff; --magenta: #ff00ff; --bg: #020205; 
            --panel: rgba(5, 7, 12, 0.98); --border: rgba(0, 255, 255, 0.15);
            --glow: 0 0 8px rgba(0, 255, 255, 0.3);
        }

        * { box-sizing: border-box; }
        body { 
            background: var(--bg); color: #a5b5b5; 
            font-family: 'Rajdhani', sans-serif; 
            margin: 0; padding: 12px; height: 100vh; overflow: hidden; display: flex; flex-direction: column;
            background-image: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
            background-size: 100% 3px, 3px 100%;
        }

        header { 
            border: 1px solid var(--border); background: var(--panel); 
            padding: 8px 20px; margin-bottom: 8px; 
            display: flex; justify-content: space-between; align-items: center;
            border-left: 4px solid var(--cyan); flex-shrink: 0;
        }

        .main-container { display: flex; flex: 1; overflow: hidden; border: 1px solid var(--border); background: rgba(0,0,0,0.2); }

        /* GAUCHE */
        .left-zone { display: flex; flex-direction: column; flex: 1; min-width: 532px; overflow: hidden; }
        .map-wrapper { width: 512px; height: 512px; margin: 10px; background: #000; position: relative; flex-shrink: 0; border: 1px solid #1a1a1a; }
        #map-bg { width: 100%; height: 100%; background-size: cover; position: absolute; opacity: 0.4; filter: brightness(0.5) saturate(0.8); }
        canvas { position: absolute; top:0; left:0; z-index: 10; }

        .watchlist-panel { flex: 1; background: var(--panel); border-top: 1px solid var(--border); padding: 12px; display: flex; flex-direction: column; overflow: hidden; }

        /* RESIZER */
        .resizer { width: 6px; background: #08080c; cursor: col-resize; transition: 0.2s; z-index: 100; border-left: 1px solid #111; border-right: 1px solid #111; }
        .resizer:hover { background: var(--cyan); box-shadow: var(--glow); }

        /* DROITE */
        .right-zone { width: 380px; min-width: 250px; max-width: 85vw; display: flex; flex-direction: column; background: var(--panel); border-left: 1px solid var(--border); }
        
        .inspector { background: rgba(0,0,0,0.4); border-bottom: 1px solid var(--border); padding: 12px; min-height: 100px; flex-shrink: 0; display: flex; align-items: center; }
        #i-img { width: 70px; height: 70px; border: 1px solid var(--border); margin-right: 15px; filter: grayscale(0.2); transition: 0.3s; }
        #i-img:hover { filter: grayscale(0); border-color: var(--cyan); }
        
        .list { flex: 1; padding: 10px; overflow-y: auto; scrollbar-width: none; }
        .list::-webkit-scrollbar { width: 2px; }
        .list::-webkit-scrollbar-thumb { background: var(--cyan); }

        /* CARDS */
        .card { 
            background: rgba(255, 255, 255, 0.01); border: 1px solid rgba(255,255,255,0.03); 
            padding: 10px; margin-bottom: 6px; cursor: pointer; position: relative; 
            transition: 0.1s; font-family: 'Fira Code', monospace; font-weight: 300; font-size: 12px;
        }
        .card:hover { background: rgba(0, 255, 255, 0.03); border-color: var(--cyan); }
        .card.selected { border-left: 2px solid var(--cyan); background: rgba(0, 255, 255, 0.06); color: #fff; }
        
        .pos-badge { font-family: 'Orbitron', sans-serif; color: var(--magenta); font-size: 9px; letter-spacing: 1px; opacity: 0.8; }
        .name-tag { font-family: 'Orbitron', sans-serif; font-size: 13px; letter-spacing: 1px; display: block; margin-bottom: 2px; }

        /* TABLEAU */
        .w-table { width: 100%; border-collapse: collapse; font-family: 'Fira Code', monospace; font-size: 10px; }
        .w-table th { text-align: left; color: var(--magenta); padding: 6px; font-family: 'Orbitron'; font-size: 9px; letter-spacing: 1px; border-bottom: 1px solid rgba(255,0,255,0.1); }
        .w-table td { padding: 6px; border-bottom: 1px solid rgba(255,255,255,0.02); }

        select, input { background: transparent; border: 1px solid var(--border); color: var(--cyan); padding: 4px 8px; font-family: 'Fira Code'; font-size: 11px; outline: none; }
        select:hover, input:focus { border-color: var(--cyan); }
        
        .action-btn { background: transparent; border: 1px solid var(--magenta); color: var(--magenta); padding: 6px 12px; font-family: 'Orbitron'; font-size: 10px; cursor: pointer; transition: 0.2s; }
        .action-btn:hover { background: var(--magenta); color: #000; box-shadow: 0 0 10px var(--magenta); }

        #clock { font-family: 'Orbitron', sans-serif; color: var(--cyan); font-size: 14px; letter-spacing: 2px; text-shadow: var(--glow); }
    </style>
</head>
<body>
    <header>
        <div>
            <span style="font-family: 'Orbitron'; font-size: 16px; font-weight: 700; letter-spacing: 4px; color: var(--cyan);">NOX//CORE</span>
            <span id="region-display" style="margin-left:20px; font-family: 'Rajdhani'; font-weight: 300; letter-spacing: 3px; color: #666;">INITIALIZING...</span>
        </div>
        <div style="display:flex; align-items:center; gap:25px;">
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size:9px; font-family:'Orbitron'; color:var(--magenta);">ZONE:</span>
                <select id="tz-selector" onchange="updateTimeDisplay()">
                    <option value="local">LOCAL</option>
                    <option value="pst">SL_PST</option>
                    <option value="utc">UTC</option>
                </select>
            </div>
            <div id="clock">00:00:00</div>
        </div>
    </header>

    <div class="main-container">
        <div class="left-zone">
            <div class="map-wrapper"><div id="map-bg"></div><canvas id="cv" width="512" height="512"></canvas></div>
            <div class="watchlist-panel">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <span style="font-family:'Orbitron'; font-size:11px; color:var(--magenta); letter-spacing:2px;">[ TARGET_PERSISTENCE ]</span>
                    <div style="display:flex; gap:5px;">
                        <input type="text" id="watch-uuid" placeholder="UID_SCANNER" style="width:180px;">
                        <button class="action-btn" onclick="addWatchManual()">ADD</button>
                    </div>
                </div>
                <div style="overflow-y:auto; flex:1;" class="list">
                    <table class="w-table">
                        <thead><tr><th>IDENTIFIER</th><th>STATUS</th><th>ARRIVAL</th><th>DEPARTURE</th><th>X</th></tr></thead>
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
                        <div id="i-name" style="font-family:'Orbitron'; font-weight:700; color:#fff; font-size:16px; letter-spacing:1px;">---</div>
                        <div id="i-pos" style="font-size:10px; color:var(--magenta); font-family:'Fira Code'; margin: 4px 0;">XY: 0.0 / 0.0</div>
                        <div id="i-time" style="font-size:10px; color:var(--cyan); font-family:'Fira Code'; margin-bottom:8px;">ACTIVE_SEC: 0</div>
                        <button id="i-btn" style="padding:4px 10px; background:var(--cyan); border:none; cursor:pointer; font-size:9px; font-family:'Orbitron'; font-weight:700; color:#000;">PROFILE_SL</button>
                    </div>
                </div>
                <div id="inspect-none" style="text-align:center; width:100%; opacity:0.2; font-family:'Orbitron'; font-size:10px; letter-spacing:2px;">NO_DATA_LINK</div>
            </div>
            <div class="list" id="feed"></div>
        </div>
    </div>

    <script>
        // --- LOGIQUE TEMPS ---
        function getFormattedTime(timestamp = null) {
            const mode = document.getElementById('tz-selector').value;
            let date = timestamp ? new Date(timestamp * 1000) : new Date();
            if (mode === 'utc') return date.toISOString().substr(11, 8);
            if (mode === 'pst') {
                const pst = new Date(date.getTime() + (date.getTimezoneOffset() * 60000) - (8 * 3600000));
                return pst.toTimeString().substr(0, 8);
            }
            return date.toTimeString().substr(0, 8);
        }

        function updateClock() { document.getElementById('clock').innerText = getFormattedTime(); }
        setInterval(updateClock, 1000);

        // --- RESIZER ---
        const resizer = document.getElementById('dragMe');
        const rightSide = document.getElementById('rightSide');
        let isResizing = false;
        resizer.addEventListener('mousedown', () => { isResizing = true; document.body.style.cursor = 'col-resize'; });
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            const newWidth = window.innerWidth - e.clientX;
            if (newWidth > 200 && newWidth < (window.innerWidth - 600)) { rightSide.style.width = `${newWidth}px`; }
        });
        document.addEventListener('mouseup', () => { isResizing = false; document.body.style.cursor = 'default'; });

        // --- DATA ---
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const colors = ["#00ffff", "#ff00ff", "#00ff9f", "#ffff00"];
        let selectedKey = null, lastData = null, pulseVal = 0;

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
                pulseVal += 0.1;
                lastData.avatars.forEach((av, i) => {
                    const color = colors[i % colors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);
                    if (selectedKey === av.key) {
                        const s = 10 + Math.sin(pulseVal) * 4;
                        ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x,y, s, 0, Math.PI*2); ctx.stroke();
                        ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x,y, 3, 0, Math.PI*2); ctx.fill();
                        document.getElementById('i-time').innerText = "UPTIME: " + formatDuration(av.start_time);
                        document.getElementById('i-pos').innerText = `XY: ${Math.round(av.x)} / ${Math.round(av.y)}`;
                    } else {
                        ctx.globalAlpha = selectedKey ? 0.1 : 0.7;
                        ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x,y, 4, 0, Math.PI*2); ctx.fill();
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
                card.innerHTML = `<span class="name-tag" style="color:${colors[i%colors.length]}">${av.name}</span>
                                  <span class="pos-badge">${Math.round(av.x)}.${Math.round(av.y)}</span>
                                  <span style="color:var(--cyan); margin-left:10px;">[${formatDuration(av.start_time)}]</span>
                                  <button onclick="addToWatch('${av.key}', '${av.name}')" style="float:right; background:none; border:1px solid #333; color:#666; font-size:8px; cursor:pointer;">LOG</button>`;
                feed.appendChild(card);
            });
            feed.scrollTop = scrollPos;

            const wBody = document.getElementById('watch-list-body');
            wBody.innerHTML = "";
            Object.keys(d.watchlist).forEach(uuid => {
                const info = d.watchlist[uuid];
                const row = document.createElement('tr');
                let c = info.online ? "var(--cyan)" : "#333";
                row.innerHTML = `<td><b>${info.name || '---'}</b></td>
                                 <td style="color:${c}; font-weight:bold;">${info.online ? 'SYNC' : 'LOST'}</td>
                                 <td>${info.arr_raw ? getFormattedTime(info.arr_raw) : '--:--'}</td>
                                 <td>${info.dep_raw ? getFormattedTime(info.dep_raw) : '--:--'}</td>
                                 <td><span style="color:var(--magenta); cursor:pointer;" onclick="removeWatch('${uuid}')">[-]</span></td>`;
                wBody.appendChild(row);
            });
        }
        function updateTimeDisplay() { fetchData(); }
        setInterval(fetchData, 2000);
        draw();
    </script>
</body>
</html>
"""

# ... (API Python inchangée par rapport à V8.0) ...
@app.route('/api', methods=['GET', 'POST'])
def handle():
    global db, times, watchlist
    now = time.time()
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
                            watchlist[w_uid]["arr_raw"] = now
                        elif not is_on and watchlist[w_uid]["online"]:
                            watchlist[w_uid]["dep_raw"] = now
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
        watchlist[uid] = {"name": name, "online": False, "arr_raw": None, "dep_raw": None}
    return "OK"

@app.route('/unwatch', methods=['POST'])
def unwatch():
    data = request.get_json(silent=True)
    uid = data.get("uuid")
    if uid in watchlist: del watchlist[uid]
    return "OK"

@app.route('/')
def home(): return render_template_string(HTML_CODE)
