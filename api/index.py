from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "NOX_ZETA_PRO_V4"

# Base de données temporaire pour les positions
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
        .item { background: rgba(255,255,255,0.03); border: 1px solid var(--border); padding: 10px; margin-bottom: 8px; transition: 0.2s; position: relative; display: flex; justify-content: space-between; align-items: center; }
        .item:hover { border-color: var(--cyan); background: rgba(0,255,255,0.05); }
        .item.watched { border-left: 3px solid var(--red); background: rgba(255, 49, 49, 0.1); }
        
        .name-box { flex: 1; }
        .name { color: var(--cyan); font-weight: 600; font-size: 14px; text-decoration: none; }
        .details { font-size: 10px; color: #666; font-family: monospace; margin-top: 4px; }

        /* Boutons Watchlist */
        .watch-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); font-family: 'Orbitron'; font-size: 12px; width: 24px; height: 24px; cursor: pointer; display: flex; justify-content: center; align-items: center; transition: 0.3s; margin-left: 10px; border-radius: 2px; }
        .watch-btn:hover { background: var(--cyan); color: black; box-shadow: 0 0 8px var(--cyan); }
        .item.watched .watch-btn { border-color: var(--red); color: var(--red); }
        .item.watched .watch-btn:hover { background: var(--red); color: white; }

        /* Radar Section */
        .map-wrapper { width: 100%; display: flex; justify-content: center; align-items: center; padding: 20px; box-sizing: border-box; }
        .map-frame { position: relative; width: 512px; height: 512px; border: 1px solid var(--cyan); background: #000; }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.4; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }

        .btn-del { color: var(--red); cursor: pointer; font-size: 12px; border: 1px solid var(--red); width: 24px; height: 24px; display: flex; justify-content: center; align-items: center; transition: 0.3s; }
        .btn-del:hover { background: var(--red); color: white; }
    </style>
</head>
<body onload="initApp()">
    <header>
        <div class="logo">NOX//ZETA CORE</div>
        <div id="status" style="font-size:12px; font-family:monospace; color:var(--cyan);">SIGNAL_STABLE</div>
    </header>

    <div class="main-container" id="container">
        <div class="column" style="width: 50%;">
            <div class="col-header">TACTICAL_RADAR // <span id="reg-name">---</span></div>
            <div class="scroll-area map-wrapper">
                <div class="map-frame">
                    <div id="map-bg"></div>
                    <canvas id="radar-canvas" width="512" height="512"></canvas>
                </div>
            </div>
        </div>

        <div class="resizer" id="resizer1"></div>

        <div class="column" style="width: 25%;">
            <div class="col-header">LIVE_SCANNER [<span id="count">0</span>]</div>
            <div class="scroll-area" id="scan-list"></div>
        </div>

        <div class="resizer" id="resizer2"></div>

        <div class="column" style="width: 25%;">
            <div class="col-header" style="color:var(--red)">PRIORITY_WATCHLIST</div>
            <div class="scroll-area" id="watch-list"></div>
        </div>
    </div>

    <script>
        let watchlist = JSON.parse(localStorage.getItem('nox_watchlist')) || [];

        function initResize() {
            const resizers = document.querySelectorAll('.resizer');
            resizers.forEach(resizer => {
                resizer.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    window.addEventListener('mousemove', resize);
                    window.addEventListener('mouseup', stopResize);
                    let prevCol = resizer.previousElementSibling;
                    let nextCol = resizer.nextElementSibling;
                    let startX = e.pageX;
                    let startWidthPrev = prevCol.offsetWidth;
                    let startWidthNext = nextCol.offsetWidth;
                    function resize(e) {
                        let diff = e.pageX - startX;
                        prevCol.style.width = (startWidthPrev + diff) + 'px';
                        nextCol.style.width = (startWidthNext - diff) + 'px';
                    }
                    function stopResize() { window.removeEventListener('mousemove', resize); }
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

                // Scanner
                const scanArea = document.getElementById('scan-list');
                scanArea.innerHTML = data.avatars.map(av => {
                    const isWatched = watchlist.includes(av.name);
                    return `
                        <div class="item ${isWatched ? 'watched' : ''}">
                            <div class="name-box">
                                <span class="name">${isWatched ? '⚠️ ' : ''}${av.name}</span>
                                <div class="details">POS: ${Math.round(av.x)}, ${Math.round(av.y)}</div>
                            </div>
                            <button class="watch-btn" onclick="toggleWatch('${av.name}')">${isWatched ? '-' : '+'}</button>
                        </div>
                    `;
                }).join('');

                // Watchlist
                const watchArea = document.getElementById('watch-list');
                watchArea.innerHTML = watchlist.map(name => `
                    <div class="item watched">
                        <div class="name-box">
                            <a href="https://my.secondlife.com/${name.replace(/ /g, '.')}" target="_blank" class="name">${name}</a>
                            <div class="details">STATUS: ${data.avatars.find(a => a.name === name) ? 'ONLINE' : 'OFFLINE'}</div>
                        </div>
                        <div class="btn-del" onclick="toggleWatch('${name}')">✖</div>
                    </div>
                `).join('');

                // Radar
                const ctx = document.getElementById('radar-canvas').getContext('2d');
                ctx.clearRect(0, 0, 512, 512);
                data.avatars.forEach(av => {
                    const isWatched = watchlist.includes(av.name);
                    ctx.fillStyle = isWatched ? "#ff3131" : "#00ffff";
                    ctx.beginPath();
                    ctx.arc(av.x * 2, 512 - (av.y * 2), isWatched ? 8 : 4, 0, Math.PI * 2);
                    ctx.fill();
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
