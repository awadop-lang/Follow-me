import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import time
from fastapi import FastAPI, Request
import os
import uvicorn

app = FastAPI()
# On ajoute 'selected' pour savoir quel avatar doit "flasher"
data_store = {"avatars": [], "last_packet_time": 0, "selected": None}

CSS = """
.gradio-container {background-color: #020a0d !important; color: #00ffff !important; font-family: 'Courier New', monospace;}
.main-title { text-shadow: 0 0 10px #00ffff; border-bottom: 2px solid #00ffff; padding-bottom: 10px; }
.stat-card { border: 1px solid #00ffff; padding: 10px; background: rgba(0,255,255,0.05); border-radius: 5px; }
/* Style pour rendre le tableau plus compact */
.table-container { font-size: 0.8em; }
"""

def get_radar_plot():
    now = time.time()
    fig = go.Figure()

    # Cercles de distance
    for r in [50, 100, 150, 200, 256]:
        fig.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, 
                      line=dict(color="rgba(0, 255, 255, 0.15)", width=1))

    status_text = "🟢 SIGNAL ACTIVE"
    # Préparation des données pour le tableau
    df_display = pd.DataFrame(columns=["Nom (Cliquer)", "X", "Y", "Z (Alt)"])

    if data_store["last_packet_time"] == 0 or (now - data_store["last_packet_time"] > 20):
        status_text = "🔴 OFFLINE"
        fig.add_annotation(text="WAITING FOR DATA...", x=0, y=0, showarrow=False, font=dict(size=20, color="red"))
    else:
        data = data_store["avatars"]
        if data:
            for d in data:
                # Calcul de la position relative au centre de la sim (128, 128)
                rel_x = d["X"] - 128
                rel_y = d["Y"] - 128
                
                # Effet de Flash : Si l'avatar est sélectionné, il devient Rose et plus gros
                is_selected = (d["Avatar"] == data_store["selected"])
                color = "#ff00ff" if is_selected else "#00ffff"
                size = 18 if is_selected else 12
                symbol = "diamond" if is_selected else "triangle-up"

                fig.add_trace(go.Scatter(
                    x=[rel_x], y=[rel_y],
                    mode='markers+text',
                    text=[d["Avatar"]],
                    textposition="top center",
                    marker=dict(size=size, color=color, symbol=symbol, 
                                line=dict(width=2, color="white" if is_selected else "rgba(0,0,0,0)")),
                    hoverinfo="text"
                ))
            
            # Remplissage du tableau avec coordonnées complètes
            df_display = pd.DataFrame([
                {"Nom (Cliquer)": d["Avatar"], "X": round(d["X"],1), "Y": round(d["Y"],1), "Z (Alt)": round(d["Z"],1)} 
                for d in data
            ])

    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(range=[-140, 140], visible=False),
        yaxis=dict(range=[-140, 140], visible=False, scaleanchor="x", scaleratio=1),
        showlegend=False, width=550, height=550
    )

    return fig, df_display, status_text

# Fonction déclenchée quand on clique sur une ligne du tableau
def on_select(evt: gr.SelectData):
    # evt.value contient le nom de l'avatar cliqué
    data_store["selected"] = evt.value
    return f"CIBLE VERROUILLÉE : {evt.value}"

with gr.Blocks(css=CSS) as demo:
    gr.HTML("<h1 class='main-title' style='text-align:center;'>🛰️ TACTICAL RADAR SYSTEM v4.5</h1>")
    
    with gr.Row():
        with gr.Column(scale=3):
            radar_map = gr.Plot(label="Local Scanner", show_label=False)
        
        with gr.Column(scale=2):
            with gr.Group(elem_classes="stat-card"):
                connection_status = gr.Markdown("🟢 Recherche de signal...")
                target_info = gr.Markdown("🎯 Cliquez sur un nom pour tracker")
            
            gr.Markdown("### 👥 LOCALISATION COMPLÈTE")
            # Le tableau devient interactif
            target_table = gr.Dataframe(
                headers=["Nom (Cliquer)", "X", "Y", "Z (Alt)"],
                interactive=False,
                elem_classes="table-container"
            )

    # Mise à jour automatique du radar
    gr.Timer(3).tick(get_radar_plot, outputs=[radar_map, target_table, connection_status])
    
    # Événement de clic sur le tableau
    target_table.select(on_select, outputs=target_info)

@app.post("/update")
async def update(request: Request):
    body = await request.body()
    content = body.decode("utf-8")
    data_store["last_packet_time"] = time.time()
    new_data = []
    if content and content != "empty":
        for entry in content.split(";"):
            parts = entry.split("|")
            if len(parts) == 2:
                name, coords = parts[0], parts[1].split(",")
                new_data.append({"Avatar": name, "X": float(coords[0]), "Y": float(coords[1]), "Z": float(coords[2])})
    data_store["avatars"] = new_data
    return {"status": "ok"}

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
