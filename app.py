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
.glass-card { background: #161b22 !important; border: 1px solid #30363d !important; border-radius: 12px; padding: 15px; }
#radar_bg { 
    width: 512px; height: 512px; 
    margin: 0 auto; 
    border: 2px solid #58a6ff; 
    position: relative; 
    background-size: contain;
    background-repeat: no-repeat;
    background-color: #000;
}
.dot { 
    position: absolute; 
    width: 12px; height: 12px; 
    background: #00ffff; 
    border: 2px solid white; 
    border-radius: 50%; 
    transform: translate(-50%, -50%);
    box-shadow: 0 0 10px #00ffff;
}
.label { 
    position: absolute; 
    color: white; 
    font-size: 10px; 
    white-space: nowrap; 
    background: rgba(0,0,0,0.6); 
    padding: 2px 5px; 
    border-radius: 4px;
    transform: translate(-50%, -25px);
}
"""

def get_map_view():
    now = time.time()
    if now - data_store["last_packet_time"] > 60:
        return "<div style='color:#8b949e; text-align:center; padding-top:200px;'>📡 ATTENTE SIGNAL...</div>"

    reg_url = data_store["region"].replace(" ", "%20")
    # On utilise l'image globale de la sim (une seule image de 256x256 étirée)
    map_img = f"https://map.secondlife.com/map-1-{reg_url}-1-128-128-objects.jpg"
    
    dots_html = ""
    for a in data_store["avatars"]:
        # Conversion coordonnées SL (0-256) vers Pixels (0-512)
        left = (a['X'] / 256) * 512
        # Inversion de l'axe Y (SL : 0 en bas, HTML : 0 en haut)
        top = 512 - ((a['Y'] / 256) * 512)
        
        dots_html += f"""
        <div class="dot" style="left: {left}px; top: {top}px;"></div>
        <div class="label" style="left: {left}px; top: {top}px;">{a['Avatar']}</div>
        """

    return f"""
    <div id="radar_bg" style="background-image: url('{map_img}');">
        {dots_html}
    </div>
    """

def update_ui():
    now = time.time()
    online = (now - data_store["last_packet_time"] < 60)
    status = f"🟢 RÉGION : {data_store['region']}" if online else "🔴 SCANNER OFFLINE"
    df = pd.DataFrame(data_store["avatars"]) if data_store["avatars"] else pd.DataFrame(columns=["Avatar", "X", "Y", "Z"])
    return get_map_view(), df, status

with gr.Blocks(css=CSS) as demo:
    gr.HTML("<h1 style='text-align:center; color:#f0f6fc;'>🛰️ SL TACTICAL LIVE MAP</h1>")
    with gr.Row():
        with gr.Column(scale=3, elem_classes="glass-card"):
            map_display = gr.HTML(get_map_view)
        with gr.Column(scale=2):
            with gr.Group(elem_classes="glass-card"):
                connection_status = gr.Markdown("🔴 INITIALISATION")
                target_table = gr.Dataframe(headers=["Avatar", "X", "Y", "Z"], interactive=False)

    gr.Timer(4).tick(update_ui, outputs=[map_display, target_table, connection_status])

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
