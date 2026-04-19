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
.glass-card { background: #161b22 !important; border: 1px solid #30363d !important; border-radius: 12px; padding: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
#map_container { height: 550px; width: 100%; border-radius: 10px; background: #000; border: 2px solid #58a6ff; }
"""

def generate_map_html():
    now = time.time()
    if now - data_store["last_packet_time"] > 60:
        return "<div style='color:#8b949e; text-align:center; padding-top:200px;'>📡 SIGNAL SCANNER PERDU...</div>"

    reg_url = data_store["region"].replace(" ", "%20")
    
    markers_js = ""
    for a in data_store["avatars"]:
        # Inversion de l'axe Y pour Leaflet (SL utilise 0 en bas, Leaflet 0 en haut en CRS.Simple)
        leaflet_y = a['Y'] 
        markers_js += f"""
        L.circleMarker([{leaflet_y}, {a['X']}], {{
            radius: 8, color: '#00ffff', weight: 2, opacity: 1, fillColor: '#00ffff', fillOpacity: 0.5
        }}).addTo(map).bindTooltip('{a['Avatar']}', {{permanent: true, direction: 'top', className: 'map-label'}});
        """

    # Utilisation d'une URL de tuiles alternative et forçage du rafraîchissement JS
    html_content = f"""
    <div id="map_container"></div>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <style>.map-label {{ background: rgba(0,0,0,0.7); color: #00ffff; border: none; font-weight: bold; }}</style>
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <script>
        var container = L.DomUtil.get('map_container');
        if(container != null){{ container._leaflet_id = null; }}
        
        var map = L.map('map_container', {{
            crs: L.CRS.Simple,
            minZoom: -2,
            maxZoom: 2,
            zoomControl: true,
            attributionControl: false
        }});

        // Tentative avec le sous-domaine 'img' qui est souvent plus stable en HTTPS
        var slTileUrl = 'https://map.secondlife.com/map-1-{reg_url}-{{z}}-{{x}}-{{y}}-objects.jpg';
        
        L.tileLayer(slTileUrl, {{
            tileSize: 256,
            noWrap: true,
            continuousWorld: true
        }}).addTo(map);

        map.setView([128, 128], 0);
        {markers_js}
    </script>
    """
    return html_content

def update_ui():
    now = time.time()
    online = (now - data_store["last_packet_time"] < 60)
    status = f"🟢 RÉGION : {data_store['region']}" if online else "🔴 SCANNER OFFLINE"
    df = pd.DataFrame(data_store["avatars"]) if data_store["avatars"] else pd.DataFrame(columns=["Avatar", "X", "Y", "Z"])
    return generate_map_html(), df, status

with gr.Blocks(css=CSS) as demo:
    gr.HTML("<h1 style='text-align:center; color:#f0f6fc;'>🛰️ SL TACTICAL LIVE MAP</h1>")
    with gr.Row():
        with gr.Column(scale=3, elem_classes="glass-card"):
            map_view = gr.HTML(generate_map_html)
        with gr.Column(scale=2):
            with gr.Group(elem_classes="glass-card"):
                connection_status = gr.Markdown("🔴 INITIALISATION")
                target_table = gr.Dataframe(headers=["Avatar", "X", "Y", "Z"], interactive=False)

    gr.Timer(4).tick(update_ui, outputs=[map_view, target_table, connection_status])

@app.post("/update")
async def update(request: Request):
    try:
        body = await request.body()
        content = body.decode("utf-8")
        if ":" in content:
            data_store["last_packet_time"] = time.time()
            reg, avs = content.split(":")
            data_store["region"] = reg.strip()
            new_data = []
            if avs != "empty":
                for entry in avs.split(";"):
                    parts = entry.split("|")
                    if len(parts) == 2:
                        name, c = parts[0], parts[1].split(",")
                        new_data.append({"Avatar": name, "X": float(c[0]), "Y": float(c[1]), "Z": round(float(c[2]), 1)})
            data_store["avatars"] = new_data
        return {"status": "ok"}
    except:
        return {"status": "error"}

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
