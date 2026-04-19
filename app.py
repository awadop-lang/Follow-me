import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import time
from fastapi import FastAPI, Request
import os
import uvicorn

app = FastAPI()
data_store = {"avatars": [], "last_packet_time": 0, "selected": None}

# CSS MODERNE - Formaté pour éviter les erreurs d'indentation
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
.gradio-container { background-color: #0d1117 !important; font-family: 'Inter', sans-serif !important; color: #c9d1d9 !important; }
.main-title { font-weight: 600; font-size: 2em; color: #f0f6fc; margin-bottom: 20px; text-align: center; }
.glass-card { background: rgba(22, 27, 34, 0.7); border: 1px solid rgba(48, 54, 61, 0.8); border-radius: 12px; padding: 20px; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5); backdrop-filter: blur(10px); }
.table-container { font-size: 0.9em; border-radius: 8px; }
.selected-label { color: #58a6ff; font-weight: 600; }
"""

def get_radar_plot():
    now = time.time()
    fig = go.Figure()

    # Cercles de distance
    for r in [50, 100, 150, 200]:
        fig.add_shape(type="circle", xref="x", yref="y", x0=-r, y0=-r, x1=r, y1=r, 
                      line=dict(color="rgba(48, 54, 61, 0.4)", width=1, dash='dot'))

    status_text = "🟢 SIGNAL ACTIF"
    df_display = pd.DataFrame(columns=["Nom", "X", "Y", "Alt"])

    if data_store["last_packet_time"] == 0 or (now - data_store["last_packet_time"] > 25):
        status_text = "🔴 HORS LIGNE"
        fig.add_annotation(text="ATTENTE SIGNAL...", x=0, y=0, showarrow=False, font=dict(color="#8b949e"))
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
        xaxis=dict(range=[-140, 140], visible=False),
        yaxis=dict(range=[-140, 140], visible=False, scaleanchor="x", scaleratio=1),
        showlegend=False, width=500, height=500
    )
    return fig, df_display, status_text

def on_select(evt: gr.SelectData):
    data_store["selected"] = evt.value
    return f"SUIVI : <span class='selected-label'>{evt.value}</span>"

with gr.Blocks(css=CSS) as demo:
    gr.HTML("<h1 class='main-title'>🛰️ SCANNER TACTIQUE</h1>")
    with gr.Row():
        with gr.Column(scale=3, elem_classes="glass-card"):
            radar_map = gr.Plot(show_label=False)
        with gr.Column(scale=2):
            with gr.Group(elem_classes="glass-card"):
                connection_status = gr.Markdown("🟢 SIGNAL ACTIF")
                target_info = gr.HTML("🎯 <i>Cliquez sur un nom pour tracker</i>")
            gr.HTML("<br>")
            target_table = gr.Dataframe(headers=["Nom", "X", "Y", "Alt"], interactive=False, elem_classes="table-container")

    gr.Timer(3).tick(get_radar_plot, outputs=[radar_map, target_table, connection_status])
    target_table.select(on_select, outputs=target_info)

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
                    new_data.append({"Avatar": name, "X": float(coords[0]), "Y": float(coords[1]), "Z": float(coords[2])})
        data_store["avatars"] = new_data
        return {"status": "ok"}
    except:
        return {"status": "error"}

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
