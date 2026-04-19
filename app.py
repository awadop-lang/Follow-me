import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import time
from fastapi import FastAPI, Request
import os
import uvicorn

# Initialisation de l'application
app = FastAPI()
data_store = {"avatars": [], "last_packet_time": 0, "selected": None}

# --- STYLE CSS MODERNE & SOBRE ---
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

.gradio-container {
    background-color: #0d1117 !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    color: #c9d1d9 !important;
}

.main-title {
    font-weight: 600 !important;
    font-size: 2rem !important;
    color: #f0f6fc !important;
    margin-bottom: 20px !important;
    text-align: center;
}

.glass-card {
    background: rgba(22, 27, 34, 0.7) !important;
    border: 1px solid rgba(48, 54, 61, 0.8) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
    backdrop-filter: blur(12px) !important;
}

.table-container {
    border-radius: 12px !important;
    overflow: hidden !important;
    background: rgba(22, 27, 34, 0.5) !important;
}

.selected-label {
    color: #58a6ff !important;
    font-weight: 600 !important;
    text-shadow: 0 0 10px rgba(88, 166, 255, 0.4);
}

footer {display: none !important;} /* Cache le footer Gradio pour plus de sobriété */
"""

def get_radar_plot():
    now = time.time()
    fig = go.Figure()

    # Cercles de distance sobres (style radar moderne)
    for r in [50, 100, 150, 200, 250]:
        fig.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, 
                      line=dict(color="rgba(139, 148, 158, 0.2)", width=1, dash='solid'))

    # Croix centrale
    fig.add_shape(type="line", x0=-256, y0=0, x1=256, y1=0, line=dict(color="rgba(139, 148, 158, 0.1)", width=1))
    fig.add_shape(type="line", x0=0, y0=-256, x1=0, y1=256, line=dict(color="rgba(139, 148, 158, 0.1)", width=1))

    status_text = "🟢 SYSTÈME ACTIF"
    df_display = pd.DataFrame(columns=["Nom", "X", "Y", "Altitude"])

    # Vérification du timeout (30 secondes)
    if data_store["last_packet_time"] == 0 or (now - data_store["last_packet_time"] > 30):
        status_text = "🔴 HORS LIGNE (ATTENTE SIGNAL)"
        fig.add_annotation(text="NO SIGNAL DETECTED", x=0, y=0, showarrow=False, font=dict(size=14, color="#8b949e"))
    else:
        data = data_store["avatars"]
        if data:
            for d in data:
                # Calcul position relative (centré sur 128,128)
                rel_x = d["X"] - 128
                rel_y = d["Y"] - 128
                
                is_selected = (d["Avatar"] == data_store["selected"])
                color = "#58a6ff" if is_selected else "#f0f6fc"
                size = 14 if is_selected else 10
                
                # Points radar
                fig.add_trace(go.Scatter(
                    x=[rel_x], y=[rel_y], mode='markers',
                    marker=dict(size=size, color=color, line=dict(width=2 if is_selected else 0, color="white")),
                    text=[d["Avatar"]], hoverinfo="text"
                ))
            
            # Mise à jour du tableau
            df_display = pd.DataFrame([
                {"Nom": d["Avatar"], "X": round(d["X"],1), "Y": round(d["Y"],1), "Altitude": round(d["Z"],1)} 
                for d in data
            ])

    fig.update_layout(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(range=[-140, 140], visible=False, fixedrange=True),
        yaxis=dict(range=[-140, 140], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1),
        showlegend=False, dragmode=False
    )
    return fig, df_display, status_text

def on_select(evt: gr.SelectData):
    data_store["selected"] = evt.value
    return f"TRAQUAGE EN COURS : <span class='selected-label'>{evt.value}</span>"

# --- INTERFACE GRADIO ---
with gr.Blocks(css=CSS, theme=gr.themes.Default(primary_hue="blue", secondary_hue="slate")) as demo:
    gr.HTML("<h1 class='main-title'>LOCAL SCANNER SYSTEM</h1>")
    
    with gr.Row():
        # Carte Radar
        with gr.Column(scale=3, elem_classes="glass-card"):
            radar_map = gr.Plot(show_label=False)
            
        # Panneau Latéral
        with gr.Column(scale=2):
            with gr.Group(elem_classes="glass-card"):
                connection_status = gr.Markdown("🟢 INITIALISATION...")
                target_info = gr.HTML("<span style='color:#8b949e;'>🎯 Sélectionnez une cible dans le tableau</span>")
            
            gr.HTML("<div style='margin-top:20px;'></div>") # Espacement
            
            with gr.Group(elem_classes="glass-card"):
                gr.Markdown("### 👥 MEMBRES DÉTECTÉS")
                target_table = gr.Dataframe(
                    headers=["Nom", "X", "Y", "Altitude"],
                    interactive=False,
                    elem_classes="table-container"
                )

    # Automatisation
    gr.Timer(3).tick(get_radar_plot, outputs=[radar_map, target_table, connection_status])
    target_table.select(on_select, outputs=target_info)

# --- API FASTAPI (Réception des données) ---
@app.post("/update")
async def update(request: Request):
    try:
        body = await request.body()
        content = body.decode("utf-8")
        data_store["last_packet_time"] = time.time()
        
        new_data = []
        if content and content != "empty":
            for entry in content.split(";"):
                parts = entry.split("|")
                if len(parts) == 2:
                    name, coords = parts[0], parts[1].split(",")
                    new_data.append({
                        "Avatar": name, 
                        "X": float(coords[0]), 
                        "Y": float(coords[1]), 
                        "Z": float(coords[2])
                    })
        data_store["avatars"] = new_data
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Montage Gradio sur FastAPI
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
