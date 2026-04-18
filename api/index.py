from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = "NOX_ZETA_FULL_STABLE_2026"

# Base de données centrale
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "OFFLINE", 
        "coords": {"x":0, "y":0}, 
        "avatars": [],
        "history": {} # Format: {"Nom": {"in": "HH:MM:SS", "out": "HH:MM:SS", "active": True}}
    }
}

INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --red: #ff3131; --bg: #020205; --panel: rgba(10, 10, 20, 0.95); --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        
        header { height: 55px; border-bottom: 1px solid var(--border); background: var(--panel); display: flex; justify-content: space-between; align-items: center; padding: 0 20px; flex-shrink: 0; box-shadow: 0 0 15px rgba(0,0,0,0.5); z-index: 10; }
        .logo { font-family: 'Orbitron'; font-weight: 700; color: var(--cyan); letter-spacing: 2px; text-shadow: 0 0 10px var(--cyan); }

        .main-container { display: flex; flex: 1; overflow: hidden; position: relative; width: 100%; }
        .column { height: 100%; overflow: hidden; display: flex; flex-direction: column; background: var(--panel); min-width: 200px; }
        .resizer { width: 4px; cursor: col-resize; background: var(--border); transition: 0.2s; flex-shrink: 0; }
        .resizer:hover { background: var(--cyan); box-shadow: 0 0 10px var(--cyan); }

        .col-header { padding: 15px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 11px; color: var(--magenta); background: rgba(0,0,0,0.4); text-transform: uppercase; letter-spacing: 1px; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 12px; scrollbar-width: thin; scrollbar-color: var(--cyan) transparent; }
        
        /* Cartes Avatars */
        .item { background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; transition: 0.3s; }
        .item:hover { border-color: var(--cyan); background: rgba(0,255,255,0.05); }
        .item.watched { border-left: 3px solid var(--red); background: rgba(255, 49, 49, 0.08); }
        
        .name-box { flex: 1; }
        .name { color: var(--cyan); font-weight: 600; font-size: 15px; text-decoration: none; display: block; }
        .item.watched .name { color: var(--red); }
        .details { font-size: 10px; color: #777; font-family: monospace; margin-top: 4px; }
        
        /* Logs */
        .log-box { font-size: 10px; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 5px; line-height: 1.4; }
        .log-in { color: #00ffaa; opacity: 0.8; }
        .log-out { color: #ff5555; opacity: 0.8; }

        .action-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); font-family: 'Orbitron'; font-size: 14px; width: 28px; height: 28px; cursor: pointer; transition: 0.2s; border-radius: 2px; }
        .action-btn:hover { background: var(--cyan); color: black; box-shadow: 0 0 10px var(--cyan); }
        .item.watched .action-btn { border-color: var(--red); color: var(--red); }

        /* Radar */
        .map-wrapper { width: 100%; display: flex; justify-content: center; align-items: center; padding: 20px; box-sizing: border-box; }
        .map-frame { position: relative; width: 512px; height: 512px; border: 1px solid var(--cyan); background: #000; box-shadow: 0 0 20px rgba(0,0,0,1); }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.45; background-size: cover; filter: brightness(0.8); }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
    </style>
</head>
<body onload="initApp()">
    <header>
        <div class="logo">NOX//ZETA SYSTEM</div>
        <div style="font-family:monospace; font-size:12px; color:var(--cyan); border:1px solid var(--cyan); padding:4px 10px;">
            LINK_STATUS: <span id="reg-name">OFFLINE</span>
        </div>
        <a href="/logout" style="color:var(--red); text-decoration:none; font-family:'Orbitron'; font-size:11px; border:1px solid var(--red); padding:5px 10px;">DISCONNECT</a>
    </header>

    <div class="main-container">
        <div class="column" id="col-radar" style="width: 45%;">
            <div class="col-header">Satellite_Uplink // Live_Grid</div>
            <div class="scroll-area map-wrapper">
                <div class="map-frame">
                    <div id="map-bg"></div>
                    <canvas id="radar-canvas" width="512" height="512"></canvas>
                </div>
            </div>
        </div>

        <div class="resizer" id="r1"></div>

        <div class="column" id="col-scanner" style="width: 25%;">
            <div class="col-header">Nearby_Signals [<span id="count">0</span>]</div>
            <div class="scroll-area" id="scan-list"></div>
        </div>

        <div class="resizer" id="r2"></div>

        <div class="column" id="col-watchlist" style="width: 30%;">
            <div class="col-header" style="color:var(--red)">Priority_Watchlist // Session_Logs</div>
            <div class="scroll-area" id="watch-list"></div>
        </div>
    </div>

    <script>
        let watchlist = JSON.parse(localStorage.getItem('nox_watchlist')) || [];

        function initResize() {
            const resizers = document.querySelectorAll('.resizer');
            resizers.forEach(resizer => {
                resizer.addEventListener('mousedown', (e) => {
                    let prevCol = resizer.previousElementSibling;
                    let nextCol = resizer.nextElementSibling;
                    let startX = e.pageX;
                    let startW = prevCol.offsetWidth;
                    let startWNext = nextCol.offsetWidth;
                    const onMouseMove = (e) => {
                        let diff = e.pageX - startX;
                        prevCol.style.width = (startW + diff) + 'px';
                        nextCol.style.width = (startWNext - diff) + 'px';
                    };
                    const onMouseUp = () => window.removeEventListener('mousemove', onMouseMove);
                    window.addEventListener('mousemove', onMouseMove);
                    window.addEventListener('mouseup', onMouseUp);
                });
            });
        }

        function toggleWatch(name) {
            if (watchlist.includes(name)) {
                watchlist = watchlist.filter(n => n !== name);
            } else {
                watchlist.push(name);
            }
            localStorage.setItem('nox_watchlist', JSON.stringify(watchlist));
            updateUI();
        }

        async function updateUI() {
            try {
                const res = await fetch('/api_data');
                const data = await res.json();
                
                document.getElementById('reg-name').innerText = data.region.toUpperCase();
                document.getElementById('count').innerText = data.avatars.length;
                
                if(data.coords) {
                    document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;
                }

                // Scanner Render
                const scanArea = document.getElementById('scan-list');
                scanArea.innerHTML = data.avatars.map(av => {
                    const isWatched = watchlist.includes(av.name);
                    return `
                        <div class="item ${isWatched ? 'watched' : ''}">
                            <div class="name-box">
                                <span class="name">${av.name}</span>
                                <div class="details">GRID_POS: ${Math.round(av.x)}, ${Math.round(av.y)}</div>
                            </div>
                            <button class="action-btn" onclick="toggleWatch('${av.name}')">${isWatched ? '-' : '+'}</button>
                        </div>`;
                }).join('');

                // Watchlist Render (avec Historique du serveur)
                const watchArea = document.getElementById('watch-list');
                watchArea.innerHTML = watchlist.map(name => {
                    const hist = data.history[name] || {in: "---", out: "---", active: false};
                    return `
                        <div class="item watched">
                            <div class="name-box">
                                <a href="https://my.secondlife.com/${name.replace(/ /g, '.')}" target="_blank" class="name">${name}</a>
                                <div class="log-box">
                                    <span class="log-in">▲ IN: ${hist.in}</span><br>
                                    <span class="log-out">▼ OUT: ${hist.out}</span>
                                </div>
                            </div>
                            <button class="action-btn" onclick="toggleWatch('${name}')" style="border-color:var(--red); color:var(--red);">✖</button>
                        </div>`;
                }).join('');

                // Radar Render
                const ctx = document.getElementById('radar-canvas').getContext('2d');
                ctx.clearRect(0, 0, 512, 512);
                data.avatars.forEach(av => {
                    const isWatched = watchlist.includes(av.name);
                    ctx.fillStyle = isWatched ? "#ff3131" : "#00ffff";
                    ctx.shadowBlur = 10; ctx.shadowColor = ctx.fillStyle;
                    ctx.beginPath();
                    ctx.arc(av.x * 2, 512 - (av.y * 2), isWatched ? 8 : 4.5, 0, Math.PI * 2);
                    ctx.fill();
                });
            } catch(e) {}
        }

        function initApp() {
            initResize();
            setInterval(updateUI, 3000);
            updateUI();
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        if data.get("operator_id") == "admin":
            now = datetime.now().strftime("%H:%M:%S")
            new_avatars = data.get('avatars', [])
            current_names = [a['name'] for a in new_avatars]
            history = users_db["admin"]["history"]
            
            # Détection entrées
            for name in current_names:
                if name not in history or history[name]['active'] == False:
                    history[name] = {'in': now, 'out': '---', 'active': True}
            
            # Détection sorties
            for name, status in history.items():
                if status['active'] and name not in current_names:
                    status['out'] = now
                    status['active'] = False

            users_db["admin"].update({
                'region': data.get('region', 'UNK'),
                'coords': data.get('grid_coords', {'x':0, 'y':0}),
                'avatars': new_avatars
            })
            return "OK", 200
        return "DENIED", 403
    
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(INTERFACE_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('u') == "admin" and request.form.get('p') == "1234":
            session['user'] = "admin"
            return redirect(url_for('index'))
    return """<body style="background:#020205; color:#0ff; font-family:'Orbitron'; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;"><form method="POST" style="border:1px solid #0ff; padding:40px; background:rgba(0,255,255,0.05); text-align:center;"><h2>NOX_AUTH</h2><input name="u" placeholder="OPERATOR" style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:10px; display:block; width:220px;"><input type="password" name="p" placeholder="KEY" style="background:transparent; border:1px solid #0ff; color:white; padding:10px; margin-bottom:20px; display:block; width:220px;"><button type="submit" style="background:#0ff; border:none; padding:10px; width:100%; font-weight:bold; cursor:pointer;">ACCESS_CORE</button></form></body>"""

@app.route('/api_data')
def api_data():
    return jsonify(users_db["admin"])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
