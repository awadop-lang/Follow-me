from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "NOX_ZETA_LOGS_V5"

# Base de données temporaire (RAZ au déploiement)
users_db = {
    "admin": {
        "pw": "1234", 
        "region": "WAITING...", 
        "coords": {"x":0, "y":0}, 
        "avatars": []
    }
}

INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --red: #ff3131; --bg: #020205; --panel: rgba(10, 10, 20, 0.9); --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        
        header { height: 50px; border-bottom: 1px solid var(--border); background: var(--panel); display: flex; justify-content: space-between; align-items: center; padding: 0 20px; flex-shrink: 0; }
        .logo { font-family: 'Orbitron'; font-weight: 700; color: var(--cyan); letter-spacing: 2px; }

        .main-container { display: flex; flex: 1; overflow: hidden; position: relative; width: 100%; }
        .column { height: 100%; overflow: hidden; display: flex; flex-direction: column; background: var(--panel); min-width: 150px; }
        .resizer { width: 4px; cursor: col-resize; background: var(--border); transition: 0.3s; flex-shrink: 0; }
        .resizer:hover { background: var(--cyan); box-shadow: 0 0 10px var(--cyan); }

        .col-header { padding: 15px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 11px; color: var(--magenta); background: rgba(0,0,0,0.3); }
        .scroll-area { flex: 1; overflow-y: auto; padding: 10px; scrollbar-width: thin; }
        
        /* Cartes Avatars */
        .item { background: rgba(255,255,255,0.02); border: 1px solid var(--border); padding: 10px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
        .item.watched { border-left: 3px solid var(--red); background: rgba(255, 49, 49, 0.05); }
        
        .name-box { flex: 1; }
        .name { color: var(--cyan); font-weight: 600; font-size: 14px; text-decoration: none; }
        .details { font-size: 10px; color: #666; font-family: monospace; margin-top: 4px; }
        
        /* Logs de connexion */
        .log-entry { font-size: 9px; margin-top: 5px; padding-top: 5px; border-top: 1px dashed #333; }
        .log-in { color: #00ffaa; }
        .log-out { color: #ff5555; }

        .watch-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); font-family: 'Orbitron'; font-size: 12px; width: 24px; height: 24px; cursor: pointer; border-radius: 2px; }
        .watch-btn:hover { background: var(--cyan); color: black; }
        .item.watched .watch-btn { border-color: var(--red); color: var(--red); }

        /* Radar */
        .map-wrapper { width: 100%; display: flex; justify-content: center; align-items: center; padding: 20px; box-sizing: border-box; }
        .map-frame { position: relative; width: 512px; height: 512px; border: 1px solid var(--cyan); background: #000; }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.4; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }

        .btn-del { color: var(--red); cursor: pointer; border: 1px solid var(--red); width: 22px; height: 22px; display: flex; justify-content: center; align-items: center; }
    </style>
</head>
<body onload="initApp()">
    <header>
        <div class="logo">NOX//ZETA CORE</div>
        <div id="status" style="font-size:12px; font-family:monospace; color:var(--cyan);">LOGGER_ACTIVE</div>
    </header>

    <div class="main-container">
        <div class="column" style="width: 45%;">
            <div class="col-header">TACTICAL_RADAR // <span id="reg-name">---</span></div>
            <div class="scroll-area map-wrapper">
                <div class="map-frame">
                    <div id="map-bg"></div>
                    <canvas id="radar-canvas" width="512" height="512"></canvas>
                </div>
            </div>
        </div>

        <div class="resizer"></div>

        <div class="column" style="width: 25%;">
            <div class="col-header">LIVE_SCANNER [<span id="count">0</span>]</div>
            <div class="scroll-area" id="scan-list"></div>
        </div>

        <div class="resizer"></div>

        <div class="column" style="width: 30%;">
            <div class="col-header" style="color:var(--red)">PRIORITY_WATCHLIST & LOGS</div>
            <div class="scroll-area" id="watch-list"></div>
        </div>
    </div>

    <script>
        // On récupère la watchlist ET l'historique des sessions
        let watchlist = JSON.parse(localStorage.getItem('nox_watchlist')) || [];
        let sessionLogs = JSON.parse(localStorage.getItem('nox_logs')) || {}; 
        let lastSeenState = {}; // Pour comparer qui est parti/arrivé

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
                    const onMouseUp = () => { window.removeEventListener('mousemove', onMouseMove); };
                    window.addEventListener('mousemove', onMouseMove);
                    window.addEventListener('mouseup', onMouseUp);
                });
            });
        }

        function toggleWatch(name) {
            if (watchlist.includes(name)) {
                watchlist = watchlist.filter(n => n !== name);
                delete sessionLogs[name];
            } else {
                watchlist.push(name);
                sessionLogs[name] = { lastStatus: false, login: '---', logout: '---' };
            }
            save();
            updateUI();
        }

        function save() {
            localStorage.setItem('nox_watchlist', JSON.stringify(watchlist));
            localStorage.setItem('nox_logs', JSON.stringify(sessionLogs));
        }

        async function updateUI() {
            try {
                const res = await fetch('/api_data');
                const data = await res.json();
                const now = new Date().toLocaleTimeString('fr-FR', {hour: '2-digit', minute:'2-digit', second:'2-digit'});

                document.getElementById('reg-name').innerText = data.region.toUpperCase();
                document.getElementById('count').innerText = data.avatars.length;
                if(data.coords) document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;

                // Logique de détection Arrivée / Départ pour la Watchlist
                watchlist.forEach(name => {
                    const isPresent = data.avatars.find(a => a.name === name);
                    if (!sessionLogs[name]) sessionLogs[name] = { login: '---', logout: '---', lastStatus: false };

                    // Détection CONNEXION
                    if (isPresent && !sessionLogs[name].lastStatus) {
                        sessionLogs[name].login = now;
                        sessionLogs[name].lastStatus = true;
                        save();
                    }
                    // Détection DÉCONNEXION
                    if (!isPresent && sessionLogs[name].lastStatus) {
                        sessionLogs[name].logout = now;
                        sessionLogs[name].lastStatus = false;
                        save();
                    }
                });

                // Rendu Scanner
                document.getElementById('scan-list').innerHTML = data.avatars.map(av => {
                    const isWatched = watchlist.includes(av.name);
                    return `<div class="item ${isWatched ? 'watched' : ''}">
                        <div class="name-box"><span class="name">${av.name}</span><div class="details">POS: ${Math.round(av.x)}, ${Math.round(av.y)}</div></div>
                        <button class="watch-btn" onclick="toggleWatch('${av.name}')">${isWatched ? '-' : '+'}</button>
                    </div>`;
                }).join('');

                // Rendu Watchlist avec Logs
                document.getElementById('watch-list').innerHTML = watchlist.map(name => {
                    const log = sessionLogs[name] || {login:'---', logout:'---', lastStatus:false};
                    return `<div class="item watched">
                        <div class="name-box">
                            <a href="https://my.secondlife.com/${name.replace(/ /g, '.')}" target="_blank" class="name">${name}</a>
                            <div class="log-entry">
                                <span class="log-in">▲ IN: ${log.login}</span><br>
                                <span class="log-out">▼ OUT: ${log.logout}</span>
                            </div>
                        </div>
                        <div class="btn-del" onclick="toggleWatch('${name}')">✖</div>
                    </div>`;
                }).join('');

                // Radar
                const ctx = document.getElementById('radar-canvas').getContext('2d');
                ctx.clearRect(0, 0, 512, 512);
                data.avatars.forEach(av => {
                    ctx.fillStyle = watchlist.includes(av.name) ? "#ff3131" : "#00ffff";
                    ctx.beginPath(); ctx.arc(av.x * 2, 512 - (av.y * 2), watchlist.includes(av.name) ? 8 : 4, 0, Math.PI * 2); ctx.fill();
                });
            } catch(e) {}
        }

        function initApp() { initResize(); setInterval(updateUI, 3000); updateUI(); }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        if data.get("operator_id") == "admin":
            users_db["admin"].update({
                'region': data.get('region', 'UNK'),
                'coords': data.get('grid_coords', {'x':0, 'y':0}),
                'avatars': data.get('avatars', [])
            })
            return "OK", 200
        return "DENIED", 403
    return render_template_string(INTERFACE_HTML)

@app.route('/api_data')
def api_data():
    return jsonify(users_db["admin"])
