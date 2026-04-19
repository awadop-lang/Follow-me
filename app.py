import gradio as gr
import pandas as pd
import time
from fastapi import FastAPI, Request
import os
import uvicorn

app = FastAPI()
# Initialisation avec des données par défaut pour éviter les erreurs au démarrage
data_store = {"avatars": [], "region": "Abbas Way", "last_packet_time": 0}

CSS = """
.gradio-container { background-color: #0d1117 !important; color: #c9d1d9 !important; font-family: sans-serif; }
.glass-card { background: #161b22 !important; border: 1px solid #30363d !important; border-radius: 12px; padding: 20px; }
#map_container { height: 500px; width: 100%; border-radius: 8px; background: #000; border: 1px solid #58a6ff; }
"""

def get_map():
    now = time.time()
    # On laisse 60 secondes de marge pour le signal
    if now - data_store["last_packet_time"] > 60:
        return "<div style='color:#8b949e; text-align:center; padding-top:150px;'>📡 ATTENTE DU SIGNAL DE SECOND LIFE...</div>"

    reg_url = data_store["region"].replace(" ", "%20")
    
    # Construction des marqueurs
    markers = ""
    for a in data_store["avatars"]:
        markers += f"L.circleMarker([{a['Y']}, {a['X']}], {{radius: 7, color: '#58a6ff', fillOpacity: 0.8}}).addTo(map).bindTooltip('{a['Avatar']}', {{permanent: true}});"

    return f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <div id="map_container"></div>
    <script>
        var map = L.map('map_container', {{crs: L.CRS.Simple, minZoom: -1, maxZoom: 2, zoomControl: false}});
        L.tileLayer('https://map.secondlife.com/map-1-{reg_url}-{{z}}-{{x}}-{{y}}-objects.jpg', {{tileSize: 256}}).addTo(map);
        map.setView([128, 128], 0);
        {markers}
    </script>
    """

def refresh():
    now = time.time()
    status = f"🟢 RÉGION : {data_store['region']}" if (now - data_store["last_packet_time"] < 60) else "🔴 HORS LIGNE"
    df = pd.DataFrame(data_store["avatars"]) if data_store["avatars"] else pd.DataFrame(columns=["Avatar", "X", "Y", "Z"])
    return get_map(), df, status

with gr.Blocks(css=CSS) as demo:
    gr.HTML("<h1 style='text-align:center;'>SL TACTICAL SCANNER</h1>")
    with gr.Row():
        with gr.Column(scale=3, elem_classes="glass-card"):
            map_html = gr.HTML(get_map)
        with gr.Column(scale=2):
            with gr.Group(elem_classes="glass-card"):
                status_ui = gr.Markdown("📡 Synchronisation...")
                table_ui = gr.Dataframe(headers=["Avatar", "X", "Y", "Z"], interactive=False)

    gr.Timer(3).tick(refresh, outputs=[map_html, table_ui, status_ui])

@app.post("/update")
async def update(request: Request):
    try:
        body = await request.body()
        content = body.decode("utf-8")
        if ":" in content:
            data_store["last_packet_time"] = time.time()
            reg, avs = content.split(":")
            data_store["region"] = reg.strip()
            new_list = []
            if avs != "empty":
                for entry in avs.split(";"):
                    p = entry.split("|")
                    if len(p) == 2:
                        name, c = p[0], p[1].split(",")
                        new_list.append({"Avatar": name, "X": float(c[0]), "Y": float(c[1]), "Z": float(c[2])})
            data_store["avatars"] = new_list
        return {"status": "ok"}
    except:
        return {"status": "error"}

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
