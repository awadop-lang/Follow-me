import gradio as gr
import pandas as pd
import plotly.express as px
import time
from fastapi import FastAPI, Request
import os
import uvicorn

# 1. Initialisation
app = FastAPI()
data_store = {"avatars": [], "last_packet_time": 0, "selected": None}

CSS = ".gradio-container {background-color: #020a0d !important; color: #00ffff !important; font-family: monospace;}"

# 2. Fonctions
def get_plot():
    now = time.time()
    conf = dict(
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(10,25,30,0.6)',
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(range=[0, 256], showgrid=True, gridcolor='rgba(0,255,255,0.1)', scaleanchor="y", scaleratio=1),
        yaxis=dict(range=[0, 256], showgrid=True, gridcolor='rgba(0,255,255,0.1)')
    )
    if data_store["last_packet_time"] == 0 or (now - data_store["last_packet_time"] > 15):
        fig = px.scatter(range_x=[0, 256], range_y=[0, 256])
        fig.update_layout(**conf)
        return fig, pd.DataFrame(columns=["Avatar", "Z"]), "🔴 OFFLINE"

    df = pd.DataFrame(data_store["avatars"])
    df["Color"] = ["#ff00ff" if n == data_store["selected"] else "#00ffff" for n in df["Avatar"]]
    fig = px.scatter(df, x="X", y="Y", text="Avatar", color="Color", color_discrete_map="identity")
    fig.update_layout(**conf)
    return fig, df[["Avatar", "Z"]], "🟢 SIGNAL ACTIVE"

def update_data(content):
    data_store["last_packet_time"] = time.time()
    new_data = []
    if content and content != "empty":
        for entry in content.split(";"):
            parts = entry.split("|")
            if len(parts) == 2:
                name, c = parts[0], parts[1].split(",")
                new_data.append({"Avatar": name, "X": float(c[0]), "Y": float(c[1]), "Z": round(float(c[2]), 1)})
    data_store["avatars"] = new_data
    return {"status": "ok"}

# 3. Interface
with gr.Blocks(css=CSS) as demo:
    gr.HTML("<h1 style='text-align:center;'>TACTICAL HUD v4.0</h1>")
    with gr.Row():
        radar = gr.Plot(show_label=False)
        with gr.Column():
            status = gr.Markdown("### 📡 MONITOR")
            table = gr.Dataframe(headers=["Avatar", "Z"], interactive=True)
    gr.Timer(3).tick(get_plot, outputs=[radar, table, status])

# 4. API et Montage
@app.post("/update")
async def update(request: Request):
    body = await request.body()
    return update_data(body.decode("utf-8"))

app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
