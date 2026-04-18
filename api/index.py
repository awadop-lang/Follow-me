from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

db = {
    "region": "SECURE_STREAM_ACTIVE...",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
times = {}

# --- INTERFACE TACTIQUE NOX V5.5 (INTEGRATED INSPECTOR) ---
HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TACTICAL_HUD // NOX_V5.5</title>
    <style>
        :root { --p: #00ffff; --bg: #010103; --panel: #05050a; --font: 'Fira Code', monospace; }
        body { background: var(--bg); color: #a0c0c0; font-family: var(--font); margin: 0; padding: 15px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { border-bottom: 2px solid var(--p); background: rgba(0,255,255,0.02); padding: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
        
        .grid { display: grid; grid-template-columns: 512px 1fr 300px; gap: 15px; flex: 1; overflow: hidden; }

        /* Bloc Carte */
        .map-wrapper { width: 512px; height: 512px; border: 1px solid #222; background: #000; position: relative; overflow: hidden; }
        #map-bg { width: 100%; height: 100%; background-size: 100% 100%; position: absolute; opacity: 0.8; filter: brightness(0.6); }
        canvas { position: absolute; top:0; left:0; z-index: 10; }
        
        /* Bloc Liste */
        .list { background: var(--panel); border: 1px solid #111; padding: 10px; overflow-y: auto; border-left: 2px solid var(--p); }
        .card { background: rgba(255,255,255,0.01); border: 1px solid #1a1a1a; padding: 10px; margin-bottom: 8px; cursor: pointer; transition: 0.2s; }
        .card:hover { background: rgba(0,255,255,0.1); border-color: var(--p); }

        /* Bloc Inspecteur (La colonne de droite) */
        .inspector { 
            background: #000; border: 1px solid #222; padding: 0; 
            display: flex; flex-direction: column; border-top: 2px solid var(--p);
            box-shadow: inset 0 0 20px rgba(0,255,255,0.05);
        }
        .inspect-header { padding: 10px; font-size: 10px; color: var(--p); background: rgba(0,255,255,0.05); text-align: center; letter-spacing: 2px; }
        
        /* Zone Photo */
        .inspect-photo-frame { 
            width: 100%; aspect-ratio: 1; 
            background: #111; border-bottom: 1px solid #222;
            display: flex; align-items: center; justify-content: center;
            overflow: hidden; position: relative;
        }
        #i-img { width: 100%; height: 100%; object-fit: cover; display: none; }
        .no-photo { font-size: 10px; opacity: 0.3; text-align: center; }

        .inspect-content { padding: 15px; flex: 1; }
        .i-label { font-size: 9px; color: var(--p); opacity: 0.6; margin-top: 10px; text-transform: uppercase; }
        .i-val { font-size: 13px; color: #fff; font-weight: bold; margin-bottom: 5px; word-break: break-all; }

        .btn-profile { 
            width: 100%; padding: 10px; background: var(--p); color: #000; 
            border: none; font-family: inherit; font-weight: bold; cursor: pointer;
            margin-top: 20px; text-transform: uppercase; display: none;
        }
        .btn-profile:hover { background: #fff; }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ TACTICAL_HUD_V5.5 ]</div>
        <div id="sim-info" style="font-size: 10px;">---</div>
    </header>

    <div class="grid">
        <div class="map-wrapper">
            <div id="map-bg"></div>
            <canvas id="cv" width="512" height="512"></canvas>
        </div>

        <div class="list" id="feed"></div>

        <div class="inspector">
            <div class="inspect-header">// AGENT_DATA_SCAN</div>
            <div class="inspect-photo-frame">
                <img id="i-img" src="" alt="Avatar Photo">
                <div id="no-selection" class="no-photo">WAITING FOR TARGET...</div>
            </div>
            <div class="inspect-content">
                <div class="i-label">Identity</div>
                <div id="i-name" class="i-val">NOT_SELECTED</div>
                
                <div class="i-label">Global Unique ID</div>
                <div id="i-key" class="i-val" style="font-size:10px;">---</div>
                
                <div class="i-label">Status</div>
                <div id="i-status" class="i-val" style="color:var(--p)">SCANNING...</div>

                <button id="i-btn" class="btn-profile">View Full Profile</button>
            </div>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const colors = ["#00ffff", "#ff00ff", "#00ff9f", "#ffff00", "#ff3f00", "#007fff"];
        let trails = {}; 

        function inspectAgent(key, name) {
            // Afficher la photo
            const img = document.getElementById('i-img');
            const placeholder = document.getElementById('no-selection');
            const btn = document.getElementById('i-btn');
            
            // On utilise l'API de Linden Lab pour la photo de profil
            img.src = `https://my-secondlife-p01.s3.amazonaws.com/users/${key.replace(/-/g, '_')}/thumb_sl_image.png`;
            img.style.display = 'block';
            placeholder.style.display = 'none';

            // Infos texte
            document.getElementById('i-name').innerText = name.toUpperCase();
            document.getElementById('i-key').innerText = key;
            document.getElementById('i-status').innerText = "TARGET_LOCKED";
            
            // Bouton
            btn.style.display = 'block';
            btn.onclick = () => window.open(`https://my.secondlife.com/${name.replace(/ /g, '.')}`, '_blank');
        }

        async function update() {
            try {
                const r = await fetch('/api');
                const d = await r.json();
                
                document.getElementById('sim-info').innerText = `REGION: ${d.region.toUpperCase()} [${d.coords.x},${d.coords.y}]`;
                document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
                
                ctx.clearRect(0,0,512,512);
                const feed = document.getElementById('feed');
                feed.innerHTML = "";

                d.avatars.forEach((av, i) => {
                    const color = colors[i % colors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);

                    if(!trails[av.key]) trails[av.key] = [];
                    let lastP = trails[av.key][trails[av.key].length - 1];
                    if(!lastP || Math.abs(lastP.x - x) > 1 || Math.abs(lastP.y - y) > 1) trails[av.key].push({x, y});
                    if(trails[av.key].length > 400) trails[av.key].shift();

                    ctx.beginPath(); ctx.strokeStyle = color; ctx.globalAlpha = 0.4; ctx.lineWidth = 1;
                    trails[av.key].forEach((p, idx) => { if(idx==0) ctx.moveTo(p.x,p.y); else ctx.lineTo(p.x,p.y); });
                    ctx.stroke(); ctx.globalAlpha = 1.0;

                    ctx.strokeStyle = color; ctx.lineWidth = 1; 
                    ctx.beginPath(); ctx.arc(x,y,6,0,7); ctx.stroke(); 
                    ctx.fillStyle = "white"; ctx.beginPath(); ctx.arc(x,y,1.5,0,7); ctx.fill(); 

                    const card = document.createElement('div');
                    card.className = "card";
                    card.onclick = () => inspectAgent(av.key, av.name);
                    card.innerHTML = `<b style="color:${color}">${av.name}</b><br><span style="font-size:10px; opacity:0.5;">POS: ${Math.floor(av.x)}, ${Math.floor(av.y)}</span>`;
                    feed.appendChild(card);
                });
            } catch(e){}
        }
        setInterval(update, 2000);
    </script>
</body>
</html>
