import gradio as gr
import pandas as pd
import time
from fastapi import FastAPI, Request
import os
import uvicorn

app = FastAPI()
data_store = {"avatars": [], "region": "Abbas Way", "last_packet_time": 0}

CSS = """
.gradio-container { background-color: #0d1117 !important; color: #c9d1d9 !important; font-family: 'Inter', sans-serif !important; }
.glass-card { background: rgba(22, 27, 34, 0.8) !important; border: 1px solid #30363d !important; border-radius: 12px !important; padding: 15px !important; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
#map_container { height: 550px; width: 100%; border-radius: 10px; background: #000; overflow: hidden; border: 1px solid #58a6ff; }
"""

def generate_map_html():
    now = time.time()
    # Si pas de données depuis 40s
    if now - data_store["last_packet_time"] > 40:
        return "<div style='color:#8b949e; text-align:center; padding-top:200px; font-family:sans-serif;'>📡 EN ATTENTE DU SIGNAL DEPUIS SECOND LIFE...</div>"

    # Nettoyage du nom de la région pour l'URL
    reg_url = data_store["region"].replace(" ", "%20")
    
    # Création des marqueurs JS pour chaque avatar
    markers_js = ""
    for a in data_store["avatars"]:
        # On inverse Y pour coller au système Leaflet (0,0 en bas à gauche dans SL)
        markers_js += f"""
        L.circleMarker([{a['Y']}, {a['X']}], {{
            radius: 8, color: '#58a6ff', fillColor: '#58a6ff', fillOpacity: 0.8
        }}).addTo(map).bindTooltip('{a['Avatar']}', {{permanent: true, direction: 'top'}});
        """

    # HTML avec Leaflet.js
    html_content = f"""
    <div id="map_container"></div>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <script>
        var map = L.map('map_container', {{
            crs: L.CRS.Simple,
            minZoom: -1,
            maxZoom: 2,
            zoomControl: false
        }});

        // URL Officielle des tuiles de Second Life
        var slTileUrl = 'https://map.secondlife.com/map-1-{reg_url}-{{z}}-{{x}}-{{y}}-objects.jpg';
        
        L.tileLayer(slTileUrl, {{
            tileSize: 256,
            continuousWorld: true,
            noWrap: true
        }}).addTo(map);

        map.setView([128, 128], 0);
        {markers_js}
    </script>
    """
    return html_content

def update_ui():
    now = time.time()
    is_online = (now - data_store["last_packet_time"] < 40)
    status = f"🟢 RÉGION : {data_store['region']}" if is_online else "🔴 SCANNER HORS LIGNE"
    
    df = pd.DataFrame(data_store["avatars"]) if data_store["avatars"] else pd.DataFrame(columns=["Avatar", "X", "Y", "Z"])
    return generate_map_html(), df, status

with gr.Blocks(css=CSS, title="SL Tactical Map") as demo:
    gr.HTML("<h1 style='text-align:center; color:#f0f6fc; margin-bottom:10px;'>🛰️ SL TACTICAL LIVE MAP</h1>")
    
    with gr.Row():
        with gr.Column(scale=3, elem_classes="glass-card"):
            map_view = gr.HTML(generate_map_html)
            
        with gr.Column(scale=2):
            with gr.Group(elem_classes="glass-card"):
                connection_status = gr.Markdown("🔴 INITIALISATION...")
                gr.HTML("<div style='margin-bottom:15px;'></div>")
                target_table = gr.Dataframe(
                    headers=["Avatar", "X", "Y", "Z"],
                    datatype=["str", "number", "number", "number"],
                    interactive=False
                )

    gr.Timer(3).tick(update_ui, outputs=[map_view, target_table, connection_status])

@app.post("/update")
async def update(request: Request):
    body = await request.body()
    content = body.decode("utf-8")
    data_store["last_packet_time"] = time.time()
    
    if ":" in content:
        reg, avs = content.split(":")
        data_store["region"] = reg.strip()
        new_data = []
        if avs != "empty":
            for entry in avs.split(";"):
                parts = entry.split("|")
                if len(parts) == 2:
                    name, c = parts[0], parts[1].split(",")
                    new_data.append({
                        "Avatar": name, "X": float(c[0]), "Y": float(c[1]), "Z": round(float(c[2]), 1)
                    })
        data_store["avatars"] = new_data
    return {"status": "ok"}

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
