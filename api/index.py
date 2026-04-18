from flask import Flask, request, jsonify, render_template_string, session, redirect, url_for
import time

app = Flask(__name__)
app.secret_key = "NOX_SYNC_FIX_171"

db = {
    "admin": {
        "region": "Initialisation...",
        "coords": {"x": 0, "y": 0},
        "avatars": [],
        "watchlist": [] 
    }
}

HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { background: #020205; color: #0ff; font-family: sans-serif; margin: 0; padding: 20px; }
        .grid { display: grid; grid-template-columns: 1fr 300px; gap: 20px; }
        .map-box { width: 512px; height: 512px; border: 1px solid #0ff; position: relative; background: #000; }
        #map-img { width: 100%; height: 100%; opacity: 0.5; }
        .item { border: 1px solid rgba(0,255,255,0.3); padding: 10px; margin-bottom: 5px; }
        .st-local { color: #0f0; } .st-grid { color: #ff0; } .st-off { color: #777; }
        button { cursor: pointer; background: none; border: 1px solid #0ff; color: #0ff; }
    </style>
</head>
<body onload="setInterval(refresh, 2000)">
    <h2>NOX//ZETA v1.7.1 - <span id="reg-name">---</span></h2>
    <div class="grid">
        <div class="map-box">
            <div id="map-img" style="background-size: cover;"></div>
        </div>
        <div>
            <h3>WATCHLIST</h3>
            <div id="w-list"></div>
            <hr>
            <h3>RADAR</h3>
            <div id="r-list"></div>
        </div>
    </div>

    <script>
        async function refresh() {
            const r = await fetch('/api_data');
            const d = await r.json();
            if(!d.watchlist) return;

            document.getElementById('reg-name').innerText = d.region;
            if(d.coords.x > 0) {
                document.getElementById('map-img').style.backgroundImage = `url('https://map.secondlife.com/map-1-${d.coords.x}-${d.coords.y}-objects.jpg')`;
            }

            document.getElementById('r-list').innerHTML = d.avatars.map(a => `
                <div class="item">${a.name} <button onclick="add('${a.name}','${a.uuid}')">+</button></div>
            `).join('');

            document.getElementById('w-list').innerHTML = d.watchlist.map(w => {
                const local = d.avatars.find(a => a.uuid === w.uuid);
                const online = w.online_sl && (Date.now()/1000 - w.last_ping < 45);
                let cls = "st-off", txt = "OFFLINE";
                if(local) { cls="st-local"; txt="SUR PLACE"; }
                else if(online) { cls="st-grid"; txt="DANS LA GRID"; }
                
                return `<div class="item ${cls}">${w.name} [${txt}] <button onclick="add('${w.name}','${w.uuid}')">x</button></div>`;
            }).join('');
        }
        async function add(n, u) { 
            await fetch('/toggle', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({name:n, uuid:u})});
            refresh();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    if 'u' not in session: return redirect('/login')
    return render_template_string(HTML_UI)

@app.route('/up_radar', methods=['POST'])
def up_radar():
    data = request.get_json()
    op = data.get("op", "admin")
    db[op].update({'avatars':data['avs'], 'region':data['reg'], 'coords':data['pos']})
    return "OK"

@app.route('/up_glob', methods=['POST'])
def up_glob():
    data = request.get_json()
    for agent in db['admin']['watchlist']:
        if agent['uuid'] == data['uuid']:
            agent['online_sl'] = (data['status'] == "1")
            agent['last_ping'] = time.time()
    return "OK"

@app.route('/get_wl')
def get_wl():
    return jsonify([a['uuid'] for a in db['admin']['watchlist']])

@app.route('/api_data')
def api_data():
    return jsonify(db['admin'])

@app.route('/toggle', methods=['POST'])
def toggle():
    d = request.get_json()
    wl = db['admin']['watchlist']
    exists = next((i for i in wl if i["uuid"] == d['uuid']), None)
    if exists: wl.remove(exists)
    else: wl.append({"name":d['name'], "uuid":d['uuid'], "online_sl":True, "last_ping":time.time()})
    return "OK"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST': session['u'] = "admin"; return redirect('/')
    return '<form method="POST"><input name="u"><button>IN</button></form>'

@app.route('/logout')
def logout(): session.clear(); return redirect('/')
