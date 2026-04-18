from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_FINAL_PROTOCOL_2026"

# Base de données en mémoire
users_db = {
    "admin": {
        "pw": "1234", 
        "is_admin": True, 
        "watchlist": {}, 
        "times": {}, 
        "region": "SYSTEM_START", 
        "coords": {"x":0, "y":0}, 
        "avatars": []
    }
}

# Interface Cyberpunk Totale
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300&family=Orbitron:wght@400;700&family=Rajdhani:wght@300;600&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --bg: #020205; --panel: rgba(5, 7, 12, 0.95); --border: rgba(0, 255, 255, 0.15); }
        body { 
            background: var(--bg); color: #a5b5b5; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden;
            background-image: linear-gradient(rgba(18,16,16,0) 50%, rgba(0,0,0,0.1) 50%), linear-gradient(90deg, rgba(255,0,0,0.03), rgba(0,255,0,0.01), rgba(0,0,255,0.03));
            background-size: 100% 3px, 3px 100%;
        }
        header { border-bottom: 1px solid var(--border); background: var(--panel); padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; }
        .btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); font-family: 'Orbitron'; cursor: pointer; padding: 5px 15px; text-decoration: none; font-size: 11px; }
        .btn:hover { background: var(--cyan); color: #000; box-shadow: 0 0 10px var(--cyan); }
        .container { display: flex; height: calc(100vh - 60px); }
        .left { flex: 1; display: flex; flex-direction: column; padding: 10px; }
        .right { width: 350px; border-left: 1px solid var(--border); background: var(--panel); overflow-y: auto; padding: 10px; }
        #map-area { position: relative; width: 512px; height: 512px; background: #000; border: 1px solid #1a1a1a; margin: 0 auto; }
        #map-img { width: 100%; height: 100%; background-size: cover; opacity: 0.4; position: absolute; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; }
        .card { background: rgba(255,255,255,0.02); border: 1px solid var(--border); padding: 10px; margin-bottom: 5px; cursor: pointer; font-family: 'Fira Code'; font-size: 12px; }
        .card:hover { border-color: var(--cyan); background: rgba(0,255,255,0.05); }
        .selected { border-left: 3px solid var(--cyan); background: rgba(0,255,255,0.1); }
    </style>
</head>
<body onload="update()">
    <header>
        <div style="font-family:'Orbitron'; color:var(--cyan); letter-spacing:3px; font-weight:700;">NOX//CORE <span id="reg-display" style="color:#666; margin-left:15px; font-weight:300;">---</span></div>
        <div style="display:flex; gap:15px; align-items:center;">
            <div id="clock" style="font-family:'Fira Code'; font-size:12px; color:var(--cyan);">00:00:00</div>
            <a href="/logout" class="btn" style="border-color:var(--magenta); color:var(--magenta);">DISCONNECT</a>
        </div>
    </header>

    <div class="container">
        <div class="left">
            <div id="map-area">
                <div id="map-img"></div>
                <canvas id="map-cv" width="512" height="512"></canvas>
            </div>
            <div style="margin-top:15px; flex:1; background:rgba(0,0,0,0.3); border:1px solid var(--border); padding:10px;">
                <h3 style="font-family:'Orbitron'; font-size:11px; color:var(--magenta); margin:0 0 10px 0;">PERSISTENCE_LOG</h3>
                <div id="logs" style="font-family:'Fira Code'; font-size:10px;"></div>
            </div>
        </div>
        <div class="right">
            <h3 style="font-family:'Orbitron'; font-size:11px; margin-bottom:15px;">ACTIVE_ENTITIES</h3>
            <div id="feed"></div>
        </div>
    </div>

    <script>
        let selected = null;
        async function update() {
            try {
                const r = await fetch('/api');
                const d = await r.json();
                document.getElementById('reg-display').innerText = d.region.toUpperCase();
                document.getElementById('map-img').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
                
                const feed = document.getElementById('feed');
                feed.innerHTML = d.avatars.map(av => `
                    <div class="card ${selected === av.key ? 'selected' : ''}" onclick="selected='${av.key}'">
                        <div style="color:var(--cyan); font-weight:700;">${av.name}</div>
                        <div style="font-size:10px; opacity:0.6;">X:${Math.round(av.x)} Y:${Math.round(av.y)}</div>
                    </div>
                `).join('');

                draw(d.avatars);
            } catch(e) {}
        }

        function draw(avatars) {
            const ctx = document.getElementById('map-cv').getContext('2d');
            ctx.clearRect(0,0,512,512);
            avatars.forEach(av => {
                ctx.fillStyle = (selected === av.key) ? "#ff00ff" : "#00ffff";
                ctx.shadowBlur = 8; ctx.shadowColor = ctx.fillStyle;
                ctx.beginPath(); ctx.arc(av.x*2, 512-(av.y*2), 5, 0, Math.PI*2); ctx.fill();
            });
        }
        setInterval(update, 3000);
        setInterval(() => { document.getElementById('clock').innerText = new Date().toLocaleTimeString(); }, 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def home():
