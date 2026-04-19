import gradio as gr
import pandas as pd
import time
from fastapi import FastAPI, Request
import os
import uvicorn

app = FastAPI()
data_store = {"avatars": [], "region": "Welcome Island", "last_packet_time": 0}

CSS = """
.gradio-container { background-color: #0d1117 !important; font-family: 'Inter', sans-serif !important; }
.glass-card { background: rgba(22, 27, 34, 0.8) !important; border: 1px solid #30363d !important; border-radius: 12px !important; padding: 15px !important; }
#map_container { height: 500px; width: 100%; border-radius: 8px; border: 1px solid #58a6ff; }
"""

def generate_map_html():
    now = time.time()
    if now - data_store["last_packet_time"] > 30:
        return "<div style='color:white; text-align:center; padding-top:100px;'>DÉCONNECTÉ : ACTIVEZ LE SCANNER DANS SL</div>"

    # Préparation des marqueurs JavaScript
    markers_js = ""
    for a in data_store["avatars"]:
        # Conversion simplifiée pour l'affichage (Leaflet utilise un système de tuiles spécifique pour SL)
        markers_js += f"L.marker([{a['Y']}, {a['X']}]).addTo(map).bindPopup('{a['Avatar']} (Alt: {a['Z']})');"

    # HTML avec Leaflet.js configuré pour les serveurs de Linden Lab
    html_content = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <div id="map_container"></div>
    <script>
        var map = L.map('map_container', {{
            crs: L.CRS.Simple,
            minZoom: -2,
            maxZoom: 2
        }});

        // URL des tuiles de la carte Second Life
        var slTileUrl = 'https://map.secondlife.com/map-1-{data_store['region'].replace(' ', '%20')}-{{z}}-{{x}}-{{y}}-objects.jpg';
        
        L.tileLayer(slTileUrl, {{
            attribution: 'Linden Lab',
            continuousWorld: true
        }}).addTo(map);

        map.setView([128, 128], 0);
        {markers_js}
    </script>
    """
    return html_content

def update_ui():
    status = "🟢 " + data_store["region"] if time.time() - data_store["last_packet_time"] < 30 else "🔴 HORS LIGNE"
    df = pd.DataFrame(data_store["avatars"]) if data_store["avatars"] else pd.DataFrame(columns=["Avatar", "Z"])
    return generate_map_html(), df, status

with gr.Blocks(css=CSS) as demo:
    gr.HTML("<h1 style='color:white; text-align:center;'>SL TACTICAL LIVE MAP</h1>")
    
    with gr.Row():
        with gr.Column(scale=3, elem_classes="glass-card"):
            map_view = gr.HTML(value=generate_map_html)
            
        with gr.Column(scale=2):
            with gr.Group(elem_classes="glass-card"):
                connection_status = gr.Markdown("🔴 EN ATTENTE")
                target_table = gr.Dataframe(headers=["Avatar", "X", "Y", "Z"], interactive=False)

    gr.Timer(3).tick(update_ui, outputs=[map_view, target_table, connection_status])

@app.post("/update")
async def update(request: Request):
    body = await request.body()
    content = body.decode("utf-8")
    data_store["last_packet_time"] = time.time()
    
    # Format attendu : "Nom Region:Nom|X,Y,Z;Nom2|X,Y,Z"
    if ":" in content:
        reg, avs = content.split(":")
        data_store["region"] = reg
        new_data = []
        if avs != "empty":
            for entry in avs.split(";"):
                parts = entry.split("|")
                if len(parts) == 2:
                    name, c = parts[0], parts[1].split(",")
                    new_data.append({"Avatar": name, "X": float(c[0]), "Y": float(c[1]), "Z": float(c[2])})
        data_store["avatars"] = new_data
    return {"status": "ok"}

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
