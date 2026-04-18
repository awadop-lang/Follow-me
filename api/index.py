from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

db = {
    "region": "SECURE_LINK_INIT...",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
times = {}
# Historique des positions pour les traînées (trails)
history = {} 

AGENT_COLORS = ["#00ffff", "#ff00ff", "#00ff9f", "#7f00ff", "#ffff00", "#ff3f00", "#007fff"]

HTML_CODE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>TACTICAL_HUD // NOX_PROTOCOL_V5</title>
    <style>
        :root {
            --bg: #020205; --panel: #05050a; --p: #00ffff; --accent: #ff00ff;
            --text: #a0c0c0; --font: 'Fira Code', monospace;
        }
        body {
            background-color: var(--bg); color: var(--text); font-family: var(--font);
            margin: 0; padding: 15px; height: 100vh; overflow: hidden;
            display: flex; flex-direction: column;
        }
        
        /* Header Tactique */
        header {
            display: flex; justify-content: space-between; align-items: flex-end;
            padding: 10px; border: 1px solid var(--p); background: rgba(0,255,255,0.05);
            margin-bottom: 15px; clip-path: polygon(0 0, 100% 0, 98% 100%, 2% 100%);
        }

        .main-layout { display: grid; grid-template-columns: 530px 1fr 250px; gap: 15px; flex: 1; overflow: hidden; }

        /* Bloc Carte */
        .map-wrapper { position: relative; width: 512px; height: 512px; border: 1px solid var(--p); background: #000; }
        #map-bg { width: 100%; height: 100%; background-size: 100% 100%; position: absolute; opacity: 0.6; filter: grayscale(0.5) contrast(1.2); }
        canvas { position: absolute; top:0; left:0; z-index: 10; }

        /* Bloc Liste Agents */
        .agent-list { background: var(--panel); border: 1px solid #111; padding: 15px; overflow-y: auto; border-left: 3px solid var(--p); }
        .av-card { 
            background: rgba(255,255,255,0.02); margin-bottom: 10px; padding: 10px; 
            border: 1px solid #1a1a1a; position: relative;
        }
        .prog-bar { width: 100%; height: 2px; background: #111; margin-top: 8px; }
        .prog-fill { height: 100%; transition: width 0.5s; }

        /* Bloc Logs */
        .log-panel { background: #000; border: 1px solid #222; padding: 10px; font-size: 10px; color: #555; overflow-y: hidden; }
        .log-entry { border-bottom: 1px solid #111; padding: 3px 0; }
        .log-in { color: var(--p); }
        .log-out { color: var(--accent); }

        /* Animations */
        @keyframes scan { from { top: 0; } to { top: 100%; } }
        .scanner-line { 
            position: absolute; width: 100%; height: 2px; background: rgba(0,255,255,0.2); 
            z-index: 11; animation: scan 3s linear infinite; box-shadow: 0 0 10px var(--p);
        }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 20px; font-weight: bold; letter-spacing: 5px;">TACTICAL_HUD V5.0</div>
        <div id="sim-id" style="color:var(--p)">CONNECTED // REGION_UNK</div>
    </header>

    <div class="main-layout">
        <div class="map-wrapper">
            <div id="map-bg"></div>
            <div class="scanner-line"></div>
            <canvas id="cv" width="512" height="512"></canvas>
        </div>

        <div class="agent-list" id="agent-feed">
            <div style="color:var(--p); font-size: 12px; margin-bottom: 15px;">// ACTIVE_TARGET_STREAM</div>
        </div>

        <div class="log-panel">
            <div style="color:#aaa; border-bottom: 1px solid #333; margin-bottom: 5px;">SESSION_LOGS</div>
            <div id="logs"></div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const agentColors = ["#00ffff", "#ff00ff", "#00ff9f", "#7f00ff", "#ffff00", "#ff3f00", "#007fff"];
        let trailMap = {}; // Stocke les positions précédentes

        async function loop() {
            try {
                const res = await fetch('/api');
                const d = await res.json();
                
                document.getElementById('sim-id').innerText = `REGION: ${d.region.toUpperCase()} // COORDS: ${d.coords.x},${d.coords.y}`;
                document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;

                ctx.clearRect(0,0,512,512);
                const feed = document.getElementById('agent-feed');
                feed.innerHTML = "";

                d.avatars.forEach((av, i) => {
                    const color = agentColors[i % agentColors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);

                    // --- Gestion des Trails (Traces) ---
                    if(!trailMap[av.key]) trailMap[av.key] = [];
                    trailMap[av.key].push({x, y});
                    if(trailMap[av.key].length > 10) trailMap[av.key].shift();

                    // Dessin Trail
                    ctx.beginPath();
                    ctx.strokeStyle = color; ctx.globalAlpha = 0.3; ctx.lineWidth = 1;
                    trailMap[av.key].forEach((p, idx) => {
                        if(idx === 0) ctx.moveTo(p.x, p.y); else ctx.lineTo(p.x, p.y);
                    });
                    ctx.stroke();
                    ctx.globalAlpha = 1.0;

                    // Dessin Target
                    ctx.strokeStyle = color; ctx.lineWidth = 2;
                    ctx.beginPath(); ctx.arc(x,y, 8, 0, 7); ctx.stroke();
                    ctx.fillStyle = "white"; ctx.beginPath(); ctx.arc(x,y, 2, 0, 7); ctx.fill();
                    ctx.font = "9px monospace"; ctx.fillText(av.name.toUpperCase(), x + 12, y + 4);

                    // HTML Feed
                    const timeS = Math.floor(Date.now()/1000 - av.start_time);
                    const p = Math.min(100, (timeS / 1800) * 100); // 30 min full

                    const card = document.createElement('div');
                    card.className = "av-card";
                    card.innerHTML = `
                        <div style="display:flex; justify-content:space-between; font-size:11px;">
                            <span style="color:${color}; font-weight:bold;">${av.name}</span>
                            <span>${Math.floor(av.x)},${Math.floor(av.y)}</span>
                        </div>
                        <div class="prog-bar"><div class="prog-fill" style="width:${p}%; background:${color}; box-shadow: 0 0 5px ${color}"></div></div>
                        <div style="font-size:9px; margin-top:5px; color:#555;">UPTIME: ${Math.floor(timeS/60)}M ${timeS%60}S</div>
                    `;
                    feed.appendChild(card);
                });
            } catch(e) {}
        }
        setInterval(loop, 2000);
    </script>
</body>
</html>
