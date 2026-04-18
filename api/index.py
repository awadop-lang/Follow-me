# ... (Gardez le début du code Flask identique jusqu'à INTERFACE_HTML) ...

INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;500;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root { --cyan: #00ffff; --magenta: #ff00ff; --red: #ff3131; --green: #00ffaa; --bg: #020205; --panel: rgba(12, 12, 25, 0.98); --border: rgba(0, 255, 255, 0.2); }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Rajdhani', sans-serif; margin: 0; height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
        header { height: 60px; border-bottom: 1px solid var(--border); background: var(--panel); display: flex; justify-content: space-between; align-items: center; padding: 0 20px; flex-shrink: 0; }
        .logo { font-family: 'Orbitron'; font-weight: 700; color: var(--cyan); letter-spacing: 2px; }
        .time-selector { background: #111; border: 1px solid var(--border); color: var(--cyan); font-family: 'Rajdhani'; font-size: 12px; padding: 5px; cursor: pointer; border-radius: 3px; }
        .main-container { display: flex; flex: 1; overflow: hidden; width: 100%; }
        .column { height: 100%; overflow: hidden; display: flex; flex-direction: column; background: var(--panel); min-width: 200px; }
        .resizer { width: 4px; cursor: col-resize; background: var(--border); transition: 0.2s; flex-shrink: 0; }
        .resizer:hover { background: var(--cyan); }
        .col-header { padding: 15px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 11px; color: var(--magenta); background: rgba(0,0,0,0.5); text-transform: uppercase; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 12px; scrollbar-width: thin; }
        
        .item { background: rgba(255,255,255,0.02); border: 1px solid var(--border); padding: 12px; margin-bottom: 10px; display:flex; justify-content:space-between; align-items:center;}
        .item.watched { border-left: 4px solid var(--red); background: rgba(255, 49, 49, 0.05); }
        .name { color: var(--cyan); font-weight: 700; font-size: 14px; font-family: 'Orbitron'; cursor: pointer; }
        .pos-label { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #666; margin-top: 2px; }
        .profile-link { color: #555; text-decoration: none; font-size: 12px; margin-left: 5px; }
        
        .log-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; width:100%; }
        .time-badge { background: rgba(0,0,0,0.5); padding: 6px; border-radius: 3px; border: 1px solid rgba(255,255,255,0.1); }
        .time-label { font-size: 8px; text-transform: uppercase; color: #888; display: block; }
        .time-value { font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; color: #fff; }
        .val-in { color: var(--green); } .val-out { color: var(--red); }
        
        .action-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); font-family: 'Orbitron'; width: 28px; height: 28px; cursor: pointer; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 5px; }
        .online { background: var(--green); box-shadow: 0 0 8px var(--green); } .offline { background: #444; }
        .map-frame { position: relative; width: 512px; height: 512px; border: 1px solid var(--cyan); background: #000; }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.4; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
    </style>
</head>
<body onload="initApp()">
    <header>
        <div class="logo">NOX//ZETA v1.2.4</div>
        <div style="display:flex; align-items:center; gap:10px;">
            <select id="tz-select" class="time-selector" onchange="updateUI()"></select>
            <div style="font-family:monospace; font-size:12px; color:var(--cyan);">[ {{ session['user'].upper() }} ]</div>
        </div>
        <a href="/logout" style="color:var(--red); text-decoration:none; font-family:'Orbitron'; font-size:11px;">LOGOUT</a>
    </header>

    <div class="main-container">
        <div class="column" style="width: 40%;"><div class="col-header">Tactical_Radar</div><div class="scroll-area" style="display:flex; justify-content:center; align-items:center;"><div class="map-frame"><div id="map-bg"></div><canvas id="radar-canvas" width="512" height="512"></canvas></div></div></div>
        <div class="resizer"></div>
        <div class="column" style="width: 25%;"><div class="col-header">Scanner [<span id="count">0</span>]</div><div id="scan-list" class="scroll-area"></div></div>
        <div class="resizer"></div>
        <div class="column" style="width: 35%;"><div class="col-header" style="color:var(--red)">Watchlist</div><div id="watch-list" class="scroll-area"></div></div>
    </div>

    <script>
        let selectedAgent = null;
        const tzSelect = document.getElementById('tz-select');
        Intl.supportedValuesOf('timeZone').forEach(tz => {
            const opt = document.createElement('option'); opt.value = tz; opt.innerText = tz;
            if(tz === "Europe/Paris") opt.selected = true;
            tzSelect.appendChild(opt);
        });

        function formatTime(ts) {
            if (!ts || ts === "---") return "---";
            return new Intl.DateTimeFormat('fr-FR', {
                timeZone: tzSelect.value, hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
            }).format(new Date(ts * 1000));
        }

        async function updateUI() {
            try {
                const res = await fetch('/api_data');
                const data = await res.json();
                const watchlist = data.watchlist || [];
                const avatars = data.avatars || [];

                document.getElementById('count').innerText = avatars.length;
                if(data.coords) document.getElementById('map-bg').style.backgroundImage = `url('https://map.secondlife.com/map-1-${data.coords.x}-${data.coords.y}-objects.jpg')`;

                document.getElementById('scan-list').innerHTML = avatars.map(av => `
                    <div class="item" style="${selectedAgent === av.name ? 'border: 1px solid var(--cyan); background: rgba(0,255,255,0.05);' : ''}">
                        <div>
                            <div>
                                <span class="name" onclick="selectedAgent='${av.name}'">${av.name}</span>
                                <a href="https://my.secondlife.com/${av.name.replace(/ /g, '.')}" target="_blank" class="profile-link">🔗</a>
                            </div>
                            <div class="pos-label">COORD: ${Math.round(av.x)}, ${Math.round(av.y)}</div>
                        </div>
                        <button class="action-btn" onclick="toggleWatch('${av.name}')">${watchlist.includes(av.name)?'✖':'+'}</button>
                    </div>`).join('');

                document.getElementById('watch-list').innerHTML = watchlist.map(name => {
                    const hist = data.history[name] || {in: null, out: null};
                    const isOnline = avatars.find(a => a.name === name);
                    const posInfo = isOnline ? `<div class="pos-label">LIVE: ${Math.round(isOnline.x)}, ${Math.round(isOnline.y)}</div>` : '<div class="pos-label">LAST SEEN: OFFLINE</div>';
                    
                    return `<div class="item watched" style="flex-direction:column; align-items:flex-start;">
                        <div style="width:100%; display:flex; justify-content:space-between;">
                            <span>
                                <span class="status-dot ${isOnline?'online':'offline'}"></span>
                                <span class="name" onclick="selectedAgent='${name}'">${name}</span>
                                <a href="https://my.secondlife.com/${name.replace(/ /g, '.')}" target="_blank" class="profile-link">🔗</a>
                                ${posInfo}
                            </span>
                            <button class="action-btn" onclick="toggleWatch('${name}')" style="border-color:var(--red); color:var(--red); height:20px; width:20px; font-size:10px;">✖</button>
                        </div>
                        <div class="log-grid">
                            <div class="time-badge"><span class="time-label">IN</span><span class="time-value val-in">${formatTime(hist.in)}</span></div>
                            <div class="time-badge"><span class="time-label">OUT</span><span class="time-value val-out">${formatTime(hist.out)}</span></div>
                        </div>
                    </div>`;
                }).join('');

                const ctx = document.getElementById('radar-canvas').getContext('2d');
                ctx.clearRect(0, 0, 512, 512);
                avatars.forEach(av => {
                    const posX = av.x * 2; const posY = 512 - (av.y * 2);
                    if (selectedAgent === av.name) {
                        ctx.strokeStyle = "#00ffff"; ctx.lineWidth = 2; ctx.beginPath();
                        ctx.arc(posX, posY, 12 + Math.sin(Date.now()/200)*4, 0, Math.PI*2); ctx.stroke();
                    }
                    ctx.fillStyle = watchlist.includes(av.name) ? "#ff3131" : "#00ffff";
                    ctx.beginPath(); ctx.arc(posX, posY, watchlist.includes(av.name) ? 7 : 4, 0, Math.PI * 2); ctx.fill();
                });
            } catch(e) { console.error(e); }
        }

        async function toggleWatch(name) {
            await fetch('/toggle_watch', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:name}) });
            updateUI();
        }

        function initApp() { setInterval(updateUI, 1000); updateUI(); }
    </script>
</body>
</html>
"""
# ... (Gardez le reste du code Flask identique) ...
