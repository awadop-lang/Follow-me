import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import time
from fastapi import FastAPI, Request
import os
import uvicorn

app = FastAPI()
data_store = {"avatars": [], "last_packet_time": 0, "selected": None}

# CSS SIMPLIFIÉ MAIS ULTRA-PRIORITAIRE (!important partout)
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

/* Fond et Police */
body, .gradio-container {
    background-color: #0d1117 !important;
    font-family: 'Inter', sans-serif !important;
}

/* Cartes Glassmorphism */
.glass-card {
    background: rgba(22, 27, 34, 0.8) !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
    padding: 20px !important;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
}

/* Titre Épuré */
.main-title {
    color: #f0f6fc !important;
    font-weight: 600 !important;
    letter-spacing: -1px !important;
    text-align: center !important;
}

/* Suppression des éléments Gradio inutiles */
footer {display: none !important;}
.min-h-\[4rem\] {display: none !important;}
"""

def get_radar_plot():
    now = time.time()
    fig = go.Figure()

    # Cercles radar grisés
    for r in [50, 100, 150, 200, 250]:
        fig.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, 
                      line=dict(color="rgba(139, 148, 158, 0.2)", width=1))

    status_text = "🟢 SCANNER ACTIF"
    df_display = pd.DataFrame(columns=["Nom", "X", "Y", "Alt"])

    if data_store["last_packet_time"] == 0 or (now - data_store["last_packet_time"] > 30):
        status_text = "🔴 HORS LIGNE"
        fig.add_annotation(text="SIGNAL PERDU", x=0, y=0, showarrow=False, font=dict(color="#8b949e"))
    else:
        data = data_store["avatars"]
        if data:
            for d in data:
                rel_x = d["X"] - 128
                rel_y = d["Y"] - 128
                is_sel = (d["Avatar"] == data_store["selected"])
                
                fig.add_trace(go.Scatter(
                    x=[rel_x], y=[rel_y], mode='markers',
                    marker=dict(size=14 if is_sel else 10, color="#58a6ff" if is_sel else "#f0f6fc",
                                line=dict(width=2 if is_sel else 0, color="white")),
                    text=[d["Avatar"]], hoverinfo="text"
                ))
            
            df_display = pd.DataFrame([
                {"Nom": d["Avatar"], "X": round(d["X"],1), "Y": round(d["Y"],1), "Alt": round(d["Z"],1)} 
                for d in data
            ])

    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(range=[-140, 140], visible=False, fixedrange=True),
        yaxis=dict(range=[-140, 140], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1),
        showlegend=False
    )
    return fig, df_display, status_text

def on_select(evt: gr.SelectData):
    data_store["selected"] = evt.value
    return f"🎯 **CIBLE : {evt.value}**"

# --- UTILISATION D'UN THÈME SOBRE PAR DÉFAUT ---
with gr.Blocks(css=CSS, theme=gr.themes.Soft(primary_hue="blue", font=[gr.themes.GoogleFont("Inter")])) as demo:
    gr.HTML("<h1 class='main-title'>TACTICAL SCANNER</h1>")
    
    with gr.Row():
        with gr.Column(scale=3, elem_classes="glass-card"):
            radar_map = gr.Plot(show_label=False)
            
        with gr.Column(scale=2):
            with gr.Group(elem_classes="glass-card"):
                connection_status = gr.Markdown("🟢 ATTENTE...")
                target_info = gr.Markdown("🎯 *Sélectionnez un nom*")
            
            gr.HTML("<div style='margin-bottom:20px;'></div>")
            
            with gr.Group(elem_classes="glass-card"):
                target_table = gr.Dataframe(
                    headers=["Nom", "X", "Y", "Alt"],
                    interactive=False
                )

    gr.Timer(3).tick(get_radar_plot, outputs=[radar_map, target_table, connection_status])
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
