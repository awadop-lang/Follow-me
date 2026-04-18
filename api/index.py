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
        .main-container { display: flex; flex: 1; overflow: hidden; width: 100%; }
        .column { height: 100%; overflow: hidden; display: flex; flex-direction: column; background: var(--panel); border-right: 1px solid var(--border); }
        .col-header { padding: 15px; border-bottom: 1px solid var(--border); font-family: 'Orbitron'; font-size: 11px; color: var(--magenta); text-transform: uppercase; }
        .scroll-area { flex: 1; overflow-y: auto; padding: 12px; }
        
        .item { background: rgba(255,255,255,0.02); border: 1px solid var(--border); padding: 12px; margin-bottom: 10px; position: relative; }
        .name { color: var(--cyan); font-weight: 700; font-size: 14px; font-family: 'Orbitron'; cursor: pointer; }
        
        /* États de connexion */
        .status-badge { font-size: 9px; padding: 2px 6px; border-radius: 3px; font-weight: bold; margin-left: 10px; border: 1px solid; }
        .st-local { color: var(--green); border-color: var(--green); background: rgba(0,255,170,0.1); }
        .st-grid { color: #f1c40f; border-color: #f1c40f; background: rgba(241,196,15,0.1); }
        .st-off { color: #555; border-color: #444; background: rgba(0,0,0,0.3); }

        .action-btn { background: transparent; border: 1px solid var(--cyan); color: var(--cyan); cursor: pointer; width: 25px; height: 25px; font-family: 'Orbitron'; }
        .map-frame { position: relative; width: 512px; height: 512px; border: 1px solid var(--cyan); background: #000; margin: auto; }
        #map-bg { width: 100%; height: 100%; position: absolute; opacity: 0.4; background-size: cover; }
        canvas { position: absolute; top: 0; left: 0; z-index: 5; pointer-events: none; }
    </style>
</head>
<body onload="initApp()">
    <header>
        <div class="logo">NOX//ZETA v1.6.1</div>
        <div style="font-family:'JetBrains Mono'; font-size:12px; color:var(--cyan);">SYSTEM_READY // OP: {{ user_name.upper() }}</div>
        <a href="/logout" style="color:var(--red); text-decoration:none; font-family:'Orbitron'; font-size:11px;">LOGOUT</a>
    </header>

    <div class="main-container">
        <div class="column" style="width: 40%; justify-content:center;">
            <div class="map-frame"><div id="map-bg"></div><canvas id="radar-canvas" width="512" height="512"></canvas></div>
        </div>
        
        <div class="column" style="width: 30%;">
            <div class="col-header">Scanner Local</div>
            <div id="scan-list" class="scroll-area"></div>
        </div>
        
        <div class="column" style="width: 30%;">
            <div class="col-header" style="color:var(--red)">Watchlist Persistante (Global)</div>
            <div id="watch-list" class="scroll-area"></div>
        </div>
    </div>

    <script>
        let selectedAgent = null;

        async function updateUI() {
            try {
                const res = await fetch('/api_data');
                const data = await res.json();
                const watchlist = data.watchlist || [];
                const localAvatars = data.avatars || [];

                // 1. Mise à jour du Scanner Local
                document.getElementById('scan-list').innerHTML = localAvatars.map(av => `
                    <div class="item">
                        <div style="display:flex; justify-content:space-between;">
                            <span class="name" onclick="selectedAgent='${av.name}'">${av.name}</span>
                            <button class="action-btn" onclick="toggleWatch('${av.name}', '${av.uuid}')">+</button>
                        </div>
                        <div style="font-size:10px; color:#666; margin-top:5px;">POS: ${Math.round(av.x)}, ${Math.round(av.y)}</div>
                    </div>`).join('');

                // 2. Mise à jour de la Watchlist Persistante
                document.getElementById('watch-list').innerHTML = watchlist.map(w => {
                    const isLocal = localAvatars.find(a => a.uuid === w.uuid);
                    const statusClass = isLocal ? 'st-local' : (w.online_sl ? 'st-grid' : 'st-off');
                    const statusText = isLocal ? 'SUR RADAR' : (w.online_sl ? 'GRID ONLINE' : 'OFFLINE');

                    return `
                    <div class="item" style="border-left: 3px solid ${isLocal ? 'var(--green)' : 'var(--red)'}">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="name">${w.name}</span>
                            <button onclick="toggleWatch('${w.name}')" style="color:var(--red); background:none; border:none; cursor:pointer;">&times;</button>
                        </div>
                        <div style="margin-top:5px;">
                            <span class="status-badge ${statusClass}">${statusText}</span>
                        </div>
                    </div>`;
                }).join('');

                // 3. Dessin Radar
                const ctx = document.getElementById('radar-canvas').getContext('2d');
                ctx.clearRect(0, 0, 512, 512);
                localAvatars.forEach(av => {
                    const posX = av.x * 2; const posY = 512 - (av.y * 2);
                    ctx.fillStyle = watchlist.some(w => w.uuid === av.uuid) ? "#ff3131" : "#00ffff";
                    ctx.beginPath(); ctx.arc(posX, posY, 6, 0, Math.PI * 2); ctx.fill();
                });

            } catch(e) { console.log("Erreur refresh UI"); }
        }

        async function toggleWatch(name, uuid = "") {
            await fetch('/toggle_watch', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({name: name, uuid: uuid})
            });
            updateUI();
        }

        function initApp() { setInterval(updateUI, 2000); updateUI(); }
    </script>
</body>
</html>
"""
