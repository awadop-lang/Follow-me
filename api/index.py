from flask import Flask, request, jsonify, render_template_string
import time

app = Flask(__name__)

db = {
    "region": "TACTICAL_NET_ACTIVE...",
    "coords": {"x": 0, "y": 0},
    "avatars": []
}
times = {}

HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TACTICAL_HUD // NOX_V6.1</title>
    <style>
        :root { --p: #00ffff; --bg: #010103; --panel: #05050a; --font: 'Fira Code', monospace; }
        body { background: var(--bg); color: #a0c0c0; font-family: var(--font); margin: 0; padding: 15px; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { border-bottom: 2px solid var(--p); background: rgba(0,255,255,0.02); padding: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
        .grid { display: grid; grid-template-columns: 512px 1fr 300px; gap: 15px; flex: 1; overflow: hidden; }
        .map-wrapper { width: 512px; height: 512px; border: 1px solid #222; background: #000; position: relative; overflow: hidden; }
        #map-bg { width: 100%; height: 100%; background-size: 100% 100%; position: absolute; opacity: 0.8; filter: brightness(0.7); }
        canvas { position: absolute; top:0; left:0; z-index: 10; }
        .list { background: var(--panel); border: 1px solid #111; padding: 15px; overflow-y: auto; border-left: 2px solid var(--p); }
        .card { background: rgba(255,255,255,0.01); border: 1px solid #1a1a1a; padding: 12px; margin-bottom: 10px; cursor: pointer; transition: 0.2s; }
        .card:hover { background: rgba(0,255,255,0.08); border-color: var(--p); transform: translateX(5px); }
        .inspector { background: #000; border: 1px solid #222; display: flex; flex-direction: column; border-top: 2px solid var(--p); }
        .inspect-header { padding: 10px; font-size: 10px; color: var(--p); background: rgba(0,255,255,0.05); text-align: center; letter-spacing: 2px; }
        .inspect-photo-frame { width: 100%; aspect-ratio: 1; background: #0a0a0a; border-bottom: 1px solid #222; display: flex; align-items: center; justify-content: center; position: relative; }
        #i-img { width: 100%; height: 100%; object-fit: cover; display: none; z-index: 2; }
        .inspect-content { padding: 15px; flex: 1; }
        .i-label { font-size: 9px; color: var(--p); opacity: 0.6; margin-top: 12px; text-transform: uppercase; }
        .i-val { font-size: 13px; color: #fff; font-weight: bold; }
        .btn-profile { width: 100%; padding: 12px; background: var(--p); color: #000; border: none; font-family: inherit; font-weight: bold; cursor: pointer; margin-top: 20px; text-transform: uppercase; display: none; }
    </style>
</head>
<body>
    <header>
        <div style="font-size: 16px; font-weight: bold; letter-spacing: 4px; color: var(--p);">[ TACTICAL_MONITOR_V6.1 ]</div>
    </header>
    <div class="grid">
        <div class="map-wrapper"><div id="map-bg"></div><canvas id="cv" width="512" height="512"></canvas></div>
        <div class="list" id="feed"></div>
        <div class="inspector">
            <div class="inspect-header">// AGENT_DOSSIER</div>
            <div class="inspect-photo-frame">
                <img id="i-img" src="" onerror="this.style.display='none'">
                <div style="font-size:10px; opacity:0.2;">SCANNING_PHOTO...</div>
            </div>
            <div class="inspect-content">
                <div class="i-label">Identity</div><div id="i-name" class="i-val">---</div>
                <div class="i-label">Duration</div><div id="i-time" class="i-val" style="color:var(--p)">00m 00s</div>
                <div class="i-label">UUID</div><div id="i-key" class="i-val" style="font-size:10px; color:#444;">---</div>
                <button id="i-btn" class="btn-profile">View Profile</button>
            </div>
        </div>
    </div>
    <script>
        const canvas = document.getElementById('cv');
        const ctx = canvas.getContext('2d');
        const colors = ["#00ffff", "#ff00ff", "#00ff9f", "#ffff00", "#ff3f00"];
        let trails = {}; let selectedKey = null;

        function inspectAgent(av) {
            selectedKey = av.key;
            const img = document.getElementById('i-img');
            const btn = document.getElementById('i-btn');
            
            // Photo fix
            img.style.display = 'none';
            img.src = `https://my-secondlife-p01.s3.amazonaws.com/users/${av.key.replace(/-/g, '_')}/thumb_sl_image.png`;
            img.onload = () => img.style.display = 'block';

            document.getElementById('i-name').innerText = av.name.toUpperCase();
            document.getElementById('i-key').innerText = av.key;
            
            // --- REFACTOR LOGIC LIEN ---
            btn.style.display = 'block';
            let nameParts = av.name.toLowerCase().split(' ');
            let path = (nameParts[1] === 'resident') ? nameParts[0] : nameParts.join('.');
            btn.onclick = () => window.open(`https://my.secondlife.com/${path}`, '_blank');
        }

        async function update() {
            try {
                const r = await fetch('/api');
                const d = await r.json();
                document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
                ctx.clearRect(0,0,512,512);
                const feed = document.getElementById('feed'); feed.innerHTML = "";
                d.avatars.forEach((av, i) => {
                    const color = colors[i % colors.length];
                    const x = av.x * 2; const y = 512 - (av.y * 2);
                    const timeS = Math.floor(Date.now()/1000 - av.start_time);
                    if(selectedKey === av.key) document.getElementById('i-time').innerText = Math.floor(timeS/60) + "m " + (timeS%60) + "s";
                    
                    ctx.strokeStyle = color; ctx.beginPath(); ctx.arc(x,y,6,0,7); ctx.stroke();
                    const card = document.createElement('div');
                    card.className = "card"; card.onclick = () => inspectAgent(av);
                    card.innerHTML = `<b style="color:${color}">${av.name}</b><br><small>${Math.floor(timeS/60)}m active</small>`;
                    feed.appendChild(card);
                });
            } catch(e){}
        }
        setInterval(update, 2000);
    </script>
</body>
</html>
"""

@app.route('/api', methods=['GET', 'POST'])
def handle():
    global db, times
    if request.method == 'POST':
        data = request.json
        db["region"] = data.get("region", "UNK")
        db["coords"] = data.get("grid_coords", {"x":0, "y":0})
        active = []
        now = time.time()
        for av in data.get("avatars", []):
            uid = av.get("key")
            if uid:
                if uid not in times: times[uid] = now
                av["start_time"] = times[uid]
                active.append(av)
        db["avatars"] = active
        return "OK", 200
    return jsonify(db)

@app.route('/')
def home(): return render_template_string(HTML_CODE)
